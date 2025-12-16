# This class creates the self signed SSL certificates for the secure communication

import os
import datetime
import ssl
from pathlib import Path
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa

class SSLHelper:
    
    def __init__(self, cert_dir=None):

        if cert_dir:
            self.cert_dir = Path(cert_dir)
        else:
            self.cert_dir = Path.home() / '.mydesk' / 'certs'
        
        self.cert_dir.mkdir(parents=True, exist_ok=True)

        self.cert_file = self.cert_dir / 'server.crt'
        self.key_file = self.cert_dir / 'server.key'

    def generate_self_signed_cert(self):
        # Generate private key and the self signed certificate for the communication

        print("Generating self-signed certificate...")

        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )

        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, "IN"),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "Rajasthan"),
            x509.NameAttribute(NameOID.LOCALITY_NAME, "Kota"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "MyDesk"),
            x509.NameAttribute(NameOID.COMMON_NAME, "mydesk.local"),
        ])

        cert = x509.CertificateBuilder().subject_name(
            subject
        ).issuer_name(
            issuer
        ).public_key(
            private_key.public_key()
        ).serial_number(
            x509.random_serial_number()
        ).not_valid_before(
            datetime.datetime.now(datetime.timezone.utc)
        ).not_valid_after(
            datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=365)
        ).add_extension(
            x509.SubjectAlternativeName([
                x509.DNSName("localhost"),
                x509.DNSName("*.local")
                ]),
            critical=False,
        ).sign(private_key, hashes.SHA256())

        with open(self.cert_file, "wb") as f:
            f.write(cert.public_bytes(serialization.Encoding.PEM))

        with open(self.key_file, "wb") as f:
            f.write(private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption()
            ))

        print(f"Certficate saved to {self.cert_file}")
        print(f"Private key saved to {self.key_file}")

    def get_server_ssl_context(self):
        # crete the file if it doesn't exist
        if not self.cert_file.exists() or not self.key_file.exists():
            self.generate_self_signed_cert()

        context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        context.load_cert_chain(self.cert_file, self.key_file)
        return context
    
    def get_client_ssl_context(self):
       
        context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
        # disabled certificate verification for self signed certs
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        
        return context
    
# Test function
if __name__ == "__main__":
    helper = SSLHelper()
    
    # Generate certificate
    helper.generate_self_signed_cert()
    
    # Test contexts
    print("\nTesting SSL contexts...")
    server_ctx = helper.get_server_ssl_context()
    print(f"Server context created: {server_ctx}")
    
    client_ctx = helper.get_client_ssl_context()
    print(f"Client context created: {client_ctx}")