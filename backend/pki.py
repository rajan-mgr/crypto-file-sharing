# backend/pki.py
"""
Public Key Infrastructure (PKI) module for SecureShare
Handles certificate issuance, validation, and revocation
"""

import os
from datetime import datetime, timedelta, timezone
from cryptography import x509
from cryptography.x509.oid import NameOID, ExtensionOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from typing import Tuple, Optional
from sqlalchemy.orm import Session
import models


def load_ca() -> Tuple[rsa.RSAPrivateKey, x509.Certificate]:
    """Load CA private key and certificate"""
    ca_key_path = os.getenv("CA_KEY_PATH", "./pki/ca.key")
    ca_cert_path = os.getenv("CA_CERT_PATH", "./pki/ca.crt")
    
    if not os.path.exists(ca_key_path):
        raise FileNotFoundError(
            f"CA private key not found at {ca_key_path}. "
            "Run 'python setup_ca.py' first!"
        )
    
    if not os.path.exists(ca_cert_path):
        raise FileNotFoundError(
            f"CA certificate not found at {ca_cert_path}. "
            "Run 'python setup_ca.py' first!"
        )
    
    # Load CA private key
    with open(ca_key_path, "rb") as f:
        ca_key = serialization.load_pem_private_key(
            f.read(),
            password=None  # In production, use encrypted key with password
        )
    
    # Load CA certificate
    with open(ca_cert_path, "rb") as f:
        ca_cert = x509.load_pem_x509_certificate(f.read())
    
    # Verify CA cert is still valid
    now = datetime.now(timezone.utc)
    if now < ca_cert.not_valid_before_utc or now > ca_cert.not_valid_after_utc:
        raise ValueError("CA certificate is not valid (expired or not yet valid)")
    
    return ca_key, ca_cert


def issue_certificate(
    csr_pem: bytes, 
    username: str,
    validity_days: int = 365
) -> Tuple[str, str, datetime]:
    """
    Issue a certificate from a Certificate Signing Request (CSR)
    
    Args:
        csr_pem: PEM-encoded CSR from the user
        username: Username to include in certificate
        validity_days: Certificate validity period in days
    
    Returns:
        Tuple of (certificate_pem, serial_number_hex, not_valid_after)
    
    Raises:
        ValueError: If CSR is invalid
    """
    # Load CA
    ca_key, ca_cert = load_ca()
    
    # Load and validate CSR
    try:
        csr = x509.load_pem_x509_csr(csr_pem)
    except Exception as e:
        raise ValueError(f"Invalid CSR format: {e}")
    
    # Verify CSR signature
    if not csr.is_signature_valid:
        raise ValueError("CSR signature validation failed")
    
    # Verify CSR subject contains the username
    csr_cn = None
    for attr in csr.subject:
        if attr.oid == NameOID.COMMON_NAME:
            csr_cn = attr.value
            break
    
    if csr_cn != username:
        raise ValueError(f"CSR CN '{csr_cn}' does not match username '{username}'")
    
    # Generate certificate
    now = datetime.now(timezone.utc)
    not_after = now + timedelta(days=validity_days)
    serial = x509.random_serial_number()
    
    # Build certificate with proper extensions
    cert_builder = (
        x509.CertificateBuilder()
        .subject_name(csr.subject)
        .issuer_name(ca_cert.subject)
        .public_key(csr.public_key())
        .serial_number(serial)
        .not_valid_before(now)
        .not_valid_after(not_after)
        # Basic Constraints: This is NOT a CA
        .add_extension(
            x509.BasicConstraints(ca=False, path_length=None),
            critical=True,
        )
        # Key Usage: Digital signature and key encipherment
        .add_extension(
            x509.KeyUsage(
                digital_signature=True,
                key_encipherment=True,
                content_commitment=True,  # For non-repudiation
                data_encipherment=False,
                key_agreement=False,
                key_cert_sign=False,
                crl_sign=False,
                encipher_only=False,
                decipher_only=False,
            ),
            critical=True,
        )
        # Extended Key Usage: Client authentication, email protection
        .add_extension(
            x509.ExtendedKeyUsage([
                x509.oid.ExtendedKeyUsageOID.CLIENT_AUTH,
                x509.oid.ExtendedKeyUsageOID.EMAIL_PROTECTION,
            ]),
            critical=False,
        )
        # Subject Key Identifier
        .add_extension(
            x509.SubjectKeyIdentifier.from_public_key(csr.public_key()),
            critical=False,
        )
        # Authority Key Identifier
        .add_extension(
            x509.AuthorityKeyIdentifier.from_issuer_public_key(ca_key.public_key()),
            critical=False,
        )
    )
    
    # Sign certificate with CA private key
    cert = cert_builder.sign(ca_key, hashes.SHA256())
    
    # Convert to PEM
    cert_pem = cert.public_bytes(serialization.Encoding.PEM).decode()
    serial_hex = format(serial, 'x')
    
    print(f"✅ Issued certificate for {username}")
    print(f"   Serial: {serial_hex}")
    print(f"   Valid: {now} to {not_after}")
    
    return cert_pem, serial_hex, not_after


