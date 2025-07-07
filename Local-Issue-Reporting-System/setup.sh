#!/bin/bash

echo "🚀 Setting up your Flask project..."

# 1. Create virtual environment if not present
if [ ! -d "venv" ]; then
  python3 -m venv venv
  echo "✅ Virtual environment created."
else
  echo "✅ Virtual environment already exists."
fi

# 2. Activate virtual environment
source venv/bin/activate
echo "✅ Virtual environment activated."

# 3. Install dependencies
echo "📦 Installing dependencies..."
pip install flask flask-wtf flask-sqlalchemy email-validator gunicorn psycopg2-binary sqlalchemy werkzeug wtforms flask-dance flask-login oauthlib pyjwt python-dotenv

# 4. Create .env file
echo "FLASK_APP=main.py" > .env
echo "FLASK_ENV=development" >> .env
echo "✅ .env file created."

# 5. Done
echo "🎉 Setup complete! You can now run your app with: flask run"
