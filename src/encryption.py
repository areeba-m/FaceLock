"""
Encryption utilities for secure data storage
Uses Fernet (symmetric encryption) for encrypting facial embeddings and TOTP secrets
"""
import os
import hashlib
from cryptography.fernet import Fernet
from config.settings import ENCRYPTION_KEY_FILE


class EncryptionManager:
    """Handles encryption and decryption of sensitive data"""
    
    def __init__(self):
        self.cipher_suite = self._load_or_create_key()
    
    def _load_or_create_key(self) -> Fernet:
        """Load existing encryption key or create a new one"""
        if os.path.exists(ENCRYPTION_KEY_FILE):
            with open(ENCRYPTION_KEY_FILE, 'rb') as key_file:
                key = key_file.read()
        else:
            key = Fernet.generate_key()
            with open(ENCRYPTION_KEY_FILE, 'wb') as key_file:
                key_file.write(key)
            # Make key file read-only
            os.chmod(ENCRYPTION_KEY_FILE, 0o400)
        
        return Fernet(key)
    
    def encrypt(self, data: bytes) -> bytes:
        """Encrypt data using Fernet symmetric encryption"""
        return self.cipher_suite.encrypt(data)
    
    def decrypt(self, encrypted_data: bytes) -> bytes:
        """Decrypt data using Fernet symmetric encryption"""
        return self.cipher_suite.decrypt(encrypted_data)
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password using SHA-256 with salt"""
        salt = os.urandom(32)
        key = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt,
            100000  # iterations
        )
        return salt.hex() + key.hex()
    
    @staticmethod
    def verify_password(stored_password: str, provided_password: str) -> bool:
        """Verify a password against its hash"""
        salt = bytes.fromhex(stored_password[:64])
        stored_key = stored_password[64:]
        
        new_key = hashlib.pbkdf2_hmac(
            'sha256',
            provided_password.encode('utf-8'),
            salt,
            100000
        )
        
        return new_key.hex() == stored_key


# Singleton instance
encryption_manager = EncryptionManager()