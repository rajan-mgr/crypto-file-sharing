# backend/schemas.py
from pydantic import BaseModel
from typing import List
from datetime import datetime


# ----------------------------
# User schemas
# ----------------------------

class UserCreate(BaseModel):
    username: str
    password: str


class UserRegister(BaseModel):
    username: str
    password: str

    # Base64-encoded values (JSON-safe) - FIXED FIELD NAMES
    salt: str  # Changed from salt_b64
    private_key_enc: str  # Changed from private_key_enc_b64

    # PEM is already text
    public_key_pem: str


class UserLogin(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


# ----------------------------
# File sharing schemas
# ----------------------------

class FileShareCreate(BaseModel):
    filename: str

    # Base64-encoded signature
    signature_b64: str

    file_hash: str
    recipients: List[str]


class FilePermissionOut(BaseModel):
    recipient: str

    # Base64-encoded symmetric key
    encrypted_sym_key_b64: str


class SharedFileOut(BaseModel):
    file_id: str
    filename: str
    owner: str

    # Base64-encoded signature
    signature_b64: str

    file_hash: str
    timestamp: datetime


class FileDownloadOut(BaseModel):
    # Base64-encoded encrypted file content
    file_data_b64: str

    signature_b64: str
    encrypted_sym_key_b64: str

    file_hash: str
    owner: str