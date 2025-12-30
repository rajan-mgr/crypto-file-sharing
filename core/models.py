from dataclasses import dataclass, asdict, field
from typing import List, Dict

@dataclass
class Certificate:
    version: str = "1.0"
    serial: str = ""
    subject: str = ""
    issuer: str = "SecureShare CA"
    valid_from: str = ""
    valid_to: str = ""
    public_key_pem: str = ""      # PEM encoded
    signature: bytes = b""       # Real signature

@dataclass
class User:
    username: str
    password_hash: str
    salt: bytes
    private_key_encrypted: bytes  # Encrypted with password-derived key
    certificate: Certificate = None
    shared_files: List[str] = field(default_factory=list)

@dataclass
class SharedFile:
    file_id: str
    filename: str
    owner: str
    encrypted_sym_key: Dict[str, bytes]  # username -> encrypted Fernet key
    signature: bytes                     # Owner's signature on file_hash
    file_hash: str
    timestamp: str