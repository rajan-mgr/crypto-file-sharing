import os
import base64
import hashlib
import requests
from pathlib import Path
from typing import List

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import serialization

from models import SharedFile
from utils import (
    generate_rsa_key_pair,
    encrypt_private_key,
    decrypt_private_key,
    derive_key_from_password,
    encrypt_sym_key_with_public,
    decrypt_sym_key_with_private,
    sign_data,
    verify_signature
)


class SecureShareSystem:
    def __init__(self):
        self.api_base = "http://127.0.0.1:8000"
        self.token = None
        self.current_user = None
        self._password = None

    def _headers(self):
        if not self.token:
            raise RuntimeError("Not authenticated")
        return {"Authorization": f"Bearer {self.token}"}

    def register(self, username: str, password: str) -> bool:
        try:
            priv_pem, pub_pem = generate_rsa_key_pair()
            salt = os.urandom(16)
            priv_enc = encrypt_private_key(priv_pem, password, salt)

            payload = {
                "username": username,
                "password": password,
                "salt": base64.urlsafe_b64encode(salt).decode('ascii'),
                "private_key_enc": base64.urlsafe_b64encode(priv_enc).decode('ascii'),
                "public_key_pem": pub_pem.decode('ascii')
            }

            r = requests.post(f"{self.api_base}/auth/register", json=payload, timeout=15)
            r.raise_for_status()

            data = r.json()
            self.token = data["access_token"]
            self.current_user = username
            self._password = password
            return True
        except Exception as e:
            print("Register error:", type(e).__name__, str(e))
            return False

    def login(self, username: str, password: str) -> bool:
        try:
            r = requests.post(
                f"{self.api_base}/auth/login",
                data={"username": username, "password": password},
                timeout=10
            )
            r.raise_for_status()
            data = r.json()
            self.token = data["access_token"]
            self.current_user = username
            self._password = password
            return True
        except Exception as e:
            print("Login error:", type(e).__name__, str(e))
            return False

    def get_my_files(self) -> List[SharedFile]:
        if not self.token:
            return []
        try:
            r = requests.get(f"{self.api_base}/files", headers=self._headers(), timeout=10)
            r.raise_for_status()
            return [
                SharedFile(
                    file_id=f["file_id"],
                    filename=f["filename"],
                    owner=f["owner"],
                    encrypted_sym_key={},  # not needed in list view
                    signature=base64.b64decode(f["signature"]),
                    file_hash=f["file_hash"],
                    timestamp=f.get("timestamp", "")
                )
                for f in r.json()
            ]
        except Exception as e:
            print("Get files error:", type(e).__name__, str(e))
            return []

    def share_file(self, file_path: str, recipients: List[str], password: str) -> bool:
        try:
            raw = Path(file_path).read_bytes()
            sym_key = Fernet.generate_key()
            encrypted = Fernet(sym_key).encrypt(raw)

            # TODO: implement proper signing once you have private key available
            signature = b"[PLACEHOLDER_SIGNATURE_NOT_IMPLEMENTED]"

            file_hash = hashlib.sha256(raw).hexdigest()

            enc_keys = {}
            # Include owner + all selected recipients
            for r in set(recipients + [self.current_user]):
                try:
                    r_pub = requests.get(
                        f"{self.api_base}/users/{r}/public-key",
                        headers=self._headers(),
                        timeout=6
                    )
                    r_pub.raise_for_status()
                    pub_pem = r_pub.json()["public_key_pem"].encode('ascii')

                    enc_sym = encrypt_sym_key_with_public(sym_key, pub_pem)
                    enc_keys[r] = base64.urlsafe_b64encode(enc_sym).decode('ascii')
                except Exception as e:
                    print(f"Failed to get public key for {r}: {e}")
                    return False

            payload = {
                "filename": Path(file_path).name,
                "encrypted_content": base64.urlsafe_b64encode(encrypted).decode(),
                "signature": base64.urlsafe_b64encode(signature).decode(),
                "file_hash": file_hash,
                "recipients": recipients,
                "encrypted_keys": enc_keys
            }

            r = requests.post(f"{self.api_base}/files", json=payload, headers=self._headers(), timeout=45)
            r.raise_for_status()
            print("File shared successfully")
            return True

        except Exception as e:
            print("Share file error:", type(e).__name__, str(e))
            return False

    def download_file(self, file_id: str, save_path: str, password: str) -> bool:
        try:
            r = requests.get(f"{self.api_base}/files/{file_id}", headers=self._headers(), timeout=30)
            r.raise_for_status()
            data = r.json()

            enc_sym_key_b64 = data.get("encrypted_sym_key")
            if not enc_sym_key_b64:
                print("Missing encrypted_sym_key in response")
                return False

            # Padding fix for base64
            enc_sym_key = base64.urlsafe_b64decode(enc_sym_key_b64 + '==')

            # Get encrypted private key + salt
            r_user = requests.get(f"{self.api_base}/users/me/private", headers=self._headers(), timeout=10)
            r_user.raise_for_status()
            user_info = r_user.json()

            salt = base64.urlsafe_b64decode(user_info["salt"] + '==')
            priv_enc = base64.urlsafe_b64decode(user_info["private_key_enc"] + '==')

            priv_pem = decrypt_private_key(priv_enc, password, salt)
            priv_key = serialization.load_pem_private_key(priv_pem, password=None)

            sym_key = decrypt_sym_key_with_private(enc_sym_key, priv_key)

            enc_content_b64 = data.get("file_data")
            enc_content = base64.urlsafe_b64decode(enc_content_b64 + '==')

            decrypted = Fernet(sym_key).decrypt(enc_content)

            Path(save_path).write_bytes(decrypted)
            print(f"File saved and decrypted: {save_path}")
            return True

        except requests.HTTPError as e:
            print(f"HTTP error {e.response.status_code}: {e.response.text}")
            return False
        except Exception as e:
            print("Download/decrypt error:", type(e).__name__, str(e))
            return False

    def logout(self):
        self.token = None
        self.current_user = None
        self._password = None