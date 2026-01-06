"""
End-to-End Encryption
پیاده‌سازی End-to-End Encryption برای محافظت داده‌ها در تمام مسیر
"""

from typing import Optional, Dict
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import os
import base64
from loguru import logger
import json


class E2EEncryption:
    """End-to-End Encryption Manager"""
    
    def __init__(self):
        """مقداردهی اولیه"""
        self.private_key: Optional[rsa.RSAPrivateKey] = None
        self.public_key: Optional[rsa.RSAPublicKey] = None
        self.peer_public_keys: Dict[str, rsa.RSAPublicKey] = {}
        self.session_keys: Dict[str, bytes] = {}
    
    def generate_key_pair(self) -> bool:
        """
        تولید key pair
        
        Returns:
            True در صورت موفقیت
        """
        try:
            self.private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048,
                backend=default_backend()
            )
            self.public_key = self.private_key.public_key()
            logger.info("Generated RSA key pair for E2E encryption")
            return True
        
        except Exception as e:
            logger.error(f"Error generating key pair: {e}")
            return False
    
    def load_private_key(self, key_path: str, password: Optional[bytes] = None) -> bool:
        """
        بارگذاری private key از فایل
        
        Args:
            key_path: مسیر فایل
            password: رمز عبور (اختیاری)
        
        Returns:
            True در صورت موفقیت
        """
        try:
            with open(key_path, 'rb') as f:
                key_data = f.read()
            
            self.private_key = serialization.load_pem_private_key(
                key_data,
                password=password,
                backend=default_backend()
            )
            self.public_key = self.private_key.public_key()
            logger.info("Loaded private key")
            return True
        
        except Exception as e:
            logger.error(f"Error loading private key: {e}")
            return False
    
    def save_private_key(self, key_path: str, password: Optional[bytes] = None) -> bool:
        """
        ذخیره private key در فایل
        
        Args:
            key_path: مسیر فایل
            password: رمز عبور (اختیاری)
        
        Returns:
            True در صورت موفقیت
        """
        if not self.private_key:
            return False
        
        try:
            encryption = serialization.NoEncryption()
            if password:
                encryption = serialization.BestAvailableEncryption(password)
            
            pem = self.private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=encryption
            )
            
            with open(key_path, 'wb') as f:
                f.write(pem)
            
            logger.info("Saved private key")
            return True
        
        except Exception as e:
            logger.error(f"Error saving private key: {e}")
            return False
    
    def get_public_key_pem(self) -> Optional[str]:
        """
        دریافت public key به صورت PEM
        
        Returns:
            Public key (PEM format)
        """
        if not self.public_key:
            return None
        
        try:
            pem = self.public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )
            return pem.decode('utf-8')
        
        except Exception as e:
            logger.error(f"Error getting public key: {e}")
            return None
    
    def add_peer_public_key(self, peer_id: str, public_key_pem: str) -> bool:
        """
        اضافه کردن public key طرف مقابل
        
        Args:
            peer_id: شناسه طرف مقابل
            public_key_pem: Public key (PEM format)
        
        Returns:
            True در صورت موفقیت
        """
        try:
            public_key = serialization.load_pem_public_key(
                public_key_pem.encode('utf-8'),
                backend=default_backend()
            )
            
            self.peer_public_keys[peer_id] = public_key
            logger.info(f"Added public key for peer: {peer_id}")
            return True
        
        except Exception as e:
            logger.error(f"Error adding peer public key: {e}")
            return False
    
    def generate_session_key(self, peer_id: str) -> Optional[bytes]:
        """
        تولید session key برای peer
        
        Args:
            peer_id: شناسه طرف مقابل
        
        Returns:
            Session key یا None
        """
        if peer_id not in self.peer_public_keys:
            logger.error(f"Peer public key not found: {peer_id}")
            return None
        
        try:
            # تولید random session key
            session_key = os.urandom(32)  # AES-256
            
            # رمزگذاری با public key طرف مقابل
            peer_public_key = self.peer_public_keys[peer_id]
            encrypted_key = peer_public_key.encrypt(
                session_key,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )
            
            # ذخیره session key
            self.session_keys[peer_id] = session_key
            
            logger.info(f"Generated session key for peer: {peer_id}")
            return encrypted_key
        
        except Exception as e:
            logger.error(f"Error generating session key: {e}")
            return None
    
    def set_session_key(self, peer_id: str, encrypted_key: bytes) -> bool:
        """
        تنظیم session key (رمزگشایی شده)
        
        Args:
            peer_id: شناسه طرف مقابل
            encrypted_key: Session key رمزگذاری شده
        
        Returns:
            True در صورت موفقیت
        """
        if not self.private_key:
            return False
        
        try:
            # رمزگشایی session key
            session_key = self.private_key.decrypt(
                encrypted_key,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )
            
            # ذخیره
            self.session_keys[peer_id] = session_key
            logger.info(f"Set session key for peer: {peer_id}")
            return True
        
        except Exception as e:
            logger.error(f"Error setting session key: {e}")
            return False
    
    def encrypt_data(self, peer_id: str, data: bytes) -> Optional[bytes]:
        """
        رمزگذاری داده برای peer
        
        Args:
            peer_id: شناسه طرف مقابل
            data: داده برای رمزگذاری
        
        Returns:
            داده رمزگذاری شده یا None
        """
        if peer_id not in self.session_keys:
            logger.error(f"Session key not found for peer: {peer_id}")
            return None
        
        try:
            session_key = self.session_keys[peer_id]
            
            # تولید IV
            iv = os.urandom(16)
            
            # رمزگذاری با AES-256-CBC
            cipher = Cipher(
                algorithms.AES(session_key),
                modes.CBC(iv),
                backend=default_backend()
            )
            encryptor = cipher.encryptor()
            
            # Padding
            pad_length = 16 - (len(data) % 16)
            padded_data = data + bytes([pad_length] * pad_length)
            
            # رمزگذاری
            ciphertext = encryptor.update(padded_data) + encryptor.finalize()
            
            # ترکیب IV و ciphertext
            encrypted = iv + ciphertext
            
            return encrypted
        
        except Exception as e:
            logger.error(f"Error encrypting data: {e}")
            return None
    
    def decrypt_data(self, peer_id: str, encrypted_data: bytes) -> Optional[bytes]:
        """
        رمزگشایی داده از peer
        
        Args:
            peer_id: شناسه طرف مقابل
            encrypted_data: داده رمزگذاری شده
        
        Returns:
            داده رمزگشایی شده یا None
        """
        if peer_id not in self.session_keys:
            logger.error(f"Session key not found for peer: {peer_id}")
            return None
        
        try:
            session_key = self.session_keys[peer_id]
            
            # جدا کردن IV و ciphertext
            iv = encrypted_data[:16]
            ciphertext = encrypted_data[16:]
            
            # رمزگشایی
            cipher = Cipher(
                algorithms.AES(session_key),
                modes.CBC(iv),
                backend=default_backend()
            )
            decryptor = cipher.decryptor()
            
            padded_data = decryptor.update(ciphertext) + decryptor.finalize()
            
            # حذف padding
            pad_length = padded_data[-1]
            data = padded_data[:-pad_length]
            
            return data
        
        except Exception as e:
            logger.error(f"Error decrypting data: {e}")
            return None
    
    def encrypt_json(self, peer_id: str, data: dict) -> Optional[str]:
        """
        رمزگذاری JSON data
        
        Args:
            peer_id: شناسه طرف مقابل
            data: داده JSON
        
        Returns:
            داده رمزگذاری شده (base64) یا None
        """
        try:
            json_data = json.dumps(data).encode('utf-8')
            encrypted = self.encrypt_data(peer_id, json_data)
            
            if encrypted:
                return base64.b64encode(encrypted).decode('utf-8')
            
            return None
        
        except Exception as e:
            logger.error(f"Error encrypting JSON: {e}")
            return None
    
    def decrypt_json(self, peer_id: str, encrypted_data: str) -> Optional[dict]:
        """
        رمزگشایی JSON data
        
        Args:
            peer_id: شناسه طرف مقابل
            encrypted_data: داده رمزگذاری شده (base64)
        
        Returns:
            داده JSON یا None
        """
        try:
            encrypted_bytes = base64.b64decode(encrypted_data)
            decrypted = self.decrypt_data(peer_id, encrypted_bytes)
            
            if decrypted:
                return json.loads(decrypted.decode('utf-8'))
            
            return None
        
        except Exception as e:
            logger.error(f"Error decrypting JSON: {e}")
            return None


# Singleton instance
_e2e_encryption: Optional[E2EEncryption] = None


def init_e2e_encryption() -> E2EEncryption:
    """مقداردهی اولیه E2E encryption"""
    global _e2e_encryption
    _e2e_encryption = E2EEncryption()
    _e2e_encryption.generate_key_pair()
    return _e2e_encryption


def get_e2e_encryption() -> Optional[E2EEncryption]:
    """دریافت instance E2E encryption"""
    return _e2e_encryption

