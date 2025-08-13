# JSON Schema for Assessment Validator

## Overview
This document defines the standardized JSON schemas used throughout the Assessment Validator system. All data structures follow these schemas to ensure consistency for AI processing, storage, and analysis.

## Core Data Structures

### 1. Session Data Schema
```json
{
  "session_id": "string",
  "uoc_code": "string",
  "assessment_type": "string",
  "filename": "string",
  "created_at": "ISO8601_timestamp",
  "uoc_data": {
    "elements": [ElementSchema],
    "performance_criteria": [PerformanceCriterionSchema],
    "performance_evidence": [EvidenceSchema],
    "knowledge_evidence": [EvidenceSchema],
    "title": "string",
    "extraction_quality": "string",
    "fetched_at": "ISO8601_timestamp",
    "method": "string",
    "source_url": "string"
  },
  "questions": [QuestionSchema],
  "mappings": {
    "mappings": [MappingSchema],
    "analysis": AnalysisSchema,
    "assessment_type": "string",
    "total_questions": "integer"
  },
  "statistics": StatisticsSchema
}
```

### 2. Question Schema
```json
{
  "id": "string",
  "text": "string",
  "question_number": "string",
  "line_number": "integer",
  "pattern_used": "string",
  "type": "string",
  "question_type": "string",
  "choices": ["string"],
  "confidence": "string"
}
```

### 3. Mapping Schema
```json
{
  "question_id": "string",
  "question_text": "string",
  "assessment_type": "string",
  "bloom_taxonomy": {
    "primary_level": "string",
    "cognitive_demand": "string",
    "asqa_assessment_suitability": "string"
  },
  "asqa_quality_assessment": {
    "competency_focus_score": "integer",
    "authenticity_score": "integer",
    "sufficiency_score": "integer",
    "overall_quality_rating": "string"
  },
  "mapping_analysis": {
    "mapped_elements": [ElementMappingSchema],
    "mapped_performance_criteria": [CriterionMappingSchema],
    "mapped_performance_evidence": [EvidenceMappingSchema],
    "mapped_knowledge_evidence": [EvidenceMappingSchema]
  },
  "comprehensive_analysis": {
    "coverage_assessment": {
      "element_coverage_completeness": "string",
      "performance_criteria_alignment": "string",
      "evidence_requirement_satisfaction": "string"
    },
    "priority_mappings": ["string"],
    "mapping_tags": ["string"]
  },
  "mapping_statistics": {
    "total_mappings": "integer",
    "average_confidence": "float",
    "asqa_compliance_distribution": {
      "full": "integer",
      "partial": "integer",
      "minimal": "integer"
    }
  },
  "overall_assessment": {
    "asqa_compliance_level": "string",
    "audit_readiness": "string",
    "risk_assessment": "string"
  },
  "audit_trail": {
    "mapped_by": "string",
    "mapping_timestamp": "ISO8601_timestamp",
    "validation_checks_passed": ["string"],
    "parsing_method": "string"
  }
}
```

### 4. Element Schema
```json
{
  "id": "string",
  "description": "string",
  "code": "string"
}
```

### 5. Performance Criterion Schema
```json
{
  "code": "string",
  "description": "string"
}
```

### 6. Evidence Schema
```json
{
  "code": "string",
  "description": "string"
}
```

### 7. Element Mapping Schema
```json
{
  "element_id": "string",
  "element_code": "string",
  "element_description": "string",
  "mapping_strength": "string",
  "confidence_score": "float",
  "asqa_validation": {
    "standard_1_8_compliance": "string",
    "audit_risk_level": "string"
  }
}
```

### 8. Criterion Mapping Schema
```json
{
  "criterion_id": "string",
  "criterion_code": "string",
  "criterion_description": "string",
  "mapping_strength": "string",
  "confidence_score": "float",
  "asqa_validation": {
    "standard_1_8_compliance": "string",
    "audit_risk_level": "string"
  }
}
```

