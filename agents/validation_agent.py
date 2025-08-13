#!/usr/bin/env python3
"""
Collaborative Validation Agent with Discussion Thread Support
Handles validation workflow with editable rationales and peer feedback
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger(__name__)

class CollaborativeValidationAgent:
    """Enhanced validation agent supporting collaborative validation workflows"""
    
    def __init__(self):
        self.name = "CollaborativeValidationAgent"
        self.validation_statuses = ['pending_review', 'in_validation', 'validated', 'peer_review', 'completed', 'audit_ready']
        self.validator_roles = ['assessor', 'validator', 'compliance_officer', 'peer_reviewer', 'sme', 'educational_expert']
        self.discussion_types = ['validation', 'suggestion', 'comment', 'approval', 'concern']
    
    def execute(self, session_data: Dict) -> Dict:
        """
        Main validation workflow - initialize collaborative validation
        
        Args:
            session_data: Complete session data with mappings
            
        Returns:
            Dict with validation summary and thread initialization
        """
        logger.info(f"🔍 CollaborativeValidationAgent: Processing session {session_data.get('session_id', 'unknown')}")
        
        # Initialize validation threads for each mapping if not already done
        if 'validation_threads' not in session_data:
            session_data['validation_threads'] = {}
            
            mappings = session_data.get('mappings', [])
            if isinstance(mappings, dict) and 'mappings' in mappings:
                # Handle case where mappings is wrapped in another dict
                actual_mappings = mappings['mappings']
            else:
                actual_mappings = mappings
            
            for mapping in actual_mappings:
                question_id = mapping.get('question_id')
                if question_id:
                    thread = self.initiate_validation_thread(
                        mapping, 
                        'system', 
                        'system'
                    )
                    session_data['validation_threads'][str(question_id)] = thread
        
        # Generate validation summary
        validation_summary = self._generate_collaborative_summary(session_data)
        
        return validation_summary
    
    def initiate_validation_thread(self, mapping: Dict, validator_id: str, validator_role: str) -> Dict:
        """
        Start validation process for a single mapping
        """
        
        validation_thread = {
            'thread_id': f"{mapping.get('question_id')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'question_id': mapping.get('question_id'),
            'question_text': mapping.get('question_text', ''),
            'assessment_type': mapping.get('assessment_type', 'KBA'),
            
            # Original system mapping
            'system_mapping': {
                'mapped_elements': mapping.get('mapping_analysis', {}).get('mapped_elements', []),
                'mapped_performance_criteria': mapping.get('mapping_analysis', {}).get('mapped_performance_criteria', []),
                'mapped_performance_evidence': mapping.get('mapping_analysis', {}).get('mapped_performance_evidence', []),
                'mapped_knowledge_evidence': mapping.get('mapping_analysis', {}).get('mapped_knowledge_evidence', []),
                'confidence_scores': self._extract_confidence_scores(mapping),
                'system_rationales': self._extract_system_rationales(mapping)
            },
            
            # Current validated mapping (starts as copy of system mapping)
            'validated_mapping': {
                'mapped_elements': mapping.get('mapping_analysis', {}).get('mapped_elements', []),
                'mapped_performance_criteria': mapping.get('mapping_analysis', {}).get('mapped_performance_criteria', []),
                'mapped_performance_evidence': mapping.get('mapping_analysis', {}).get('mapped_performance_evidence', []),
                'mapped_knowledge_evidence': mapping.get('mapping_analysis', {}).get('mapped_knowledge_evidence', []),
                'validator_rationales': {},  # Will be populated by validators
                'validation_status': 'pending_review'
            },
            
            # Discussion thread
            'validation_discussion': [],
            
            # Validation metadata
            'validation_metadata': {
                'initiated_by': validator_id,
                'initiated_at': datetime.now().isoformat(),
                'last_updated': datetime.now().isoformat(),
                'validation_status': 'pending_review',
                'validators_involved': [validator_id],
                'validation_round': 1
            }
        }
        
        return validation_thread
    
    def submit_validation(self, thread_id: str, validator_data: Dict) -> Dict:
        """
        Submit validation with edited rationales and mapping updates
        """
        
        validation_entry = {
            'entry_id': f"{thread_id}_{len(validator_data.get('existing_discussion', []))}",
            'validator_id': validator_data.get('validator_id'),
            'validator_role': validator_data.get('validator_role'),
            'validation_type': 'validation',
            'timestamp': datetime.now().isoformat(),
            
            # Mapping updates
            'mapping_updates': {
                'elements_updated': validator_data.get('elements_updates', []),
                'criteria_updated': validator_data.get('criteria_updates', []),
                'evidence_updated': validator_data.get('evidence_updates', []),
                'knowledge_updated': validator_data.get('knowledge_updates', [])
            },
            
            # Updated rationales - key feature for human expertise
            'validator_rationales': {
                'pc_rationales': validator_data.get('pc_rationales', {}),
                'ke_rationales': validator_data.get('ke_rationales', {}),
                'pe_rationales': validator_data.get('pe_rationales', {}),
                'element_rationales': validator_data.get('element_rationales', {})
            },
            
            # Validation decisions
            'validation_decisions': {
                'overall_status': validator_data.get('overall_status', 'validated'),
                'confidence_adjustments': validator_data.get('confidence_adjustments', {}),
                'asqa_compliance_assessment': validator_data.get('asqa_compliance', {}),
                'recommendations': validator_data.get('recommendations', [])
            },
            
            # Comments
            'validation_comments': validator_data.get('comments', ''),
            'specific_concerns': validator_data.get('concerns', []),
            'improvement_suggestions': validator_data.get('suggestions', [])
        }
        
        return validation_entry
    
    def add_peer_feedback(self, thread_id: str, peer_data: Dict) -> Dict:
        """
        Add peer feedback to existing validation
        """
        
        peer_entry = {
            'entry_id': f"{thread_id}_peer_{datetime.now().strftime('%H%M%S')}",
            'reviewer_id': peer_data.get('reviewer_id'),
            'reviewer_role': peer_data.get('reviewer_role', 'peer_reviewer'),
            'validation_type': peer_data.get('feedback_type', 'comment'),
            'timestamp': datetime.now().isoformat(),
            
            # Feedback content
            'feedback_content': {
                'original_validator': peer_data.get('responding_to_validator'),
                'feedback_text': peer_data.get('feedback_text', ''),
                'feedback_category': peer_data.get('category', 'general'),
                'agreement_level': peer_data.get('agreement', 'neutral'),
            },
            
            # Specific feedback on rationales
            'rationale_feedback': {
                'pc_feedback': peer_data.get('pc_feedback', {}),
                'ke_feedback': peer_data.get('ke_feedback', {}),
                'suggestions': peer_data.get('rationale_suggestions', [])
            },
            
            # Alternative suggestions
            'alternative_mappings': peer_data.get('alternative_mappings', {}),
            'alternative_rationales': peer_data.get('alternative_rationales', {}),
            
            # References
            'references_to_discussion': peer_data.get('discussion_references', []),
            'tagged_validators': peer_data.get('tagged_validators', [])
        }
        
        return peer_entry
    
    def update_thread_status(self, thread_data: Dict, new_status: str, updated_by: str) -> Dict:
        """Update validation thread status and metadata"""
        
        thread_data['validation_metadata'].update({
            'validation_status': new_status,
            'last_updated': datetime.now().isoformat(),
            'last_updated_by': updated_by
        })
        
        # Add validator to involved list if not already there
        if updated_by not in thread_data['validation_metadata']['validators_involved']:
            thread_data['validation_metadata']['validators_involved'].append(updated_by)
        
        # Status-specific updates
        if new_status == 'peer_review':
            thread_data['validation_metadata']['peer_review_started'] = datetime.now().isoformat()
        elif new_status == 'completed':
            thread_data['validation_metadata']['completed_at'] = datetime.now().isoformat()
            thread_data['validation_metadata']['final_validator'] = updated_by
        elif new_status == 'audit_ready':
            thread_data['validation_metadata']['audit_ready_at'] = datetime.now().isoformat()
        
        return thread_data
    
    def _generate_collaborative_summary(self, session_data: Dict) -> Dict:
        """Generate summary for collaborative validation session"""
        
        threads = session_data.get('validation_threads', {})
        
        summary = {
            'total_mappings': len(threads),
            'pending_review': 0,
            'in_validation': 0,
            'validated': 0,
            'peer_review': 0,
            'completed': 0,
            'audit_ready': 0,
            'validation_score': 0.0,
            'collaborative_metrics': {
                'total_validators': set(),
                'total_discussions': 0,
                'consensus_level': 'unknown'
            }
        }
        
        for thread in threads.values():
            status = thread.get('validation_metadata', {}).get('validation_status', 'pending_review')
            if status in summary:
                summary[status] += 1
            
            # Track validators
            validators = thread.get('validation_metadata', {}).get('validators_involved', [])
            summary['collaborative_metrics']['total_validators'].update(validators)
            
            # Count discussions
            discussions = len(thread.get('validation_discussion', []))
            summary['collaborative_metrics']['total_discussions'] += discussions
        
        # Convert set to count
        summary['collaborative_metrics']['total_validators'] = len(summary['collaborative_metrics']['total_validators'])
        
        # Calculate validation score
        total = summary['total_mappings']
        if total > 0:
            completed = summary['completed'] + summary['audit_ready']
            summary['validation_score'] = (completed / total) * 100
        
        return summary
    
    def _extract_confidence_scores(self, mapping: Dict) -> Dict:
        """Extract confidence scores from system mapping"""
        
        confidence_scores = {}
        
        # Performance criteria confidence
        for pc in mapping.get('mapping_analysis', {}).get('mapped_performance_criteria', []):
            pc_id = pc.get('criterion_id', pc.get('criterion_code'))
            confidence_scores[f"pc_{pc_id}"] = pc.get('confidence_score', 0)
        
        # Knowledge evidence confidence
        for ke in mapping.get('mapping_analysis', {}).get('mapped_knowledge_evidence', []):
            ke_id = ke.get('evidence_id', ke.get('evidence_code'))
            confidence_scores[f"ke_{ke_id}"] = ke.get('confidence_score', 0)
        
        return confidence_scores
    
    def _extract_system_rationales(self, mapping: Dict) -> Dict:
        """Extract system-generated rationales/justifications"""
        
        rationales = {}
        
        # Extract from performance criteria
        for pc in mapping.get('mapping_analysis', {}).get('mapped_performance_criteria', []):
            pc_id = pc.get('criterion_id', pc.get('criterion_code'))
            rationales[f"pc_{pc_id}"] = f"Mapped to {pc_id}: {pc.get('criterion_description', 'System generated mapping based on content analysis')}"
        
        # Extract from knowledge evidence
        for ke in mapping.get('mapping_analysis', {}).get('mapped_knowledge_evidence', []):
            ke_id = ke.get('evidence_id', ke.get('evidence_code'))
            rationales[f"ke_{ke_id}"] = f"Mapped to {ke_id}: {ke.get('evidence_description', 'System generated mapping based on content analysis')}"
        
        return rationales

    def generate_validation_summary(self, thread_data: Dict) -> Dict:
        """Generate summary of validation thread for reporting"""
        
        discussion = thread_data.get('validation_discussion', [])
        
        # Count different types of entries
        validations = [entry for entry in discussion if entry.get('validation_type') == 'validation']
        comments = [entry for entry in discussion if entry.get('validation_type') == 'comment']
        suggestions = [entry for entry in discussion if entry.get('validation_type') == 'suggestion']
        
        # Extract final rationales
        final_rationales = {}
        if validations:
            latest_validation = validations[-1]
            final_rationales = latest_validation.get('validator_rationales', {})
        
        # Calculate consensus level
        agreement_scores = [entry.get('feedback_content', {}).get('agreement_level', 'neutral') 
                          for entry in discussion if 'feedback_content' in entry]
        consensus_level = self._calculate_consensus(agreement_scores)
        
        summary = {
            'thread_id': thread_data.get('thread_id'),
            'question_id': thread_data.get('question_id'),
            'validation_status': thread_data.get('validation_metadata', {}).get('validation_status'),
            
            'participation_summary': {
                'total_validators': len(thread_data.get('validation_metadata', {}).get('validators_involved', [])),
                'total_entries': len(discussion),
                'validations_submitted': len(validations),
                'peer_comments': len(comments),
                'suggestions_made': len(suggestions)
            },
            
            'consensus_analysis': {
                'consensus_level': consensus_level,
                'agreement_distribution': self._analyze_agreement_distribution(agreement_scores),
                'disputed_aspects': self._identify_disputed_aspects(discussion)
            },
            
            'final_mapping_state': {
                'validated_mapping': thread_data.get('validated_mapping', {}),
                'final_rationales': final_rationales,
                'confidence_levels': self._extract_final_confidence_levels(thread_data),
                'asqa_compliance_status': self._determine_final_asqa_status(thread_data)
            },
            
            'quality_indicators': {
                'rationale_quality': self._assess_rationale_quality(final_rationales),
                'mapping_completeness': self._assess_mapping_completeness(thread_data),
                'validation_thoroughness': self._assess_validation_thoroughness(discussion)
            }
        }
        
        return summary
    
    def _calculate_consensus(self, agreement_scores: List[str]) -> str:
        """Calculate consensus level from agreement scores"""
        
        if not agreement_scores:
            return 'no_feedback'
        
        agree_count = agreement_scores.count('agree')
        total_count = len(agreement_scores)
        
        if agree_count / total_count >= 0.8:
            return 'strong_consensus'
        elif agree_count / total_count >= 0.6:
            return 'moderate_consensus'
        elif agree_count / total_count >= 0.4:
            return 'weak_consensus'
        else:
            return 'no_consensus'
    
    def _analyze_agreement_distribution(self, agreement_scores: List[str]) -> Dict:
        """Analyze distribution of agreement levels"""
        
        distribution = {
            'agree': agreement_scores.count('agree'),
            'disagree': agreement_scores.count('disagree'),
            'partial': agreement_scores.count('partial'),
            'neutral': agreement_scores.count('neutral')
        }
        
        return distribution
    
    def _identify_disputed_aspects(self, discussion: List[Dict]) -> List[str]:
        """Identify which aspects of the mapping are disputed"""
        
        disputed = []
        
        for entry in discussion:
            if entry.get('feedback_content', {}).get('agreement_level') == 'disagree':
                category = entry.get('feedback_content', {}).get('feedback_category', 'general')
                if category not in disputed:
                    disputed.append(category)
        
        return disputed
    
    def _extract_final_confidence_levels(self, thread_data: Dict) -> Dict:
        """Extract final confidence levels from validated mapping"""
        
        confidence_levels = {}
        
        # Get latest validation entry
        validations = [entry for entry in thread_data.get('validation_discussion', []) 
                      if entry.get('validation_type') == 'validation']
        
        if validations:
            latest = validations[-1]
            confidence_levels = latest.get('validation_decisions', {}).get('confidence_adjustments', {})
        
        return confidence_levels
    
    def _determine_final_asqa_status(self, thread_data: Dict) -> str:
        """Determine final ASQA compliance status"""
        
        validations = [entry for entry in thread_data.get('validation_discussion', []) 
                      if entry.get('validation_type') == 'validation']
        
        if validations:
            latest = validations[-1]
            asqa_assessment = latest.get('validation_decisions', {}).get('asqa_compliance_assessment', {})
            return asqa_assessment.get('overall_compliance', 'pending_review')
        
        return 'pending_review'
    
    def _assess_rationale_quality(self, rationales: Dict) -> str:
        """Assess quality of final rationales"""
        
        if not rationales:
            return 'no_rationales'
        
        # Simple quality check based on length and content
        quality_scores = []
        for rationale_dict in rationales.values():
            if isinstance(rationale_dict, dict):
                for rationale in rationale_dict.values():
                    if isinstance(rationale, str):
                        score = min(1.0, len(rationale) / 100)  # Basic length check
                        if any(word in rationale.lower() for word in ['because', 'demonstrates', 'requires', 'addresses']):
                            score += 0.2  # Bonus for explanatory language
                        quality_scores.append(score)
        
        if not quality_scores:
            return 'no_rationales'
        
        avg_quality = sum(quality_scores) / len(quality_scores)
        
        if avg_quality >= 0.8:
            return 'high_quality'
        elif avg_quality >= 0.6:
            return 'moderate_quality'
        else:
            return 'needs_improvement'
    
    def _assess_mapping_completeness(self, thread_data: Dict) -> float:
        """Assess completeness of validated mapping"""
        
        validated_mapping = thread_data.get('validated_mapping', {})
        
        component_counts = [
            len(validated_mapping.get('mapped_elements', [])),
            len(validated_mapping.get('mapped_performance_criteria', [])),
            len(validated_mapping.get('mapped_performance_evidence', [])),
            len(validated_mapping.get('mapped_knowledge_evidence', []))
        ]
        
        # Calculate completeness score (basic heuristic)
        total_mappings = sum(component_counts)
        if total_mappings >= 4:  # At least one mapping per component type
            return 1.0
        elif total_mappings >= 2:
            return 0.7
        elif total_mappings >= 1:
            return 0.4
        else:
            return 0.0
    
    def _assess_validation_thoroughness(self, discussion: List[Dict]) -> str:
        """Assess thoroughness of validation process"""
        
        if len(discussion) >= 3:
            return 'thorough'
        elif len(discussion) >= 2:
            return 'adequate'
        elif len(discussion) >= 1:
            return 'minimal'
        else:
            return 'incomplete'

    def analyze_coverage_quality(self, session_data: Dict) -> Dict:
        """
        Comprehensive coverage analysis focusing on quality over quantity
        
        Args:
            session_data: Complete session data with mappings
            
        Returns:
            Dict with detailed coverage analysis
        """
        logger.info("🔍 Analyzing coverage quality...")
        
        mappings = session_data.get('mappings', [])
        if isinstance(mappings, dict) and 'mappings' in mappings:
            actual_mappings = mappings['mappings']
        else:
            actual_mappings = mappings
        
        uoc_data = session_data.get('uoc_data', {})
        
        # Calculate real statistics
        total_questions = len(actual_mappings)
        assessment_methods = {}
        bloom_levels = {}
        element_coverage = {}
        
        # Track additional details for remediation planning
        low_confidence_qids: List[str] = []
        missing_evidence_qids: List[str] = []
        higher_order_levels = {'APPLY', 'ANALYZE', 'EVALUATE', 'CREATE'}
        non_higher_order_qids: List[str] = []

        # Analyze each mapping
        for mapping in actual_mappings:
            # Assessment method analysis
            method = mapping.get('assessment_type', 'KBA')
            assessment_methods[method] = assessment_methods.get(method, 0) + 1
            
            # Bloom's taxonomy analysis
            bloom_level = mapping.get('bloom_taxonomy', {}).get('primary_level', 'UNDERSTAND')
            bloom_levels[bloom_level] = bloom_levels.get(bloom_level, 0) + 1
            if str(bloom_level).upper() not in higher_order_levels:
                non_higher_order_qids.append(mapping.get('question_id'))
            
            # Element coverage analysis
            for element in mapping.get('mapping_analysis', {}).get('mapped_elements', []):
                element_id = element.get('element_id', 'Unknown')
                if element_id not in element_coverage:
                    element_coverage[element_id] = {
                        'count': 0,
                        'confidence_sum': 0,
                        'questions': []
                    }
                element_coverage[element_id]['count'] += 1
                element_coverage[element_id]['confidence_sum'] += element.get('confidence_score', 0)
                element_coverage[element_id]['questions'].append(mapping.get('question_id'))

            # Evidence check and confidence check
            ma = mapping.get('mapping_analysis', {})
            has_ke = bool(ma.get('mapped_knowledge_evidence'))
            has_pe = bool(ma.get('mapped_performance_evidence'))
            if not has_ke and not has_pe:
                missing_evidence_qids.append(mapping.get('question_id'))

            # Average confidence across all mapped items for this question
            scores = []
            for cat in ['mapped_elements', 'mapped_performance_criteria', 'mapped_performance_evidence', 'mapped_knowledge_evidence']:
                for item in ma.get(cat, []) or []:
                    scores.append(item.get('confidence_score', 0))
            if scores and (sum(scores) / len(scores)) < 0.6:
                low_confidence_qids.append(mapping.get('question_id'))
        
        # Calculate percentages
        method_percentages = {}
        for method, count in assessment_methods.items():
            method_percentages[method] = round((count / total_questions) * 100, 1)
        
        bloom_percentages = {}
        for level, count in bloom_levels.items():
            bloom_percentages[level] = round((count / total_questions) * 100, 1)
        
        # Generate gap analysis
        critical_gaps = []
        moderate_issues = []
        recommendations = []
        
        # Check for critical gaps
        if bloom_percentages.get('EVALUATE', 0) < 10:
            critical_gaps.append({
                'title': 'Missing Higher-Order Thinking',
                'description': f'Only {bloom_percentages.get("EVALUATE", 0)}% of questions assess evaluation skills. Need more analysis and evaluation questions.',
                'type': 'critical'
            })
        
        if method_percentages.get('PEP', 0) < 20:
            critical_gaps.append({
                'title': 'Insufficient Practical Assessment',
                'description': f'Only {method_percentages.get("PEP", 0)}% PEP questions. Need more workplace application scenarios.',
                'type': 'critical'
            })
        
        # Check for moderate issues
        for element_id, coverage in element_coverage.items():
            if coverage['count'] < 2:
                moderate_issues.append({
                    'title': f'Element {element_id} Under-Covered',
                    'description': f'Element {element_id} has only {coverage["count"]} question(s). Consider adding more questions for comprehensive coverage.',
                    'type': 'moderate'
                })
        
        # Generate recommendations
        if bloom_percentages.get('EVALUATE', 0) < 10:
            recommendations.append({
                'title': 'Add Higher-Order Thinking Questions',
                'description': 'Create 2-3 evaluation and analysis questions to improve cognitive progression.',
                'type': 'recommendation'
            })
        
        if method_percentages.get('PEP', 0) < 20:
            recommendations.append({
                'title': 'Add Scenario-Based Questions',
                'description': 'Create 3-4 workplace scenario questions to improve practical assessment coverage.',
                'type': 'recommendation'
            })
        
        # Build remediation tasks (action-oriented)
        remediation_tasks: List[Dict[str, Any]] = []

        # Task: Under-covered elements (fewer than 2 questions)
        for element_id, coverage in element_coverage.items():
            if coverage['count'] < 2:
                remediation_tasks.append({
                    'id': f'remed_element_{element_id}',
                    'standard_code': '1.8',
                    'category': 'coverage',
                    'severity': 'moderate',
                    'summary': f'Increase coverage for {element_id}',
                    'rationale': f'{element_id} has only {coverage["count"]} question(s).',
                    'impacted_elements': [element_id],
                    'impacted_questions': coverage['questions'],
                    'suggested_actions': [
                        'Draft 1–2 additional assessment items aligned to this element',
                        'Ensure at least one Performance Criterion under this element is explicitly assessed'
                    ],
                    'owner_role': 'assessor',
                    'due_days': 7,
                    'acceptance_criteria': [
                        'At least 2 questions map to the element',
                        'Minimum one PC under the element covered with >=70% mapping confidence'
                    ]
                })

        # Task: Add practical/workplace evidence (low PEP)
        if (assessment_methods.get('PEP', 0) / max(1, total_questions)) < 0.2:
            remediation_tasks.append({
                'id': 'remed_method_pep',
                'standard_code': '1.4',
                'category': 'assessment_method',
                'severity': 'moderate',
                'summary': 'Increase practical/workplace evidence (PEP)',
                'rationale': f"PEP items are {assessment_methods.get('PEP',0)} of {total_questions}; target at least 20%.",
                'impacted_elements': list(element_coverage.keys()),
                'impacted_questions': non_higher_order_qids,
                'suggested_actions': [
                    'Add 2–3 workplace scenario tasks with observable performance evidence',
                    'Collect third-party reports or logs demonstrating competency in context'
                ],
                'owner_role': 'assessor',
                'due_days': 10,
                'acceptance_criteria': ['PEP items reach >=20% of total questions']
            })

        # Task: Add higher-order thinking questions
        if (sum(bloom_levels.get(level, 0) for level in ['EVALUATE', 'ANALYZE', 'CREATE']) / max(1, total_questions)) < 0.1:
            remediation_tasks.append({
                'id': 'remed_bloom_higher',
                'standard_code': '1.4',
                'category': 'cognitive_progression',
                'severity': 'moderate',
                'summary': 'Add higher-order questions (ANALYZE/EVALUATE/CREATE)',
                'rationale': 'Higher-order questions below 10% threshold.',
                'impacted_elements': list(element_coverage.keys()),
                'impacted_questions': non_higher_order_qids,
                'suggested_actions': [
                    'Add 2–3 evaluation-level prompts requiring rationale and justification',
                    'Convert 1–2 recall items into scenario-based analysis tasks'
                ],
                'owner_role': 'assessor',
                'due_days': 7,
                'acceptance_criteria': ['>=10% items at ANALYZE/EVALUATE/CREATE levels']
            })

        # Task: Missing evidence alignment
        if missing_evidence_qids:
            remediation_tasks.append({
                'id': 'remed_evidence_alignment',
                'standard_code': '1.5',
                'category': 'evidence',
                'severity': 'high',
                'summary': 'Add Knowledge/Performance Evidence alignment',
                'rationale': 'Some questions lack explicit KE/PE mapping.',
                'impacted_elements': list(element_coverage.keys()),
                'impacted_questions': missing_evidence_qids,
                'suggested_actions': [
                    'Amend items to reference specific KE/PE requirements',
                    'Attach marking guidance explaining how evidence is judged sufficient/authentic/current'
                ],
                'owner_role': 'assessor',
                'due_days': 5,
                'acceptance_criteria': ['All items have KE or PE linkage documented']
            })

        # Task: Low-confidence mappings
        if low_confidence_qids:
            remediation_tasks.append({
                'id': 'remed_low_confidence',
                'standard_code': '1.6',
                'category': 'judgement_quality',
                'severity': 'medium',
                'summary': 'Refine low-confidence mappings',
                'rationale': 'Average mapping confidence <60% for listed items.',
                'impacted_elements': list(element_coverage.keys()),
                'impacted_questions': low_confidence_qids,
                'suggested_actions': [
                    'Clarify wording of the question to target the intended element/PC',
                    'Add assessor notes with explicit evidence indicators'
                ],
                'owner_role': 'validator',
                'due_days': 5,
                'acceptance_criteria': ['Re-mapped items reach >=70% confidence']
            })

        coverage_analysis = {
            'summary_metrics': {
                'total_questions': total_questions,
                'mapped_questions': len([m for m in actual_mappings if m.get('mapping_analysis')]),
                'validation_threads': len(session_data.get('validation_threads', {}))
            },
            'assessment_method_analysis': {
                'distribution': assessment_methods,
                'percentages': method_percentages
            },
            'competency_progression_analysis': {
                'bloom_distribution': bloom_levels,
                'bloom_percentages': bloom_percentages
            },
            'element_coverage_quality': {
                'element_analysis': element_coverage,
                'coverage_summary': {
                    'total_elements': len(element_coverage),
                    'well_covered': len([e for e in element_coverage.values() if e['count'] >= 3]),
                    'under_covered': len([e for e in element_coverage.values() if e['count'] < 2])
                }
            },
            'gap_analysis': {
                'critical_gaps': critical_gaps,
                'moderate_issues': moderate_issues,
                'recommendations': recommendations
            },
            'remediation_tasks': remediation_tasks
        }
        
        return coverage_analysis

    def _analyze_element_coverage_quality(self, mappings: List[Dict], uoc_data: Dict) -> Dict:
        """Analyze coverage quality by element and assessment method"""
        
        coverage_quality = {
            'element_analysis': {},
            'assessment_method_gaps': [],
            'competency_progression_gaps': [],
            'critical_coverage_issues': []
        }
        
        # Group mappings by element
        element_mappings = {}
        for mapping in mappings:
            for element in mapping.get('mapping_analysis', {}).get('mapped_elements', []):
                element_id = element.get('element_id')
                if element_id not in element_mappings:
                    element_mappings[element_id] = []
                element_mappings[element_id].append(mapping)
        
        # Analyze each element
        for element_id, element_questions in element_mappings.items():
            question_types = [q.get('assessment_type', 'unknown') for q in element_questions]
            
            # Assessment method analysis
            mcq_heavy = question_types.count('KBA') > len(question_types) * 0.7
            lacks_practical = 'SBA' not in question_types and 'PEP' not in question_types
            
            # Bloom's taxonomy analysis
            bloom_levels = [q.get('bloom_taxonomy', {}).get('primary_level', 'REMEMBER') for q in element_questions]
            lacks_application = not any(level in ['APPLY', 'ANALYZE', 'EVALUATE', 'CREATE'] for level in bloom_levels)
            
            # Evidence type analysis
            has_knowledge = any(q.get('mapping_analysis', {}).get('mapped_knowledge_evidence') for q in element_questions)
            has_performance = any(q.get('mapping_analysis', {}).get('mapped_performance_evidence') for q in element_questions)
            
            coverage_quality['element_analysis'][element_id] = {
                'question_count': len(element_questions),
                'assessment_method_diversity': len(set(question_types)),
                'mcq_heavy': mcq_heavy,
                'lacks_practical_assessment': lacks_practical,
                'lacks_higher_order_thinking': lacks_application,
                'has_knowledge_evidence': has_knowledge,
                'has_performance_evidence': has_performance,
                'coverage_quality_score': self._calculate_element_coverage_score(element_questions)
            }
            
            # Flag critical issues
            if mcq_heavy and lacks_practical:
                coverage_quality['critical_coverage_issues'].append(
                    f"Element {element_id}: Over-reliance on MCQ, needs practical assessment"
                )
            
            if lacks_application:
                coverage_quality['assessment_method_gaps'].append(
                    f"Element {element_id}: Missing higher-order thinking assessment"
                )
        
        return coverage_quality

    def _calculate_element_coverage_score(self, element_questions: List[Dict]) -> float:
        """Calculate coverage quality score for an element (0-1)"""
        
        score = 0.0
        
        # Assessment method diversity (0.4 weight)
        question_types = [q.get('assessment_type', 'unknown') for q in element_questions]
        unique_types = len(set(question_types))
        method_score = min(1.0, unique_types / 3)  # Max score at 3+ different types
        score += method_score * 0.4
        
        # Bloom's taxonomy coverage (0.3 weight)
        bloom_levels = [q.get('bloom_taxonomy', {}).get('primary_level', 'REMEMBER') for q in element_questions]
        unique_bloom = len(set(bloom_levels))
        bloom_score = min(1.0, unique_bloom / 4)  # Max score at 4+ levels
        score += bloom_score * 0.3
        
        # Evidence type coverage (0.3 weight)
        has_knowledge = any(q.get('mapping_analysis', {}).get('mapped_knowledge_evidence') for q in element_questions)
        has_performance = any(q.get('mapping_analysis', {}).get('mapped_performance_evidence') for q in element_questions)
        evidence_score = (int(has_knowledge) + int(has_performance)) / 2
        score += evidence_score * 0.3
        
        return round(score, 2)

    def _analyze_assessment_methods(self, mappings: List[Dict]) -> Dict:
        """Analyze assessment method distribution and gaps"""
        
        method_analysis = {
            'method_distribution': {},
            'method_gaps': [],
            'quality_indicators': []
        }
        
        # Count assessment methods
        for mapping in mappings:
            method = mapping.get('assessment_type', 'unknown')
            method_analysis['method_distribution'][method] = method_analysis['method_distribution'].get(method, 0) + 1
        
        # Analyze gaps
        total_questions = len(mappings)
        kba_count = method_analysis['method_distribution'].get('KBA', 0)
        sba_count = method_analysis['method_distribution'].get('SBA', 0)
        pep_count = method_analysis['method_distribution'].get('PEP', 0)
        
        if kba_count > total_questions * 0.7:
            method_analysis['method_gaps'].append("Over-reliance on knowledge-based assessment")
            method_analysis['quality_indicators'].append("Needs more skills-based and practical assessment")
        
        if sba_count == 0:
            method_analysis['method_gaps'].append("No skills-based assessment questions")
            method_analysis['quality_indicators'].append("Add skills demonstration questions")
        
        if pep_count == 0:
            method_analysis['method_gaps'].append("No practical evidence questions")
            method_analysis['quality_indicators'].append("Add workplace application questions")
        
        return method_analysis

    def _analyze_competency_progression(self, mappings: List[Dict]) -> Dict:
        """Analyze competency progression from knowledge to application"""
        
        progression_analysis = {
            'bloom_distribution': {},
            'progression_gaps': [],
            'skill_level_analysis': {}
        }
        
        # Analyze Bloom's taxonomy distribution
        for mapping in mappings:
            bloom_level = mapping.get('bloom_taxonomy', {}).get('primary_level', 'REMEMBER')
            progression_analysis['bloom_distribution'][bloom_level] = progression_analysis['bloom_distribution'].get(bloom_level, 0) + 1
        
        # Identify progression gaps
        total_questions = len(mappings)
        remember_count = progression_analysis['bloom_distribution'].get('REMEMBER', 0)
        understand_count = progression_analysis['bloom_distribution'].get('UNDERSTAND', 0)
        apply_count = progression_analysis['bloom_distribution'].get('APPLY', 0)
        analyze_count = progression_analysis['bloom_distribution'].get('ANALYZE', 0)
        
        if remember_count + understand_count > total_questions * 0.8:
            progression_analysis['progression_gaps'].append("Too many lower-order thinking questions")
            progression_analysis['progression_gaps'].append("Need more application and analysis questions")
        
        if apply_count + analyze_count < total_questions * 0.3:
            progression_analysis['progression_gaps'].append("Insufficient higher-order thinking assessment")
        
        # Skill level analysis
        progression_analysis['skill_level_analysis'] = {
            'foundation_knowledge': remember_count + understand_count,
            'applied_skills': apply_count + analyze_count,
            'workplace_integration': total_questions - (remember_count + understand_count + apply_count + analyze_count)
        }
        
        return progression_analysis

    def _generate_coverage_recommendations(self, coverage_analysis: Dict) -> List[str]:
        """Generate actionable recommendations based on coverage analysis"""
        
        recommendations = []
        
        # Element-specific recommendations
        for element_id, analysis in coverage_analysis['element_coverage_quality']['element_analysis'].items():
            if analysis['mcq_heavy']:
                recommendations.append(f"Element {element_id}: Add practical assessment questions")
            
            if analysis['lacks_practical_assessment']:
                recommendations.append(f"Element {element_id}: Include skills demonstration")
            
            if analysis['lacks_higher_order_thinking']:
                recommendations.append(f"Element {element_id}: Add application/analysis questions")
        
        # Assessment method recommendations
        for gap in coverage_analysis['element_coverage_quality']['assessment_method_gaps']:
            recommendations.append(gap)
        
        # Critical issues
        for issue in coverage_analysis['element_coverage_quality']['critical_coverage_issues']:
            recommendations.append(f"CRITICAL: {issue}")
        
        return recommendations

    def export_validation_data(self, session_data: Dict, format: str = 'json') -> str:
        """Export validation data in specified format"""
        
        if format == 'json':
            return json.dumps(session_data, indent=2)
        
        elif format == 'csv':
            # Generate CSV format for validation threads
            csv_lines = ['question_id,validation_status,validators_count,discussion_entries,consensus_level']
            
            for thread_id, thread_data in session_data.get('validation_threads', {}).items():
                metadata = thread_data.get('validation_metadata', {})
                discussion = thread_data.get('validation_discussion', [])
                
                # Calculate consensus
                agreement_scores = [entry.get('feedback_content', {}).get('agreement_level', 'neutral') 
                                  for entry in discussion if 'feedback_content' in entry]
                consensus = self._calculate_consensus(agreement_scores)
                
                csv_lines.append(f"{thread_data.get('question_id', '')},"
                               f"{metadata.get('validation_status', 'pending_review')},"
                               f"{len(metadata.get('validators_involved', []))},"
                               f"{len(discussion)},"
                               f"{consensus}")
            
            return '\n'.join(csv_lines)
        
        else:
            raise ValueError(f"Unsupported export format: {format}")

# Test function
def test_collaborative_validation_agent():
    """Test the CollaborativeValidationAgent"""
    
    print("🧪 Testing CollaborativeValidationAgent...")
    
    agent = CollaborativeValidationAgent()
    
    # Create test session data with mapping
    test_mapping = {
        'question_id': 'Q1',
        'question_text': 'Test question about infection control',
        'assessment_type': 'KBA',
        'mapping_analysis': {
            'mapped_performance_criteria': [
                {
                    'criterion_id': 'PC1.1',
                    'criterion_code': 'PC1.1',
                    'criterion_description': 'Apply infection control procedures',
                    'confidence_score': 0.85
                }
            ],
            'mapped_knowledge_evidence': [
                {
                    'evidence_id': 'KE1.1',
                    'evidence_code': 'KE1.1',
                    'evidence_description': 'Knowledge of infection control principles',
                    'confidence_score': 0.90
                }
            ],
            'mapped_elements': [],
            'mapped_performance_evidence': []
        }
    }
    
    test_session = {
        'session_id': 'TEST_COLLAB_001',
        'uoc_code': 'HLTINF006',
        'mappings': [test_mapping]
    }
    
    # Test initialization
    summary = agent.execute(test_session)
    print(f"✅ Initialization summary: {summary}")
    
    return agent

if __name__ == "__main__":
    test_collaborative_validation_agent()