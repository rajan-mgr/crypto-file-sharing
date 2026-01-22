#!/usr/bin/env python3
"""
Setup script to create Certificate Authority (CA) for SecureShare PKI
Run this ONCE before starting the backend server
"""

import os
from pathlib import Path
from datetime import datetime, timedelta, timezone
from cryptography import x509
from cryptography.x509.oid import NameOID, ExtensionOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa


def create_ca():
    """Create self-signed Certificate Authority"""
    
    # Create pki directory if it doesn't exist
    pki_dir = Path("./pki")
    pki_dir.mkdir(exist_ok=True)
    
    ca_key_path = pki_dir / "ca.key"
    ca_cert_path = pki_dir / "ca.crt"
    
    # Check if CA already exists
    if ca_key_path.exists() and ca_cert_path.exists():
        print("⚠️  CA already exists!")
        response = input("Do you want to recreate it? This will invalidate all existing certificates! (yes/no): ")
        if response.lower() not in ['yes', 'y']:
            print("❌ CA creation cancelled")
            return False
    
    print("🔐 Generating CA private key (4096-bit RSA)...")
    # Generate CA private key (4096-bit for higher security)
    ca_private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=4096
    )
    
    # Create CA certificate (self-signed)
    print("📜 Creating self-signed CA certificate...")
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, "NP"),
        x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "Bagmati"),
        x509.NameAttribute(NameOID.LOCALITY_NAME, "Kathmandu"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "SecureShare"),
        x509.NameAttribute(NameOID.ORGANIZATIONAL_UNIT_NAME, "Certificate Authority"),
        x509.NameAttribute(NameOID.COMMON_NAME, "SecureShare Root CA"),
    ])
    
    ca_cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(ca_private_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.now(timezone.utc))
        .not_valid_after(datetime.now(timezone.utc) + timedelta(days=3650))  # 10 years
        # CA extensions
        .add_extension(
            x509.BasicConstraints(ca=True, path_length=0),
            critical=True,
        )
        .add_extension(
            x509.KeyUsage(
                digital_signature=True,
                key_cert_sign=True,
                crl_sign=True,
                key_encipherment=False,
                content_commitment=False,
                data_encipherment=False,
                key_agreement=False,
                encipher_only=False,
                decipher_only=False,
            ),
            critical=True,
        )
        .add_extension(
            x509.SubjectKeyIdentifier.from_public_key(ca_private_key.public_key()),
            critical=False,
        )
        .sign(ca_private_key, hashes.SHA256())
    )
    
    # Save CA private key (unencrypted for server use - in production, encrypt this!)
    print("💾 Saving CA private key...")
    with open(ca_key_path, "wb") as f:
        f.write(ca_private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        ))
    
    # Set restrictive permissions on CA private key
    os.chmod(ca_key_path, 0o600)
    
    # Save CA certificate
    print("💾 Saving CA certificate...")
    with open(ca_cert_path, "wb") as f:
        f.write(ca_cert.public_bytes(serialization.Encoding.PEM))
    
    print("\n" + "=" * 70)
    print("✅ Certificate Authority created successfully!")
    print("=" * 70)
    print(f"\n📁 CA Files Location:")
    print(f"   Private Key: {ca_key_path.absolute()}")
    print(f"   Certificate: {ca_cert_path.absolute()}")
    print(f"\n📋 CA Certificate Details:")
    print(f"   Subject: {ca_cert.subject.rfc4514_string()}")
    print(f"   Serial:  {hex(ca_cert.serial_number)}")
    print(f"   Valid:   {ca_cert.not_valid_before_utc} to {ca_cert.not_valid_after_utc}")
    print(f"\n⚠️  SECURITY WARNING:")
    print(f"   Keep {ca_key_path} secure! It can sign certificates for any user.")
    print(f"   In production, encrypt this key with a strong passphrase.")
    print("\n✅ You can now start the backend server.\n")
    
    return True


def verify_ca():
    """Verify CA exists and is valid"""
    pki_dir = Path("./pki")
    ca_key_path = pki_dir / "ca.key"
    ca_cert_path = pki_dir / "ca.crt"
    
    if not ca_key_path.exists():
        print("❌ CA private key not found!")
        return False
    
    if not ca_cert_path.exists():
        print("❌ CA certificate not found!")
        return False
    
    try:
        # Load and verify CA cert
        with open(ca_cert_path, "rb") as f:
            ca_cert = x509.load_pem_x509_certificate(f.read())
        
        print("✅ CA certificate is valid")
        print(f"   Subject: {ca_cert.subject.rfc4514_string()}")
        print(f"   Serial: {hex(ca_cert.serial_number)}")
        print(f"   Valid until: {ca_cert.not_valid_after_utc}")
        
        # Check if expired
        if datetime.now(timezone.utc) > ca_cert.not_valid_after_utc:
            print("⚠️  WARNING: CA certificate has expired!")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error verifying CA: {e}")
        return False


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print(" SecureShare PKI - Certificate Authority Setup")
    print("=" * 70 + "\n")
    
    # Check if CA exists
    pki_dir = Path("./pki")
    ca_exists = (pki_dir / "ca.key").exists() and (pki_dir / "ca.crt").exists()
    
    if ca_exists:
        print("ℹ️  CA already exists. Verifying...\n")
        if verify_ca():
            print("\n✅ CA is ready to use!")
            print("\nTo recreate CA, run this script again and choose 'yes' when prompted.\n")
        else:
            print("\n⚠️  CA verification failed. Recreating CA...\n")
            create_ca()
    else:
        print("ℹ️  No CA found. Creating new CA...\n")
        create_ca()