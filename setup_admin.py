#!/usr/bin/env python3
"""
Setup script to create the first admin account
"""
import os
import sys
sys.path.append('.')

from app import app, db
from models import Admin
from werkzeug.security import generate_password_hash

def create_admin_account():
    """Create the first admin account"""
    with app.app_context():
        # Check if admin already exists
        existing_admin = Admin.query.first()
        if existing_admin:
            print(f"Admin account already exists: {existing_admin.username}")
            return
        
        # Create admin account
        username = "admin"
        password = os.environ.get("ADMIN_PASSWORD")
        if not password:
            print("❌ Error: ADMIN_PASSWORD environment variable is required")
            print("Please set ADMIN_PASSWORD before running this script")
            return
        email = "admin@civic.local"
        
        admin = Admin()
        admin.username = username
        admin.email = email
        admin.role = "admin"
        admin.active = True
        admin.set_password(password)
        
        try:
            db.session.add(admin)
            db.session.commit()
            
            print("✓ Admin account created successfully!")
            print(f"Username: {username}")
            print("⚠️  Password set from environment variable")
            print("🔗 Login at: /admin/login")
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error creating admin account: {e}")

if __name__ == "__main__":
    create_admin_account()