#!/usr/bin/env python3
"""
Assessment Validator - Flask Application with Authentication
Enhanced with Azure AD authentication and validator invitation system
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for, session, make_response, flash
import os
import json
from datetime import datetime
import traceback
import logging

# Import our improved integration
from main import run_assessment_analysis
from agents.fetch_agent import FetchAgent
from config import Config

# Import authentication system
from auth.auth_manager import setup_authentication
from auth.validator_manager import ValidatorManager
from auth.invitation_service import InvitationService
from auth.entra_external_id_auth import entra_external_id_auth

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__, template_folder='templates')
app.config.from_object(Config)

# File upload configuration
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Initialize authentication
auth_manager = setup_authentication(app)

# Initialize validator management
validator_manager = ValidatorManager(app.config.get('VALIDATOR_STORAGE', 'storage/validators'))
invitation_service = InvitationService()

# Initialize fetch agent (will be recreated as needed)
fetch_agent = None

@app.before_request
def cleanup_old_sessions():
    """Clean up old session files periodically"""
    try:
        # Clean up old session files (older than 24 hours)
        session_dir = 'storage/sessions'
        if os.path.exists(session_dir):
            current_time = datetime.now()
            for filename in os.listdir(session_dir):
                filepath = os.path.join(session_dir, filename)
                if os.path.isfile(filepath):
                    file_time = datetime.fromtimestamp(os.path.getmtime(filepath))
                    if (current_time - file_time).days > 1:  # Older than 24 hours
                        os.remove(filepath)
                        logger.info(f"🧹 Cleaned up old session file: {filename}")
    except Exception as e:
        logger.warning(f"⚠️ Session cleanup error: {e}")

@app.route('/')
def index():
    """Main page - UoC code entry"""
    if not auth_manager.is_authenticated():
        return render_template('login.html')
    
    user = auth_manager.get_current_user()
    return render_template('index.html', current_user=user)

# ====================
# ADMIN ROUTES
# ====================

@app.route('/admin')
@auth_manager.require_role(['Admin', 'Manager', 'Compliance Officer'])
def admin_dashboard():
    """Admin dashboard - only for managers, compliance officers, and admins"""
    try:
        # Get dashboard statistics
        validators = validator_manager._load_validators()
        invitations = validator_manager._load_invitations()
        
        stats = {
            'total_validators': len(validators),
            'active_validators': len([v for v in validators.values() if v['status'] == 'active']),
            'pending_invitations': len([i for i in invitations.values() if i['status'] == 'pending']),
            'assessments_validated': sum(v.get('validation_stats', {}).get('assessments_validated', 0) for v in validators.values())
        }
        
        # Get pending invitations and active validators
        pending_invitations = validator_manager.get_pending_invitations()
        active_validators = [v for v in validators.values() if v['status'] == 'active']
        
        return render_template('admin_dashboard.html', 
                             stats=stats,
                             pending_invitations=pending_invitations,
                             active_validators=active_validators)
    except Exception as e:
        logger.error(f"Error loading admin dashboard: {e}")
        flash(f"Error loading dashboard: {str(e)}", 'error')
        return redirect(url_for('index'))

@app.route('/admin/invite-validator', methods=['POST'])
@auth_manager.require_role(['Admin', 'Manager', 'Compliance Officer'])
def admin_invite_validator():
    """Admin function to invite a validator"""
    try:
        email = request.form.get('email', '').strip().lower()
        role = request.form.get('role', '').strip()
        validator_type = request.form.get('validator_type', 'external').strip()
        rto_id = request.form.get('rto_id', 'RTO_001').strip()
        
        if not email or not role:
            return jsonify({'success': False, 'error': 'Email and role are required'}), 400
        
        # Get current user info
        current_user = auth_manager.get_current_user()
        invited_by = current_user.get('email', 'system')
        
        # Create invitation
        invitation = validator_manager.invite_validator(
            email=email,
            role=role,
            rto_id=rto_id,
            invited_by=invited_by,
            validator_type=validator_type
        )
        
        # Send invitation email
        email_sent = invitation_service.send_validator_invitation(invitation)
        
        if email_sent:
            logger.info(f"Validator invitation sent: {email}")
            return jsonify({
                'success': True, 
                'message': f'Invitation sent to {email}',
                'invitation_id': invitation['id']
            })
        else:
            logger.warning(f"Invitation created but email failed for: {email}")
            return jsonify({
                'success': True, 
                'message': f'Invitation created for {email} (email delivery may have failed)',
                'invitation_id': invitation['id']
            })
        
    except Exception as e:
        logger.error(f"Error inviting validator: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/admin/stats')
@auth_manager.require_role(['Admin', 'Manager', 'Compliance Officer'])
def admin_get_stats():
    """Get updated statistics for admin dashboard"""
    try:
        validators = validator_manager._load_validators()
        invitations = validator_manager._load_invitations()
        
        stats = {
            'total_validators': len(validators),
            'active_validators': len([v for v in validators.values() if v['status'] == 'active']),
            'pending_invitations': len([i for i in invitations.values() if i['status'] == 'pending']),
            'assessments_validated': sum(v.get('validation_stats', {}).get('assessments_validated', 0) for v in validators.values())
        }
        
        return jsonify(stats)
        
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/admin/cancel-invitation/<invitation_id>', methods=['POST'])
@auth_manager.require_role(['Admin', 'Manager', 'Compliance Officer'])
def admin_cancel_invitation(invitation_id):
    """Cancel a pending invitation"""
    try:
        invitations = validator_manager._load_invitations()
        
        if invitation_id in invitations:
            invitations[invitation_id]['status'] = 'cancelled'
            invitations[invitation_id]['cancelled_at'] = datetime.now().isoformat()
            validator_manager._save_invitations(invitations)
            
            logger.info(f"Invitation cancelled: {invitation_id}")
            return jsonify({'success': True, 'message': 'Invitation cancelled'})
        else:
            return jsonify({'success': False, 'error': 'Invitation not found'}), 404
            
    except Exception as e:
        logger.error(f"Error cancelling invitation: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/admin/deactivate-validator/<validator_id>', methods=['POST'])
@auth_manager.require_role(['Admin', 'Manager', 'Compliance Officer'])
def admin_deactivate_validator(validator_id):
    """Deactivate a validator"""
    try:
        data = request.get_json() or {}
        reason = data.get('reason', '')
        
        validators = validator_manager._load_validators()
        
        if validator_id in validators:
            validator = validators[validator_id]
            validator_manager.deactivate_validator(
                email=validator['email'],
                rto_id=validator['rto_id'],
                reason=reason
            )
            
            logger.info(f"Validator deactivated: {validator_id}")
            return jsonify({'success': True, 'message': 'Validator deactivated'})
        else:
            return jsonify({'success': False, 'error': 'Validator not found'}), 404
            
    except Exception as e:
        logger.error(f"Error deactivating validator: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/admin/cleanup-expired', methods=['POST'])
@auth_manager.require_role(['Admin', 'Manager', 'Compliance Officer'])
def admin_cleanup_expired():
    """Remove expired invitations"""
    try:
        invitations = validator_manager._load_invitations()
        current_time = datetime.now()
        
        expired_count = 0
        for invitation_id, invitation in list(invitations.items()):
            if invitation['status'] == 'pending':
                expires_at = datetime.fromisoformat(invitation['expires_at'])
                if current_time > expires_at:
                    invitation['status'] = 'expired'
                    expired_count += 1
        
        validator_manager._save_invitations(invitations)
        
        logger.info(f"Cleaned up {expired_count} expired invitations")
        return jsonify({'success': True, 'count': expired_count})
        
    except Exception as e:
        logger.error(f"Error cleaning up expired invitations: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# ====================
# VALIDATOR ROUTES
# ====================

@app.route('/validator/accept-invitation')
def validator_accept_invitation():
    """Handle validator invitation acceptance"""
    token = request.args.get('token')
    
    if not token:
        flash('Invalid invitation link', 'error')
        return redirect(url_for('login'))
    
    # For now, redirect to login - the actual acceptance will happen after login
    session['invitation_token'] = token
    return redirect(url_for('login'))

@app.route('/validator/dashboard')
@auth_manager.require_auth
def validator_dashboard():
    """Validator-specific dashboard"""
    user = auth_manager.get_current_user()
    validator_data = validator_manager.get_validator_dashboard_data(user['email'])
    
    return render_template('validator_dashboard.html', 
                         validator_data=validator_data,
                         current_user=user)

# ====================
# EXISTING ROUTES WITH AUTHENTICATION
# ====================

@app.route('/fetch-uoc', methods=['POST'])
@auth_manager.require_auth
def fetch_uoc():
    """Step 1: Fetch UoC data from training.gov.au (now protected)"""
    try:
        uoc_code = request.form.get('uoc_code', '').strip().upper()
        
        if not uoc_code:
            return jsonify({'error': 'UoC code is required'}), 400
        
        logger.info(f"🔍 Fetching UoC components for {uoc_code}...")
        
        # Initialize FetchAgent with current API key
        from agents.fetch_agent import FetchAgent
        fetch_agent = FetchAgent(
            gemini_api_key=app.config['GEMINI_API_KEY']
        )
        
        # Check if force fresh fetch is requested
        force_fresh = request.form.get('force_fresh', 'false').lower() == 'true'
        logger.info(f"📋 Form data - force_fresh: {request.form.get('force_fresh', 'not found')}")
        logger.info(f"📋 Form data - force_fresh processed: {force_fresh}")
        if force_fresh:
            logger.info("🔄 Force fresh fetch requested")
        else:
            logger.info("📋 Using cached data (force_fresh not checked)")
        
        # Fetch UoC data
        uoc_data = fetch_agent.execute(uoc_code, force_fresh=force_fresh)
        
        # Store in session for next step
        session['uoc_code'] = uoc_code
        session['uoc_data'] = uoc_data
        
        # Log validator activity
        user = auth_manager.get_current_user()
        logger.info(f"UoC fetched by validator: {user.get('email', 'unknown')}")
        
        return jsonify({
            'success': True,
            'uoc_code': uoc_code,
            'uoc_title': uoc_data.get('title', 'Unknown'),
            'elements_count': len(uoc_data.get('elements', [])),
            'performance_criteria_count': len(uoc_data.get('performance_criteria', [])),
            'redirect_url': url_for('upload_assessment')
        })
        
    except Exception as e:
        logger.error(f"❌ Error fetching UoC: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': f'Error fetching UoC data: {str(e)}'}), 500

@app.route('/upload-assessment')
@auth_manager.require_auth
def upload_assessment():
    """Step 2: Upload assessment file (now protected)"""
    if 'uoc_code' not in session:
        flash('Please fetch UoC data first', 'warning')
        return redirect(url_for('index'))
    
    return render_template('upload_assessment.html', 
                         uoc_code=session['uoc_code'],
                         uoc_data=session.get('uoc_data', {}))

@app.route('/process-assessment', methods=['POST'])
@auth_manager.require_auth
def process_assessment():
    """Step 3: Process assessment file (now protected)"""
    try:
        # Your existing process_assessment code here
        # Just add user logging
        user = auth_manager.get_current_user()
        logger.info(f"Assessment processed by validator: {user.get('email', 'unknown')}")
        
        # ... existing implementation ...
        return jsonify({'success': True, 'message': 'Assessment processed successfully'})
        
    except Exception as e:
        logger.error(f"❌ Error processing assessment: {str(e)}")
        return jsonify({'error': f'Error processing assessment: {str(e)}'}), 500

@app.route('/dashboard/<session_id>')
@auth_manager.require_auth
def dashboard(session_id):
    """Main validation dashboard (now protected)"""
    try:
        # Your existing dashboard code here
        user = auth_manager.get_current_user()
        logger.info(f"Dashboard accessed by validator: {user.get('email', 'unknown')}")
        
        return render_template('dashboard.html', 
                             session_id=session_id,
                             current_user=user)
                             
    except Exception as e:
        logger.error(f"❌ Error loading dashboard: {str(e)}")
        flash(f"Error loading dashboard: {str(e)}", 'error')
        return redirect(url_for('index'))

# ====================
# ERROR HANDLERS
# ====================

@app.errorhandler(403)
def forbidden_error(error):
    return render_template('error.html', 
                         error_code=403,
                         error_message="Access denied. You don't have permission to access this resource."), 403

@app.errorhandler(404)
def not_found_error(error):
    return render_template('error.html', 
                         error_code=404,
                         error_message="The page you're looking for doesn't exist."), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('error.html', 
                         error_code=500,
                         error_message="An internal server error occurred."), 500

if __name__ == '__main__':
    print("🚀 Starting Assessment Validator (Computer-assisted) with Authentication...")
    print("📊 Visit http://localhost:5001 to start")
    print("🔐 Users will be redirected to Microsoft login")
    print("👨‍💼 Admin users can access /admin for validator management")
    
    # Initialize application
    Config.init_app(app)
    
    app.run(debug=True, host='0.0.0.0', port=5001)