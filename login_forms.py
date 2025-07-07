from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Length

class AdminLoginForm(FlaskForm):
    """Form for admin login"""
    username = StringField('Username', validators=[
        DataRequired(message='Username is required'),
        Length(min=3, max=64, message='Username must be between 3 and 64 characters')
    ])
    
    password = PasswordField('Password', validators=[
        DataRequired(message='Password is required')
    ])
    
    remember_me = BooleanField('Remember Me')
    
    submit = SubmitField('Login')

class CreateAdminForm(FlaskForm):
    """Form for creating new admin account"""
    username = StringField('Username', validators=[
        DataRequired(message='Username is required'),
        Length(min=3, max=64, message='Username must be between 3 and 64 characters')
    ])
    
    email = StringField('Email', validators=[
        DataRequired(message='Email is required'),
        Length(max=120, message='Email cannot exceed 120 characters')
    ])
    
    password = PasswordField('Password', validators=[
        DataRequired(message='Password is required'),
        Length(min=6, message='Password must be at least 6 characters long')
    ])
    
    role = StringField('Role', validators=[
        Length(max=20, message='Role cannot exceed 20 characters')
    ], default='admin')
    
    submit = SubmitField('Create Admin')