from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, TextAreaField, SelectField, SubmitField, HiddenField
from wtforms.validators import DataRequired, Email, Length

class IssueForm(FlaskForm):
    """Form for submitting civic issues"""
    name = StringField('Your Name', validators=[
        DataRequired(message='Name is required'),
        Length(min=2, max=100, message='Name must be between 2 and 100 characters')
    ])
    
    email = StringField('Your Email', validators=[
        DataRequired(message='Email is required'),
        Email(message='Please enter a valid email address')
    ])
    
    category = SelectField('Issue Category', choices=[
        ('roads', 'Roads & Infrastructure'),
        ('potholes', 'Potholes'),
        ('cleanliness', 'Cleanliness & Sanitation'),
        ('street_lights', 'Street Lights'),
        ('water_supply', 'Water Supply'),
        ('drainage', 'Drainage'),
        ('waste_management', 'Waste Management'),
        ('traffic', 'Traffic Issues'),
        ('other', 'Other')
    ], validators=[DataRequired(message='Please select an issue category')])
    
    description = TextAreaField('Describe the Issue', validators=[
        DataRequired(message='Issue description is required'),
        Length(min=10, max=1000, message='Description must be between 10 and 1000 characters')
    ])
    
    location = StringField('Location', validators=[
        DataRequired(message='Location is required'),
        Length(min=5, max=200, message='Location must be between 5 and 200 characters')
    ])
    
    photo = FileField('Upload Photo Evidence', validators=[
        FileAllowed(['jpg', 'jpeg', 'png', 'gif'], 'Only image files are allowed!')
    ])
    
    latitude = HiddenField('Latitude')
    longitude = HiddenField('Longitude')
    
    submit = SubmitField('Submit Issue')

class AdminUpdateForm(FlaskForm):
    """Form for admin to update issue status"""
    status = SelectField('Status', choices=[
        ('submitted', 'Submitted'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
        ('rejected', 'Rejected')
    ], validators=[DataRequired()])
    
    priority = SelectField('Priority', choices=[
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent')
    ], validators=[DataRequired()])
    
    admin_notes = TextAreaField('Admin Notes', validators=[
        Length(max=500, message='Notes cannot exceed 500 characters')
    ])
    
    assigned_to = StringField('Assigned To', validators=[
        Length(max=100, message='Assigned to field cannot exceed 100 characters')
    ])
    
    submit = SubmitField('Update Issue')
