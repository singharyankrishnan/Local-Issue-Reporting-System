import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import logging
import os

# Authority email mappings by category
AUTHORITY_EMAILS = {
    'roads': ['roads.dept@civic.gov', 'infrastructure@city.gov'],
    'potholes': ['roads.dept@civic.gov', 'maintenance@city.gov'],
    'cleanliness': ['sanitation@civic.gov', 'health.dept@city.gov'],
    'street_lights': ['electrical@civic.gov', 'utilities@city.gov'],
    'water_supply': ['water.dept@civic.gov', 'utilities@city.gov'],
    'drainage': ['drainage@civic.gov', 'water.dept@city.gov'],
    'waste_management': ['waste@civic.gov', 'sanitation@city.gov'],
    'traffic': ['traffic@civic.gov', 'police@city.gov'],
    'other': ['general@civic.gov', 'admin@city.gov']
}

def send_authority_notification(issue):
    """Send email notification to relevant authorities"""
    try:
        # Get authority emails for this category
        recipients = AUTHORITY_EMAILS.get(issue.category, AUTHORITY_EMAILS['other'])
        
        # Create email content
        subject = f"New Civic Issue Reported - {issue.category.replace('_', ' ').title()} (#{issue.id})"
        
        body = f"""
New civic issue has been reported and requires attention:

Issue ID: #{issue.id}
Category: {issue.category.replace('_', ' ').title()}
Priority: {issue.priority.title()}
Status: {issue.status.title()}

Reporter Information:
Name: {issue.name}
Email: {issue.email}

Issue Details:
Location: {issue.location}
Description: {issue.description}

Coordinates:
Latitude: {issue.latitude if issue.latitude else 'Not provided'}
Longitude: {issue.longitude if issue.longitude else 'Not provided'}

Photo Evidence: {'Available' if issue.photo_filename else 'None provided'}

Reported on: {issue.created_at.strftime('%B %d, %Y at %I:%M %p')}

Please log into the admin panel to review and update this issue:
{get_admin_panel_url()}/issue/{issue.id}

This is an automated notification from the Civic Issues Reporting System.
        """
        
        # Send email to each authority
        for recipient in recipients:
            send_email(recipient, subject, body)
        
        # Update issue notification status
        from app import db
        issue.authority_notified = True
        issue.notification_sent_at = datetime.utcnow()
        db.session.commit()
        
        logging.info(f"Authority notification sent for issue #{issue.id} to {len(recipients)} recipients")
        
    except Exception as e:
        logging.error(f"Failed to send authority notification for issue #{issue.id}: {str(e)}")
        raise

def send_email(to_email, subject, body):
    """Send individual email using SMTP"""
    try:
        # Email configuration (set via environment variables)
        smtp_server = os.environ.get("SMTP_SERVER", "smtp.gmail.com")
        smtp_port = int(os.environ.get("SMTP_PORT", "587"))
        sender_email = os.environ.get("SENDER_EMAIL", "civic.system@example.com")
        sender_password = os.environ.get("SENDER_PASSWORD")  # Must be set via environment variable
        
        # Create message
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = to_email
        msg['Subject'] = subject
        
        # Add body to email
        msg.attach(MIMEText(body, 'plain'))
        
        # Check if we're in development mode (no password set)
        if not sender_password:
            # Development mode - just log the email instead of sending
            logging.info(f"EMAIL NOTIFICATION (Development Mode):")
            logging.info(f"To: {to_email}")
            logging.info(f"Subject: {subject}")
            logging.info(f"Body: {body[:200]}...")
        else:
            # Production mode - actually send the email
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            server.login(sender_email, sender_password)
            text = msg.as_string()
            server.sendmail(sender_email, to_email, text)
            server.quit()
            logging.info(f"Email sent to {to_email}")
        
    except Exception as e:
        logging.error(f"Failed to send email to {to_email}: {str(e)}")
        raise

def get_admin_panel_url():
    """Get the base URL for the admin panel"""
    # In production, this would be the actual domain
    return "http://localhost:5000"

def send_status_update_notification(issue, old_status):
    """Send notification when issue status is updated"""
    try:
        subject = f"Issue Status Update - #{issue.id}"
        
        body = f"""
Your reported civic issue has been updated:

Issue ID: #{issue.id}
Category: {issue.category.replace('_', ' ').title()}
Location: {issue.location}

Status Update:
Previous Status: {old_status.title()}
New Status: {issue.status.title()}
Priority: {issue.priority.title()}

{f'Assigned to: {issue.assigned_to}' if issue.assigned_to else ''}
{f'Admin Notes: {issue.admin_notes}' if issue.admin_notes else ''}

Updated on: {issue.updated_at.strftime('%B %d, %Y at %I:%M %p')}

Thank you for reporting this issue. We will continue to keep you updated on its progress.

This is an automated notification from the Civic Issues Reporting System.
        """
        
        # Send to issue reporter
        send_email(issue.email, subject, body)
        
        logging.info(f"Status update notification sent for issue #{issue.id} to {issue.email}")
        
    except Exception as e:
        logging.error(f"Failed to send status update notification for issue #{issue.id}: {str(e)}")