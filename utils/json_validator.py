"""
JSON Schema Validation Utility for Assessment Validator

This module provides validation functions to ensure all data structures
follow the standardized JSON schemas for optimal AI processing.
"""

import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import jsonschema
from jsonschema import validate, ValidationError

logger = logging.getLogger(__name__)

# Core JSON Schemas
SESSION_SCHEMA = {
    "type": "object",
    "required": ["session_id", "uoc_code", "assessment_type", "uoc_data", "questions", "mappings"],
    "properties": {
        "session_id": {"type": "string"},
        "uoc_code": {"type": "string"},
        "assessment_type": {"type": "string"},
        "filename": {"type": "string"},
        "created_at": {"type": "string", "format": "date-time"},
        "uoc_data": {"type": "object"},
        "questions": {"type": "array"},
        "mappings": {"type": "object"},
        "statistics": {"type": "object"}
    }
}

QUESTION_SCHEMA = {
    "type": "object",
    "required": ["id", "text"],
    "properties": {
        "id": {"type": "string"},
        "text": {"type": "string"},
        "question_number": {"type": "string"},
        "line_number": {"type": "integer"},
        "pattern_used": {"type": "string"},
        "type": {"type": "string"},
        "question_type": {"type": "string"},
        "choices": {"type": "array", "items": {"type": "string"}},
        "confidence": {"type": "string"}
    }
}

MAPPING_SCHEMA = {
    "type": "object",
    "required": ["question_id", "question_text", "mapping_analysis"],
    "properties": {
        "question_id": {"type": "string"},
        "question_text": {"type": "string"},
        "assessment_type": {"type": "string"},
        "bloom_taxonomy": {"type": "object"},
        "asqa_quality_assessment": {"type": "object"},
        "mapping_analysis": {"type": "object"},
        "comprehensive_analysis": {"type": "object"},
        "mapping_statistics": {"type": "object"},
        "overall_assessment": {"type": "object"},
        "audit_trail": {"type": "object"}
    }
}

API_RESPONSE_SCHEMA = {
    "type": "object",
    "required": ["success"],
    "properties": {
        "success": {"type": "boolean"},
        "data": {"type": "object"},
        "message": {"type": "string"},
        "error": {"type": "string"},
        "timestamp": {"type": "string", "format": "date-time"}
    }
}

def validate_session_data(data: Dict[str, Any]) -> bool:
    """
    Validate session data against the standardized schema
    
    Args:
        data: Session data dictionary
        
    Returns:
        bool: True if valid, False otherwise
        
    Raises:
        ValidationError: If data doesn't match schema
    """
    try:
        validate(instance=data, schema=SESSION_SCHEMA)
        logger.info("✅ Session data validation passed")
        return True
    except ValidationError as e:
        logger.error(f"❌ Session data validation failed: {e.message}")
        return False

def validate_question_data(data: Dict[str, Any]) -> bool:
    """
    Validate question data against the standardized schema
    
    Args:
        data: Question data dictionary
        
    Returns:
        bool: True if valid, False otherwise
    """
    try:
        validate(instance=data, schema=QUESTION_SCHEMA)
        return True
    except ValidationError as e:
        logger.error(f"❌ Question data validation failed: {e.message}")
        return False

def validate_mapping_data(data: Dict[str, Any]) -> bool:
    """
    Validate mapping data against the standardized schema
    
    Args:
        data: Mapping data dictionary
        
    Returns:
        bool: True if valid, False otherwise
    """
    try:
        validate(instance=data, schema=MAPPING_SCHEMA)
        return True
    except ValidationError as e:
        logger.error(f"❌ Mapping data validation failed: {e.message}")
        return False

def validate_api_response(data: Dict[str, Any]) -> bool:
    """
    Validate API response against the standardized schema
    
    Args:
        data: API response dictionary
        
    Returns:
        bool: True if valid, False otherwise
    """
    try:
        validate(instance=data, schema=API_RESPONSE_SCHEMA)
        return True
    except ValidationError as e:
        logger.error(f"❌ API response validation failed: {e.message}")
        return False

def validate_questions_list(questions: List[Dict[str, Any]]) -> bool:
    """
    Validate a list of questions
    
    Args:
        questions: List of question dictionaries
        
    Returns:
        bool: True if all questions are valid, False otherwise
    """
    if not isinstance(questions, list):
        logger.error("❌ Questions must be a list")
        return False
    
    for i, question in enumerate(questions):
        if not validate_question_data(question):
            logger.error(f"❌ Question {i} validation failed")
            return False
    
    logger.info(f"✅ All {len(questions)} questions validated successfully")
    return True

