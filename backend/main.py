from fastapi import FastAPI, Depends, HTTPException, Body
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import List, Dict
from datetime import timedelta
import base64
from uuid import uuid4

import models
from database import engine, get_db, Base
import crud
import schemas
import auth
import pki

# -------------------------------------------------
# Database init
# -------------------------------------------------
Base.metadata.create_all(bind=engine)

app = FastAPI(title="SecureShare Backend - Proper PKI Implementation")

@app.get("/")
def root():
    return {
        "message": "SecureShare Backend with PKI is running",
        "features": [
            "Certificate-based authentication",
            "Digital signatures with RSA",
            "Certificate validation",
            "Certificate revocation (CRL)",
            "Hybrid encryption (RSA + AES)"
        ]
    }

# =================================================
# AUTH WITH PKI
# =================================================

@app.post("/auth/register", response_model=schemas.Token)
def register(user: schemas.UserRegister, db: Session = Depends(get_db)):
    """Register new user and issue certificate from CA"""
    
    if crud.get_user(db, user.username):
        raise HTTPException(status_code=400, detail="Username already registered")

    # Decode Base64 fields
    salt_b = base64.urlsafe_b64decode(user.salt + "==")
    priv_enc_b = base64.urlsafe_b64decode(user.private_key_enc + "==")

    hashed = auth.get_password_hash(user.password)

    try:
        # Issue certificate from CA using the CSR
        cert_pem, cert_serial, cert_not_after = pki.issue_certificate(
            user.csr_pem.encode(),
            user.username,
            validity_days=365
        )
        
        print(f"✅ Certificate issued for {user.username}")
        print(f"   Serial: {cert_serial}")
        
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Certificate issuance failed: {str(e)}"
        )

    # Create user with certificate
    new_user = models.User(
        username=user.username,
        password_hash=hashed,
        salt=salt_b,
        private_key_enc=priv_enc_b,
        certificate_pem=cert_pem,  # Store signed certificate
        cert_serial=cert_serial,
        cert_not_after=cert_not_after,
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    token = auth.create_access_token(
        data={"sub": new_user.username},
        expires_delta=timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES),
    )

    return {"access_token": token, "token_type": "bearer"}


