from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, LargeBinary
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base

# ---------------- USER ----------------

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(Text, nullable=False)
    salt = Column(LargeBinary, nullable=False)

    # Encrypted private key (password-protected with user's password)
    private_key_enc = Column(LargeBinary, nullable=False)

    # -------- PKI CERTIFICATE FIELDS --------
    # Signed X.509 certificate (PEM format) - issued by CA
    certificate_pem = Column(Text, nullable=True)
    
    # Certificate serial number (for revocation checking)
    cert_serial = Column(String(40), nullable=True, unique=True, index=True)
    
    # Certificate expiry date
    cert_not_after = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    files = relationship("SharedFile", back_populates="owner", cascade="all, delete-orphan")

# ---------------- SHARED FILE ----------------

class SharedFile(Base):
    __tablename__ = "files"

    id = Column(Integer, primary_key=True, index=True)
    file_id = Column(String(36), unique=True, nullable=False, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    filename = Column(String(255), nullable=False)
    
    # Encrypted file content (encrypted with symmetric key)
    file_data = Column(LargeBinary, nullable=False)
    
    # SHA-256 hash of original file (for integrity verification)
    file_hash = Column(String(64), nullable=False)
    
    # Digital signature (RSA signature of file hash using owner's private key)
    signature = Column(LargeBinary, nullable=False)
    
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    
    # Denormalized owner username for easier queries
    owner_username = Column(String(100), nullable=False)

    owner = relationship("User", back_populates="files")
    permissions = relationship("FilePermission", back_populates="file", cascade="all, delete-orphan")

# ---------------- FILE PERMISSIONS ----------------

class FilePermission(Base):
    __tablename__ = "file_permissions"

    id = Column(Integer, primary_key=True, index=True)
    file_id = Column(String(36), ForeignKey("files.file_id"), nullable=False)
    
    # Username of recipient
    recipient = Column(String(100), nullable=False)
    
    # Symmetric key encrypted with recipient's public key (from their certificate)
    encrypted_sym_key = Column(LargeBinary, nullable=False)
    
    granted_at = Column(DateTime(timezone=True), server_default=func.now())

    file = relationship("SharedFile", back_populates="permissions")

# ---------------- CERTIFICATE REVOCATION LIST ----------------

class RevokedCert(Base):
    """
    Certificate Revocation List (CRL)
    Tracks revoked certificates to prevent their use
    """
    __tablename__ = "revoked_certs"

    id = Column(Integer, primary_key=True, index=True)
    
    # Certificate serial number (hex string)
    cert_serial = Column(String(40), unique=True, nullable=False, index=True)
    
    # Revocation timestamp
    revoked_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Optional: reason for revocation
    reason = Column(String(255), nullable=True)