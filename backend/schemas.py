# backend/schemas.py
from pydantic import BaseModel
from typing import List
from datetime import datetime

# ============================
# USER SCHEMAS
# ============================

class UserCreate(BaseModel):
    username: str
    password: str


class UserRegister(BaseModel):
    username: str
    password: str

    # Base64-encoded values (JSON-safe)
    salt: str
    private_key_enc: str

    # PKI
    csr_pem: str  # Certificate Signing Request (PEM text)


class UserLogin(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


# ============================
# FILE UPLOAD / SHARING
# ============================

class FileUpload(BaseModel):
    owner: str
    filename: str

    # Base64-encoded encrypted file content
    encrypted_data: str

    # Base64-encoded digital signature
    signature: str


class FileShareCreate(BaseModel):
    file_id: int
    recipients: List[str]


class FilePermissionOut(BaseModel):
    recipient: str

    # Base64-encoded encrypted symmetric key
    encrypted_sym_key_b64: str


class SharedFileOut(BaseModel):
    file_id: int
    filename: str
    owner: str

    # Base64-encoded digital signature
    signature_b64: str

    file_hash: str
    timestamp: datetime

    class Config:
        from_attributes = True


class FileDownloadOut(BaseModel):
    # Base64-encoded encrypted file content
    file_data_b64: str

    # Base64-encoded digital signature
    signature_b64: str

    # Base64-encoded encrypted symmetric key
    encrypted_sym_key_b64: str

    file_hash: str
    owner: str
