# core/secure_share.py
import os
import uuid
import hashlib
from .models import User, SharedFile, Certificate
from .utils import (
    generate_rsa_key_pair, encrypt_private_key, decrypt_private_key,
    derive_key_from_password, encrypt_sym_key_with_public,
    decrypt_sym_key_with_private, sign_data, verify_signature
)
from .database import DatabaseManager
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import serialization

class SecureShareSystem:
    def __init__(self):
        # Update these with your real Ubuntu server credentials
        self.db = DatabaseManager(
            host="100.112.140.126",
            dbname="mysecurefileshare",
            user="postgres",
            password="post"
        )
        self.current_user = None

    def register_user(self, username, password):
        if self.db.get_user(username):
            return False
        
        priv_pem, pub_pem = generate_rsa_key_pair()
        salt = os.urandom(16)
        priv_enc = encrypt_private_key(priv_pem, password, salt)
        
        # In a real app, generate a proper certificate here
        # For now, we store the PEM string
        self.db.save_user(username, hashlib.sha256(password.encode()).hexdigest(), 
                         salt, priv_enc, pub_pem.decode())
        return True

    def login_user(self, username, password):
        user_data = self.db.get_user(username)
        if user_data and user_data['password_hash'] == hashlib.sha256(password.encode()).hexdigest():
            self.current_user = username
            return True
        return False

    def get_all_users(self):
        return self.db.get_all_usernames()

    def share_file(self, filepath, recipients, password):
        user_data = self.db.get_user(self.current_user)
        
        # FIX: Wrap private_key_enc and salt in bytes() 
        # because Postgres returns them as memoryview objects
        priv_pem = decrypt_private_key(
            bytes(user_data['private_key_enc']), 
            password, 
            bytes(user_data['salt'])
        )
        priv_key = serialization.load_pem_private_key(priv_pem, password=None)

        # 1. Encrypt File Content
        sym_key = Fernet.generate_key()
        f = Fernet(sym_key)
        with open(filepath, 'rb') as file:
            data = file.read()
        encrypted_data = f.encrypt(data)

        # 2. Sign File
        signature = sign_data(data, priv_key)
        file_hash = hashlib.sha256(data).hexdigest()
        file_id = str(uuid.uuid4())

        # 3. Encrypt Sym Key for each recipient
        all_recipients = set(recipients) | {self.current_user}
        permissions = {}
        for r_name in all_recipients:
            r_data = self.db.get_user(r_name)
            permissions[r_name] = encrypt_sym_key_with_public(sym_key, r_data['public_key_pem'].encode())

        # 4. Save to Postgres
        self.db.save_file(file_id, os.path.basename(filepath), self.current_user, 
                         encrypted_data, signature, file_hash, permissions)
        return True
    def get_shared_files(self):
        # Return list of SharedFile objects for the UI
        rows = self.db.get_user_files(self.current_user)
        files = []
        for r in rows:
            files.append(SharedFile(
                file_id=r['file_id'], filename=r['filename'], owner=r['owner'],
                encrypted_sym_key={}, # Simplified for UI list
                signature=r['signature'], file_hash=r['file_hash'], timestamp=str(r['timestamp'])
            ))
        return files

    def download_file(self, file_id, save_path, password):
        row = self.db.get_file_for_download(file_id, self.current_user)
        if not row: return False

        # 1. Unlock Private Key
        user_data = self.db.get_user(self.current_user)
        # FIX: Wrap salt and private_key_enc here too
        priv_pem = decrypt_private_key(
            bytes(user_data['private_key_enc']), 
            password, 
            bytes(user_data['salt'])
        )
        priv_key = serialization.load_pem_private_key(priv_pem, password=None)

        # 2. Decrypt Symmetric Key
        # FIX: encrypted_sym_key comes from DB, wrap in bytes()
        sym_key = decrypt_sym_key_with_private(bytes(row['encrypted_sym_key']), priv_key)

        # 3. Decrypt File
        f = Fernet(sym_key)
        # FIX: file_data comes from DB, wrap in bytes()
        decrypted_data = f.decrypt(bytes(row['file_data']))

        # 4. Verify Signature
        owner_data = self.db.get_user(row['owner'])
        if verify_signature(decrypted_data, bytes(row['signature']), owner_data['public_key_pem'].encode()):
            with open(save_path, 'wb') as file:
                file.write(decrypted_data)
            return True
        return False