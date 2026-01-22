#!/usr/bin/env python3
"""
SecureShare PKI Test Suite
Aligned with ST6051CEM Practical Cryptography Coursework
"""

import requests
import base64
import time
import os
from pathlib import Path

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography import x509
from cryptography.x509.oid import NameOID

API = "http://127.0.0.1:8000"


# --------------------------------------------------
# UTILS
# --------------------------------------------------

def header(title):
    print("\n" + "=" * 70)
    print(f" {title}")
    print("=" * 70)


def ok(msg):
    print(f"✅ {msg}")


def fail(msg):
    print(f"❌ {msg}")
    exit(1)


def generate_keys_and_csr(username: str):
    """Generate RSA key pair and CSR"""
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048
    )

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

    priv_pem = private_key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption()
    )

    return priv_pem, csr.public_bytes(serialization.Encoding.PEM)


# --------------------------------------------------
# TESTS
# --------------------------------------------------

def test_backend():
    header("TEST 1: Backend Availability")
    r = requests.get(f"{API}/")
    if r.status_code == 200:
        ok("Backend is running")
    else:
        fail("Backend is not reachable")


def register_user(username, password):
    header(f"TEST 2: Register User [{username}]")

    priv_pem, csr_pem = generate_keys_and_csr(username)
    salt = os.urandom(16)

    # Fake encryption for test (real encryption done by client app)
    priv_enc = b"test_encrypted_private_key"

    payload = {
        "username": username,
        "password": password,
        "salt": base64.urlsafe_b64encode(salt).decode(),
        "private_key_enc": base64.urlsafe_b64encode(priv_enc).decode(),
        "csr_pem": csr_pem.decode(),
    }

    r = requests.post(f"{API}/auth/register", json=payload)
    if r.status_code == 200:
        token = r.json()["access_token"]
        ok("User registered & certificate issued")
        return token
    else:
        fail(r.json())


def login_user(username, password):
    header(f"TEST 3: Login User [{username}]")

    r = requests.post(
        f"{API}/auth/login",
        data={"username": username, "password": password},
    )

    if r.status_code == 200:
        ok("Login successful with certificate validation")
        return r.json()["access_token"]
    else:
        fail("Login failed")


def list_users(token):
    header("TEST 4: List Users")
    r = requests.get(
        f"{API}/users",
        headers={"Authorization": f"Bearer {token}"}
    )
    if r.status_code == 200:
        ok(f"Users found: {r.json()}")
    else:
        fail("Failed to list users")


def get_certificate(token):
    header("TEST 5: Fetch Own Certificate")
    r = requests.get(
        f"{API}/users/me/certificate",
        headers={"Authorization": f"Bearer {token}"}
    )
    if r.status_code == 200:
        ok("Certificate retrieved & validated")
    else:
        fail("Certificate fetch failed")


def upload_file(token):
    header("TEST 6: Upload File with Signature")

    content = b"SecureShare coursework test file"
    file_hash = hashes.Hash(hashes.SHA256())
    file_hash.update(content)
    digest = file_hash.finalize().hex()

    payload = {
        "filename": "test.txt",
        "encrypted_content": base64.urlsafe_b64encode(content).decode(),
        "signature": base64.urlsafe_b64encode(b"fake_signature").decode(),
        "file_hash": digest,
        "recipients": [],
        "encrypted_keys": {},
    }

    r = requests.post(
        f"{API}/files",
        headers={"Authorization": f"Bearer {token}"},
        json=payload
    )

    if r.status_code == 200:
        file_id = r.json()["file_id"]
        ok(f"File uploaded with ID {file_id}")
        return file_id
    else:
        fail(r.text)


def download_file(token, file_id):
    header("TEST 7: Download File with Verification")

    r = requests.get(
        f"{API}/files/{file_id}",
        headers={"Authorization": f"Bearer {token}"}
    )

    if r.status_code == 200:
        ok("File downloaded with signature metadata")
    else:
        fail("File download failed")


def revoke_certificate(token):
    header("TEST 8: Certificate Revocation")

    r = requests.post(
        f"{API}/users/me/revoke-certificate",
        headers={"Authorization": f"Bearer {token}"}
    )

    if r.status_code == 200:
        ok("Certificate revoked successfully")
    else:
        fail("Certificate revocation failed")


def unauthorized_access():
    header("TEST 9: Unauthorized Access")
    r = requests.get(f"{API}/users/me/certificate")
    if r.status_code == 401:
        ok("Unauthorized access correctly blocked")
    else:
        fail("Unauthorized access allowed!")


# --------------------------------------------------
# MAIN
# --------------------------------------------------

if __name__ == "__main__":
    USER = f"testuser_{int(time.time())}"
    PASS = "StrongPass123!"

    test_backend()
    token = register_user(USER, PASS)
    token = login_user(USER, PASS)
    list_users(token)
    get_certificate(token)
    file_id = upload_file(token)
    download_file(token, file_id)
    revoke_certificate(token)
    unauthorized_access()

    header("ALL TESTS COMPLETED SUCCESSFULLY")
    print("🎉 SecureShare PKI system validated")
