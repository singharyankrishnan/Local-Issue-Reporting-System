import os
import uuid
from datetime import datetime
from urllib.parse import urlparse
from werkzeug.utils import secure_filename
from flask import render_template, request, redirect, url_for, flash, jsonify, session, send_from_directory
from flask_login import login_user, logout_user, login_required, current_user
import app

from forms import IssueForm, AdminUpdateForm
from login_forms import AdminLoginForm, CreateAdminForm
from email_service import send_authority_notification, send_status_update_notification
import logging

@app.app.route('/')
def index():
    from models import Issue
    """Main page for citizens to report issues"""
    form = IssueForm()
    return render_template('index.html', form=form)

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'jpg', 'jpeg', 'png', 'gif'}

def save_uploaded_file(file):
    """Save uploaded file and return filename"""
    if file and allowed_file(file.filename):
        # Generate unique filename
        filename = secure_filename(file.filename)
        name, ext = os.path.splitext(filename)
        unique_filename = f"{uuid.uuid4().hex}_{name}{ext}"
        
        # Save file
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(file_path)
        return unique_filename
    return None

@app.app.route('/uploads/<filename>')
def uploaded_file(filename):
    """Serve uploaded files"""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.app.route('/submit_issue', methods=['POST'])
def submit_issue():
    from models import Issue
    """Handle issue submission"""
    form = IssueForm()
    from app import db
    if form.validate_on_submit():
        try:
            # Handle photo upload
            photo_filename = None
            if form.photo.data:
                photo_filename = save_uploaded_file(form.photo.data)
            # Parse coordinates
            latitude = float(form.latitude.data) if form.latitude.data else None
            longitude = float(form.longitude.data) if form.longitude.data else None
            # Create new issue
            issue = Issue()
            issue.name = form.name.data
            issue.email = form.email.data
            issue.category = form.category.data
            issue.description = form.description.data
            issue.location = form.location.data
            issue.latitude = latitude
            issue.longitude = longitude
            issue.photo_filename = photo_filename
            issue.status = 'submitted'
            issue.priority = 'medium'
            db.session.add(issue)
            db.session.commit()
            # Send notification to authorities
            try:
                send_authority_notification(issue)
            except Exception as e:
                app.app.logger.warning(f'Failed to send notification for issue {issue.id}: {str(e)}')
            flash('Your issue has been submitted successfully! Authorities have been notified.', 'success')
            app.app.logger.info(f'New issue submitted: {issue.id} - {issue.category}')
        except Exception as e:
            db.session.rollback()
            app.app.logger.error(f'Error submitting issue: {str(e)}')
            flash('An error occurred while submitting your issue. Please try again.', 'error')
    else:
        # Display form validation errors
        for field_name, errors in form.errors.items():
            for error in errors:
                field_display = str(field_name).replace("_", " ").title()
                flash(f'{field_display}: {error}', 'error')
    return redirect(url_for('index'))

