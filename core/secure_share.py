# core/secure_share.py

import json
import datetime
import base64
from pathlib import Path
from dataclasses import asdict

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
from cryptography.fernet import Fernet
import hashlib
import os

from .models import User, Certificate, SharedFile
from .utils import (
    generate_rsa_key_pair,
    encrypt_private_key,
    decrypt_private_key,
    encrypt_sym_key_with_public,
    decrypt_sym_key_with_private,
    sign_data,
    verify_signature,
)


class SecureShareSystem:
    def __init__(self, data_dir="data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        (self.data_dir / "files").mkdir(exist_ok=True)

        self.users: dict[str, User] = {}
        self.shared_files: dict[str, SharedFile] = {}
        self.revoked_certs: set[str] = set()
        self.current_user: str | None = None

        self._load_data()

    def register_user(self, username: str, password: str) -> bool:
        if username in self.users:
            return False

        salt = os.urandom(16)
        private_pem, public_pem = generate_rsa_key_pair()
        encrypted_private = encrypt_private_key(private_pem, password, salt)

        cert = Certificate(
            serial=f"CERT_{datetime.datetime.now().strftime('%Y%m%d')}_{len(self.users)+1:04d}",
            subject=username,
            valid_from=datetime.datetime.now().isoformat(),
            valid_to=(datetime.datetime.now() + datetime.timedelta(days=365)).isoformat(),
            public_key_pem=public_pem.decode("utf-8"),
            signature=b""
        )

        user = User(
            username=username,
            password_hash=hashlib.sha256(password.encode()).hexdigest(),
            salt=salt,
            private_key_encrypted=encrypted_private,
            certificate=cert,
            shared_files=[]
        )

        self.users[username] = user
        self._save_data()
        return True

    def login_user(self, username: str, password: str) -> bool:
        if username not in self.users:
            return False

        user = self.users[username]
        expected_hash = hashlib.sha256(password.encode()).hexdigest()
        if user.password_hash != expected_hash:
            return False

        try:
            decrypt_private_key(user.private_key_encrypted, password, user.salt)
            self.current_user = username
            return True
        except Exception:
            return False

    def get_private_key(self, password: str):
        user = self.users[self.current_user]
        private_pem = decrypt_private_key(user.private_key_encrypted, password, user.salt)
        return serialization.load_pem_private_key(private_pem, password=None)

    def share_file(self, filepath: str, recipients: list[str], password: str) -> bool:
        if not self.current_user:
            return False

        try:
            sym_key = Fernet.generate_key()
            cipher = Fernet(sym_key)

            with open(filepath, "rb") as f:
                plaintext = f.read()

            encrypted_data = cipher.encrypt(plaintext)
            file_hash = hashlib.sha256(plaintext).hexdigest()
            hash_bytes = file_hash.encode()

            # MD5 used only for short non-cryptographic identifier - safe here # nosec B324
            file_id = f"file_{datetime.datetime.now().timestamp()}_{hashlib.md5(plaintext, usedforsecurity=False).hexdigest()[:8]}"
            enc_path = self.data_dir / "files" / f"{file_id}.enc"
            with open(enc_path, "wb") as f:
                f.write(encrypted_data)

            private_key = self.get_private_key(password)
            signature = sign_data(hash_bytes, private_key)

            encrypted_keys = {}
            owner_pub_pem = self.users[self.current_user].certificate.public_key_pem.encode()
            encrypted_keys[self.current_user] = encrypt_sym_key_with_public(sym_key, owner_pub_pem)

            for recipient in recipients:
                pub_pem = self.users[recipient].certificate.public_key_pem.encode()
                encrypted_keys[recipient] = encrypt_sym_key_with_public(sym_key, pub_pem)

            shared_file = SharedFile(
                file_id=file_id,
                filename=Path(filepath).name,
                owner=self.current_user,
                encrypted_sym_key=encrypted_keys,
                signature=signature,
                file_hash=file_hash,
                timestamp=datetime.datetime.now().isoformat()
            )

            self.shared_files[file_id] = shared_file
            self.users[self.current_user].shared_files.append(file_id)
            self._save_data()
            return True

        except Exception as e:
            print(f"Error sharing file: {e}")
            return False

    def get_shared_files(self):
        if not self.current_user:
            return []

        files = []
        for sf in self.shared_files.values():
            if sf.owner == self.current_user or self.current_user in sf.encrypted_sym_key:
                files.append(sf)
        return files

    def download_file(self, file_id: str, save_path: str, password: str) -> bool:
        if file_id not in self.shared_files:
            return False

        sf = self.shared_files[file_id]
        if self.current_user not in sf.encrypted_sym_key:
            return False

        try:
            enc_path = self.data_dir / "files" / f"{file_id}.enc"
            with open(enc_path, "rb") as f:
                enc_data = f.read()

            private_key = self.get_private_key(password)
            enc_sym_key = sf.encrypted_sym_key[self.current_user]
            sym_key = decrypt_sym_key_with_private(enc_sym_key, private_key)

            cipher = Fernet(sym_key)
            decrypted = cipher.decrypt(enc_data)

            if hashlib.sha256(decrypted).hexdigest() != sf.file_hash:
                return False

            owner_pub_pem = self.users[sf.owner].certificate.public_key_pem.encode()
            if not verify_signature(sf.file_hash.encode(), sf.signature, owner_pub_pem):
                return False

            with open(save_path, "wb") as f:
                f.write(decrypted)
            return True

        except Exception as e:
            print(f"Error downloading file: {e}")
            return False

    def revoke_file_access(self, file_id: str, username: str) -> bool:
        if file_id not in self.shared_files:
            return False

        sf = self.shared_files[file_id]
        if sf.owner != self.current_user:
            return False

        if username in sf.encrypted_sym_key:
            del sf.encrypted_sym_key[username]
            self._save_data()
            return True
        return False

    def get_all_users(self):
        return list(self.users.keys())

    def _save_data(self):
        users_data = {}
        for u in self.users.values():
            cert_dict = asdict(u.certificate)
            cert_dict["signature"] = base64.b64encode(cert_dict["signature"]).decode()

            users_data[u.username] = {
                "username": u.username,
                "password_hash": u.password_hash,
                "salt": base64.b64encode(u.salt).decode(),
                "private_key_encrypted": base64.b64encode(u.private_key_encrypted).decode(),
                "certificate": cert_dict,
                "shared_files": u.shared_files,
            }

        with open(self.data_dir / "users.json", "w") as f:
            json.dump(users_data, f, indent=2)

        files_data = {}
        for fid, sf in self.shared_files.items():
            data = asdict(sf)
            data["encrypted_sym_key"] = {
                k: base64.b64encode(v).decode() for k, v in data["encrypted_sym_key"].items()
            }
            data["signature"] = base64.b64encode(data["signature"]).decode()
            files_data[fid] = data

        with open(self.data_dir / "shared_files.json", "w") as f:
            json.dump(files_data, f, indent=2)

    def _load_data(self):
        users_file = self.data_dir / "users.json"
        if users_file.exists():
            with open(users_file) as f:
                data = json.load(f)

            migrated = False
            for ud in data.values():
                cert_data = ud.get("certificate")
                if cert_data and "public_key" in cert_data and "public_key_pem" not in cert_data:
                    cert_data["public_key_pem"] = cert_data.pop("public_key")
                    migrated = True
            if migrated:
                with open(users_file, "w") as f:
                    json.dump(data, f, indent=2)

            for ud in data.values():
                cert_data = ud["certificate"]
                signature_b64 = cert_data.get("signature", "")
                cert_data["signature"] = base64.b64decode(signature_b64) if signature_b64 else b""

                cert = Certificate(**cert_data)

                user = User(
                    username=ud["username"],
                    password_hash=ud["password_hash"],
                    salt=base64.b64decode(ud["salt"]),
                    private_key_encrypted=base64.b64decode(ud["private_key_encrypted"]),
                    certificate=cert,
                    shared_files=ud.get("shared_files", []),
                )
                self.users[user.username] = user

        files_file = self.data_dir / "shared_files.json"
        if files_file.exists():
            with open(files_file) as f:
                data = json.load(f)

            for fid, fd in data.items():
                fd["encrypted_sym_key"] = {
                    k: base64.b64decode(v) for k, v in fd["encrypted_sym_key"].items()
                }
                fd["signature"] = base64.b64decode(fd["signature"])
                sf = SharedFile(**fd)
                self.shared_files[fid] = sf


# Ensure newline at end of file