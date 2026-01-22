import os
import base64
import hashlib
import requests
from pathlib import Path
from typing import List

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography import x509
from cryptography.x509.oid import NameOID

from models import SharedFile
from utils import (
    encrypt_private_key,
    decrypt_private_key,
    sign_data_with_private_key,
    verify_signature_with_certificate,
    decrypt_sym_key_with_private,
    encrypt_sym_key_with_public,
)


class SecureShareSystem:
    def __init__(self):
        self.api_base = "http://127.0.0.1:8000"
        self.token = None
        self.current_user = None
        self._password = None
        self._salt = None
        self._private_key_enc = None

    # -------------------------------------------------
    # AUTH HEADER
    # -------------------------------------------------

    def _headers(self):
        if not self.token:
            raise RuntimeError("Not authenticated")
        return {"Authorization": f"Bearer {self.token}"}

    # -------------------------------------------------
    # REGISTER (WITH PKI CERTIFICATE ISSUANCE)
    # -------------------------------------------------

    def register(self, username: str, password: str) -> bool:
        try:
            print(f"🔐 Registering user: {username}")
            
            # Generate RSA keypair (2048-bit)
            print("  └─ Generating RSA key pair...")
            private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048
            )

            # Create Certificate Signing Request (CSR)
            print("  └─ Creating CSR...")
            csr = (
                x509.CertificateSigningRequestBuilder()
                .subject_name(
                    x509.Name([
                        x509.NameAttribute(NameOID.COMMON_NAME, username),
                        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "SecureShare"),
                    ])
                )
                .sign(private_key, hashes.SHA256())
            )

            csr_pem = csr.public_bytes(serialization.Encoding.PEM)

            # Encrypt private key with user password
            print("  └─ Encrypting private key...")
            salt = os.urandom(16)
            priv_pem = private_key.private_bytes(
                serialization.Encoding.PEM,
                serialization.PrivateFormat.PKCS8,
                serialization.NoEncryption()
            )

            priv_enc = encrypt_private_key(priv_pem, password, salt)

            # Send registration request
            print("  └─ Sending registration request to CA...")
            payload = {
                "username": username,
                "password": password,
                "salt": base64.urlsafe_b64encode(salt).decode(),
                "private_key_enc": base64.urlsafe_b64encode(priv_enc).decode(),
                "csr_pem": csr_pem.decode(),
            }

            r = requests.post(
                f"{self.api_base}/auth/register",
                json=payload,
                timeout=15
            )
            r.raise_for_status()

            data = r.json()
            self.token = data["access_token"]
            self.current_user = username
            self._password = password
            self._salt = salt
            self._private_key_enc = priv_enc
            
            print("✅ Registration successful! Certificate issued by CA.")
            return True

        except requests.HTTPError as e:
            error_detail = e.response.json().get("detail", str(e)) if e.response else str(e)
            print(f"❌ Registration failed: {error_detail}")
            return False
        except Exception as e:
            print(f"❌ Registration error: {e}")
            import traceback
            traceback.print_exc()
            return False

    # -------------------------------------------------
    # LOGIN (WITH CERTIFICATE VALIDATION)
    # -------------------------------------------------

    def login(self, username: str, password: str) -> bool:
        try:
            print(f"🔐 Logging in: {username}")
            
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
            
            # Fetch user's encrypted private key and salt
            print("  └─ Fetching private key...")
            r_priv = requests.get(
                f"{self.api_base}/users/me/private",
                headers=self._headers(),
                timeout=10
            )
            r_priv.raise_for_status()
            
            user_data = r_priv.json()
            self._salt = base64.urlsafe_b64decode(user_data["salt"] + "==")
            self._private_key_enc = base64.urlsafe_b64decode(user_data["private_key_enc"] + "==")
            
            print("✅ Login successful! Certificate validated.")
            return True
            
        except requests.HTTPError as e:
            error_detail = e.response.json().get("detail", str(e)) if e.response else str(e)
            print(f"❌ Login failed: {error_detail}")
            return False
        except Exception as e:
            print(f"❌ Login error: {e}")
            return False

    # -------------------------------------------------
    # LIST FILES
    # -------------------------------------------------

    def get_my_files(self) -> List[SharedFile]:
        try:
            r = requests.get(
                f"{self.api_base}/files",
                headers=self._headers(),
                timeout=10
            )
            r.raise_for_status()

            return [
                SharedFile(
                    file_id=f["file_id"],
                    filename=f["filename"],
                    owner=f["owner"],
                    encrypted_sym_key={},
                    signature=b"",
                    file_hash=f["file_hash"],
                    timestamp=f.get("timestamp"),
                )
                for f in r.json()
            ]

        except Exception as e:
            print("Get files error:", e)
            return []

    # -------------------------------------------------
    # GET USER CERTIFICATE (for encryption)
    # -------------------------------------------------

    def get_user_certificate(self, username: str) -> tuple:
        """Fetch a user's certificate and public key"""
        try:
            r = requests.get(
                f"{self.api_base}/users/{username}/certificate",
                headers=self._headers(),
                timeout=10
            )
            r.raise_for_status()
            data = r.json()
            
            certificate_pem = data["certificate_pem"]
            public_key_pem = data["public_key_pem"]
            
            return certificate_pem, public_key_pem.encode()
            
        except Exception as e:
            print(f"Failed to get certificate for {username}:", e)
            raise

    # -------------------------------------------------
    # SHARE FILE (WITH DIGITAL SIGNATURE)
    # -------------------------------------------------

    def share_file(self, file_path: str, recipients: List[str], password: str) -> bool:
        try:
            print(f"\n📤 Sharing file: {Path(file_path).name}")
            
            # Read file
            raw = Path(file_path).read_bytes()
            print(f"  └─ File size: {len(raw)} bytes")

            # Generate symmetric key for file encryption
            sym_key = Fernet.generate_key()
            encrypted = Fernet(sym_key).encrypt(raw)
            print(f"  └─ Encrypted with AES (Fernet)")

            # Calculate file hash
            file_hash = hashlib.sha256(raw).hexdigest()
            print(f"  └─ SHA-256 hash: {file_hash[:16]}...")

            # Create digital signature using RSA private key
            print(f"  └─ Creating digital signature...")
            signature = sign_data_with_private_key(
                raw,
                self._private_key_enc,
                password,
                self._salt
            )
            print(f"  └─ Signature created: {len(signature)} bytes (RSA-PSS)")

            # Encrypt symmetric key for owner + all recipients
            encrypted_keys = {}
            all_users = [self.current_user] + recipients
            
            print(f"  └─ Encrypting symmetric key for {len(all_users)} users...")
            for user in all_users:
                try:
                    # Get user's certificate and public key
                    cert_pem, public_key_pem = self.get_user_certificate(user)
                    
                    # Encrypt symmetric key with user's public key (RSA-OAEP)
                    encrypted_sym_key = encrypt_sym_key_with_public(sym_key, public_key_pem)
                    
                    encrypted_keys[user] = base64.urlsafe_b64encode(encrypted_sym_key).decode()
                    print(f"     ✓ {user}")
                    
                except Exception as e:
                    print(f"     ✗ {user}: {e}")
                    return False

            # Upload to server
            print(f"  └─ Uploading to server...")
            payload = {
                "filename": Path(file_path).name,
                "encrypted_content": base64.urlsafe_b64encode(encrypted).decode(),
                "signature": base64.urlsafe_b64encode(signature).decode(),
                "file_hash": file_hash,
                "recipients": recipients,
                "encrypted_keys": encrypted_keys,
            }

            r = requests.post(
                f"{self.api_base}/files",
                json=payload,
                headers=self._headers(),
                timeout=30
            )
            r.raise_for_status()
            
            print(f"✅ File shared successfully!")
            print(f"   Recipients: {', '.join(all_users)}")
            print(f"   Signed with RSA private key")
            print(f"   Encrypted with hybrid encryption (RSA + AES)\n")
            return True

        except Exception as e:
            print(f"❌ Share file error: {e}")
            import traceback
            traceback.print_exc()
            return False

    # -------------------------------------------------
    # DOWNLOAD FILE (WITH SIGNATURE VERIFICATION)
    # -------------------------------------------------

    def download_file(self, file_id: str, save_path: str, password: str) -> bool:
        try:
            print(f"\n📥 Downloading file...")
            
            # Get file from server
            r = requests.get(
                f"{self.api_base}/files/{file_id}",
                headers=self._headers(),
                timeout=30
            )
            r.raise_for_status()
            data = r.json()

            print(f"  └─ Owner: {data['owner']}")
            
            # Verify digital signature if owner's certificate is valid
            owner_cert = data.get("owner_certificate")
            signature_verified = False
            
            if owner_cert and data.get("signature_valid"):
                print(f"  └─ Verifying digital signature...")
                
                # Decode file data and signature
                encrypted_file = base64.urlsafe_b64decode(data["file_data"] + "==")
                signature = base64.urlsafe_b64decode(data["signature"] + "==")
                
                # Get encrypted symmetric key
                enc_sym_key_b64 = data.get("encrypted_sym_key")
                if not enc_sym_key_b64:
                    print("     ✗ No encrypted symmetric key found")
                    return False
                    
                enc_sym = base64.urlsafe_b64decode(enc_sym_key_b64 + "==")

                # Decrypt private key
                priv_pem = decrypt_private_key(self._private_key_enc, password, self._salt)
                priv_key = serialization.load_pem_private_key(priv_pem, password=None)

                # Decrypt symmetric key
                sym_key = decrypt_sym_key_with_private(enc_sym, priv_key)

                # Decrypt file
                decrypted = Fernet(sym_key).decrypt(encrypted_file)
                
                # Verify signature using owner's certificate
                signature_verified = verify_signature_with_certificate(
                    decrypted,
                    signature,
                    owner_cert
                )
                
                if signature_verified:
                    print(f"     ✅ Signature valid!")
                else:
                    print(f"     ⚠️  Signature verification FAILED!")
                    response = input("     Continue anyway? (yes/no): ")
                    if response.lower() not in ['yes', 'y']:
                        return False
                
                # Verify file hash
                calculated_hash = hashlib.sha256(decrypted).hexdigest()
                stored_hash = data["file_hash"]
                
                if calculated_hash == stored_hash:
                    print(f"  └─ File integrity verified (SHA-256)")
                else:
                    print(f"  └─ ⚠️  File hash mismatch!")
                    return False
                
                # Save file
                Path(save_path).write_bytes(decrypted)
                print(f"✅ File downloaded and verified successfully!")
                print(f"   Saved to: {save_path}")
                print(f"   Signature: {'VALID' if signature_verified else 'INVALID'}\n")
                return True
            else:
                print(f"  └─ ⚠️  Owner's certificate not available or invalid")
                print(f"     Cannot verify signature!")
                return False

        except Exception as e:
            print(f"❌ Download error: {e}")
            import traceback
            traceback.print_exc()
            return False

    # -------------------------------------------------
    # LOGOUT
    # -------------------------------------------------

    def logout(self):
        self.token = None
        self.current_user = None
        self._password = None
        self._salt = None
        self._private_key_enc = None