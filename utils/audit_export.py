#!/usr/bin/env python3
"""
Audit Export Utilities for Assessment Validator
Generates audit-ready reports and exports
"""

import json
import csv
import os
from datetime import datetime
from typing import Dict, List, Any

def generate_audit_report(session_data: Dict) -> Dict:
    """
    Generate a comprehensive audit report for RTO validation
    
    Args:
        session_data: Complete session data with mappings and validation
        
    Returns:
        Dict containing audit report data
    """
    
    print(f"📊 Generating audit report for session {session_data.get('session_id', 'unknown')}")
    
    # Extract key information
    uoc_code = session_data.get('uoc_code', 'Unknown')
    session_id = session_data.get('session_id', 'Unknown')
    assessment_type = session_data.get('assessment_type', 'Unknown')
    created_at = session_data.get('created_at', '')
    
    # Get UoC data
    uoc_data = session_data.get('uoc_data', {})
    questions = session_data.get('questions', [])
    mappings = session_data.get('mappings', [])
    
    # Calculate statistics
    total_questions = len(questions)
    total_mappings = len(mappings)
    approved_mappings = len([m for m in mappings if m.get('validation_status') == 'approved'])
    rejected_mappings = len([m for m in mappings if m.get('validation_status') == 'rejected'])
    pending_mappings = len([m for m in mappings if m.get('validation_status') == 'pending'])
    
    # Calculate coverage
    uoc_elements = uoc_data.get('elements', [])
    covered_elements = set()
    for mapping in mappings:
        if mapping.get('validation_status') == 'approved':
            mapped_elements = mapping.get('mapped_elements', [])
            covered_elements.update(mapped_elements)
    
    coverage_percentage = (len(covered_elements) / len(uoc_elements) * 100) if uoc_elements else 0
    
    # Generate audit report
    audit_report = {
        'report_metadata': {
            'report_type': 'RTO_Validation_Audit',
            'generated_at': datetime.now().isoformat(),
            'session_id': session_id,
            'uoc_code': uoc_code,
            'assessment_type': assessment_type,
            'created_at': created_at
        },
        'summary_statistics': {
            'total_questions': total_questions,
            'total_mappings': total_mappings,
            'approved_mappings': approved_mappings,
            'rejected_mappings': rejected_mappings,
            'pending_mappings': pending_mappings,
            'approval_rate': (approved_mappings / total_mappings * 100) if total_mappings > 0 else 0,
            'coverage_percentage': coverage_percentage,
            'total_uoc_elements': len(uoc_elements),
            'covered_elements': len(covered_elements)
        },
        'uoc_information': {
            'code': uoc_code,
            'title': uoc_data.get('title', 'Unknown'),
            'elements': uoc_elements,
            'performance_criteria': uoc_data.get('performance_criteria', []),
            'performance_evidence': uoc_data.get('performance_evidence', []),
            'knowledge_evidence': uoc_data.get('knowledge_evidence', [])
        },
        'mapping_details': [],
        'validation_audit_trail': [],
        'quality_metrics': {
            'average_confidence': 0.0,
            'low_confidence_mappings': 0,
            'high_confidence_mappings': 0
        },
        'recommendations': []
    }
    
    # Process mapping details
    total_confidence = 0
    low_confidence_count = 0
    high_confidence_count = 0
    
    for mapping in mappings:
        confidence = mapping.get('confidence_score', 0)
        total_confidence += confidence
        
        if confidence < 0.7:
            low_confidence_count += 1
        elif confidence > 0.8:
            high_confidence_count += 1
        
        mapping_detail = {
            'question_id': mapping.get('question_id', ''),
            'question_text': mapping.get('question_text', ''),
            'mapped_elements': mapping.get('mapped_elements', []),
            'confidence_score': confidence,
            'validation_status': mapping.get('validation_status', 'pending'),
            'audit_trail': mapping.get('audit_trail', [])
        }
        
        audit_report['mapping_details'].append(mapping_detail)
        
        # Collect validation audit trail
        for audit_entry in mapping.get('audit_trail', []):
            audit_report['validation_audit_trail'].append({
                'question_id': mapping.get('question_id'),
                'timestamp': audit_entry.get('timestamp'),
                'action': audit_entry.get('action'),
                'validator_role': audit_entry.get('validator_role'),
                'comments': audit_entry.get('comments')
            })
    
    # Calculate quality metrics
    if total_mappings > 0:
        audit_report['quality_metrics']['average_confidence'] = total_confidence / total_mappings
        audit_report['quality_metrics']['low_confidence_mappings'] = low_confidence_count
        audit_report['quality_metrics']['high_confidence_mappings'] = high_confidence_count
    
    # Generate recommendations
    if coverage_percentage < 80:
        audit_report['recommendations'].append({
            'type': 'coverage',
            'priority': 'high',
            'message': f'UoC coverage is only {coverage_percentage:.1f}%. Consider adding more questions to cover all elements.',
            'action': 'Review assessment design to ensure all UoC elements are covered'
        })
    
    if low_confidence_count > total_mappings * 0.3:
        audit_report['recommendations'].append({
            'type': 'quality',
            'priority': 'medium',
            'message': f'{low_confidence_count} mappings have low confidence scores. Consider manual review.',
            'action': 'Review low-confidence mappings for accuracy'
        })
    
    if pending_mappings > 0:
        audit_report['recommendations'].append({
            'type': 'validation',
            'priority': 'medium',
            'message': f'{pending_mappings} mappings are pending validation.',
            'action': 'Complete validation of pending mappings'
        })
    
    return audit_report