def validate_mappings_list(mappings: List[Dict[str, Any]]) -> bool:
    """
    Validate a list of mappings
    
    Args:
        mappings: List of mapping dictionaries
        
    Returns:
        bool: True if all mappings are valid, False otherwise
    """
    if not isinstance(mappings, list):
        logger.error("❌ Mappings must be a list")
        return False
    
    for i, mapping in enumerate(mappings):
        if not validate_mapping_data(mapping):
            logger.error(f"❌ Mapping {i} validation failed")
            return False
    
    logger.info(f"✅ All {len(mappings)} mappings validated successfully")
    return True

def create_validated_session_data(
    session_id: str,
    uoc_code: str,
    assessment_type: str,
    uoc_data: Dict[str, Any],
    questions: List[Dict[str, Any]],
    mappings: Dict[str, Any],
    filename: str = None
) -> Dict[str, Any]:
    """
    Create and validate a complete session data structure
    
    Args:
        session_id: Unique session identifier
        uoc_code: Unit of competency code
        assessment_type: Type of assessment
        uoc_data: UoC data dictionary
        questions: List of question dictionaries
        mappings: Mappings data dictionary
        filename: Optional filename
        
    Returns:
        Dict: Validated session data
        
    Raises:
        ValidationError: If data doesn't match schema
    """
    session_data = {
        "session_id": session_id,
        "uoc_code": uoc_code,
        "assessment_type": assessment_type,
        "filename": filename or "unknown.txt",
        "created_at": datetime.now().isoformat(),
        "uoc_data": uoc_data,
        "questions": questions,
        "mappings": mappings,
        "statistics": {
            "total_questions": len(questions),
            "total_mappings": len(mappings.get("mappings", [])),
            "assessment_type": assessment_type,
            "uoc_info": {
                "code": uoc_code,
                "title": uoc_data.get("title", "Unknown")
            }
        }
    }
    
    if validate_session_data(session_data):
        return session_data
    else:
        raise ValidationError("Session data validation failed")

def export_validated_json(data: Dict[str, Any], filename: str) -> bool:
    """
    Export validated JSON data to file
    
    Args:
        data: Data dictionary to export
        filename: Output filename
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Validate the data structure
        if not validate_session_data(data):
            logger.error("❌ Data validation failed before export")
            return False
        
        # Add export metadata
        export_data = {
            "metadata": {
                "exported_at": datetime.now().isoformat(),
                "schema_version": "1.0",
                "total_questions": len(data.get("questions", [])),
                "total_mappings": len(data.get("mappings", {}).get("mappings", []))
            },
            "data": data
        }
        
        # Write to file
        with open(filename, 'w') as f:
            json.dump(export_data, f, indent=2, default=str)
        
        logger.info(f"✅ Exported validated JSON to {filename}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Export failed: {str(e)}")
        return False

def load_and_validate_json(filename: str) -> Optional[Dict[str, Any]]:
    """
    Load and validate JSON data from file
    
    Args:
        filename: Input filename
        
    Returns:
        Optional[Dict]: Validated data or None if invalid
    """
    try:
        with open(filename, 'r') as f:
            data = json.load(f)
        
        # If it's an export file with metadata, extract the data
        if "metadata" in data and "data" in data:
            data = data["data"]
        
        if validate_session_data(data):
            logger.info(f"✅ Loaded and validated JSON from {filename}")
            return data
        else:
            logger.error(f"❌ JSON validation failed for {filename}")
            return None
            
    except Exception as e:
        logger.error(f"❌ Failed to load JSON from {filename}: {str(e)}")
        return None

def get_json_schema_summary() -> Dict[str, Any]:
    """
    Get a summary of all JSON schemas for documentation
    
    Returns:
        Dict: Schema summary
    """
    return {
        "schemas": {
            "session": SESSION_SCHEMA,
            "question": QUESTION_SCHEMA,
            "mapping": MAPPING_SCHEMA,
            "api_response": API_RESPONSE_SCHEMA
        },
        "validation_functions": [
            "validate_session_data",
            "validate_question_data", 
            "validate_mapping_data",
            "validate_api_response",
            "validate_questions_list",
            "validate_mappings_list"
        ],
        "utility_functions": [
            "create_validated_session_data",
            "export_validated_json",
            "load_and_validate_json"
        ]
    }

# Example usage
if __name__ == "__main__":
    # Test validation
    test_session = {
        "session_id": "TEST_001",
        "uoc_code": "CHCAGE011",
        "assessment_type": "KBA",
        "uoc_data": {},
        "questions": [],
        "mappings": {"mappings": []}
    }
    
    print("Testing JSON validation...")
    if validate_session_data(test_session):
        print("✅ Test session validation passed")
    else:
        print("❌ Test session validation failed") 