"""
KOMUDHA Boutique - Configuration
Production-Ready Flask Configuration
"""
import os
from datetime import timedelta


class Config:
    # ── Flask Core ──────────────────────────────────────────────────
    SECRET_KEY = os.environ.get('SECRET_KEY', 'komudha-super-secret-key-change-in-production-2024')
    DEBUG = False
    TESTING = False

    # ── Session ─────────────────────────────────────────────────────
    PERMANENT_SESSION_LIFETIME = timedelta(days=30)
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'

    # ── Database ─────────────────────────────────────────────────────
    DB_HOST = os.environ.get('DB_HOST', 'localhost')
    DB_PORT = int(os.environ.get('DB_PORT', 3306))
    DB_USER = os.environ.get('DB_USER', 'root')
    DB_PASSWORD = os.environ.get('DB_PASSWORD', '')
    DB_NAME = os.environ.get('DB_NAME', 'komudha_boutique')

    # ── Uploads ──────────────────────────────────────────────────────
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'static', 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

    # ── Razorpay ────────────────────────────────────────────────────
    RAZORPAY_KEY_ID = os.environ.get('RAZORPAY_KEY_ID', 'rzp_test_your_key_here')
    RAZORPAY_KEY_SECRET = os.environ.get('RAZORPAY_KEY_SECRET', 'your_secret_here')

    # ── SMS / OTP ────────────────────────────────────────────────────
    # Using Fast2SMS or Twilio - configure below
    SMS_API_KEY = os.environ.get('SMS_API_KEY', 'your_fast2sms_api_key')
    SMS_SENDER_ID = os.environ.get('SMS_SENDER_ID', 'KOMDHA')
    OTP_EXPIRY_MINUTES = 10
    # For development: set to True to use console OTP (no SMS sent)
    DEV_MODE_OTP = os.environ.get('DEV_MODE_OTP', 'True') == 'True'
    DEV_OTP = '123456'  # Fixed OTP for development

    # ── Admin ────────────────────────────────────────────────────────
    ADMIN_MOBILE = os.environ.get('ADMIN_MOBILE', '9876543210')

    # ── WhatsApp ─────────────────────────────────────────────────────
    WHATSAPP_NUMBER = os.environ.get('WHATSAPP_NUMBER', '919876543210')

    # ── Shipping ─────────────────────────────────────────────────────
    SHIPPING_CHARGE = 99
    FREE_SHIPPING_ABOVE = 999

    # ── Pagination ───────────────────────────────────────────────────
    PRODUCTS_PER_PAGE = 12


class DevelopmentConfig(Config):
    DEBUG = True
    DEV_MODE_OTP = True


class ProductionConfig(Config):
    DEBUG = False
    DEV_MODE_OTP = False
    SESSION_COOKIE_SECURE = True


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
