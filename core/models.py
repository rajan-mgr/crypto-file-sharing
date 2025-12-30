# core/models.py

from dataclasses import dataclass, field
from typing import List, Dict


@dataclass
class Certificate:
    version: str = "1.0"
    serial: str = ""
    subject: str = ""
    issuer: str = "SecureShare CA"
    valid_from: str = ""
    valid_to: str = ""
    public_key_pem: str = ""
    signature: bytes = b""


@dataclass
class User:
    username: str
    password_hash: str
    salt: bytes
    private_key_encrypted: bytes
    certificate: Certificate = None
    shared_files: List[str] = field(default_factory=list)


@dataclass
class SharedFile:
    file_id: str
    filename: str
    owner: str
    encrypted_sym_key: Dict[str, bytes]
    signature: bytes
    file_hash: str
    timestamp: str


# Ensure newline at end of file
