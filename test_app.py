#!/usr/bin/env python3
"""
CryptoShare Application Test Suite
Tests all major functionality of the secure file sharing system
"""

import requests
import base64
import os
import time
from pathlib import Path
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa


class CryptoShareTester:
    def __init__(self, api_base="http://localhost:8000"):
        self.api_base = api_base
        self.test_users = []
        self.test_files = []
        self.tokens = {}
        
    def print_header(self, text):
        """Print a formatted header"""
        print(f"\n{'='*70}")
        print(f"  {text}")
        print(f"{'='*70}")
    
    def print_test(self, test_name, passed, message=""):
        """Print test result"""
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {test_name}")
        if message:
            print(f"       {message}")
    
    def test_backend_connection(self):
        """Test if backend is running"""
        self.print_header("Testing Backend Connection")
        try:
            response = requests.get(f"{self.api_base}/", timeout=5)
            if response.status_code == 200:
                data = response.json()
                self.print_test("Backend Connection", True, f"Message: {data.get('message')}")
                return True
            else:
                self.print_test("Backend Connection", False, f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.print_test("Backend Connection", False, f"Error: {str(e)}")
            return False
    
    def generate_test_keys(self):
        """Generate RSA key pair for testing"""
        private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        public_pem = private_key.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        return private_pem, public_pem
    
    def test_user_registration(self, username, password):
        """Test user registration"""
        self.print_header(f"Testing User Registration - {username}")
        
        try:
            # Generate keys
            priv_pem, pub_pem = self.generate_test_keys()
            salt = os.urandom(16)
            
            # Mock encrypted private key (for testing)
            priv_enc = b"mock_encrypted_private_key_" + os.urandom(32)
            
            payload = {
                "username": username,
                "password": password,
                "salt": base64.urlsafe_b64encode(salt).decode('ascii').rstrip('='),
                "private_key_enc": base64.urlsafe_b64encode(priv_enc).decode('ascii').rstrip('='),
                "public_key_pem": pub_pem.decode('ascii')
            }
            
            response = requests.post(f"{self.api_base}/auth/register", json=payload, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                self.tokens[username] = data.get("access_token")
                self.test_users.append(username)
                self.print_test(f"Register {username}", True, f"Token received")
                return True
            else:
                error = response.json().get("detail", "Unknown error")
                self.print_test(f"Register {username}", False, f"Error: {error}")
                return False
                
        except Exception as e:
            self.print_test(f"Register {username}", False, f"Exception: {str(e)}")
            return False
    
    def test_user_login(self, username, password):
        """Test user login"""
        self.print_header(f"Testing User Login - {username}")
        
        try:
            data = {
                "username": username,
                "password": password
            }
            
            response = requests.post(
                f"{self.api_base}/auth/login",
                data=data,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                self.tokens[username] = result.get("access_token")
                self.print_test(f"Login {username}", True, "Token received")
                return True
            else:
                self.print_test(f"Login {username}", False, f"Status: {response.status_code}")
                return False
                
        except Exception as e:
            self.print_test(f"Login {username}", False, f"Exception: {str(e)}")
            return False
    
    def test_list_users(self):
        """Test listing all users"""
        self.print_header("Testing List Users")
        
        try:
            response = requests.get(f"{self.api_base}/users", timeout=5)
            
            if response.status_code == 200:
                users = response.json()
                self.print_test("List Users", True, f"Found {len(users)} users: {', '.join(users)}")
                return True
            else:
                self.print_test("List Users", False, f"Status: {response.status_code}")
                return False
                
        except Exception as e:
            self.print_test("List Users", False, f"Exception: {str(e)}")
            return False
    
    def test_get_public_key(self, username):
        """Test getting a user's public key"""
        self.print_header(f"Testing Get Public Key - {username}")
        
        try:
            response = requests.get(f"{self.api_base}/users/{username}/public-key", timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                pub_key = data.get("public_key_pem", "")
                key_preview = pub_key[:50] + "..." if len(pub_key) > 50 else pub_key
                self.print_test(f"Get Public Key ({username})", True, f"Key: {key_preview}")
                return True
            else:
                self.print_test(f"Get Public Key ({username})", False, f"Status: {response.status_code}")
                return False
                
        except Exception as e:
            self.print_test(f"Get Public Key ({username})", False, f"Exception: {str(e)}")
            return False
    
    def test_get_my_public_key(self, username):
        """Test getting current user's public key (authenticated)"""
        self.print_header(f"Testing Get My Public Key - {username}")
        
        if username not in self.tokens:
            self.print_test(f"Get My Public Key ({username})", False, "No token available")
            return False
        
        try:
            headers = {"Authorization": f"Bearer {self.tokens[username]}"}
            response = requests.get(f"{self.api_base}/users/me/public-key", headers=headers, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                pub_key = data.get("public_key_pem", "")
                key_preview = pub_key[:50] + "..." if len(pub_key) > 50 else pub_key
                self.print_test(f"Get My Public Key ({username})", True, f"Key: {key_preview}")
                return True
            else:
                error = response.json().get("detail", "Unknown error")
                self.print_test(f"Get My Public Key ({username})", False, f"Error: {error}")
                return False
                
        except Exception as e:
            self.print_test(f"Get My Public Key ({username})", False, f"Exception: {str(e)}")
            return False
    
    def test_create_test_file(self, filename="test_file.txt", content="Hello, this is a test file!"):
        """Create a test file for sharing"""
        self.print_header(f"Creating Test File - {filename}")
        
        try:
            test_path = Path(filename)
            test_path.write_text(content)
            self.print_test(f"Create Test File", True, f"Created: {filename}")
            return str(test_path.absolute())
        except Exception as e:
            self.print_test(f"Create Test File", False, f"Exception: {str(e)}")
            return None
    
    def test_file_operations(self, owner_username):
        """Test file list/download operations"""
        self.print_header(f"Testing File Operations - {owner_username}")
        
        if owner_username not in self.tokens:
            self.print_test(f"File Operations ({owner_username})", False, "No token available")
            return False
        
        try:
            headers = {"Authorization": f"Bearer {self.tokens[owner_username]}"}
            response = requests.get(f"{self.api_base}/files", headers=headers, timeout=5)
            
            if response.status_code == 200:
                files = response.json()
                self.print_test(f"List Files ({owner_username})", True, f"Found {len(files)} files")
                
                # Print file details
                for f in files:
                    print(f"       - {f.get('filename')} (Owner: {f.get('owner')})")
                
                return True
            else:
                self.print_test(f"List Files ({owner_username})", False, f"Status: {response.status_code}")
                return False
                
        except Exception as e:
            self.print_test(f"File Operations ({owner_username})", False, f"Exception: {str(e)}")
            return False
    
    def test_invalid_login(self):
        """Test login with invalid credentials"""
        self.print_header("Testing Invalid Login")
        
        try:
            data = {
                "username": "nonexistent_user",
                "password": "wrong_password"
            }
            
            response = requests.post(f"{self.api_base}/auth/login", data=data, timeout=5)
            
            if response.status_code == 401:
                self.print_test("Invalid Login (Expected Failure)", True, "Correctly rejected")
                return True
            else:
                self.print_test("Invalid Login (Expected Failure)", False, f"Unexpected status: {response.status_code}")
                return False
                
        except Exception as e:
            self.print_test("Invalid Login (Expected Failure)", False, f"Exception: {str(e)}")
            return False
    
    def test_unauthorized_access(self):
        """Test accessing protected endpoint without token"""
        self.print_header("Testing Unauthorized Access")
        
        try:
            response = requests.get(f"{self.api_base}/users/me/public-key", timeout=5)
            
            if response.status_code == 401:
                self.print_test("Unauthorized Access (Expected Failure)", True, "Correctly rejected")
                return True
            else:
                self.print_test("Unauthorized Access (Expected Failure)", False, f"Unexpected status: {response.status_code}")
                return False
                
        except Exception as e:
            self.print_test("Unauthorized Access (Expected Failure)", False, f"Exception: {str(e)}")
            return False
    
    def cleanup(self):
        """Clean up test files"""
        self.print_header("Cleanup")
        
        try:
            test_file = Path("test_file.txt")
            if test_file.exists():
                test_file.unlink()
                self.print_test("Cleanup Test File", True, "Removed test_file.txt")
        except Exception as e:
            self.print_test("Cleanup Test File", False, f"Exception: {str(e)}")
    
    def run_all_tests(self):
        """Run complete test suite"""
        print("\n" + "="*70)
        print("  CRYPTOSHARE APPLICATION TEST SUITE")
        print("="*70)
        
        results = {
            "passed": 0,
            "failed": 0,
            "total": 0
        }
        
        # Test 1: Backend Connection
        if self.test_backend_connection():
            results["passed"] += 1
        else:
            results["failed"] += 1
            print("\n❌ Backend not running! Start with: docker-compose up -d")
            return results
        results["total"] += 1
        
        time.sleep(0.5)
        
        # Test 2: User Registration
        test_user1 = f"testuser1_{int(time.time())}"
        test_user2 = f"testuser2_{int(time.time())}"
        
        if self.test_user_registration(test_user1, "testpass123"):
            results["passed"] += 1
        else:
            results["failed"] += 1
        results["total"] += 1
        
        time.sleep(0.5)
        
        if self.test_user_registration(test_user2, "testpass456"):
            results["passed"] += 1
        else:
            results["failed"] += 1
        results["total"] += 1
        
        time.sleep(0.5)
        
        # Test 3: User Login
        if self.test_user_login(test_user1, "testpass123"):
            results["passed"] += 1
        else:
            results["failed"] += 1
        results["total"] += 1
        
        time.sleep(0.5)
        
        # Test 4: List Users
        if self.test_list_users():
            results["passed"] += 1
        else:
            results["failed"] += 1
        results["total"] += 1
        
        time.sleep(0.5)
        
        # Test 5: Get Public Key
        if self.test_get_public_key(test_user1):
            results["passed"] += 1
        else:
            results["failed"] += 1
        results["total"] += 1
        
        time.sleep(0.5)
        
        # Test 6: Get My Public Key (Authenticated)
        if self.test_get_my_public_key(test_user1):
            results["passed"] += 1
        else:
            results["failed"] += 1
        results["total"] += 1
        
        time.sleep(0.5)
        
        # Test 7: File Operations
        if self.test_file_operations(test_user1):
            results["passed"] += 1
        else:
            results["failed"] += 1
        results["total"] += 1
        
        time.sleep(0.5)
        
        # Test 8: Invalid Login (Expected Failure)
        if self.test_invalid_login():
            results["passed"] += 1
        else:
            results["failed"] += 1
        results["total"] += 1
        
        time.sleep(0.5)
        
        # Test 9: Unauthorized Access (Expected Failure)
        if self.test_unauthorized_access():
            results["passed"] += 1
        else:
            results["failed"] += 1
        results["total"] += 1
        
        # Cleanup
        self.cleanup()
        
        # Print Summary
        self.print_header("TEST SUMMARY")
        print(f"\nTotal Tests:  {results['total']}")
        print(f"✅ Passed:    {results['passed']}")
        print(f"❌ Failed:    {results['failed']}")
        
        success_rate = (results['passed'] / results['total'] * 100) if results['total'] > 0 else 0
        print(f"\nSuccess Rate: {success_rate:.1f}%")
        
        if results['failed'] == 0:
            print("\n🎉 ALL TESTS PASSED! 🎉")
        else:
            print(f"\n⚠️  {results['failed']} test(s) failed. Check output above for details.")
        
        print("\n" + "="*70 + "\n")
        
        return results


def main():
    """Main test runner"""
    tester = CryptoShareTester()
    results = tester.run_all_tests()
    
    # Exit with appropriate code
    exit(0 if results['failed'] == 0 else 1)


if __name__ == "__main__":
    main()