def export_audit_report_csv(session_data: Dict, output_path: str = None) -> str:
    """
    Export audit report as CSV
    
    Args:
        session_data: Complete session data
        output_path: Optional output file path
        
    Returns:
        Path to generated CSV file
    """
    
    audit_report = generate_audit_report(session_data)
    
    if not output_path:
        session_id = session_data.get('session_id', 'unknown')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_path = f"storage/exports/audit_report_{session_id}_{timestamp}.csv"
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        
        # Write header
        writer.writerow([
            'Question ID', 'Question Text', 'Mapped Elements', 
            'Confidence Score', 'Validation Status', 'Validator Role',
            'Validation Comments', 'Validation Date'
        ])
        
        # Write mapping data
        for mapping in audit_report['mapping_details']:
            # Get latest validation info
            latest_validation = None
            if mapping['audit_trail']:
                latest_validation = mapping['audit_trail'][-1]
            
            writer.writerow([
                mapping['question_id'],
                mapping['question_text'][:100] + '...' if len(mapping['question_text']) > 100 else mapping['question_text'],
                '; '.join(mapping['mapped_elements']),
                f"{mapping['confidence_score']:.3f}",
                mapping['validation_status'],
                latest_validation.get('validator_role', '') if latest_validation else '',
                latest_validation.get('comments', '') if latest_validation else '',
                latest_validation.get('timestamp', '') if latest_validation else ''
            ])
    
    print(f"📄 CSV export saved to: {output_path}")
    return output_path

def export_audit_report_json(session_data: Dict, output_path: str = None) -> str:
    """
    Export audit report as JSON
    
    Args:
        session_data: Complete session data
        output_path: Optional output file path
        
    Returns:
        Path to generated JSON file
    """
    
    audit_report = generate_audit_report(session_data)
    
    if not output_path:
        session_id = session_data.get('session_id', 'unknown')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_path = f"storage/exports/audit_report_{session_id}_{timestamp}.json"
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as jsonfile:
        json.dump(audit_report, jsonfile, indent=2, ensure_ascii=False)
    
    print(f"📄 JSON export saved to: {output_path}")
    return output_path

def generate_validation_summary(session_data: Dict) -> Dict:
    """
    Generate a concise validation summary
    
    Args:
        session_data: Complete session data
        
    Returns:
        Dict with validation summary
    """
    
    mappings = session_data.get('mappings', [])
    
    summary = {
        'total_mappings': len(mappings),
        'status_breakdown': {
            'approved': len([m for m in mappings if m.get('validation_status') == 'approved']),
            'rejected': len([m for m in mappings if m.get('validation_status') == 'rejected']),
            'pending': len([m for m in mappings if m.get('validation_status') == 'pending']),
            'needs_revision': len([m for m in mappings if m.get('validation_status') == 'needs_revision'])
        },
        'confidence_breakdown': {
            'high': len([m for m in mappings if m.get('confidence_score', 0) > 0.8]),
            'medium': len([m for m in mappings if 0.7 <= m.get('confidence_score', 0) <= 0.8]),
            'low': len([m for m in mappings if m.get('confidence_score', 0) < 0.7])
        },
        'coverage': {
            'total_elements': len(session_data.get('uoc_data', {}).get('elements', [])),
            'covered_elements': len(set().union(*[set(m.get('mapped_elements', [])) for m in mappings if m.get('validation_status') == 'approved']))
        }
    }
    
    # Calculate percentages
    total = summary['total_mappings']
    if total > 0:
        summary['approval_rate'] = (summary['status_breakdown']['approved'] / total) * 100
        summary['average_confidence'] = sum(m.get('confidence_score', 0) for m in mappings) / total
    
    if summary['coverage']['total_elements'] > 0:
        summary['coverage']['percentage'] = (summary['coverage']['covered_elements'] / summary['coverage']['total_elements']) * 100
    
    return summary

# Test function
def test_audit_export():
    """Test the audit export functionality"""
    
    print("🧪 Testing audit export...")
    
    # Create test session data
    test_session = {
        'session_id': 'TEST_AUDIT_001',
        'uoc_code': 'HLTINF006',
        'assessment_type': 'KBA',
        'created_at': datetime.now().isoformat(),
        'uoc_data': {
            'title': 'Test Unit of Competency',
            'elements': [
                {'id': '1', 'description': 'Element 1'},
                {'id': '2', 'description': 'Element 2'}
            ],
            'performance_criteria': [
                {'code': '1.1', 'description': 'PC 1.1'},
                {'code': '1.2', 'description': 'PC 1.2'}
            ]
        },
        'questions': [
            {'id': 'Q1', 'text': 'Test question 1'},
            {'id': 'Q2', 'text': 'Test question 2'}
        ],
        'mappings': [
            {
                'question_id': 'Q1',
                'question_text': 'Test question 1',
                'mapped_elements': ['1.1'],
                'confidence_score': 0.85,
                'validation_status': 'approved',
                'audit_trail': [
                    {
                        'timestamp': datetime.now().isoformat(),
                        'action': 'accept',
                        'validator_role': 'assessor',
                        'comments': 'Good mapping'
                    }
                ]
            },
            {
                'question_id': 'Q2',
                'question_text': 'Test question 2',
                'mapped_elements': ['1.2'],
                'confidence_score': 0.75,
                'validation_status': 'pending'
            }
        ]
    }
    
    # Test audit report generation
    report = generate_audit_report(test_session)
    print(f"✅ Audit report generated with {len(report['mapping_details'])} mappings")
    
    # Test summary generation
    summary = generate_validation_summary(test_session)
    print(f"✅ Validation summary: {summary['approval_rate']:.1f}% approval rate")
    
    return report

if __name__ == "__main__":
    test_audit_export() 