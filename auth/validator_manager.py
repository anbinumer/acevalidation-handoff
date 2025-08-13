#!/usr/bin/env python3
"""
Validator Management System for RTO Assessment Validation
Handles validator invitations, onboarding, and role management
"""

import os
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

class ValidatorManager:
    """Manages validator invitations and user management for RTOs"""
    
    def __init__(self, storage_dir: str = "storage/validators"):
        self.storage_dir = storage_dir
        self.validators_file = os.path.join(storage_dir, "validators.json")
        self.invitations_file = os.path.join(storage_dir, "invitations.json")
        
        # Ensure storage directory exists
        os.makedirs(storage_dir, exist_ok=True)
        
        # Initialize files if they don't exist
        self._init_storage_files()
    
    def _init_storage_files(self):
        """Initialize storage files if they don't exist"""
        if not os.path.exists(self.validators_file):
            with open(self.validators_file, 'w') as f:
                json.dump({}, f)
        
        if not os.path.exists(self.invitations_file):
            with open(self.invitations_file, 'w') as f:
                json.dump({}, f)
    
    def _load_validators(self) -> Dict:
        """Load validators from storage"""
        try:
            with open(self.validators_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading validators: {e}")
            return {}
    
    def _save_validators(self, validators: Dict):
        """Save validators to storage"""
        try:
            with open(self.validators_file, 'w') as f:
                json.dump(validators, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Error saving validators: {e}")
    
    def _load_invitations(self) -> Dict:
        """Load invitations from storage"""
        try:
            with open(self.invitations_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading invitations: {e}")
            return {}
    
    def _save_invitations(self, invitations: Dict):
        """Save invitations to storage"""
        try:
            with open(self.invitations_file, 'w') as f:
                json.dump(invitations, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Error saving invitations: {e}")
    
    def invite_validator(self, email: str, role: str, rto_id: str, invited_by: str, 
                        validator_type: str = "external") -> Dict:
        """
        Invite a validator to the system
        
        Args:
            email: Validator's email address
            role: Role to assign (validator, assessor, manager, etc.)
            rto_id: RTO organization ID
            invited_by: Email of admin who sent invitation
            validator_type: Type of validator (external, internal, expert)
        
        Returns:
            Dict containing invitation details
        """
        invitations = self._load_invitations()
        
        invitation_id = f"{email}_{rto_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        invitation = {
            'id': invitation_id,
            'email': email,
            'role': role,
            'rto_id': rto_id,
            'validator_type': validator_type,
            'invited_by': invited_by,
            'invited_at': datetime.now().isoformat(),
            'status': 'pending',
            'expires_at': (datetime.now() + timedelta(days=7)).isoformat(),
            'accepted_at': None,
            'first_login': None
        }
        
        invitations[invitation_id] = invitation
        self._save_invitations(invitations)
        
        logger.info(f"Validator invitation sent: {email} for RTO {rto_id}")
        return invitation
    
    def accept_invitation(self, email: str, user_info: Dict) -> bool:
        """
        Accept a validator invitation when user first logs in
        
        Args:
            email: Validator's email
            user_info: User information from Azure AD
        
        Returns:
            bool: True if invitation found and accepted
        """
        invitations = self._load_invitations()
        validators = self._load_validators()
        
        # Find pending invitation for this email
        for invitation_id, invitation in invitations.items():
            if (invitation['email'].lower() == email.lower() and 
                invitation['status'] == 'pending'):
                
                # Check if invitation has expired
                expires_at = datetime.fromisoformat(invitation['expires_at'])
                if datetime.now() > expires_at:
                    invitation['status'] = 'expired'
                    self._save_invitations(invitations)
                    logger.warning(f"Invitation expired for {email}")
                    return False
                
                # Accept the invitation
                invitation['status'] = 'accepted'
                invitation['accepted_at'] = datetime.now().isoformat()
                invitation['first_login'] = datetime.now().isoformat()
                
                # Create validator record
                validator_id = f"{email}_{invitation['rto_id']}"
                validator = {
                    'id': validator_id,
                    'email': email,
                    'role': invitation['role'],
                    'rto_id': invitation['rto_id'],
                    'validator_type': invitation['validator_type'],
                    'invited_by': invitation['invited_by'],
                    'status': 'active',
                    'created_at': datetime.now().isoformat(),
                    'last_login': datetime.now().isoformat(),
                    'profile': {
                        'displayName': user_info.get('displayName'),
                        'firstName': user_info.get('firstName'),
                        'lastName': user_info.get('lastName'),
                        'jobTitle': user_info.get('jobTitle'),
                        'department': user_info.get('department'),
                        'organization': user_info.get('organization')
                    },
                    'validation_stats': {
                        'assessments_validated': 0,
                        'total_mappings_reviewed': 0,
                        'avg_confidence_score': 0.0,
                        'last_validation_date': None
                    }
                }
                
                validators[validator_id] = validator
                
                # Save both files
                self._save_invitations(invitations)
                self._save_validators(validators)
                
                logger.info(f"Validator invitation accepted: {email}")
                return True
        
        logger.warning(f"No pending invitation found for {email}")
        return False
    
    def get_validator_status(self, email: str) -> Optional[Dict]:
        """
        Get validator status and information
        
        Args:
            email: Validator's email
        
        Returns:
            Dict with validator information or None if not found
        """
        validators = self._load_validators()
        invitations = self._load_invitations()
        
        # Check active validators first
        for validator in validators.values():
            if validator['email'].lower() == email.lower():
                return validator
        
        # Check pending invitations
        for invitation in invitations.values():
            if (invitation['email'].lower() == email.lower() and 
                invitation['status'] == 'pending'):
                return {
                    'status': 'invited',
                    'role': invitation['role'],
                    'rto_id': invitation['rto_id'],
                    'invited_at': invitation['invited_at'],
                    'expires_at': invitation['expires_at']
                }
        
        return None
    
    def get_rto_validators(self, rto_id: str) -> List[Dict]:
        """Get all validators for a specific RTO"""
        validators = self._load_validators()
        return [v for v in validators.values() if v['rto_id'] == rto_id]
    
    def get_pending_invitations(self, rto_id: str = None) -> List[Dict]:
        """Get pending invitations, optionally filtered by RTO"""
        invitations = self._load_invitations()
        pending = [inv for inv in invitations.values() if inv['status'] == 'pending']
        
        if rto_id:
            pending = [inv for inv in pending if inv['rto_id'] == rto_id]
        
        return pending
    
    def update_validator_stats(self, email: str, stats_update: Dict):
        """Update validator statistics after completing validation"""
        validators = self._load_validators()
        
        for validator in validators.values():
            if validator['email'].lower() == email.lower():
                for key, value in stats_update.items():
                    if key in validator['validation_stats']:
                        validator['validation_stats'][key] = value
                
                validator['last_login'] = datetime.now().isoformat()
                break
        
        self._save_validators(validators)
    
    def deactivate_validator(self, email: str, rto_id: str, reason: str = ""):
        """Deactivate a validator"""
        validators = self._load_validators()
        
        for validator in validators.values():
            if (validator['email'].lower() == email.lower() and 
                validator['rto_id'] == rto_id):
                validator['status'] = 'inactive'
                validator['deactivated_at'] = datetime.now().isoformat()
                validator['deactivation_reason'] = reason
                break
        
        self._save_validators(validators)
        logger.info(f"Validator deactivated: {email} for RTO {rto_id}")
    
    def get_validator_dashboard_data(self, email: str) -> Dict:
        """Get dashboard data for a validator"""
        validator = self.get_validator_status(email)
        if not validator or validator.get('status') != 'active':
            return {}
        
        return {
            'validator_info': validator,
            'recent_validations': self._get_recent_validations(email),
            'performance_stats': validator.get('validation_stats', {}),
            'assigned_assessments': self._get_assigned_assessments(email)
        }
    
    def _get_recent_validations(self, email: str) -> List[Dict]:
        """Get recent validation activities for a validator"""
        # This would integrate with your validation session storage
        # For now, return empty list
        return []
    
    def _get_assigned_assessments(self, email: str) -> List[Dict]:
        """Get assessments assigned to a validator"""
        # This would integrate with your assessment assignment system
        # For now, return empty list
        return []