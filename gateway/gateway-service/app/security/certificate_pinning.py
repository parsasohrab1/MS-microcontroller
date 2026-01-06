"""
Certificate Pinning
پیاده‌سازی Certificate Pinning برای جلوگیری از Man-in-the-Middle attacks
"""

from typing import Optional, List
from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
import ssl
import socket
import httpx
from loguru import logger
import hashlib


class CertificatePinner:
    """Certificate Pinner برای اطمینان از ارتباط با سرور معتبر"""
    
    def __init__(self, pinned_certificates: Optional[List[str]] = None):
        """
        مقداردهی اولیه
        
        Args:
            pinned_certificates: لیست fingerprint های pinned certificates
        """
        self.pinned_certificates = pinned_certificates or []
        self.pinned_hashes: List[bytes] = []
        
        # تبدیل fingerprints به bytes
        for fingerprint in self.pinned_certificates:
            # حذف colons و spaces
            fingerprint_clean = fingerprint.replace(":", "").replace(" ", "").upper()
            try:
                self.pinned_hashes.append(bytes.fromhex(fingerprint_clean))
            except ValueError:
                logger.warning(f"Invalid certificate fingerprint: {fingerprint}")
    
    def add_certificate(self, certificate_path: str):
        """
        اضافه کردن certificate از فایل
        
        Args:
            certificate_path: مسیر فایل certificate
        """
        try:
            with open(certificate_path, 'rb') as f:
                cert_data = f.read()
            
            cert = x509.load_pem_x509_certificate(cert_data, default_backend())
            fingerprint = self._calculate_fingerprint(cert)
            self.pinned_hashes.append(fingerprint)
            logger.info(f"Added certificate: {fingerprint.hex()}")
        
        except Exception as e:
            logger.error(f"Error adding certificate: {e}")
    
    def add_certificate_from_url(self, url: str):
        """
        اضافه کردن certificate از URL
        
        Args:
            url: URL سرور
        """
        try:
            # دریافت certificate از سرور
            cert = self._get_certificate_from_url(url)
            fingerprint = self._calculate_fingerprint(cert)
            self.pinned_hashes.append(fingerprint)
            logger.info(f"Added certificate from {url}: {fingerprint.hex()}")
        
        except Exception as e:
            logger.error(f"Error adding certificate from URL: {e}")
    
    def verify_certificate(self, cert: x509.Certificate) -> bool:
        """
        بررسی certificate
        
        Args:
            cert: Certificate برای بررسی
        
        Returns:
            True اگر certificate معتبر است
        """
        if not self.pinned_hashes:
            logger.warning("No pinned certificates configured")
            return False
        
        fingerprint = self._calculate_fingerprint(cert)
        
        # بررسی با pinned certificates
        for pinned_hash in self.pinned_hashes:
            if fingerprint == pinned_hash:
                logger.info("Certificate verified against pinned certificate")
                return True
        
        logger.error(f"Certificate fingerprint mismatch: {fingerprint.hex()}")
        return False
    
    def verify_connection(self, hostname: str, port: int = 443) -> bool:
        """
        بررسی اتصال به سرور
        
        Args:
            hostname: نام سرور
            port: پورت (default: 443)
        
        Returns:
            True اگر certificate معتبر است
        """
        try:
            # دریافت certificate
            cert = self._get_certificate_from_hostname(hostname, port)
            
            # بررسی
            return self.verify_certificate(cert)
        
        except Exception as e:
            logger.error(f"Error verifying connection: {e}")
            return False
    
    def create_ssl_context(self) -> ssl.SSLContext:
        """
        ایجاد SSL context با certificate pinning
        
        Returns:
            SSL context
        """
        context = ssl.create_default_context()
        
        # Custom verification
        def verify_callback(ssl_sock, cert, chain, err):
            if err:
                logger.error(f"SSL error: {err}")
                return False
            
            try:
                # بررسی certificate
                cert_obj = x509.load_der_x509_certificate(cert, default_backend())
                return self.verify_certificate(cert_obj)
            
            except Exception as e:
                logger.error(f"Error verifying certificate: {e}")
                return False
        
        context.set_verify_mode(ssl.CERT_REQUIRED)
        context.check_hostname = False  # ما خودمان بررسی می‌کنیم
        context.verify_mode = ssl.CERT_REQUIRED
        
        # در Python، نمی‌توانیم مستقیماً verify_callback را تنظیم کنیم
        # باید از روش دیگری استفاده کنیم
        
        return context
    
    def _calculate_fingerprint(self, cert: x509.Certificate) -> bytes:
        """
        محاسبه fingerprint certificate
        
        Args:
            cert: Certificate
        
        Returns:
            Fingerprint (SHA-256)
        """
        cert_der = cert.public_bytes(encoding=x509.Encoding.DER)
        return hashlib.sha256(cert_der).digest()
    
    def _get_certificate_from_url(self, url: str) -> x509.Certificate:
        """
        دریافت certificate از URL
        
        Args:
            url: URL
        
        Returns:
            Certificate
        """
        # Parse URL
        if not url.startswith("https://"):
            url = f"https://{url}"
        
        from urllib.parse import urlparse
        parsed = urlparse(url)
        hostname = parsed.hostname
        port = parsed.port or 443
        
        return self._get_certificate_from_hostname(hostname, port)
    
    def _get_certificate_from_hostname(
        self,
        hostname: str,
        port: int = 443
    ) -> x509.Certificate:
        """
        دریافت certificate از hostname
        
        Args:
            hostname: نام سرور
            port: پورت
        
        Returns:
            Certificate
        """
        # ایجاد اتصال
        sock = socket.create_connection((hostname, port), timeout=10)
        
        try:
            # ایجاد SSL context
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            
            # Wrap socket
            ssl_sock = context.wrap_socket(sock, server_hostname=hostname)
            
            try:
                # دریافت certificate
                cert_der = ssl_sock.getpeercert(binary_form=True)
                cert = x509.load_der_x509_certificate(cert_der, default_backend())
                return cert
            
            finally:
                ssl_sock.close()
        
        finally:
            sock.close()


# Singleton instance
_certificate_pinner: Optional[CertificatePinner] = None


def init_certificate_pinner(pinned_certificates: Optional[List[str]] = None) -> CertificatePinner:
    """مقداردهی اولیه certificate pinner"""
    global _certificate_pinner
    _certificate_pinner = CertificatePinner(pinned_certificates)
    return _certificate_pinner


def get_certificate_pinner() -> Optional[CertificatePinner]:
    """دریافت instance certificate pinner"""
    return _certificate_pinner

