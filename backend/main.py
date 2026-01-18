from fastapi import FastAPI, Depends, HTTPException, status, Body
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

print("Creating tables if not exist...")
Base.metadata.create_all(bind=engine)
print("Database ready.")

app = FastAPI(title="Secure Share Backend")


@app.get("/")
def root():
    return {"message": "Secure Share Backend is running"}


# ────────────────────────────────────────────────
#   Authentication
# ────────────────────────────────────────────────

@app.post("/auth/register", response_model=schemas.Token)
def register(user: schemas.UserRegister, db: Session = Depends(get_db)):
    try:
        if crud.get_user(db, user.username):
            raise HTTPException(status_code=400, detail="Username already registered")

        salt_b = base64.urlsafe_b64decode(user.salt + '==')
        priv_enc_b = base64.urlsafe_b64decode(user.private_key_enc + '==')

        hashed = auth.get_password_hash(user.password)

        new_user = models.User(
            username=user.username,
            password_hash=hashed,
            salt=salt_b,
            private_key_enc=priv_enc_b,
            public_key_pem=user.public_key_pem
        )

        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        token = auth.create_access_token(
            data={"sub": new_user.username},
            expires_delta=timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
        )

        return {"access_token": token, "token_type": "bearer"}

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")


@app.post("/auth/login", response_model=schemas.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = crud.get_user(db, form_data.username)
    if not user or not auth.verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Incorrect username or password")

    token = auth.create_access_token(
        data={"sub": user.username},
        expires_delta=timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return {"access_token": token, "token_type": "bearer"}


# ────────────────────────────────────────────────
#   Users
# ────────────────────────────────────────────────

@app.get("/users")
def get_users(db: Session = Depends(get_db)):
    """List all usernames (for recipient selection in frontend)"""
    return [row[0] for row in db.query(models.User.username).all()]


@app.get("/users/me/private")
def get_my_private_info(
    current_user: str = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    user = crud.get_user(db, current_user)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {
        "salt": base64.urlsafe_b64encode(user.salt).decode('ascii'),
        "private_key_enc": base64.urlsafe_b64encode(user.private_key_enc).decode('ascii')
    }


@app.get("/users/me/public-key")
def get_my_public_key(
    current_user: str = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's public key for certificate display"""
    print(f"DEBUG: Looking for user: '{current_user}' (type: {type(current_user)})")
    user = crud.get_user(db, current_user)
    print(f"DEBUG: User found: {user is not None}")
    if user:
        print(f"DEBUG: User object: username={user.username}")
    if not user:
        raise HTTPException(status_code=404, detail=f"User not found: {current_user}")
    return {"public_key_pem": user.public_key_pem}


@app.get("/users/{username}/public-key")
def get_public_key(username: str, db: Session = Depends(get_db)):
    user = crud.get_user(db, username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"public_key_pem": user.public_key_pem}


# ────────────────────────────────────────────────
#   Files - Upload / Share
# ────────────────────────────────────────────────

@app.post("/files")
def upload_file(
    filename: str = Body(...),
    encrypted_content: str = Body(...),
    signature: str = Body(...),
    file_hash: str = Body(...),
    recipients: List[str] = Body(...),
    encrypted_keys: Dict[str, str] = Body(...),
    current_user: str = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    try:
        file_id = str(uuid4())

        enc_content_b = base64.urlsafe_b64decode(encrypted_content + '==')
        sig_b = base64.urlsafe_b64decode(signature + '==')

        db_file = models.SharedFile(
            file_id=file_id,
            filename=filename,
            owner=current_user,
            file_data=enc_content_b,
            signature=sig_b,
            file_hash=file_hash
        )
        db.add(db_file)
        db.commit()
        db.refresh(db_file)

        # Store encrypted symmetric key for each recipient (including owner)
        for recipient, key_b64 in encrypted_keys.items():
            key_b = base64.urlsafe_b64decode(key_b64 + '==')
            db_perm = models.FilePermission(
                file_id=file_id,
                recipient=recipient,
                encrypted_sym_key=key_b
            )
            db.add(db_perm)

        db.commit()
        return {"status": "success", "file_id": file_id}

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"File upload failed: {str(e)}")


# ────────────────────────────────────────────────
#   Files - List
# ────────────────────────────────────────────────

@app.get("/files")
def list_files(
    current_user: str = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    files = crud.get_user_files(db, current_user)
    return [
        {
            "file_id": f.file_id,
            "filename": f.filename,
            "owner": f.owner,
            "signature": base64.urlsafe_b64encode(f.signature).decode('ascii'),
            "file_hash": f.file_hash,
            "timestamp": f.timestamp.isoformat() if f.timestamp else None
        }
        for f in files
    ]


# ────────────────────────────────────────────────
#   Files - Download
# ────────────────────────────────────────────────

@app.get("/files/{file_id}")
def get_file(
    file_id: str,
    current_user: str = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    file_row, perm_row = crud.get_file_with_permission(db, file_id, current_user)
    if not file_row or (not perm_row and file_row.owner != current_user):
        raise HTTPException(status_code=404, detail="File not found or access denied")

    return {
        "file_data": base64.urlsafe_b64encode(file_row.file_data).decode('ascii'),
        "signature": base64.urlsafe_b64encode(file_row.signature).decode('ascii'),
        "encrypted_sym_key": base64.urlsafe_b64encode(perm_row.encrypted_sym_key).decode('ascii')
            if perm_row else None,
        "file_hash": file_row.file_hash,
        "owner": file_row.owner,
        "timestamp": file_row.timestamp.isoformat() if file_row.timestamp else None
    }


# ────────────────────────────────────────────────
#   Files - Delete (only owner)
# ────────────────────────────────────────────────

@app.delete("/files/{file_id}")
def delete_file(
    file_id: str,
    current_user: str = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    file_row = crud.get_file_by_id(db, file_id)
    if not file_row:
        raise HTTPException(status_code=404, detail="File not found")

    if file_row.owner != current_user:
        raise HTTPException(status_code=403, detail="Only the file owner can delete this file")

    # Delete all associated permissions first
    db.query(models.FilePermission).filter(models.FilePermission.file_id == file_id).delete()
    # Then delete the file record
    db.delete(file_row)
    db.commit()

    return {"status": "file deleted", "file_id": file_id}


# ────────────────────────────────────────────────
#   Files - Revoke access for one user (only owner)
# ────────────────────────────────────────────────

@app.delete("/files/{file_id}/access/{target_username}")
def revoke_access(
    file_id: str,
    target_username: str,
    current_user: str = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    file_row = crud.get_file_by_id(db, file_id)
    if not file_row:
        raise HTTPException(status_code=404, detail="File not found")

    if file_row.owner != current_user:
        raise HTTPException(status_code=403, detail="Only the file owner can revoke access")

    if target_username == current_user:
        raise HTTPException(status_code=400, detail="Cannot revoke your own access — delete the file instead")

    perm = crud.get_file_permission(db, file_id, target_username)
    if not perm:
        raise HTTPException(status_code=404, detail=f"No access found for user {target_username}")

    db.delete(perm)
    db.commit()

    return {"status": "access revoked", "user": target_username, "file_id": file_id}