import unittest
from unittest.mock import MagicMock, patch
import hashlib
import os
import uuid
from core.secure_share import SecureShareSystem
from core.utils import generate_rsa_key_pair

class TestSecureShareLogic(unittest.TestCase):

    def setUp(self):
        """Set up the system with a mocked database before every test."""
        # Patch DatabaseManager so we don't need a real Postgres connection
        with patch('core.secure_share.DatabaseManager') as MockDB:
            self.system = SecureShareSystem()
            self.mock_db = self.system.db

    # --- Registration Tests ---

    def test_registration_success(self):
        """Test that a new user can register correctly."""
        self.mock_db.get_user.return_value = None  # Simulate user doesn't exist
        
        result = self.system.register_user("new_user", "password123")
        
        self.assertTrue(result)
        self.assertTrue(self.mock_db.save_user.called)

    def test_registration_duplicate_user(self):
        """Test that registering an existing username fails."""
        self.mock_db.get_user.return_value = {'username': 'existing_user'}
        
        result = self.system.register_user("existing_user", "password")
        self.assertFalse(result)

    # --- Login Tests ---

    def test_login_success(self):
        """Test login with correct credentials."""
        password = "mypassword"
        pwd_hash = hashlib.sha256(password.encode()).hexdigest()
        
        self.mock_db.get_user.return_value = {
            'username': 'alice',
            'password_hash': pwd_hash
        }
        
        result = self.system.login_user("alice", password)
        self.assertTrue(result)
        self.assertEqual(self.system.current_user, "alice")

    def test_login_wrong_password(self):
        """Test login fails with incorrect password."""
        self.mock_db.get_user.return_value = {
            'username': 'alice',
            'password_hash': 'correct_hash_here'
        }
        
        result = self.system.login_user("alice", "wrong_password")
        self.assertFalse(result)

    # --- Cryptography Logic Tests ---

    @patch('builtins.open', unittest.mock.mock_open(read_data=b"secret file data"))
    def test_share_file_logic(self):
        """Tests the encryption and signing flow during sharing."""
        self.system.current_user = "alice"
        
        # Generate a REAL RSA public key for the mock to avoid MalformedFraming error
        _, real_pub_pem = generate_rsa_key_pair()
        
        dummy_user = {
            'private_key_enc': b'enc_data',
            'salt': b'0123456789abcdef',
            'public_key_pem': real_pub_pem.decode()
        }
        
        self.mock_db.get_user.return_value = dummy_user
        
        # Mocking external crypto calls to keep test focused on logic
        with patch('core.secure_share.decrypt_private_key') as mock_decrypt, \
             patch('core.secure_share.serialization.load_pem_private_key'), \
             patch('core.secure_share.sign_data') as mock_sign:
            
            mock_decrypt.return_value = b"fake_pem_bytes"
            mock_sign.return_value = b"fake_signature"
            
            result = self.system.share_file("test.txt", ["bob"], "password")
            
            self.assertTrue(result)
            self.assertTrue(self.mock_db.save_file.called)

    def test_download_file_logic(self):
        """Tests the decryption and verification flow during download."""
        self.system.current_user = "alice"
        _, real_pub_pem = generate_rsa_key_pair()
        
        # Mock DB response for the file request
        mock_file_row = {
            'file_id': '123',
            'filename': 'test.txt',
            'owner': 'bob',
            'file_data': b'encrypted_blob',
            'signature': b'sig_bytes',
            'encrypted_sym_key': b'enc_key_bytes'
        }
        
        # Mock DB response for the user keys
        mock_user_data = {
            'private_key_enc': b'enc_priv',
            'salt': b'salt_bytes',
            'public_key_pem': real_pub_pem.decode()
        }

        self.mock_db.get_file_for_download.return_value = mock_file_row
        self.mock_db.get_user.return_value = mock_user_data

        with patch('core.secure_share.decrypt_private_key'), \
             patch('core.secure_share.serialization.load_pem_private_key'), \
             patch('core.secure_share.decrypt_sym_key_with_private'), \
             patch('core.secure_share.Fernet') as mock_fernet, \
             patch('core.secure_share.verify_signature') as mock_verify, \
             patch('builtins.open', unittest.mock.mock_open()):
            
            # Setup mock behavior
            mock_fernet.return_value.decrypt.return_value = b"decrypted_content"
            mock_verify.return_value = True # Simulate valid signature
            
            result = self.system.download_file("123", "downloads/test.txt", "password")
            
            self.assertTrue(result)

if __name__ == '__main__':
    unittest.main()