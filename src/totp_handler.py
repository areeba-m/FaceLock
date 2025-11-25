"""
TOTP (Time-based One-Time Password) handler
Implements RFC 6238 for two-factor authentication
"""
import pyotp
import qrcode
from io import BytesIO
from PIL import Image
from typing import Optional
from config.settings import TOTP_INTERVAL, TOTP_DIGITS, TOTP_ISSUER


class TOTPHandler:
    """Handles TOTP generation and verification"""
    
    def __init__(self):
        self.interval = TOTP_INTERVAL
        self.digits = TOTP_DIGITS
        self.issuer = TOTP_ISSUER
    
    def generate_secret(self) -> str:
        """Generate a new random TOTP secret"""
        return pyotp.random_base32()
    
    def get_totp_uri(self, secret: str, username: str) -> str:
        """
        Generate TOTP provisioning URI for QR code
        Compatible with Google Authenticator, Authy, etc.
        """
        totp = pyotp.TOTP(secret, interval=self.interval, digits=self.digits)
        return totp.provisioning_uri(
            name=username,
            issuer_name=self.issuer
        )
    
    def generate_qr_code(self, secret: str, username: str) -> Image.Image:
        """
        Generate QR code image for TOTP setup
        """
        uri = self.get_totp_uri(secret, username)
        
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(uri)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        return img
    
    def get_current_otp(self, secret: str) -> str:
        """
        Get current TOTP code
        """
        totp = pyotp.TOTP(secret, interval=self.interval, digits=self.digits)
        return totp.now()
    
    def verify_otp(self, secret: str, provided_otp: str, window: int = 1) -> bool:
        """
        Verify provided OTP against secret
        window: number of time steps to check before/after current time
        """
        if not provided_otp or not provided_otp.isdigit():
            return False
        
        totp = pyotp.TOTP(secret, interval=self.interval, digits=self.digits)
        
        # Verify with window for clock skew tolerance
        return totp.verify(provided_otp, valid_window=window)
    
    def get_remaining_time(self, secret: str) -> int:
        """
        Get remaining seconds until current OTP expires
        """
        import time
        current_time = int(time.time())
        time_remaining = self.interval - (current_time % self.interval)
        return time_remaining
    
    def save_qr_code(self, secret: str, username: str, filepath: str):
        """
        Save QR code to file
        """
        img = self.generate_qr_code(secret, username)
        img.save(filepath)
    
    def get_backup_codes(self, count: int = 10) -> list:
        """
        Generate backup codes for emergency access
        """
        import secrets
        import string
        
        backup_codes = []
        for _ in range(count):
            code = ''.join(secrets.choice(string.digits) for _ in range(8))
            # Format as XXXX-XXXX
            formatted_code = f"{code[:4]}-{code[4:]}"
            backup_codes.append(formatted_code)
        
        return backup_codes


# Singleton instance
totp_handler = TOTPHandler()