#!/usr/bin/env python3
"""
KOMUDHA Boutique - Quick Start Script
Run this to start the development server.
"""
import os, sys

# Load .env if present
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

os.environ.setdefault('FLASK_ENV', 'development')
os.environ.setdefault('FLASK_DEBUG', '1')

from app import app

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print("\n" + "="*55)
    print("  🌸  KOMUDHA Boutique — Development Server")
    print("="*55)
    print(f"  🚀  Running at:  http://localhost:{port}")
    print(f"  🔧  Admin panel: http://localhost:{port}/admin")
    print(f"  📱  Dev OTP:     123456  (any mobile number)")
    print("="*55 + "\n")
    app.run(host='0.0.0.0', port=port, debug=True)
