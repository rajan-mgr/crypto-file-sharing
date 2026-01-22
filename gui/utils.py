# gui/utils.py
"""
Cryptographic utilities for SecureShare
Implements proper PKI with RSA signatures
"""

import os
import base64
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
from cryptography.fernet import Fernet


# =========================================================
# KEY GENERATION
# =========================================================

def generate_rsa_key_pair():
    """Generate RSA 2048-bit key pair"""
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048
    )

    private_pem = private_key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption()
    )

    public_pem = private_key.public_key().public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo
    )

    return private_pem, public_pem


# =========================================================
# PASSWORD-BASED KEY DERIVATION
# =========================================================

def derive_key_from_password(password: str, salt: bytes) -> bytes:
    """Derive encryption key from password using Scrypt KDF"""
    kdf = Scrypt(
        salt=salt,
        length=32,
        n=2**14,  # 16384
        r=8,
        p=1
    )
    return base64.urlsafe_b64encode(kdf.derive(password.encode()))


# =========================================================
# PRIVATE KEY ENCRYPTION / DECRYPTION
# =========================================================

def encrypt_private_key(private_pem: bytes, password: str, salt: bytes) -> bytes:
    """Encrypt private key with password-derived key (Fernet/AES)"""
    key = derive_key_from_password(password, salt)
    fernet = Fernet(key)
    return fernet.encrypt(private_pem)


def decrypt_private_key(encrypted_private_key: bytes, password: str, salt: bytes) -> bytes:
    """Decrypt private key with password-derived key"""
    key = derive_key_from_password(password, salt)
    fernet = Fernet(key)
    return fernet.decrypt(encrypted_private_key)


# =========================================================
# SYMMETRIC KEY ENCRYPTION (RSA-OAEP)
# =========================================================

def encrypt_sym_key_with_public(sym_key: bytes, public_pem: bytes) -> bytes:
    """Encrypt symmetric key with RSA public key (OAEP padding)"""
    public_key = serialization.load_pem_public_key(public_pem)
    return public_key.encrypt(
        sym_key,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )


def decrypt_sym_key_with_private(enc_sym_key: bytes, private_key) -> bytes:
    """Decrypt symmetric key with RSA private key"""
    return private_key.decrypt(
        enc_sym_key,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )


# =========================================================
# DIGITAL SIGNATURES (RSA-PSS)
# =========================================================

def sign_data_with_private_key(data: bytes, private_key_pem: bytes, password: str, salt: bytes) -> bytes:
    """
    Create RSA digital signature using private key
    
    Args:
        data: Raw data to sign
        private_key_pem: Encrypted private key (PEM format)
        password: User password to decrypt private key
        salt: Salt used for key derivation
    
    Returns:
        RSA signature bytes
    """
    # Decrypt private key
    decrypted_pem = decrypt_private_key(private_key_pem, password, salt)
    
    # Load private key
    private_key = serialization.load_pem_private_key(
        decrypted_pem,
        password=None
    )
    
    # Create signature using RSA-PSS with SHA-256
    signature = private_key.sign(
        data,
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH
        ),
        hashes.SHA256()
    )
    
    return signature


def verify_signature_with_public_key(data: bytes, signature: bytes, public_key_pem: bytes) -> bool:
    """
    Verify RSA digital signature using public key
    
    Args:
        data: Original data
        signature: RSA signature to verify
        public_key_pem: Public key (PEM format)
    
    Returns:
        True if signature is valid, False otherwise
    """
    try:
        # Load public key
        public_key = serialization.load_pem_public_key(public_key_pem)
        
        # Verify signature using RSA-PSS with SHA-256
        public_key.verify(
            signature,
            data,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        
        return True
        
    except Exception as e:
        print(f"Signature verification failed: {e}")
        return False


def verify_signature_with_certificate(data: bytes, signature: bytes, certificate_pem: str) -> bool:
    """
    Verify RSA digital signature using X.509 certificate
    
    Args:
        data: Original data
        signature: RSA signature to verify
        certificate_pem: X.509 certificate (PEM format)
    
    Returns:
        True if signature is valid, False otherwise
    """
    try:
        from cryptography import x509
        
        # Load certificate
        cert = x509.load_pem_x509_certificate(certificate_pem.encode())
        
        # Extract public key from certificate
        public_key = cert.public_key()
        
        # Verify signature
        public_key.verify(
            signature,
            data,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        
        return True
        
    except Exception as e:
        print(f"Certificate-based signature verification failed: {e}")
        return False


# =========================================================
# LEGACY COMPATIBILITY (for old code)
# =========================================================

def sign_data(data: bytes, password: str) -> bytes:
    """
    Legacy signature function - just returns SHA-256 hash
    This is NOT a proper digital signature!
    Use sign_data_with_private_key() instead.
    """
    digest = hashes.Hash(hashes.SHA256())
    digest.update(data)
    return digest.finalize()