def validate_certificate(
    cert_pem: str,
    db: Session,
    check_revocation: bool = True
) -> Tuple[bool, Optional[str]]:
    """
    Validate a user certificate
    
    Args:
        cert_pem: PEM-encoded certificate
        db: Database session for checking revocation
        check_revocation: Whether to check CRL
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        # Load certificate
        cert = x509.load_pem_x509_certificate(cert_pem.encode())
        
        # Load CA certificate for verification
        _, ca_cert = load_ca()
        
        # 1. Check certificate dates
        now = datetime.now(timezone.utc)
        if now < cert.not_valid_before_utc:
            return False, "Certificate not yet valid"
        if now > cert.not_valid_after_utc:
            return False, "Certificate has expired"
        
        # 2. Verify issuer matches our CA
        if cert.issuer != ca_cert.subject:
            return False, "Certificate not issued by trusted CA"
        
        # 3. Verify signature
        try:
            ca_public_key = ca_cert.public_key()
            ca_public_key.verify(
                cert.signature,
                cert.tbs_certificate_bytes,
                padding.PKCS1v15(),
                cert.signature_hash_algorithm,
            )
        except Exception as e:
            return False, f"Signature verification failed: {e}"
        
        # 4. Check revocation list
        if check_revocation:
            serial_hex = format(cert.serial_number, 'x')
            revoked = db.query(models.RevokedCert).filter(
                models.RevokedCert.cert_serial == serial_hex
            ).first()
            
            if revoked:
                return False, f"Certificate revoked on {revoked.revoked_at}"
        
        # 5. Verify basic constraints (must not be CA)
        try:
            basic_constraints = cert.extensions.get_extension_for_oid(
                ExtensionOID.BASIC_CONSTRAINTS
            ).value
            if basic_constraints.ca:
                return False, "Invalid certificate: marked as CA"
        except x509.ExtensionNotFound:
            pass  # Extension is optional for end-entity certs
        
        return True, None
        
    except Exception as e:
        return False, f"Certificate validation error: {e}"


def revoke_certificate(cert_serial: str, db: Session) -> bool:
    """
    Revoke a certificate by adding it to the CRL
    
    Args:
        cert_serial: Certificate serial number (hex string)
        db: Database session
    
    Returns:
        True if revoked successfully
    """
    try:
        # Check if already revoked
        existing = db.query(models.RevokedCert).filter(
            models.RevokedCert.cert_serial == cert_serial
        ).first()
        
        if existing:
            print(f"⚠️  Certificate {cert_serial} already revoked")
            return True
        
        # Add to revocation list
        revoked_cert = models.RevokedCert(cert_serial=cert_serial)
        db.add(revoked_cert)
        db.commit()
        
        print(f"✅ Certificate {cert_serial} revoked")
        return True
        
    except Exception as e:
        print(f"❌ Failed to revoke certificate: {e}")
        db.rollback()
        return False


def extract_public_key_from_cert(cert_pem: str) -> bytes:
    """
    Extract public key from certificate in PEM format
    
    Args:
        cert_pem: PEM-encoded certificate
    
    Returns:
        Public key in PEM format (bytes)
    """
    cert = x509.load_pem_x509_certificate(cert_pem.encode())
    public_key = cert.public_key()
    
    return public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )


def get_cert_info(cert_pem: str) -> dict:
    """
    Extract information from a certificate
    
    Returns dict with certificate details
    """
    cert = x509.load_pem_x509_certificate(cert_pem.encode())
    
    # Extract subject info
    subject_dict = {}
    for attr in cert.subject:
        subject_dict[attr.oid._name] = attr.value
    
    return {
        "serial": format(cert.serial_number, 'x'),
        "subject": subject_dict,
        "issuer": cert.issuer.rfc4514_string(),
        "not_before": cert.not_valid_before_utc.isoformat(),
        "not_after": cert.not_valid_after_utc.isoformat(),
        "version": cert.version.name,
        "signature_algorithm": cert.signature_algorithm_oid._name,
    }