### 9. Evidence Mapping Schema
```json
{
  "evidence_id": "string",
  "evidence_code": "string",
  "evidence_description": "string",
  "mapping_strength": "string",
  "confidence_score": "float",
  "asqa_validation": {
    "standard_1_8_compliance": "string",
    "audit_risk_level": "string"
  }
}
```

### 10. Analysis Schema
```json
{
  "elements_coverage": {
    "mapped": "integer",
    "total": "integer",
    "percentage": "float"
  },
  "performance_criteria_coverage": {
    "mapped": "integer",
    "total": "integer",
    "percentage": "float"
  },
  "performance_evidence_coverage": {
    "mapped": "integer",
    "total": "integer",
    "percentage": "float"
  },
  "knowledge_evidence_coverage": {
    "mapped": "integer",
    "total": "integer",
    "percentage": "float"
  }
}
```

### 11. Statistics Schema
```json
{
  "total_questions": "integer",
  "total_mappings": "integer",
  "assessment_type": "string",
  "uoc_info": {
    "code": "string",
    "title": "string"
  }
}
```

## API Response Schemas

### 12. Success Response Schema
```json
{
  "success": true,
  "data": "object",
  "message": "string",
  "timestamp": "ISO8601_timestamp"
}
```

### 13. Error Response Schema
```json
{
  "success": false,
  "error": "string",
  "details": "object",
  "timestamp": "ISO8601_timestamp"
}
```

### 14. Assessment Processing Response Schema
```json
{
  "success": true,
  "redirect_url": "string",
  "session_id": "string"
}
```

## Benefits of Standardized JSON

### For AI Processing:
1. **Consistent Structure**: AI can reliably parse and understand data
2. **Type Safety**: Clear data types for validation
3. **Nested Relationships**: Hierarchical data for complex analysis
4. **Metadata**: Rich context for AI decision-making

### For Storage:
1. **Efficient Querying**: JSON indexes for fast retrieval
2. **Version Control**: Track changes over time
3. **Backup/Restore**: Simple file-based storage
4. **Interoperability**: Easy to export/import

### For Analysis:
1. **Statistical Analysis**: Structured data for metrics
2. **Trend Analysis**: Historical data patterns
3. **Quality Assessment**: Standardized quality metrics
4. **Compliance Tracking**: ASQA compliance indicators

## Implementation Guidelines

### 1. Data Validation
- All JSON must conform to these schemas
- Use JSON Schema validation libraries
- Implement runtime type checking

### 2. Version Control
- Include schema version in metadata
- Maintain backward compatibility
- Document schema evolution

### 3. Performance Optimization
- Use JSON compression for large datasets
- Implement lazy loading for nested data
- Cache frequently accessed data

### 4. Security Considerations
- Validate all JSON input
- Sanitize user-generated content
- Implement access controls for sensitive data

## Usage Examples

### Creating a New Session
```python
session_data = {
    "session_id": f"{uoc_code}_{timestamp}",
    "uoc_code": uoc_code,
    "assessment_type": assessment_type,
    "created_at": datetime.now().isoformat(),
    "uoc_data": uoc_data,
    "questions": questions,
    "mappings": mapping_results,
    "statistics": statistics
}
```

### Validating JSON Structure
```python
import jsonschema

def validate_session_data(data):
    schema = load_json_schema("session_schema.json")
    jsonschema.validate(data, schema)
    return True
```

### Exporting for AI Analysis
```python
def export_for_ai_analysis(session_data):
    return {
        "metadata": {
            "version": "1.0",
            "exported_at": datetime.now().isoformat(),
            "total_questions": len(session_data["questions"]),
            "total_mappings": len(session_data["mappings"]["mappings"])
        },
        "data": session_data
    }
```

This standardized JSON approach ensures that all data is:
- **AI-friendly**: Structured for machine learning
- **Human-readable**: Clear and well-documented
- **Scalable**: Handles large datasets efficiently
- **Interoperable**: Works with external systems
- **Auditable**: Complete audit trail for compliance 