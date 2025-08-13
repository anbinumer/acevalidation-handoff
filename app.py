#!/usr/bin/env python3
"""
Assessment Validator - Flask Application
Uses the improved main.py integration for robust assessment analysis
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for, session, make_response, flash
import os
import json
import logging
from datetime import datetime
from werkzeug.utils import secure_filename
import io
import openpyxl

# Import our improved integration
from main import run_assessment_analysis
from agents.fetch_agent import FetchAgent
from config import Config

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
    return render_template('index.html')

@app.route('/fetch-uoc', methods=['POST'])
def fetch_uoc():
    """Step 1: Fetch UoC data from training.gov.au"""
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
def upload_assessment():
    """Step 2: Upload assessment file"""
    # Check if we have UoC data from previous step
    if 'uoc_code' not in session:
        return redirect(url_for('index'))
    
    return render_template('upload_assessment.html', 
                         uoc_code=session.get('uoc_code'),
                         uoc_data=session.get('uoc_data'))

@app.route('/process-assessment', methods=['POST'])
def process_assessment():
    """Step 3: Process uploaded assessment file using improved integration"""
    try:
        logger.info("🔄 Processing assessment request...")
        
        # Get session data
        uoc_code = session.get('uoc_code')
        uoc_data = session.get('uoc_data')
        
        logger.info(f"📋 Session data - UoC code: {uoc_code}")
        logger.info(f"📋 Session data - UoC data keys: {list(uoc_data.keys()) if uoc_data else 'None'}")
        
        if not uoc_code or not uoc_data:
            logger.error("❌ Missing session data")
            return jsonify({'error': 'UoC data not found. Please start over.'}), 400
        
        # Check upload method
        upload_method = request.form.get('upload_method', 'file')
        assessment_type = request.form.get('assessment_type', '')
        
        logger.info(f"📋 Form data - Upload method: {upload_method}")
        logger.info(f"📋 Form data - Assessment type: {assessment_type}")
        logger.info(f"📋 Form data - Files: {list(request.files.keys())}")
        
        if upload_method == 'file':
            # Handle file upload
            uploaded_file = request.files.get('assessment_file')
            if not uploaded_file:
                return jsonify({'error': 'Assessment file is required'}), 400
            
            # File size validation
            if request.content_length and request.content_length > app.config['MAX_CONTENT_LENGTH']:
                return jsonify({'error': f'File too large. Maximum size is {app.config["MAX_CONTENT_LENGTH"] // (1024*1024)}MB'}), 400
            
            # Save uploaded file
            filename = f"{uoc_code}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uploaded_file.filename}"
            filepath = os.path.join('storage/assessments', filename)
            uploaded_file.save(filepath)
            
            logger.info(f"📄 Processing uploaded file: {filename}")
            
            # Use improved integration
            results = run_assessment_analysis(
                file_path=filepath,
                uoc_data=uoc_data,
                api_key=app.config['GEMINI_API_KEY']
            )
            
        else:
            # Handle text paste
            assessment_text = request.form.get('assessment_text', '').strip()
            if not assessment_text:
                return jsonify({'error': 'Assessment text is required'}), 400
            
            logger.info(f"📋 Processing pasted text (length: {len(assessment_text)})")
            
            # Use improved integration
            results = run_assessment_analysis(
                text_content=assessment_text,
                uoc_data=uoc_data,
                api_key=app.config['GEMINI_API_KEY']
            )
        
        # Check if analysis was successful
        if not results['success']:
            return jsonify({'error': results['error']}), 500
        
        # Save results (including mappings from the analysis)
        session_id = f"{uoc_code}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        session_data = {
            'session_id': session_id,
            'uoc_code': uoc_code,
            'assessment_type': results['statistics']['assessment_type'],
            'filename': filename if upload_method == 'file' else 'pasted_text.txt',
            'uoc_data': uoc_data,
            'questions': results['questions'],
            'mappings': results['mappings'],  # Save the actual mappings from analysis
            'statistics': {
                'total_questions': len(results['questions']),
                'total_mappings': len(results['mappings']),  # Use actual mapping count
                'assessment_type': results['statistics']['assessment_type'],
                'uoc_info': results['statistics']['uoc_info']
            },
            'created_at': datetime.now().isoformat()
        }
        
        # Ensure storage/mappings directory exists
        os.makedirs('storage/mappings', exist_ok=True)
        
        # Save session data
        session_file = f"storage/mappings/{session_id}.json"
        logger.info(f"💾 Saving session data to: {session_file}")
        with open(session_file, 'w') as f:
            json.dump(session_data, f, indent=2)
        logger.info(f"✅ Session data saved successfully")
        
        # Clear session data
        session.pop('uoc_code', None)
        session.pop('uoc_data', None)
        
        return jsonify({
            'success': True,
            'redirect_url': url_for('review_questions', session_id=session_id)
        })
        
    except Exception as e:
        logger.error(f"❌ Error processing assessment: {str(e)}")
        return jsonify({'error': f'LLM access failed or is unavailable. {str(e)}'}), 500

@app.route('/review-questions/<session_id>')
def review_questions(session_id):
    """Step 3: Review extracted questions before mapping"""
    try:
        # Load session data
        session_file = f"storage/mappings/{session_id}.json"
        with open(session_file, 'r') as f:
            session_data = json.load(f)
        
        return render_template('review_questions.html', 
                             session_data=session_data,
                             session_id=session_id)
        
    except Exception as e:
        logger.error(f"❌ Error loading review questions: {str(e)}")
        return f"Error loading session: {str(e)}", 404

@app.route('/dashboard/<session_id>')
def dashboard(session_id):
    """Main validation dashboard"""
    try:
        # Load session data
        session_file = f"storage/mappings/{session_id}.json"
        with open(session_file, 'r') as f:
            session_data = json.load(f)
        
        response = make_response(render_template('dashboard.html', 
                             session_data=session_data,
                             session_id=session_id))
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response
        
    except Exception as e:
        logger.error(f"❌ Error loading dashboard: {str(e)}")
        return f"Error loading session: {str(e)}", 404

@app.route('/mapping-review/<session_id>')
def mapping_review(session_id):
    """Show mapping review interface for HITL adjustments"""
    try:
        # Load session data
        session_file = f"storage/mappings/{session_id}.json"
        logger.info(f"📂 Loading session data for mapping review: {session_file}")
        
        with open(session_file, 'r') as f:
            session_data = json.load(f)
        
        # Associate mappings with their questions
        mappings_by_question = {}
        if 'mappings' in session_data:
            for mapping in session_data['mappings']:
                question_id = mapping.get('question_id')
                if question_id:
                    if question_id not in mappings_by_question:
                        mappings_by_question[question_id] = []
                    mappings_by_question[question_id].append(mapping)
        
        # Add mappings to each question
        for question in session_data['questions']:
            question_id = question.get('id')
            if question_id in mappings_by_question:
                question['mappings'] = mappings_by_question[question_id]
            else:
                question['mappings'] = []
        
        return render_template('mapping_review.html', 
                             session_id=session_id, 
                             session_data=session_data)
    except FileNotFoundError:
        flash('Session not found', 'error')
        return redirect(url_for('index'))
    except Exception as e:
        logger.error(f"❌ Error loading mapping review: {e}")
        flash('Error loading mapping review', 'error')
        return redirect(url_for('index'))

@app.route('/proceed-to-mapping/<session_id>', methods=['POST'])
def proceed_to_mapping(session_id):
    """Proceed from question review to mapping review (HITL step)"""
    try:
        # Ensure storage/mappings directory exists
        os.makedirs('storage/mappings', exist_ok=True)
        
        # Load session data
        session_file = f"storage/mappings/{session_id}.json"
        logger.info(f"📂 Loading session data from: {session_file}")
        with open(session_file, 'r') as f:
            session_data = json.load(f)
        
        # Update questions if any were modified
        updated_questions = request.json.get('questions', []) if request.is_json else []
        if updated_questions:
            session_data['questions'] = updated_questions
            # Save updated session data
            with open(session_file, 'w') as f:
                json.dump(session_data, f, indent=2)
        
        # Perform mapping with the updated questions
        logger.info(f"🗺️  Starting mapping for session {session_id}")
        
        from main import run_assessment_analysis
        
        # Get UoC data from session and prepare it properly
        uoc_data_raw = session_data.get('uoc_data', {})
        api_key = app.config['GEMINI_API_KEY']
        
        # Construct proper UoC data structure with top-level uoc_code and title
        uoc_data = {
            'uoc_code': session_data.get('uoc_code', 'Unknown'),
            'title': session_data.get('uoc_data', {}).get('title', 'Unknown'),
            'elements': uoc_data_raw.get('elements', []),
            'performance_criteria': uoc_data_raw.get('performance_criteria', []),
            'performance_evidence': uoc_data_raw.get('performance_evidence', []),
            'knowledge_evidence': uoc_data_raw.get('knowledge_evidence', [])
        }
        
        # Run mapping only (using pre-extracted questions)
        logger.info(f"📋 Starting mapping with {len(session_data['questions'])} questions")
        logger.info(f"📋 UoC data keys: {list(uoc_data.keys()) if uoc_data else 'None'}")
        
        mapping_results = run_assessment_analysis(
            uoc_data=uoc_data,
            api_key=api_key,
            mapping_only=True,
            questions=session_data['questions']
        )
        
        logger.info(f"📋 Mapping results keys: {list(mapping_results.keys()) if mapping_results else 'None'}")
        logger.info(f"📋 Mapping success: {mapping_results.get('success', 'Not found')}")
        
        # Debug mapping results structure
        if mapping_results and 'mappings' in mapping_results:
            mappings = mapping_results['mappings']
            logger.info(f"📋 Number of mappings: {len(mappings)}")
            if mappings:
                logger.info(f"📋 First mapping type: {type(mappings[0])}")
                logger.info(f"📋 First mapping keys: {list(mappings[0].keys()) if isinstance(mappings[0], dict) else 'Not a dict'}")
        
        if mapping_results['success']:
            # Update session with mapping results
            session_data['mappings'] = mapping_results['mappings']
            session_data['statistics'] = mapping_results['statistics']
            
            # Save updated session
            with open(session_file, 'w') as f:
                json.dump(session_data, f, indent=2)
            
            logger.info(f"✅ Mapping completed for session {session_id}")
            
            # Check if there were API issues during mapping
            api_issues = False
            fallback_count = 0
            if 'mappings' in mapping_results:
                # Count questions that used fallback mappings (indicates API issues)
                try:
                    fallback_count = sum(1 for mapping in mapping_results['mappings'] 
                                       if isinstance(mapping, dict) and mapping.get('mapping_source') == 'fallback')
                    if fallback_count > 0:
                        api_issues = True
                        logger.warning(f"⚠️  {fallback_count} questions used fallback mappings due to API issues")
                        logger.warning(f"⚠️  This may indicate temporary API issues or rate limiting")
                except Exception as e:
                    logger.warning(f"⚠️  Error checking fallback mappings: {e}")
                    fallback_count = 0
            
            return jsonify({
                'success': True,
                'redirect_url': url_for('mapping_review', session_id=session_id),  # Changed to mapping review
                'api_issues': api_issues,
                'fallback_count': fallback_count
            })
        else:
            logger.error(f"❌ Mapping failed: {mapping_results.get('error', 'Unknown error')}")
            return jsonify({
                'success': False,
                'error': mapping_results.get('error', 'Mapping failed')
            }), 500
        
    except Exception as e:
        logger.error(f"❌ Error proceeding to mapping: {str(e)}")
        return jsonify({'error': f'LLM access failed or is unavailable. {str(e)}'}), 500

@app.route('/api/export/<session_id>')
def export_audit_report(session_id):
    """Generate audit-ready export"""
    try:
        # Load session data
        session_file = f"storage/mappings/{session_id}.json"
        with open(session_file, 'r') as f:
            session_data = json.load(f)
        
        # Generate audit report
        from utils.audit_export import generate_audit_report
        report = generate_audit_report(session_data)
        
        return jsonify(report)
        
    except Exception as e:
        logger.error(f"❌ Error generating export: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/clear-cache/<uoc_code>')
def clear_cache(uoc_code):
    """Clear cache for specific UoC (for testing)"""
    try:
        from agents.fetch_agent import FetchAgent
        fetch_agent = FetchAgent(gemini_api_key=app.config['GEMINI_API_KEY'])
        
        success = fetch_agent.clear_cache(uoc_code)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Cache cleared for {uoc_code}'
            })
        else:
            return jsonify({
                'success': False,
                'message': f'No cache found for {uoc_code}'
            })
        
    except Exception as e:
        logger.error(f"❌ Error clearing cache: {str(e)}")
        return jsonify({'error': str(e)}), 500

if app.config.get('DEBUG'):
    @app.route('/test')
    def test_agents():
    """Test endpoint to verify all agents are working"""
    try:
        results = {}
        
        # Test FetchAgent
        logger.info("🧪 Testing FetchAgent...")
        from agents.fetch_agent import FetchAgent
        test_fetch_agent = FetchAgent(gemini_api_key=app.config['GEMINI_API_KEY'])
        test_uoc = test_fetch_agent.execute("HLTINF006")
        results['fetch_agent'] = f"✅ Fetched {len(test_uoc.get('elements', []))} elements for HLTINF006"
        
        # Test improved integration
        logger.info("🧪 Testing improved integration...")
        test_uoc_data = {
            'uoc_code': 'TEST001',
            'title': 'Test Unit',
            'elements': [{'id': 'E1', 'description': 'Test element'}],
            'performance_criteria': [{'code': 'PC1.1', 'description': 'Test criterion'}],
            'performance_evidence': [],
            'knowledge_evidence': []
        }
        
        test_text = "1. What is the main purpose of this test? A) To test B) To validate"
        test_results = run_assessment_analysis(
            text_content=test_text,
            uoc_data=test_uoc_data,
            api_key=app.config['GEMINI_API_KEY']
        )
        
        if test_results['success']:
            results['integration'] = f"✅ Integration test passed: {test_results['statistics']['total_questions']} questions extracted"
        else:
            results['integration'] = f"❌ Integration test failed: {test_results['error']}"
        
        return jsonify({
            'status': 'success',
            'timestamp': datetime.now().isoformat(),
            'tests': results
        })
        
    except Exception as e:
        logger.error(f"❌ Test error: {str(e)}")
        return jsonify({
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

if app.config.get('DEBUG'):
    @app.route('/api/test-comment', methods=['POST'])
    def test_comment_api():
    """Test endpoint for comment API"""
    try:
        data = request.get_json()
        return jsonify({
            'success': True,
            'message': 'Test comment API working',
            'received_data': data
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/validation/<session_id>')
def validation_screen(session_id):
    """Collaborative validation screen for question mappings"""
    try:
        # Load session data
        session_path = os.path.join('storage', 'mappings', f'{session_id}.json')
        
        if not os.path.exists(session_path):
            return render_template('error.html', error="Session not found"), 404
        
        with open(session_path, 'r') as f:
            session_data = json.load(f)
        
        # Initialize collaborative validation if not already done
        if not session_data.get('validation_initialized'):
            from main import initialize_collaborative_validation
            session_data = initialize_collaborative_validation(session_data)
            
            # Save updated session data
            with open(session_path, 'w') as f:
                json.dump(session_data, f, indent=2)
        
        response = make_response(render_template('validation.html', 
                             session_data=session_data,
                             session_id=session_id))
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response
    
    except Exception as e:
        app.logger.error(f"Error loading validation screen: {str(e)}")
        return render_template('error.html', error=str(e)), 500

@app.route('/api/validation/<session_id>/coverage-analysis', methods=['GET'])
def get_coverage_analysis(session_id):
    """Get comprehensive coverage analysis for a session"""
    try:
        # Load session data
        session_path = os.path.join('storage', 'mappings', f'{session_id}.json')
        
        if not os.path.exists(session_path):
            return jsonify({'success': False, 'error': 'Session not found'}), 404
        
        with open(session_path, 'r') as f:
            session_data = json.load(f)
        
        # Run coverage analysis
        from agents.validation_agent import CollaborativeValidationAgent
        validation_agent = CollaborativeValidationAgent()
        
        coverage_analysis = validation_agent.analyze_coverage_quality(session_data)
        
        return jsonify({
            'success': True,
            'coverage_analysis': coverage_analysis
        })
        
    except Exception as e:
        app.logger.error(f"Error getting coverage analysis: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/validation/<session_id>/comment', methods=['POST'])
def add_validation_comment(session_id):
    """Add comment to validation discussion thread"""
    try:
        data = request.get_json()
        
        # Load session data
        session_path = os.path.join('storage', 'mappings', f'{session_id}.json')
        
        # Check if session file exists
        if not os.path.exists(session_path):
            return jsonify({'success': False, 'error': 'Session not found'}), 404
        
        with open(session_path, 'r') as f:
            session_data = json.load(f)
        
        # Ensure validation_threads structure exists
        if 'validation_threads' not in session_data:
            session_data['validation_threads'] = {}
        
        # Find the thread for the question
        question_id = data.get('question_id', '5')
        if str(question_id) not in session_data['validation_threads']:
            # Create thread if it doesn't exist using actual mapping data
            from agents.validation_agent import CollaborativeValidationAgent
            validation_agent = CollaborativeValidationAgent()
            
            # Find the mapping for this question
            question_mapping = None
            for mapping in session_data.get('mappings', []):
                if str(mapping.get('question_id')) == str(question_id):
                    question_mapping = mapping
                    break
            
            if question_mapping:
                thread = validation_agent.initiate_validation_thread(
                    question_mapping, 
                    'system', 
                    'system'
                )
                session_data['validation_threads'][str(question_id)] = thread
            else:
                # Create basic thread if no mapping found
                session_data['validation_threads'][str(question_id)] = {
                    'thread_id': f'{session_id}_q{question_id}',
                    'question_id': question_id,
                    'validation_discussion': [],
                    'validation_metadata': {
                        'last_updated': datetime.now().isoformat()
                    }
                }
        
        thread_data = session_data['validation_threads'][str(question_id)]
        
        # Create comment entry
        comment_entry = {
            'reviewer_id': data.get('user_id', 'current_user'),
            'reviewer_name': data.get('user_name', 'Current User'),
            'reviewer_role': data.get('user_role', 'assessor'),
            'feedback_type': data.get('comment_type', 'comment'),
            'feedback_text': data.get('comment_text', ''),
            'timestamp': datetime.now().isoformat(),
            'agreement': 'neutral'
        }
        
        # Add comment to discussion
        thread_data['validation_discussion'].append(comment_entry)
        thread_data['validation_metadata']['last_updated'] = datetime.now().isoformat()
        
        # Save updated session
        with open(session_path, 'w') as f:
            json.dump(session_data, f, indent=2)
        
        return jsonify({
            'success': True, 
            'comment': comment_entry,
            'message': 'Comment added successfully'
        })
        
    except Exception as e:
        app.logger.error(f"Error adding validation comment: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/validation/<session_id>/compliance-summary', methods=['GET'])
def get_compliance_summary(session_id):
    """Summarize ASQA compliance with actionable question links for HITL."""
    try:
        # Load session data
        session_path = os.path.join('storage', 'mappings', f'{session_id}.json')
        if not os.path.exists(session_path):
            return jsonify({'success': False, 'error': 'Session not found'}), 404

        with open(session_path, 'r') as f:
            session_data = json.load(f)

        mappings = session_data.get('mappings', [])
        if isinstance(mappings, dict) and 'mappings' in mappings:
            actual_mappings = mappings['mappings']
        else:
            actual_mappings = mappings

        total = max(1, len(actual_mappings))

        # Buckets
        method_counts = {'KBA': 0, 'SBA': 0, 'PEP': 0, 'Mixed': 0}
        low_cog_question_ids = []  # REMEMBER/UNDERSTAND
        missing_evidence_qids = []  # no KE and no PE
        low_confidence_qids = []  # avg item confidence < 0.6

        def average_confidence(mapping):
            ma = mapping.get('mapping_analysis', {})
            scores = []
            for key in ['mapped_elements', 'mapped_performance_criteria', 'mapped_performance_evidence', 'mapped_knowledge_evidence']:
                for item in ma.get(key, []) or []:
                    c = item.get('confidence_score') or 0
                    scores.append(c)
            return (sum(scores) / len(scores)) if scores else 0

        for m in actual_mappings:
            method = m.get('assessment_type', 'Mixed')
            if method not in method_counts:
                method = 'Mixed'
            method_counts[method] += 1

            # Cognitive level
            level = (m.get('bloom_taxonomy', {}) or {}).get('primary_level', '').upper()
            if level in ['REMEMBER', 'UNDERSTAND']:
                low_cog_question_ids.append(m.get('question_id'))

            # Evidence presence
            ma = m.get('mapping_analysis', {})
            has_ke = bool(ma.get('mapped_knowledge_evidence'))
            has_pe = bool(ma.get('mapped_performance_evidence'))
            if not has_ke and not has_pe:
                missing_evidence_qids.append(m.get('question_id'))

            # Confidence
            if average_confidence(m) < 0.6:
                low_confidence_qids.append(m.get('question_id'))

        # Percentages
        pep_pct = round(method_counts['PEP'] / total * 100, 1)
        sba_pct = round(method_counts['SBA'] / total * 100, 1)

        # Construct standards summary
        standards = []

        # ASQA 1.4 – Assessment Methods
        issues_14 = []
        if pep_pct < 20:
            issues_14.append({
                'title': 'Increase practical or workplace evidence',
                'description': f'PEP items are {pep_pct}% of total; target at least 20%.',
                'question_ids': [q for q in low_cog_question_ids if q is not None]
            })
        if sba_pct < 20:
            issues_14.append({
                'title': 'Add skills-based assessment',
                'description': f'SBA items are {sba_pct}% of total; target a balanced mix.',
                'question_ids': [q for q in low_cog_question_ids if q is not None]
            })
        standards.append({
            'code': '1.4',
            'title': 'Assessment Methods',
            'status': 'REVIEW' if issues_14 else 'PASS',
            'description': 'Assessment methods should provide valid, sufficient and current evidence across contexts.',
            'issues': issues_14
        })

        # ASQA 1.5 – Assessment Evidence
        issues_15 = []
        if missing_evidence_qids:
            issues_15.append({
                'title': 'Missing evidence alignment',
                'description': 'Some items have no Knowledge or Performance Evidence linkage.',
                'question_ids': [q for q in missing_evidence_qids if q is not None]
            })
        standards.append({
            'code': '1.5',
            'title': 'Assessment Evidence',
            'status': 'REVIEW' if issues_15 else 'PASS',
            'description': 'Evidence requirements must be clearly demonstrated and mapped.',
            'issues': issues_15
        })

        # ASQA 1.6 – Assessment Judgement
        issues_16 = []
        if low_confidence_qids:
            issues_16.append({
                'title': 'Low mapping confidence',
                'description': 'These items have low average mapping confidence (<60%).',
                'question_ids': [q for q in low_confidence_qids if q is not None]
            })
        standards.append({
            'code': '1.6',
            'title': 'Assessment Judgement',
            'status': 'REVIEW' if issues_16 else 'PASS',
            'description': 'Judgements should be consistent and based on clear, confident evidence alignment.',
            'issues': issues_16
        })

        # ASQA 1.8 – Assessment Validation (overall)
        # Consider REVIEW if any other standard is REVIEW
        overall_review = any(s['status'] == 'REVIEW' for s in standards)
        standards.insert(0, {
            'code': '1.8',
            'title': 'Assessment Validation',
            'status': 'REVIEW' if overall_review else 'PASS',
            'description': 'Overall validation outcome based on methods, evidence and judgement quality.',
            'issues': []
        })

        return jsonify({'success': True, 'standards': standards})

    except Exception as e:
        app.logger.error(f"Error building compliance summary: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/validation/<session_id>/export-remediation.xlsx', methods=['GET'])
def export_remediation_plan(session_id):
    """Export remediation tasks to an Excel workbook for audit handover."""
    try:
        session_path = os.path.join('storage', 'mappings', f'{session_id}.json')
        if not os.path.exists(session_path):
            return jsonify({'success': False, 'error': 'Session not found'}), 404

        with open(session_path, 'r') as f:
            session_data = json.load(f)

        from agents.validation_agent import CollaborativeValidationAgent
        validation_agent = CollaborativeValidationAgent()
        coverage = validation_agent.analyze_coverage_quality(session_data)
        tasks = coverage.get('remediation_tasks', [])

        # Build workbook
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = 'Remediation Plan'

        headers = [
            'Standard', 'Category', 'Severity', 'Summary', 'Rationale',
            'Impacted Elements', 'Impacted Questions', 'Suggested Actions',
            'Owner Role', 'Due (days)', 'Acceptance Criteria'
        ]
        ws.append(headers)

        for t in tasks:
            ws.append([
                t.get('standard_code', ''),
                t.get('category', ''),
                t.get('severity', ''),
                t.get('summary', ''),
                t.get('rationale', ''),
                ', '.join(t.get('impacted_elements', []) or []),
                ', '.join([str(q) for q in (t.get('impacted_questions', []) or [])]),
                ' | '.join(t.get('suggested_actions', []) or []),
                t.get('owner_role', ''),
                t.get('due_days', ''),
                ' | '.join(t.get('acceptance_criteria', []) or [])
            ])

        # Auto width (simple)
        for column_cells in ws.columns:
            length = max(len(str(cell.value)) if cell.value else 0 for cell in column_cells)
            ws.column_dimensions[column_cells[0].column_letter].width = min(60, length + 2)

        # Add cover sheet with session metadata
        meta = wb.create_sheet('Session Info', 0)
        meta.append(['Session ID', session_id])
        meta.append(['UoC Code', session_data.get('uoc_code', '')])
        title = session_data.get('uoc_data', {}).get('title', '')
        meta.append(['UoC Title', title])
        meta.append(['Generated', datetime.now().isoformat()])

        # Stream bytes
        buffer = io.BytesIO()
        wb.save(buffer)
        buffer.seek(0)

        response = make_response(buffer.getvalue())
        response.headers['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        response.headers['Content-Disposition'] = f'attachment; filename="{session_id}_remediation_plan.xlsx"'
        return response

    except Exception as e:
        app.logger.error(f"Error exporting remediation plan: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/validation/<session_id>/intelligent-dashboard', methods=['GET'])
def get_intelligent_dashboard_data(session_id):
    """Get intelligent dashboard data including analytics, insights, and predictions"""
    try:
        # Load session data
        session_path = os.path.join('storage', 'mappings', f'{session_id}.json')
        
        if not os.path.exists(session_path):
            return jsonify({'success': False, 'error': 'Session not found'}), 404
        
        with open(session_path, 'r') as f:
            session_data = json.load(f)
        
        # Run intelligent analysis
        from agents.validation_agent import CollaborativeValidationAgent
        validation_agent = CollaborativeValidationAgent()
        
        # Get coverage analysis
        coverage_analysis = validation_agent.analyze_coverage_quality(session_data)
        
        # Calculate intelligent metrics
        mappings = session_data.get('mappings', [])
        if isinstance(mappings, dict) and 'mappings' in mappings:
            actual_mappings = mappings['mappings']
        else:
            actual_mappings = mappings
        
        # Calculate real-time analytics
        total_questions = len(actual_mappings)
        total_mappings = sum(1 for m in actual_mappings if m.get('mapping_analysis'))
        
        # Calculate average confidence
        total_confidence = 0
        confidence_count = 0
        low_confidence_count = 0
        
        for mapping in actual_mappings:
            if mapping.get('mapping_analysis'):
                mapping_confidence = 0
                mapping_count = 0
                
                for category in ['mapped_elements', 'mapped_performance_criteria', 'mapped_performance_evidence', 'mapped_knowledge_evidence']:
                    items = mapping.get('mapping_analysis', {}).get(category, [])
                    for item in items:
                        confidence = item.get('confidence_score', 0)
                        mapping_confidence += confidence
                        mapping_count += 1
                
                if mapping_count > 0:
                    avg_confidence = mapping_confidence / mapping_count
                    total_confidence += avg_confidence
                    confidence_count += 1
                    
                    if avg_confidence < 0.6:
                        low_confidence_count += 1
        
        average_confidence = (total_confidence / confidence_count * 100) if confidence_count > 0 else 0
        
        # Calculate coverage percentages
        uoc_data = session_data.get('uoc_data', {})
        total_elements = len(uoc_data.get('elements', []))
        total_criteria = len(uoc_data.get('performance_criteria', []))
        total_knowledge_evidence = len(uoc_data.get('knowledge_evidence', []))
        total_performance_evidence = len(uoc_data.get('performance_evidence', []))
        
        # Count mapped components
        mapped_elements = set()
        mapped_criteria = set()
        mapped_knowledge_evidence = set()
        mapped_performance_evidence = set()
        
        # Build per-element structures for detailed coverage
        element_list = uoc_data.get('elements', []) or []
        # Normalize element descriptors into a mapping by code (E1, E2, ...)
        element_code_to_info = {}
        for idx, element in enumerate(element_list, start=1):
            # Support both {'id': 'E1'} and {'code': 'E1'} and missing codes
            code = element.get('code') or element.get('id') or f"E{idx}"
            title = element.get('title') or element.get('description') or f"Element {idx}"
            element_code_to_info[code] = {
                'code': code,
                'title': title,
                'pcs': [],
                'mapped_pc_codes': set(),
                'question_ids': set(),
                'confidences': [],
                'assessment_type_counts': {'KBA': 0, 'SBA': 0, 'PEP': 0, 'Mixed': 0}
            }

        # Map PCs to elements by code prefix (e.g., PC1.2 belongs to E1)
        pc_list = uoc_data.get('performance_criteria', []) or []
        pc_code_to_element_code = {}
        for pc in pc_list:
            pc_code = pc.get('code') or pc.get('criterion_id') or pc.get('criterion_code')
            if not pc_code:
                continue
            # Extract element number from PC code pattern PC{n}.{m}
            element_num = None
            try:
                # Remove 'PC' then split by '.' → first segment like '1'
                number_part = pc_code.replace('PC', '').split('.')[0]
                element_num = int(number_part)
            except Exception:
                element_num = None
            element_code = f"E{element_num}" if element_num else None
            if element_code and element_code in element_code_to_info:
                element_code_to_info[element_code]['pcs'].append(pc.get('code') or pc_code)
                pc_code_to_element_code[pc_code] = element_code

        for mapping in actual_mappings:
            if mapping.get('mapping_analysis'):
                for element in mapping.get('mapping_analysis', {}).get('mapped_elements', []):
                    mapped_elements.add(element.get('element_id', ''))
                    # Track element-level stats
                    element_code = element.get('element_code') or element.get('element_id')
                    if element_code in element_code_to_info:
                        element_code_to_info[element_code]['question_ids'].add(mapping.get('question_id'))
                        conf = element.get('confidence_score') or 0
                        element_code_to_info[element_code]['confidences'].append(conf)
                for criterion in mapping.get('mapping_analysis', {}).get('mapped_performance_criteria', []):
                    mapped_criteria.add(criterion.get('criterion_id', ''))
                    # Attribute PC to its parent element
                    pc_code = criterion.get('criterion_code') or criterion.get('criterion_id')
                    element_code = pc_code_to_element_code.get(pc_code)
                    if element_code in element_code_to_info:
                        element_code_to_info[element_code]['mapped_pc_codes'].add(pc_code)
                        element_code_to_info[element_code]['question_ids'].add(mapping.get('question_id'))
                        conf = criterion.get('confidence_score') or 0
                        element_code_to_info[element_code]['confidences'].append(conf)
                for evidence in mapping.get('mapping_analysis', {}).get('mapped_knowledge_evidence', []):
                    mapped_knowledge_evidence.add(evidence.get('evidence_id', ''))
                for evidence in mapping.get('mapping_analysis', {}).get('mapped_performance_evidence', []):
                    mapped_performance_evidence.add(evidence.get('evidence_id', ''))

                # Assessment type counts per element (approx via PCs attribution)
                assessment_type = mapping.get('assessment_type', 'Mixed')
                if assessment_type not in ['KBA', 'SBA', 'PEP']:
                    assessment_type = 'Mixed'
                # Count against each attributed element for this mapping
                attributed_element_codes = set()
                for criterion in mapping.get('mapping_analysis', {}).get('mapped_performance_criteria', []):
                    pc_code = criterion.get('criterion_code') or criterion.get('criterion_id')
                    el_code = pc_code_to_element_code.get(pc_code)
                    if el_code:
                        attributed_element_codes.add(el_code)
                for el_code in attributed_element_codes:
                    if el_code in element_code_to_info:
                        element_code_to_info[el_code]['assessment_type_counts'][assessment_type] = (
                            element_code_to_info[el_code]['assessment_type_counts'].get(assessment_type, 0) + 1
                        )
        
        # Calculate coverage percentages
        elements_coverage = (len(mapped_elements) / total_elements * 100) if total_elements > 0 else 0
        criteria_coverage = (len(mapped_criteria) / total_criteria * 100) if total_criteria > 0 else 0
        knowledge_coverage = (len(mapped_knowledge_evidence) / total_knowledge_evidence * 100) if total_knowledge_evidence > 0 else 0
        performance_coverage = (len(mapped_performance_evidence) / total_performance_evidence * 100) if total_performance_evidence > 0 else 0
        
        # Generate intelligent insights
        insights = []
        
        # Critical gaps insight
        unmapped_questions = total_questions - total_mappings
        if unmapped_questions > 0:
            insights.append({
                'type': 'critical',
                'title': 'Unmapped Questions Detected',
                'description': f'{unmapped_questions} questions have no mappings and require attention.',
                'action': 'Review and map these questions to ensure complete coverage.'
            })
        
        # Quality insight
        if average_confidence < 70:
            insights.append({
                'type': 'warning',
                'title': 'Low Average Confidence',
                'description': f'Average mapping confidence is {average_confidence:.1f}%.',
                'action': 'Review low-confidence mappings to improve accuracy.'
            })
        elif average_confidence >= 80:
            insights.append({
                'type': 'success',
                'title': 'High Quality Mappings',
                'description': f'Average mapping confidence is {average_confidence:.1f}%.',
                'action': 'Excellent mapping quality meets audit standards.'
            })
        
        # Coverage insights
        if elements_coverage < 80:
            insights.append({
                'type': 'warning',
                'title': 'Incomplete Element Coverage',
                'description': f'Only {elements_coverage:.1f}% of elements are covered.',
                'action': 'Add questions to cover missing elements for complete assessment.'
            })
        
        # Generate predictive insights
        predictions = []
        
        # Predict likely gaps based on patterns
        if elements_coverage < 90:
            predictions.append({
                'title': 'Likely Coverage Gaps',
                'confidence': 85,
                'description': 'Pattern analysis suggests missing coverage in key elements.',
                'action': 'Review element coverage and add relevant questions.'
            })
        
        # Predict quality improvements
        if low_confidence_count > total_questions * 0.2:
            predictions.append({
                'title': 'Quality Improvement Needed',
                'confidence': 75,
                'description': f'{low_confidence_count} mappings have low confidence scores.',
                'action': 'Review and refine these mappings for better accuracy.'
            })
        
        # Generate risk assessment
        risks = []
        
        if low_confidence_count > 0:
            risks.append({
                'type': 'quality',
                'severity': 'medium' if low_confidence_count <= 3 else 'high',
                'title': 'Low Confidence Mappings',
                'description': f'{low_confidence_count} mappings have confidence scores below 60%.',
                'impact': 'May affect audit compliance and mapping accuracy.',
                'recommendation': 'Review and validate these mappings before final submission.'
            })
        
        if elements_coverage < 80:
            risks.append({
                'type': 'coverage',
                'severity': 'high',
                'title': 'Incomplete Coverage',
                'description': f'Only {elements_coverage:.1f}% of elements are covered.',
                'impact': 'May fail audit requirements for comprehensive assessment.',
                'recommendation': 'Add questions to cover missing elements.'
            })
        
        # Build detailed per-element coverage payload
        coverage_by_element = []
        gaps = []
        for code, info in element_code_to_info.items():
            total_pcs_for_element = len(info['pcs']) if info['pcs'] else 0
            mapped_pcs_for_element = len(info['mapped_pc_codes'])
            coverage_pct = (mapped_pcs_for_element / total_pcs_for_element * 100) if total_pcs_for_element > 0 else (100 if len(info['question_ids']) > 0 else 0)
            avg_conf = (sum(info['confidences']) / len(info['confidences']) * 100) if info['confidences'] else 0
            coverage_state = 'covered' if coverage_pct >= 99.9 else ('partial' if coverage_pct > 0 else 'unmapped')
            coverage_by_element.append({
                'code': code,
                'title': info['title'],
                'coveragePct': round(coverage_pct, 1),
                'questionCount': len(info['question_ids']),
                'avgConfidence': round(avg_conf, 1),
                'assessmentType': info['assessment_type_counts'],
                'pcs': [{'code': pc_code,
                         'covered': pc_code in info['mapped_pc_codes']}
                        for pc_code in info['pcs']]
            })
            if coverage_state in ['unmapped', 'partial']:
                gaps.append({
                    'code': code,
                    'title': info['title'],
                    'type': 'Element',
                    'status': 'Unmapped' if coverage_state == 'unmapped' else 'Partial',
                    'questionCount': len(info['question_ids']),
                    'avgConfidence': round(avg_conf, 1)
                })

        # Build confidence histogram buckets (0-100 step 10)
        histogram_buckets = [0] * 10
        for m in actual_mappings:
            ma = m.get('mapping_analysis', {})
            for category in ['mapped_elements', 'mapped_performance_criteria', 'mapped_performance_evidence', 'mapped_knowledge_evidence']:
                for item in ma.get(category, []) or []:
                    c = item.get('confidence_score') or 0
                    # Confidence scores are 0..1 in mapping_agent; normalize to 0..100 if needed
                    if c <= 1.0:
                        c = c * 100
                    bucket = min(9, int(c // 10))
                    histogram_buckets[bucket] += 1

        # Compile intelligent dashboard data
        dashboard_data = {
            'success': True,
            'analytics': {
                'total_questions': total_questions,
                'total_mappings': total_mappings,
                'average_confidence': round(average_confidence, 1),
                'low_confidence_count': low_confidence_count,
                'coverage_percentage': round((total_mappings / total_questions * 100) if total_questions > 0 else 0, 1)
            },
            'coverage': {
                'elements': {
                    'percentage': round(elements_coverage, 1),
                    'mapped': len(mapped_elements),
                    'total': total_elements
                },
                'performance_criteria': {
                    'percentage': round(criteria_coverage, 1),
                    'mapped': len(mapped_criteria),
                    'total': total_criteria
                },
                'knowledge_evidence': {
                    'percentage': round(knowledge_coverage, 1),
                    'mapped': len(mapped_knowledge_evidence),
                    'total': total_knowledge_evidence
                },
                'performance_evidence': {
                    'percentage': round(performance_coverage, 1),
                    'mapped': len(mapped_performance_evidence),
                    'total': total_performance_evidence
                }
            },
            'coverageByElement': coverage_by_element,
            'gaps': gaps,
            'assessmentTypeBreakdown': coverage_by_element,  # reuse structure; frontend reads assessmentType
            'confidenceHistogram': histogram_buckets,
            'insights': insights,
            'predictions': predictions,
            'risks': risks,
            'recommendations': coverage_analysis.get('gap_analysis', {}).get('recommendations', [])
        }
        
        return jsonify(dashboard_data)
        
    except Exception as e:
        app.logger.error(f"Error getting intelligent dashboard data: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/mapping/<session_id>/add', methods=['POST'])
def add_mapping(session_id):
    """Add a new mapping for a question"""
    try:
        data = request.json
        question_id = data.get('question_id')
        mapped_to = data.get('mapped_to')
        confidence_score = data.get('confidence_score', 80)
        notes = data.get('notes', '')
        
        # Load session data
        session_file = f"storage/mappings/{session_id}.json"
        with open(session_file, 'r') as f:
            session_data = json.load(f)
        
        # Find the UoC component description
        component_description = ""
        uoc_data = session_data.get('uoc_data', {})
        
        if mapped_to.startswith('E'):
            element_id = mapped_to[1:]  # Remove 'E' prefix
            for element in uoc_data.get('elements', []):
                if element.get('id') == element_id:
                    component_description = element.get('description', '')
                    break
        elif mapped_to.startswith('PC'):
            pc_code = mapped_to[2:]  # Remove 'PC' prefix
            for pc in uoc_data.get('performance_criteria', []):
                if pc.get('code') == pc_code:
                    component_description = pc.get('description', '')
                    break
        elif mapped_to.startswith('PE'):
            pe_code = mapped_to[2:]  # Remove 'PE' prefix
            for pe in uoc_data.get('performance_evidence', []):
                if pe.get('code') == pe_code:
                    component_description = pe.get('description', '')
                    break
        elif mapped_to.startswith('KE'):
            ke_code = mapped_to[2:]  # Remove 'KE' prefix
            for ke in uoc_data.get('knowledge_evidence', []):
                if ke.get('code') == ke_code:
                    component_description = ke.get('description', '')
                    break
        
        # Create new mapping
        new_mapping = {
            'id': f"mapping_{len(session_data.get('mappings', [])) + 1}",
            'question_id': question_id,
            'mapped_to': mapped_to,
            'description': component_description,
            'confidence_score': confidence_score,
            'confidence_level': 'high' if confidence_score >= 80 else 'medium' if confidence_score >= 60 else 'low',
            'notes': notes,
            'mapping_source': 'manual',
            'created_at': datetime.now().isoformat()
        }
        
        # Add to mappings
        if 'mappings' not in session_data:
            session_data['mappings'] = []
        session_data['mappings'].append(new_mapping)
        
        # Update statistics
        session_data['statistics']['total_mappings'] = len(session_data['mappings'])
        session_data['statistics']['mapped_questions'] = len(set(m['question_id'] for m in session_data['mappings']))
        session_data['statistics']['unmapped_questions'] = session_data['statistics']['total_questions'] - session_data['statistics']['mapped_questions']
        
        # Save updated session
        with open(session_file, 'w') as f:
            json.dump(session_data, f, indent=2)
        
        return jsonify({
            'success': True,
            'mapping': new_mapping,
            'statistics': session_data['statistics']
        })
        
    except Exception as e:
        logger.error(f"❌ Error adding mapping: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/mapping/<session_id>/edit', methods=['POST'])
def edit_mapping(session_id):
    """Edit an existing mapping"""
    try:
        data = request.json
        mapping_id = data.get('mapping_id')
        mapped_to = data.get('mapped_to')
        confidence_score = data.get('confidence_score', 80)
        notes = data.get('notes', '')
        
        # Load session data
        session_file = f"storage/mappings/{session_id}.json"
        with open(session_file, 'r') as f:
            session_data = json.load(f)
        
        # Find and update the mapping
        for mapping in session_data.get('mappings', []):
            if mapping.get('id') == mapping_id:
                mapping['mapped_to'] = mapped_to
                mapping['confidence_score'] = confidence_score
                mapping['confidence_level'] = 'high' if confidence_score >= 80 else 'medium' if confidence_score >= 60 else 'low'
                mapping['notes'] = notes
                mapping['updated_at'] = datetime.now().isoformat()
                
                # Update description
                uoc_data = session_data.get('uoc_data', {})
                component_description = ""
                
                if mapped_to.startswith('E'):
                    element_id = mapped_to[1:]
                    for element in uoc_data.get('elements', []):
                        if element.get('id') == element_id:
                            component_description = element.get('description', '')
                            break
                elif mapped_to.startswith('PC'):
                    pc_code = mapped_to[2:]
                    for pc in uoc_data.get('performance_criteria', []):
                        if pc.get('code') == pc_code:
                            component_description = pc.get('description', '')
                            break
                elif mapped_to.startswith('PE'):
                    pe_code = mapped_to[2:]
                    for pe in uoc_data.get('performance_evidence', []):
                        if pe.get('code') == pe_code:
                            component_description = pe.get('description', '')
                            break
                elif mapped_to.startswith('KE'):
                    ke_code = mapped_to[2:]
                    for ke in uoc_data.get('knowledge_evidence', []):
                        if ke.get('code') == ke_code:
                            component_description = ke.get('description', '')
                            break
                
                mapping['description'] = component_description
                break
        
        # Save updated session
        with open(session_file, 'w') as f:
            json.dump(session_data, f, indent=2)
        
        return jsonify({
            'success': True,
            'mapping': mapping
        })
        
    except Exception as e:
        logger.error(f"❌ Error editing mapping: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/mapping/<session_id>/remove', methods=['POST'])
def remove_mapping(session_id):
    """Remove a mapping"""
    try:
        data = request.json
        mapping_id = data.get('mapping_id')
        
        # Load session data
        session_file = f"storage/mappings/{session_id}.json"
        with open(session_file, 'r') as f:
            session_data = json.load(f)
        
        # Remove the mapping
        session_data['mappings'] = [m for m in session_data.get('mappings', []) if m.get('id') != mapping_id]
        
        # Update statistics
        session_data['statistics']['total_mappings'] = len(session_data['mappings'])
        session_data['statistics']['mapped_questions'] = len(set(m['question_id'] for m in session_data['mappings']))
        session_data['statistics']['unmapped_questions'] = session_data['statistics']['total_questions'] - session_data['statistics']['mapped_questions']
        
        # Save updated session
        with open(session_file, 'w') as f:
            json.dump(session_data, f, indent=2)
        
        return jsonify({
            'success': True,
            'statistics': session_data['statistics']
        })
        
    except Exception as e:
        logger.error(f"❌ Error removing mapping: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/mapping/<session_id>/component/<component_code>', methods=['GET'])
def get_component_description(session_id, component_code):
    """Get the full description of a UoC component"""
    try:
        # Load session data
        session_file = f"storage/mappings/{session_id}.json"
        with open(session_file, 'r') as f:
            session_data = json.load(f)
        
        uoc_data = session_data.get('uoc_data', {})
        component_description = ""
        
        if component_code.startswith('E'):
            element_id = component_code[1:]
            for element in uoc_data.get('elements', []):
                if element.get('id') == element_id:
                    component_description = element.get('description', '')
                    break
        elif component_code.startswith('PC'):
            pc_code = component_code[2:]
            for pc in uoc_data.get('performance_criteria', []):
                if pc.get('code') == pc_code:
                    component_description = pc.get('description', '')
                    break
        elif component_code.startswith('PE'):
            pe_code = component_code[2:]
            for pe in uoc_data.get('performance_evidence', []):
                if pe.get('code') == pe_code:
                    component_description = pe.get('description', '')
                    break
        elif component_code.startswith('KE'):
            ke_code = component_code[2:]
            for ke in uoc_data.get('knowledge_evidence', []):
                if ke.get('code') == ke_code:
                    component_description = ke.get('description', '')
                    break
        
        return jsonify({
            'success': True,
            'component_code': component_code,
            'description': component_description
        })
        
    except Exception as e:
        logger.error(f"❌ Error getting component description: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    import sys
    
    # Parse command line arguments
    port = 5001
    if len(sys.argv) > 1:
        for i, arg in enumerate(sys.argv):
            if arg == '--port' and i + 1 < len(sys.argv):
                try:
                    port = int(sys.argv[i + 1])
                except ValueError:
                    logger.error("Invalid port number")
                    sys.exit(1)
    
    # Create directories if they don't exist
    os.makedirs('storage/assessments', exist_ok=True)
    os.makedirs('storage/mappings', exist_ok=True)
    os.makedirs('storage/sessions', exist_ok=True)
    logger.info("🚀 Starting Assessment Validator (Computer-assisted) with improved integration...")
    logger.info(f"📊 Visit http://localhost:{port} to start")
    logger.info(f"🧪 Visit http://localhost:{port}/test to test agents")
    logger.info(f"🔍 Visit http://localhost:{port}/validation/<session_id> for validation")
    
    app.run(debug=True, host='0.0.0.0', port=port) 