@app.app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    from models import Admin
    """Admin login page"""
    if current_user.is_authenticated:
        return redirect(url_for('admin_panel'))
    
    form = AdminLoginForm()
    
    if form.validate_on_submit():
        admin = Admin.query.filter_by(username=form.username.data).first()
        
        if admin and admin.check_password(form.password.data):
            login_user(admin, remember=form.remember_me.data)
            flash('Successfully logged in!', 'success')
            
            # Redirect to originally requested page or admin panel
            next_page = request.args.get('next')
            if next_page:
                # Parse the URL to check if it's safe
                parsed_url = urlparse(next_page)
                # Only allow relative URLs (no netloc) and same-origin URLs
                if parsed_url.netloc == '' and next_page.startswith('/') and not next_page.startswith('//'):
                    return redirect(next_page)
            # Default to admin panel if no valid next page
            return redirect(url_for('admin_panel'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('admin_login.html', form=form)

@app.app.route('/admin/logout')
@login_required
def admin_logout():
    """Admin logout"""
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

@app.app.route('/admin')
@login_required
def admin_panel():
    from models import Issue
    """Admin panel to view and manage issues"""
    # Get filter parameters
    status_filter = request.args.get('status', 'all')
    category_filter = request.args.get('category', 'all')
    priority_filter = request.args.get('priority', 'all')
    
    from app import db
    # Build query
    query = Issue.query
    if status_filter != 'all':
        query = query.filter(Issue.status == status_filter)
    if category_filter != 'all':
        query = query.filter(Issue.category == category_filter)
    if priority_filter != 'all':
        query = query.filter(Issue.priority == priority_filter)
    # Order by most recent first
    issues = query.order_by(Issue.created_at.desc()).all()
    # Get counts for dashboard
    total_issues = Issue.query.count()
    submitted_count = Issue.query.filter_by(status='submitted').count()
    in_progress_count = Issue.query.filter_by(status='in_progress').count()
    resolved_count = Issue.query.filter_by(status='resolved').count()
    stats = {
        'total': total_issues,
        'submitted': submitted_count,
        'in_progress': in_progress_count,
        'resolved': resolved_count
    }
    return render_template('admin.html', 
                         issues=issues, 
                         stats=stats,
                         current_status=status_filter,
                         current_category=category_filter,
                         current_priority=priority_filter)

@app.app.route('/all-issues')
def all_issues():
    from models import Issue
    """Display all submitted issues for public viewing"""
    # Get filter parameters
    status_filter = request.args.get('status', 'all')
    category_filter = request.args.get('category', 'all')
    priority_filter = request.args.get('priority', 'all')
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    from app import db
    # Build query
    query = Issue.query
    if status_filter != 'all':
        query = query.filter_by(status=status_filter)
    if category_filter != 'all':
        query = query.filter_by(category=category_filter)
    if priority_filter != 'all':
        query = query.filter_by(priority=priority_filter)
    # Get paginated issues
    issues = query.order_by(Issue.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    # Get summary statistics
    total_issues = Issue.query.count()
    pending_issues = Issue.query.filter_by(status='submitted').count()
    in_progress_issues = Issue.query.filter_by(status='in_progress').count()
    resolved_issues = Issue.query.filter_by(status='resolved').count()
    return render_template('all_issues.html',
                         issues=issues,
                         total_issues=total_issues,
                         pending_issues=pending_issues,
                         in_progress_issues=in_progress_issues,
                         resolved_issues=resolved_issues,
                         status_filter=status_filter,
                         category_filter=category_filter,
                         priority_filter=priority_filter)

@app.app.route('/issue/<int:issue_id>')
@login_required
def issue_detail(issue_id):
    from models import Issue
    """View detailed information about a specific issue"""
    issue = Issue.query.get_or_404(issue_id)
    form = AdminUpdateForm(obj=issue)
    return render_template('issue_detail.html', issue=issue, form=form)

@app.app.route('/update_issue/<int:issue_id>', methods=['POST'])
@login_required
def update_issue(issue_id):
    from models import Issue
    """Update issue status and details"""
    from app import db
    issue = Issue.query.get_or_404(issue_id)
    old_status = issue.status
    form = AdminUpdateForm()
    if form.validate_on_submit():
        try:
            issue.status = form.status.data
            issue.priority = form.priority.data
            issue.admin_notes = form.admin_notes.data
            issue.assigned_to = form.assigned_to.data
            db.session.commit()
            # Send status update notification if status changed
            if old_status != issue.status:
                try:
                    send_status_update_notification(issue, old_status)
                except Exception as e:
                    app.app.logger.warning(f'Failed to send status update notification for issue {issue_id}: {str(e)}')
            flash('Issue updated successfully!', 'success')
            app.app.logger.info(f'Issue {issue_id} updated by admin {current_user.username}')
        except Exception as e:
            db.session.rollback()
            app.app.logger.error(f'Error updating issue {issue_id}: {str(e)}')
            flash('An error occurred while updating the issue.', 'error')
    else:
        for field_name, errors in form.errors.items():
            for error in errors:
                field_display = str(field_name).replace("_", " ").title()
                flash(f'{field_display}: {error}', 'error')
    return redirect(url_for('issue_detail', issue_id=issue_id))

@app.app.route('/admin/create', methods=['GET', 'POST'])
def create_admin():
    from models import Admin
    """Create admin account - for initial setup only"""
    # Check if any admin exists
    if Admin.query.first():
        flash('Admin account already exists. Please contact an existing admin.', 'error')
        return redirect(url_for('admin_login'))
    
    from app import db
    form = CreateAdminForm()
    if form.validate_on_submit():
        try:
            admin = Admin(
                username=form.username.data,
                email=form.email.data,
                role=form.role.data or 'admin'
            )
            admin.set_password(form.password.data)
            db.session.add(admin)
            db.session.commit()
            flash('Admin account created successfully! You can now log in.', 'success')
            app.app.logger.info(f'Admin account created: {admin.username}')
            return redirect(url_for('admin_login'))
        except Exception as e:
            db.session.rollback()
            app.app.logger.error(f'Error creating admin: {str(e)}')
            flash('An error occurred while creating the admin account.', 'error')
    return render_template('create_admin.html', form=form)

@app.app.route('/analytics')
@login_required
def analytics_dashboard():
    from models import Issue
    """Analytics dashboard for government officials"""
    from sqlalchemy import func, extract, case
    
    # Get time-based statistics
    current_year = datetime.now().year
    current_month = datetime.now().month
    
    from app import db
    # Issues by status
    status_stats = db.session.query(
        Issue.status,
        func.count(Issue.id).label('count')
    ).group_by(Issue.status).all()
    # Issues by category
    category_stats = db.session.query(
        Issue.category,
        func.count(Issue.id).label('count')
    ).group_by(Issue.category).all()
    # Issues by priority
    priority_stats = db.session.query(
        Issue.priority,
        func.count(Issue.id).label('count')
    ).group_by(Issue.priority).all()
    # Monthly trends (last 12 months)
    monthly_stats = db.session.query(
        extract('year', Issue.created_at).label('year'),
        extract('month', Issue.created_at).label('month'),
        func.count(Issue.id).label('count')
    ).group_by(
        extract('year', Issue.created_at),
        extract('month', Issue.created_at)
    ).order_by(
        extract('year', Issue.created_at),
        extract('month', Issue.created_at)
    ).limit(12).all()
    # Resolution time analysis
    resolved_issues = db.session.query(Issue).filter_by(status='resolved').all()
    avg_resolution_time = 0
    if resolved_issues:
        total_time = sum([(issue.updated_at - issue.created_at).days for issue in resolved_issues])
        avg_resolution_time = total_time / len(resolved_issues)
    # Geographic distribution (if coordinates available)
    geo_stats = db.session.query(
        Issue.latitude,
        Issue.longitude,
        Issue.category,
        Issue.status,
        Issue.priority,
        Issue.id
    ).filter(
        Issue.latitude.isnot(None),
        Issue.longitude.isnot(None)
    ).all()
    # Performance metrics
    total_issues = Issue.query.count()
    resolved_count = Issue.query.filter_by(status='resolved').count()
    in_progress_count = Issue.query.filter_by(status='in_progress').count()
    pending_count = Issue.query.filter_by(status='submitted').count()
    resolution_rate = (resolved_count / total_issues * 100) if total_issues > 0 else 0
    # Authority notification stats
    notified_count = Issue.query.filter_by(authority_notified=True).count()
    notification_rate = (notified_count / total_issues * 100) if total_issues > 0 else 0
    analytics_data = {
        'status_stats': {item.status: item.count for item in status_stats},
        'category_stats': {item.category: item.count for item in category_stats},
        'priority_stats': {item.priority: item.count for item in priority_stats},
        'monthly_stats': [{'year': int(item.year), 'month': int(item.month), 'count': item.count} for item in monthly_stats],
        'geo_stats': [{'lat': float(item.latitude), 'lng': float(item.longitude), 'category': item.category, 'status': item.status, 'priority': item.priority, 'id': item.id} for item in geo_stats],
        'performance': {
            'total_issues': total_issues,
            'resolved_count': resolved_count,
            'in_progress_count': in_progress_count,
            'pending_count': pending_count,
            'resolution_rate': round(resolution_rate, 1),
            'avg_resolution_time': round(avg_resolution_time, 1),
            'notification_rate': round(notification_rate, 1)
        }
    }
    return render_template('analytics.html', analytics=analytics_data)

@app.app.route('/api/issues')
def api_issues():
    from models import Issue
    """API endpoint to get issues data"""
    from app import db
    issues = Issue.query.all()
    return jsonify([issue.to_dict() for issue in issues])

@app.app.route('/api/analytics')
@login_required
def api_analytics():
    from models import Issue
    """API endpoint for analytics data"""
    from sqlalchemy import func, extract
    
    # Get various statistics for charts
    from app import db
    data = {
        'category_distribution': dict(db.session.query(Issue.category, func.count(Issue.id)).group_by(Issue.category).all()),
        'status_distribution': dict(db.session.query(Issue.status, func.count(Issue.id)).group_by(Issue.status).all()),
        'priority_distribution': dict(db.session.query(Issue.priority, func.count(Issue.id)).group_by(Issue.priority).all()),
        'monthly_trends': [
            {'month': f"{int(item[0])}-{int(item[1]):02d}", 'count': item[2]}
            for item in db.session.query(
                extract('year', Issue.created_at),
                extract('month', Issue.created_at),
                func.count(Issue.id)
            ).group_by(
                extract('year', Issue.created_at),
                extract('month', Issue.created_at)
            ).order_by(
                extract('year', Issue.created_at),
                extract('month', Issue.created_at)
            ).limit(12).all()
        ]
    }
    return jsonify(data)

@app.app.errorhandler(404)
def not_found_error(error):
    return render_template('base.html', error_message="Page not found"), 404

@app.app.errorhandler(500)
def internal_error(error):
    from app import db
    db.session.rollback()
    return render_template('base.html', error_message="An internal error occurred"), 500