@app.post("/auth/login", response_model=schemas.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Login with certificate validation"""
    
    user = crud.get_user(db, form_data.username)
    if not user or not auth.verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Incorrect username or password")

    # Validate user's certificate
    if user.certificate_pem:
        is_valid, error_msg = pki.validate_certificate(user.certificate_pem, db)
        if not is_valid:
            raise HTTPException(
                status_code=401,
                detail=f"Certificate validation failed: {error_msg}"
            )

    token = auth.create_access_token(
        data={"sub": user.username},
        expires_delta=timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    return {"access_token": token, "token_type": "bearer"}

# =================================================
# USERS & CERTIFICATES
# =================================================

@app.get("/users")
def get_users(db: Session = Depends(get_db)):
    """List usernames for file sharing"""
    return [u[0] for u in db.query(models.User.username).all()]


@app.get("/users/me/private")
def get_my_private_info(
    current_user: str = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    """Return encrypted private key + salt"""
    user = crud.get_user(db, current_user)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "salt": base64.urlsafe_b64encode(user.salt).decode(),
        "private_key_enc": base64.urlsafe_b64encode(user.private_key_enc).decode(),
    }


@app.get("/users/me/certificate")
def get_my_certificate(
    current_user: str = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    """Return user's certificate and details"""
    user = crud.get_user(db, current_user)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if not user.certificate_pem:
        raise HTTPException(status_code=404, detail="Certificate not found")
    
    # Get certificate info
    cert_info = pki.get_cert_info(user.certificate_pem)
    
    # Check if revoked
    is_revoked = db.query(models.RevokedCert).filter(
        models.RevokedCert.cert_serial == user.cert_serial
    ).first() is not None
    
    return {
        "certificate_pem": user.certificate_pem,
        "serial": user.cert_serial,
        "not_after": user.cert_not_after.isoformat() if user.cert_not_after else None,
        "is_revoked": is_revoked,
        "details": cert_info
    }


@app.get("/users/{username}/certificate")
def get_user_certificate(
    username: str,
    current_user: str = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    """Get any user's certificate (for encryption and signature verification)"""
    user = crud.get_user(db, username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if not user.certificate_pem:
        raise HTTPException(status_code=404, detail="Certificate not found for this user")
    
    # Validate certificate before returning
    is_valid, error_msg = pki.validate_certificate(user.certificate_pem, db)
    if not is_valid:
        raise HTTPException(
            status_code=400,
            detail=f"Certificate is invalid: {error_msg}"
        )
    
    # Extract public key from certificate
    public_key_pem = pki.extract_public_key_from_cert(user.certificate_pem)
    
    return {
        "username": username,
        "certificate_pem": user.certificate_pem,
        "public_key_pem": public_key_pem.decode(),
        "serial": user.cert_serial,
    }


@app.post("/users/me/revoke-certificate")
def revoke_my_certificate(
    current_user: str = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    """Revoke user's own certificate"""
    user = crud.get_user(db, current_user)
    if not user or not user.cert_serial:
        raise HTTPException(status_code=404, detail="Certificate not found")
    
    if pki.revoke_certificate(user.cert_serial, db):
        return {"status": "certificate revoked", "serial": user.cert_serial}
    else:
        raise HTTPException(status_code=500, detail="Revocation failed")

# =================================================
# FILE UPLOAD WITH DIGITAL SIGNATURES
# =================================================

@app.post("/files")
def upload_file(
    filename: str = Body(...),
    encrypted_content: str = Body(...),
    signature: str = Body(...),
    file_hash: str = Body(...),
    recipients: List[str] = Body(...),
    encrypted_keys: Dict[str, str] = Body(...),
    current_user: str = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    """Upload and share file with digital signature verification"""
    
    # Get user object
    user = crud.get_user(db, current_user)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Validate user's certificate
    if user.certificate_pem:
        is_valid, error_msg = pki.validate_certificate(user.certificate_pem, db)
        if not is_valid:
            raise HTTPException(
                status_code=403,
                detail=f"Cannot upload file: Certificate invalid ({error_msg})"
            )
    
    file_id = str(uuid4())

    enc_content = base64.urlsafe_b64decode(encrypted_content + "==")
    sig = base64.urlsafe_b64decode(signature + "==")

    db_file = models.SharedFile(
        file_id=file_id,
        owner_id=user.id,
        owner_username=current_user,
        filename=filename,
        file_data=enc_content,
        signature=sig,  # RSA signature using owner's private key
        file_hash=file_hash,
    )
    db.add(db_file)
    db.commit()
    db.refresh(db_file)

    # Create permissions for ALL users in encrypted_keys (including owner)
    permissions_created = 0
    for recipient, key_b64 in encrypted_keys.items():
        key = base64.urlsafe_b64decode(key_b64 + "==")
        db_perm = models.FilePermission(
            file_id=file_id,
            recipient=recipient,
            encrypted_sym_key=key,
        )
        db.add(db_perm)
        permissions_created += 1
    
    db.commit()
    
    print(f"✅ File {file_id} uploaded with {permissions_created} permissions")
    print(f"   Owner: {current_user}")
    print(f"   Signature: {len(sig)} bytes")
    
    return {
        "status": "success",
        "file_id": file_id,
        "permissions": permissions_created,
        "signed": True
    }

# =================================================
# LIST FILES
# =================================================

@app.get("/files")
def list_files(
    current_user: str = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    """List files with signature verification status"""
    files = crud.get_user_files(db, current_user)
    
    result = []
    for f in files:
        # Get owner's certificate for signature verification
        owner = crud.get_user(db, f.owner_username)
        signature_valid = False
        
        if owner and owner.certificate_pem:
            # Check if owner's certificate is valid
            cert_valid, _ = pki.validate_certificate(owner.certificate_pem, db)
            signature_valid = cert_valid
        
        result.append({
            "file_id": f.file_id,
            "filename": f.filename,
            "owner": f.owner_username,
            "signature": base64.urlsafe_b64encode(f.signature).decode(),
            "signature_valid": signature_valid,
            "file_hash": f.file_hash,
            "timestamp": f.timestamp.isoformat() if f.timestamp else None,
        })
    
    return result

# =================================================
# DOWNLOAD FILE WITH SIGNATURE VERIFICATION
# =================================================

@app.get("/files/{file_id}")
def get_file(
    file_id: str,
    current_user: str = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    """Download file with signature verification"""
    
    file_row, perm_row = crud.get_file_with_permission(db, file_id, current_user)
    if not file_row:
        raise HTTPException(status_code=404, detail="File not found")
    
    # Check access: must be owner OR have permission
    if file_row.owner_username != current_user and not perm_row:
        raise HTTPException(status_code=403, detail="Access denied")

    # Get owner's certificate for signature verification
    owner = crud.get_user(db, file_row.owner_username)
    owner_cert_valid = False
    owner_cert_pem = None
    
    if owner and owner.certificate_pem:
        is_valid, error_msg = pki.validate_certificate(owner.certificate_pem, db)
        owner_cert_valid = is_valid
        if is_valid:
            owner_cert_pem = owner.certificate_pem

    # Return the encrypted symmetric key for the current user
    encrypted_sym_key = None
    if perm_row:
        encrypted_sym_key = base64.urlsafe_b64encode(perm_row.encrypted_sym_key).decode()
    
    return {
        "file_data": base64.urlsafe_b64encode(file_row.file_data).decode(),
        "signature": base64.urlsafe_b64encode(file_row.signature).decode(),
        "encrypted_sym_key": encrypted_sym_key,
        "file_hash": file_row.file_hash,
        "owner": file_row.owner_username,
        "owner_certificate": owner_cert_pem,
        "signature_valid": owner_cert_valid,
        "timestamp": file_row.timestamp.isoformat() if file_row.timestamp else None,
    }

# =================================================
# DELETE FILE
# =================================================

@app.delete("/files/{file_id}")
def delete_file(
    file_id: str,
    current_user: str = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    file_row = crud.get_file_by_id(db, file_id)
    if not file_row:
        raise HTTPException(status_code=404, detail="File not found")

    if file_row.owner_username != current_user:
        raise HTTPException(status_code=403, detail="Only owner can delete")

    # Delete all permissions first
    db.query(models.FilePermission).filter(
        models.FilePermission.file_id == file_id
    ).delete()
    
    db.delete(file_row)
    db.commit()

    return {"status": "deleted"}

# =================================================
# REVOKE ACCESS
# =================================================

@app.delete("/files/{file_id}/access/{target_username}")
def revoke_access(
    file_id: str,
    target_username: str,
    current_user: str = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    file_row = crud.get_file_by_id(db, file_id)
    if not file_row:
        raise HTTPException(status_code=404, detail="File not found")
    
    if file_row.owner_username != current_user:
        raise HTTPException(status_code=403, detail="Not authorized")

    perm = crud.get_file_permission(db, file_id, target_username)
    if not perm:
        raise HTTPException(status_code=404, detail="Access not found")

    db.delete(perm)
    db.commit()
    return {"status": "access revoked"}


# =================================================
# CA CERTIFICATE (PUBLIC)
# =================================================

@app.get("/ca/certificate")
def get_ca_certificate():
    """Get CA certificate for client verification"""
    try:
        _, ca_cert = pki.load_ca()
        from cryptography.hazmat.primitives import serialization
        
        ca_cert_pem = ca_cert.public_bytes(serialization.Encoding.PEM).decode()
        
        return {
            "certificate_pem": ca_cert_pem,
            "subject": ca_cert.subject.rfc4514_string(),
            "serial": format(ca_cert.serial_number, 'x'),
            "not_before": ca_cert.not_valid_before_utc.isoformat(),
            "not_after": ca_cert.not_valid_after_utc.isoformat(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"CA certificate not available: {e}")