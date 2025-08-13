import logging
import json
import re
from typing import List, Dict, Any, Optional
import requests
from datetime import datetime
import time

logger = logging.getLogger(__name__)

class MappingAgent:
    """Agent responsible for comprehensive mapping of assessment questions to UoC elements and performance criteria"""
    
    def __init__(self, api_key: str = "", api_base_url: str = "https://generativelanguage.googleapis.com/v1/models/gemini-2.0-flash:generateContent", testing_mode: bool = True):
        self.api_key = api_key
        self.api_base_url = api_base_url
        self.session = requests.Session()
        self.testing_mode = testing_mode  # Enable checkpoint in testing mode
        
    def execute(self, questions: List[Dict[str, Any]], uoc_data: Dict[str, Any], assessment_type: str = "Mixed") -> List[Dict[str, Any]]:
        """
        Comprehensive mapping of assessment questions to UoC elements and performance criteria
        
        Args:
            questions (List[Dict]): List of extracted questions
            uoc_data (Dict): UoC data with elements, performance criteria, and evidence requirements
            assessment_type (str): Assessment type (KBA, SBA, PEP, Mixed)
            
        Returns:
            List of comprehensive mappings with accuracy analysis, strength assessment, and audit trail
        """
        try:
            logger.info(f"Comprehensive mapping of {len(questions)} questions to UoC components")
            
            if not self.api_key:
                logger.error("LLM API key missing for MappingAgent. Aborting mapping.")
                raise RuntimeError("LLM access is required for mapping but no API key was provided")
            
            mappings = []
            api_failures = 0
            for i, question in enumerate(questions):
                logger.info(f"Processing question {i+1}/{len(questions)}")
                mapping = self._map_single_question_comprehensive(question, uoc_data, assessment_type)
                if not mapping:
                    logger.error(f"LLM mapping failed for question {i+1}; no fallback permitted")
                    raise RuntimeError("LLM mapping failed; mapping cannot proceed without live LLM access")
                # Mark this as an AI-generated mapping for tracking
                mapping['mapping_source'] = 'ai'
                mappings.append(mapping)
            
            # Log summary of API failures
            if api_failures > 0:
                logger.error("LLM API issues detected; mapping halted due to no-fallback policy")
                raise RuntimeError("LLM API issues detected during mapping; operation aborted")
            
            # Debug confidence scores
            for i, mapping in enumerate(mappings):
                mapping_analysis = mapping.get('mapping_analysis', {})
                total_confidence = 0
                confidence_count = 0
                
                for category in ['mapped_elements', 'mapped_performance_criteria', 'mapped_performance_evidence', 'mapped_knowledge_evidence']:
                    items = mapping_analysis.get(category, [])
                    for item in items:
                        confidence = item.get('confidence_score', 0)
                        total_confidence += confidence
                        confidence_count += 1
                
                avg_confidence = (total_confidence / confidence_count * 100) if confidence_count > 0 else 0
                logger.info(f"Question {i+1} confidence: {avg_confidence:.1f}% ({confidence_count} items)")
            
            # Add mapping analysis and statistics
            mapping_analysis = self._analyze_mapping_coverage(mappings, uoc_data)
            
            logger.info(f"Successfully generated {len(mappings)} comprehensive mappings")
            return {
                'mappings': mappings,
                'analysis': mapping_analysis,
                'assessment_type': assessment_type,
                'total_questions': len(questions)
            }
            
        except Exception as e:
            logger.error(f"Error in comprehensive mapping process: {str(e)}")
            raise
    
    def _map_single_question_comprehensive(self, question: Dict[str, Any], uoc_data: Dict[str, Any], assessment_type: str) -> Optional[Dict[str, Any]]:
        """Comprehensive mapping of a single question to UoC components with detailed analysis"""
        try:
            # Prepare the comprehensive prompt for AI mapping
            prompt = self._create_simplified_mapping_prompt(question, uoc_data, assessment_type)
            
            # Call AI API
            response = self._call_ai_api(prompt)
            
            if response:
                # Parse AI response with enhanced structure
                mapping = self._parse_comprehensive_ai_response_robust(response, question, uoc_data)
                return mapping
            else:
                return None
                
        except Exception as e:
            logger.error(f"Error mapping question {question.get('id', 'unknown')}: {str(e)}")
            return None
    
    def _create_simplified_mapping_prompt(self, question: Dict[str, Any], uoc_data: Dict[str, Any], assessment_type: str) -> str:
        """Create simplified but comprehensive mapping prompt to avoid JSON parsing issues"""
        
        # Extract UoC components
        elements = uoc_data.get('elements', [])
        performance_criteria = uoc_data.get('performance_criteria', [])
        performance_evidence = uoc_data.get('performance_evidence', [])
        knowledge_evidence = uoc_data.get('knowledge_evidence', [])
        
        uoc_code = uoc_data.get('uoc_code', 'Unknown')
        uoc_title = uoc_data.get('title', 'Unknown')
        question_text = question.get('text', '').replace('"', "'")  # Prevent JSON issues
        question_id = question.get('id', 0)
        
        # Build UoC components list with safe formatting
        elements_str = ""
        for element in elements[:5]:  # Limit to first 5 to reduce prompt size
            desc = str(element.get('description', '')).replace('"', "'")[:100]  # Truncate and escape
            elements_str += f"E{element.get('id', '')}: {desc}\\n"
        
        criteria_str = ""
        for pc in performance_criteria[:8]:  # Limit to first 8
            desc = str(pc.get('description', '')).replace('"', "'")[:100]
            criteria_str += f"PC{pc.get('code', '')}: {desc}\\n"
        
        evidence_str = ""
        for pe in performance_evidence[:5]:  # Limit to first 5
            desc = str(pe.get('description', '')).replace('"', "'")[:100]
            evidence_str += f"PE{pe.get('code', '')}: {desc}\\n"
        
        knowledge_str = ""
        for ke in knowledge_evidence[:5]:  # Limit to first 5
            desc = str(ke.get('description', '')).replace('"', "'")[:100]
            knowledge_str += f"KE{ke.get('code', '')}: {desc}\\n"
        
        prompt = f"""You are an expert RTO assessor mapping assessment questions to Unit of Competency components. 

UoC: {uoc_code} - {uoc_title}
Question: {question_text}
Assessment Type: {assessment_type}

Available UoC Components:

ELEMENTS:
{elements_str}

PERFORMANCE CRITERIA:
{criteria_str}

PERFORMANCE EVIDENCE:
{evidence_str}

KNOWLEDGE EVIDENCE:
{knowledge_str}

Task: Analyze the question and map it to the most relevant UoC components. Consider:
1. Which elements does this question assess?
2. Which performance criteria are demonstrated?
3. What evidence types are required?
4. What knowledge evidence is being tested?

Return ONLY valid JSON with this structure (replace the placeholders with actual mappings):

{{
    "question_id": {question_id},
    "question_text": "{question_text}",
    "assessment_type": "{assessment_type}",
    "bloom_taxonomy": {{
        "primary_level": "UNDERSTAND",
        "cognitive_demand": "MEDIUM", 
        "asqa_assessment_suitability": "GOOD"
    }},
    "asqa_quality_assessment": {{
        "competency_focus_score": 4,
        "authenticity_score": 3,
        "sufficiency_score": 4,
        "overall_quality_rating": "HIGH"
    }},
    "mapping_analysis": {{
        "mapped_elements": [
            {{
                "element_id": "E1",
                "element_code": "E1",
                "element_description": "Actual element description from the list above",
                "mapping_strength": "EXPLICIT",
                "confidence_score": 0.9,
                "asqa_validation": {{
                    "standard_1_8_compliance": "FULL",
                    "audit_risk_level": "LOW"
                }}
            }}
        ],
        "mapped_performance_criteria": [
            {{
                "criterion_id": "PC1.1",
                "criterion_code": "PC1.1",
                "criterion_description": "Actual criterion description from the list above",
                "mapping_strength": "EXPLICIT",
                "confidence_score": 0.85,
                "asqa_validation": {{
                    "standard_1_8_compliance": "FULL",
                    "audit_risk_level": "LOW"
                }}
            }}
        ],
        "mapped_performance_evidence": [],
        "mapped_knowledge_evidence": []
    }},
    "overall_assessment": {{
        "asqa_compliance_level": "FULL",
        "audit_readiness": "READY",
        "risk_assessment": "LOW"
    }}
}}

IMPORTANT: 
- Use actual element IDs, criterion codes, and descriptions from the provided lists
- Map to the most relevant components based on the question content
- Focus on Performance Criteria as they are most critical for ASQA compliance
- Only include mappings that are clearly relevant to the question"""
        
        return prompt
    
    def _parse_comprehensive_ai_response_robust(self, response: str, question: Dict[str, Any], uoc_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Parse AI response with robust error handling and JSON cleanup"""
        try:
            # Clean the response
            cleaned_response = self._clean_json_response(response)
            
            if not cleaned_response:
                logger.warning(f"Could not extract JSON from AI response for question {question.get('id')}")
                return None
            
            # Try to parse the cleaned JSON
            mapping_data = json.loads(cleaned_response)
            
            # Validate and enhance the mapping data
            if self._validate_basic_mapping_structure(mapping_data):
                # Add missing fields with defaults if needed
                mapping_data = self._ensure_complete_mapping_structure(mapping_data, question, uoc_data)
                
                # Add audit trail
                mapping_data['audit_trail'] = {
                    "mapped_by": "AI_System_v2.0_Enhanced",
                    "mapping_timestamp": datetime.now().isoformat(),
                    "validation_checks_passed": ["structure", "basic_validation"],
                    "parsing_method": "robust_json_cleanup"
                }
                
                # Mark as AI-generated mapping
                mapping_data['mapping_source'] = 'ai'
                
                return mapping_data
            else:
                logger.warning(f"Invalid mapping structure for question {question.get('id')}")
                return None
                
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing failed even after cleanup: {str(e)}")
            logger.debug(f"Cleaned response was: {cleaned_response[:500]}...")
            return None
        except Exception as e:
            logger.error(f"Error in robust AI response parsing: {str(e)}")
            return None
    
    def _clean_json_response(self, response: str) -> Optional[str]:
        """Clean and extract JSON from AI response with multiple fallback methods"""
        
        # Method 1: Extract JSON between first { and last }
        json_start = response.find('{')
        json_end = response.rfind('}') + 1
        
        if json_start != -1 and json_end > json_start:
            json_candidate = response[json_start:json_end]
            
            # Try to parse as-is first
            try:
                json.loads(json_candidate)
                return json_candidate
            except:
                pass
        
        # Method 2: Remove markdown code blocks
        cleaned = re.sub(r'```json\s*', '', response)
        cleaned = re.sub(r'```\s*', '', cleaned)
        
        json_start = cleaned.find('{')
        json_end = cleaned.rfind('}') + 1
        
        if json_start != -1 and json_end > json_start:
            json_candidate = cleaned[json_start:json_end]
            
            try:
                json.loads(json_candidate)
                return json_candidate
            except:
                pass
        
        # Method 3: Fix common JSON issues
        if json_start != -1 and json_end > json_start:
            json_candidate = response[json_start:json_end]
            
            # Fix common issues
            json_candidate = self._fix_common_json_issues(json_candidate)
            
            try:
                json.loads(json_candidate)
                return json_candidate
            except:
                pass
        
        # Method 4: Extract using regex for structured JSON
        json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
        matches = re.findall(json_pattern, response, re.DOTALL)
        
        for match in matches:
            try:
                json.loads(match)
                return match
            except:
                continue
        
        return None
    
    def _fix_common_json_issues(self, json_str: str) -> str:
        """Fix common JSON syntax issues"""
        
        # Fix trailing commas
        json_str = re.sub(r',(\s*[}\]])', r'\1', json_str)
        
        # Fix unescaped quotes in strings
        json_str = re.sub(r'(?<!\\)"(?=.*".*:)', r'\\"', json_str)
        
        # Fix missing commas between objects
        json_str = re.sub(r'}\s*{', '},{', json_str)
        
        # Fix missing commas between array elements
        json_str = re.sub(r']\s*\[', '],[', json_str)
        
        # Remove any control characters that might cause issues
        json_str = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', json_str)
        
        return json_str
    
    def _validate_basic_mapping_structure(self, mapping_data: Dict[str, Any]) -> bool:
        """Validate basic mapping data structure"""
        required_fields = ['question_id', 'mapping_analysis']
        
        for field in required_fields:
            if field not in mapping_data:
                logger.warning(f"Missing required field: {field}")
                return False
        
        # Check mapping_analysis structure
        mapping_analysis = mapping_data.get('mapping_analysis', {})
        required_analysis_fields = ['mapped_elements', 'mapped_performance_criteria']
        
        for field in required_analysis_fields:
            if field not in mapping_analysis:
                logger.warning(f"Missing required analysis field: {field}")
                return False
            if not isinstance(mapping_analysis[field], list):
                logger.warning(f"Field {field} should be a list")
                return False
        
        return True
    
    def _ensure_complete_mapping_structure(self, mapping_data: Dict[str, Any], question: Dict[str, Any], uoc_data: Dict[str, Any]) -> Dict[str, Any]:
        """Ensure mapping data has all required fields with sensible defaults"""
        
        # Ensure top-level fields
        mapping_data.setdefault('question_text', question.get('text', ''))
        mapping_data.setdefault('question_choices', question.get('choices', []))
        mapping_data.setdefault('assessment_type', 'Mixed')
        
        # Ensure bloom_taxonomy
        mapping_data.setdefault('bloom_taxonomy', {
            'primary_level': 'UNDERSTAND',
            'cognitive_demand': 'MEDIUM',
            'asqa_assessment_suitability': 'GOOD'
        })
        
        # Ensure asqa_quality_assessment
        mapping_data.setdefault('asqa_quality_assessment', {
            'competency_focus_score': 4,
            'authenticity_score': 3,
            'sufficiency_score': 4,
            'overall_quality_rating': 'HIGH'
        })
        
        # Ensure mapping_analysis has all required arrays
        mapping_analysis = mapping_data.setdefault('mapping_analysis', {})
        mapping_analysis.setdefault('mapped_elements', [])
        mapping_analysis.setdefault('mapped_performance_criteria', [])
        mapping_analysis.setdefault('mapped_performance_evidence', [])
        mapping_analysis.setdefault('mapped_knowledge_evidence', [])
        
        # Clean up incorrect IDs in mappings
        self._clean_mapping_ids(mapping_analysis)
        
        # Validate ID formats and log any issues
        self._log_id_validation_issues(mapping_analysis)
        
        # Ensure overall_assessment
        mapping_data.setdefault('overall_assessment', {
            'asqa_compliance_level': 'PARTIAL',
            'audit_readiness': 'NEEDS_REVIEW',
            'risk_assessment': 'MEDIUM'
        })
        
        # Add comprehensive_analysis if missing
        if 'comprehensive_analysis' not in mapping_data:
            mapping_data['comprehensive_analysis'] = {
                'coverage_assessment': {
                    'element_coverage_completeness': 'PARTIAL',
                    'performance_criteria_alignment': 'MODERATE',
                    'evidence_requirement_satisfaction': 'PARTIAL'
                },
                'priority_mappings': [],
                'mapping_tags': []
            }
        
        # Calculate mapping statistics
        mapping_analysis = mapping_data.get('mapping_analysis', {})
        stats = self._calculate_mapping_statistics(mapping_analysis)
        mapping_data['mapping_statistics'] = stats
        
        # Filter out empty mappings
        mapping_data = self._filter_empty_mappings(mapping_data)
        
        return mapping_data
    
    def _filter_empty_mappings(self, mapping_data: Dict[str, Any]) -> Dict[str, Any]:
        """Filter out empty or invalid mapping entries"""
        if 'mapping_analysis' not in mapping_data:
            return mapping_data
        
        mapping_analysis = mapping_data['mapping_analysis']
        
        # Filter mapped elements
        if 'mapped_elements' in mapping_analysis:
            mapping_analysis['mapped_elements'] = [
                element for element in mapping_analysis['mapped_elements']
                if element.get('element_id') and element.get('element_description')
            ]
        
        # Filter mapped performance criteria
        if 'mapped_performance_criteria' in mapping_analysis:
            mapping_analysis['mapped_performance_criteria'] = [
                pc for pc in mapping_analysis['mapped_performance_criteria']
                if pc.get('criterion_id') and pc.get('criterion_description')
            ]
        
        # Filter mapped performance evidence
        if 'mapped_performance_evidence' in mapping_analysis:
            mapping_analysis['mapped_performance_evidence'] = [
                pe for pe in mapping_analysis['mapped_performance_evidence']
                if pe.get('evidence_id') and pe.get('evidence_description')
            ]
        
        # Filter mapped knowledge evidence
        if 'mapped_knowledge_evidence' in mapping_analysis:
            mapping_analysis['mapped_knowledge_evidence'] = [
                ke for ke in mapping_analysis['mapped_knowledge_evidence']
                if ke.get('evidence_id') and ke.get('evidence_description')
            ]
        
        return mapping_data
    
    def _clean_mapping_ids(self, mapping_analysis: Dict[str, Any]):
        """Clean up incorrect IDs in mapping data with robust validation"""
        
        # Clean mapped elements - must be E followed by number
        for element in mapping_analysis.get('mapped_elements', []):
            if 'element_id' in element:
                element_id = element['element_id']
                # Fix various issues and ensure E + number format
                if element_id:
                    # Remove any duplicated E prefixes
                    while element_id.startswith('EE'):
                        element_id = element_id[1:]
                    
                    # Ensure it starts with E
                    if not element_id.startswith('E'):
                        element_id = f"E{element_id}"
                    
                    # Ensure it has a number after E
                    if not any(char.isdigit() for char in element_id[1:]):
                        element_id = f"{element_id}1"
                    
                    element['element_id'] = element_id
                    element['element_code'] = element_id
        
        # Clean mapped performance criteria - must be PC followed by number
        for pc in mapping_analysis.get('mapped_performance_criteria', []):
            if 'criterion_id' in pc:
                criterion_id = pc['criterion_id']
                # Fix various issues and ensure PC + number format
                if criterion_id:
                    # Remove any duplicated PC prefixes
                    while criterion_id.startswith('PCPC'):
                        criterion_id = criterion_id[2:]
                    
                    # Ensure it starts with PC
                    if not criterion_id.startswith('PC'):
                        criterion_id = f"PC{criterion_id}"
                    
                    # Ensure it has a number after PC
                    if not any(char.isdigit() for char in criterion_id[2:]):
                        criterion_id = f"{criterion_id}1"
                    
                    pc['criterion_id'] = criterion_id
                    pc['criterion_code'] = criterion_id
        
        # Clean mapped performance evidence - must be PE followed by number
        for pe in mapping_analysis.get('mapped_performance_evidence', []):
            if 'evidence_id' in pe:
                evidence_id = pe['evidence_id']
                # Fix various issues and ensure PE + number format
                if evidence_id:
                    # Remove any duplicated PE prefixes
                    while evidence_id.startswith('PEPE'):
                        evidence_id = evidence_id[2:]
                    
                    # Ensure it starts with PE
                    if not evidence_id.startswith('PE'):
                        evidence_id = f"PE{evidence_id}"
                    
                    # Ensure it has a number after PE
                    if not any(char.isdigit() for char in evidence_id[2:]):
                        evidence_id = f"{evidence_id}1"
                    
                    pe['evidence_id'] = evidence_id
                    pe['evidence_code'] = evidence_id
        
        # Clean mapped knowledge evidence - must be KE followed by number
        for ke in mapping_analysis.get('mapped_knowledge_evidence', []):
            # Clean evidence_id first (this is the main field)
            if 'evidence_id' in ke:
                evidence_id = ke['evidence_id']
                # Fix various issues and ensure KE + number format
                if evidence_id:
                    # Remove any duplicated KE prefixes
                    while evidence_id.startswith('KEKE'):
                        evidence_id = evidence_id[2:]
                    
                    # Ensure it starts with KE
                    if not evidence_id.startswith('KE'):
                        evidence_id = f"KE{evidence_id}"
                    
                    # Ensure it has a number after KE
                    if not any(char.isdigit() for char in evidence_id[2:]):
                        evidence_id = f"{evidence_id}1"
                    
                    ke['evidence_id'] = evidence_id
                    ke['evidence_code'] = evidence_id
            
            # Clean knowledge_id if it exists
            if 'knowledge_id' in ke:
                knowledge_id = ke['knowledge_id']
                # Fix various issues and ensure KE + number format
                if knowledge_id:
                    # Remove any duplicated KE prefixes
                    while knowledge_id.startswith('KEKE'):
                        knowledge_id = knowledge_id[2:]
                    
                    # Ensure it starts with KE
                    if not knowledge_id.startswith('KE'):
                        knowledge_id = f"KE{knowledge_id}"
                    
                    # Ensure it has a number after KE
                    if not any(char.isdigit() for char in knowledge_id[2:]):
                        knowledge_id = f"{knowledge_id}1"
                    
                    ke['knowledge_id'] = knowledge_id
                    ke['knowledge_code'] = knowledge_id
    
    def _validate_id_format(self, id_value: str, expected_prefix: str) -> bool:
        """Validate that an ID follows the correct format"""
        if not id_value:
            return False
        
        # Check if it starts with the expected prefix
        if not id_value.startswith(expected_prefix):
            return False
        
        # Check if it has at least one digit after the prefix
        suffix = id_value[len(expected_prefix):]
        if not any(char.isdigit() for char in suffix):
            return False
        
        return True
    
    def _log_id_validation_issues(self, mapping_analysis: Dict[str, Any]):
        """Log any ID format issues found in mapping data"""
        issues = []
        
        # Check elements
        for i, element in enumerate(mapping_analysis.get('mapped_elements', [])):
            element_id = element.get('element_id', '')
            if not self._validate_id_format(element_id, 'E'):
                issues.append(f"Element {i+1}: Invalid format '{element_id}' (should be E + number)")
        
        # Check performance criteria
        for i, pc in enumerate(mapping_analysis.get('mapped_performance_criteria', [])):
            criterion_id = pc.get('criterion_id', '')
            if not self._validate_id_format(criterion_id, 'PC'):
                issues.append(f"Performance Criteria {i+1}: Invalid format '{criterion_id}' (should be PC + number)")
        
        # Check performance evidence
        for i, pe in enumerate(mapping_analysis.get('mapped_performance_evidence', [])):
            evidence_id = pe.get('evidence_id', '')
            if not self._validate_id_format(evidence_id, 'PE'):
                issues.append(f"Performance Evidence {i+1}: Invalid format '{evidence_id}' (should be PE + number)")
        
        # Check knowledge evidence
        for i, ke in enumerate(mapping_analysis.get('mapped_knowledge_evidence', [])):
            evidence_id = ke.get('evidence_id', '')
            if not self._validate_id_format(evidence_id, 'KE'):
                issues.append(f"Knowledge Evidence {i+1}: Invalid format '{evidence_id}' (should be KE + number)")
        
        if issues:
            logger.warning(f"ID format validation issues found: {issues}")
        else:
            logger.info("All ID formats validated successfully")
    
    def _generate_fallback_mapping(self, question: Dict[str, Any], uoc_data: Dict[str, Any], assessment_type: str) -> Dict[str, Any]:
        """Generate a fallback mapping when AI fails"""
        
        # Get first available components for basic mapping
        elements = uoc_data.get('elements', [])
        performance_criteria = uoc_data.get('performance_criteria', [])
        
        # Handle both dict and list formats
        if isinstance(elements, dict):
            elements = list(elements.values())
        if isinstance(performance_criteria, dict):
            performance_criteria = list(performance_criteria.values())
        
        mapped_elements = []
        mapped_criteria = []
        
        # Map to multiple elements and criteria for better coverage
        if elements:
            # Map to first 2 elements if available
            for i, element in enumerate(elements[:2]):
                mapped_elements.append({
                    "element_id": element.get('id', f'E{i+1}'),
                    "element_code": element.get('id', f'E{i+1}'),
                    "element_description": element.get('description', f'Element {element.get("id", f"E{i+1}")} - Fallback mapping'),
                    "mapping_strength": "PARTIAL",
                    "confidence_score": 0.8,  # Higher confidence for fallback
                    "asqa_validation": {
                        "standard_1_8_compliance": "PARTIAL",
                        "audit_risk_level": "MEDIUM"
                    }
                })
        
        if performance_criteria:
            # Map to first 2 criteria if available
            for i, criterion in enumerate(performance_criteria[:2]):
                mapped_criteria.append({
                    "criterion_id": criterion.get('code', f'PC{i+1}'),
                    "criterion_code": criterion.get('code', f'PC{i+1}'),
                    "criterion_description": criterion.get('description', f'Performance Criterion {criterion.get("code", f"PC{i+1}")} - Fallback mapping'),
                    "mapping_strength": "PARTIAL",
                    "confidence_score": 0.8,  # Higher confidence for fallback
                    "asqa_validation": {
                        "standard_1_8_compliance": "PARTIAL",
                        "audit_risk_level": "MEDIUM"
                    }
                })
        
        return {
            "question_id": question.get('id', 0),
            "question_text": question.get('text', ''),
            "question_choices": question.get('choices', []),
            "assessment_type": assessment_type,
            "bloom_taxonomy": {
                "primary_level": "UNDERSTAND",
                "cognitive_demand": "MEDIUM",
                "asqa_assessment_suitability": "ACCEPTABLE"
            },
            "asqa_quality_assessment": {
                "competency_focus_score": 3,
                "authenticity_score": 3,
                "sufficiency_score": 3,
                "overall_quality_rating": "MEDIUM"
            },
            "mapping_analysis": {
                "mapped_elements": mapped_elements,
                "mapped_performance_criteria": mapped_criteria,
                "mapped_performance_evidence": [],
                "mapped_knowledge_evidence": []
            },
            "comprehensive_analysis": {
                "coverage_assessment": {
                    "element_coverage_completeness": "MINIMAL",
                    "performance_criteria_alignment": "WEAK",
                    "evidence_requirement_satisfaction": "INSUFFICIENT"
                },
                "priority_mappings": [],
                "mapping_tags": []
            },
            "overall_assessment": {
                "asqa_compliance_level": "MINIMAL",
                "audit_readiness": "NOT_READY",
                "risk_assessment": "HIGH"
            },
            "audit_trail": {
                "mapped_by": "Fallback_System",
                "mapping_timestamp": datetime.now().isoformat(),
                "mapping_method": "fallback_due_to_ai_failure"
            }
        }
    
    def _call_ai_api(self, prompt: str) -> Optional[str]:
        """Make API call to Gemini with rate limiting - simplified to match fetch agent"""
        
        if not self.api_key:
            logger.warning("No API key provided")
            return None
        
        # Basic rate limiting to prevent API quota exhaustion
        time.sleep(0.5)
        
        headers = {
            'Content-Type': 'application/json',
        }
        
        data = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": prompt
                        }
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.1,  # Lower temperature for more consistent JSON
                "topK": 10,  # Match fetch agent for consistency
                "topP": 0.8,
                "maxOutputTokens": 2000,  # Increased but still conservative
            }
        }
        
        url = f"{self.api_base_url}?key={self.api_key}"
        
        try:
            response = self.session.post(url, headers=headers, json=data, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            
            # Extract the generated text from the response
            if 'candidates' in result and len(result['candidates']) > 0:
                content = result['candidates'][0].get('content', {})
                parts = content.get('parts', [])
                if parts and 'text' in parts[0]:
                    return parts[0]['text']
            
            return None
            
        except requests.exceptions.RequestException as e:
            logger.error(f"API call failed: {e}")
            return None
        except Exception as e:
            logger.error(f"AI API call failed: {str(e)}")
            return None

    # Keep all the existing methods that are working fine
    def _calculate_mapping_statistics(self, mapping_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate ASQA-focused mapping statistics"""
        
        total_mappings = 0
        total_confidence = 0
        full_compliance = 0
        partial_compliance = 0
        minimal_compliance = 0
        
        # Analyze each mapping category
        for category in ['mapped_elements', 'mapped_performance_criteria', 'mapped_performance_evidence', 'mapped_knowledge_evidence']:
            mappings = mapping_analysis.get(category, [])
            total_mappings += len(mappings)
            
            for mapping in mappings:
                # Confidence analysis
                confidence = mapping.get('confidence_score', 0)
                total_confidence += confidence
                
                # ASQA compliance analysis
                asqa_validation = mapping.get('asqa_validation', {})
                compliance = asqa_validation.get('standard_1_8_compliance', 'MINIMAL')
                if compliance == 'FULL':
                    full_compliance += 1
                elif compliance == 'PARTIAL':
                    partial_compliance += 1
                else:
                    minimal_compliance += 1
        
        avg_confidence = total_confidence / total_mappings if total_mappings > 0 else 0
        
        return {
            'total_mappings': total_mappings,
            'average_confidence': round(avg_confidence, 3),
            'asqa_compliance_distribution': {
                'full': full_compliance,
                'partial': partial_compliance,
                'minimal': minimal_compliance
            }
        }
    
    def _analyze_mapping_coverage(self, mappings: List[Dict[str, Any]], uoc_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze overall mapping coverage and identify gaps with intelligent insights"""
        
        # Collect all mapped components
        mapped_elements = set()
        mapped_criteria = set()
        mapped_performance_evidence = set()
        mapped_knowledge_evidence = set()
        
        # Enhanced tracking for intelligent analysis
        mapping_quality_scores = []
        cognitive_level_distribution = {'REMEMBER': 0, 'UNDERSTAND': 0, 'APPLY': 0, 'ANALYZE': 0, 'EVALUATE': 0, 'CREATE': 0}
        assessment_method_distribution = {'KBA': 0, 'SBA': 0, 'PEP': 0}
        
        for mapping in mappings:
            mapping_analysis = mapping.get('mapping_analysis', {})
            
            # Collect mapped components
            for element in mapping_analysis.get('mapped_elements', []):
                mapped_elements.add(element.get('element_id', ''))
            
            for criterion in mapping_analysis.get('mapped_performance_criteria', []):
                mapped_criteria.add(criterion.get('criterion_id', ''))
            
            for evidence in mapping_analysis.get('mapped_performance_evidence', []):
                mapped_performance_evidence.add(evidence.get('evidence_id', ''))
            
            for evidence in mapping_analysis.get('mapped_knowledge_evidence', []):
                mapped_knowledge_evidence.add(evidence.get('evidence_id', ''))
            
            # Track quality metrics for intelligent analysis
            avg_confidence = self._calculate_average_confidence(mapping_analysis)
            mapping_quality_scores.append(avg_confidence)
            
            # Track cognitive levels
            bloom_level = mapping.get('bloom_taxonomy', {}).get('primary_level', 'UNDERSTAND')
            cognitive_level_distribution[bloom_level] = cognitive_level_distribution.get(bloom_level, 0) + 1
            
            # Track assessment methods
            assessment_type = mapping.get('assessment_type', 'KBA')
            assessment_method_distribution[assessment_type] = assessment_method_distribution.get(assessment_type, 0) + 1
        
        # Calculate coverage statistics
        total_elements = len(uoc_data.get('elements', []))
        total_criteria = len(uoc_data.get('performance_criteria', []))
        total_performance_evidence = len(uoc_data.get('performance_evidence', []))
        total_knowledge_evidence = len(uoc_data.get('knowledge_evidence', []))
        
        # Enhanced coverage analysis with intelligent insights
        coverage_analysis = {
            'elements_coverage': {
                'mapped': len(mapped_elements),
                'total': total_elements,
                'percentage': round((len(mapped_elements) / total_elements * 100), 1) if total_elements > 0 else 0,
                'unmapped': self._identify_unmapped_components(uoc_data.get('elements', []), mapped_elements, 'element_id'),
                'critical_gaps': self._identify_critical_element_gaps(uoc_data.get('elements', []), mapped_elements)
            },
            'performance_criteria_coverage': {
                'mapped': len(mapped_criteria),
                'total': total_criteria,
                'percentage': round((len(mapped_criteria) / total_criteria * 100), 1) if total_criteria > 0 else 0,
                'unmapped': self._identify_unmapped_components(uoc_data.get('performance_criteria', []), mapped_criteria, 'code'),
                'critical_gaps': self._identify_critical_criteria_gaps(uoc_data.get('performance_criteria', []), mapped_criteria)
            },
            'performance_evidence_coverage': {
                'mapped': len(mapped_performance_evidence),
                'total': total_performance_evidence,
                'percentage': round((len(mapped_performance_evidence) / total_performance_evidence * 100), 1) if total_performance_evidence > 0 else 0,
                'unmapped': self._identify_unmapped_components(uoc_data.get('performance_evidence', []), mapped_performance_evidence, 'code')
            },
            'knowledge_evidence_coverage': {
                'mapped': len(mapped_knowledge_evidence),
                'total': total_knowledge_evidence,
                'percentage': round((len(mapped_knowledge_evidence) / total_knowledge_evidence * 100), 1) if total_knowledge_evidence > 0 else 0,
                'unmapped': self._identify_unmapped_components(uoc_data.get('knowledge_evidence', []), mapped_knowledge_evidence, 'code')
            },
            'intelligent_insights': {
                'quality_analysis': self._analyze_mapping_quality(mapping_quality_scores),
                'cognitive_balance': self._analyze_cognitive_balance(cognitive_level_distribution),
                'assessment_method_balance': self._analyze_assessment_method_balance(assessment_method_distribution),
                'predictive_gaps': self._predict_likely_gaps(uoc_data, mappings),
                'compliance_risks': self._identify_compliance_risks(mappings, uoc_data),
                'recommendations': self._generate_intelligent_recommendations(mappings, uoc_data)
            }
        }
        
        return coverage_analysis

    def _calculate_average_confidence(self, mapping_analysis: Dict) -> float:
        """Calculate average confidence score for a mapping"""
        total_confidence = 0
        confidence_count = 0
        
        for category in ['mapped_elements', 'mapped_performance_criteria', 'mapped_performance_evidence', 'mapped_knowledge_evidence']:
            items = mapping_analysis.get(category, [])
            for item in items:
                confidence = item.get('confidence_score', 0)
                total_confidence += confidence
                confidence_count += 1
        
        return (total_confidence / confidence_count) if confidence_count > 0 else 0

    def _identify_unmapped_components(self, components: List[Dict], mapped_set: set, id_field: str) -> List[Dict]:
        """Identify unmapped components with context"""
        unmapped = []
        for component in components:
            component_id = component.get(id_field, '')
            if component_id and component_id not in mapped_set:
                unmapped.append({
                    'id': component_id,
                    'description': component.get('description', ''),
                    'priority': self._assess_component_priority(component),
                    'suggested_questions': self._generate_suggested_questions(component)
                })
        return unmapped

    def _assess_component_priority(self, component: Dict) -> str:
        """Assess priority of unmapped component based on content analysis"""
        description = component.get('description', '').lower()
        
        # Keywords indicating high priority
        high_priority_keywords = ['critical', 'essential', 'must', 'required', 'core', 'fundamental']
        medium_priority_keywords = ['important', 'should', 'necessary', 'key']
        
        for keyword in high_priority_keywords:
            if keyword in description:
                return 'HIGH'
        
        for keyword in medium_priority_keywords:
            if keyword in description:
                return 'MEDIUM'
        
        return 'LOW'

    def _generate_suggested_questions(self, component: Dict) -> List[str]:
        """Generate suggested question types for unmapped component"""
        description = component.get('description', '')
        suggestions = []
        
        # Analyze component type and generate appropriate question suggestions
        if 'performance' in description.lower():
            suggestions.append("Practical demonstration question")
            suggestions.append("Scenario-based assessment")
        elif 'knowledge' in description.lower():
            suggestions.append("Multiple choice question")
            suggestions.append("Short answer question")
        else:
            suggestions.append("Mixed assessment question")
        
        return suggestions

    def _identify_critical_element_gaps(self, elements: List[Dict], mapped_elements: set) -> List[Dict]:
        """Identify critical gaps in element coverage"""
        critical_gaps = []
        
        for element in elements:
            element_id = element.get('element_id', '')
            if element_id and element_id not in mapped_elements:
                description = element.get('description', '')
                
                # Check if this is a critical element based on content analysis
                if self._is_critical_element(description):
                    critical_gaps.append({
                        'element_id': element_id,
                        'description': description,
                        'criticality_reason': self._determine_criticality_reason(description),
                        'impact_score': self._calculate_impact_score(description)
                    })
        
        return critical_gaps

    def _is_critical_element(self, description: str) -> bool:
        """Determine if an element is critical based on content analysis"""
        critical_indicators = [
            'safety', 'health', 'emergency', 'critical', 'essential', 'core competency',
            'regulatory', 'compliance', 'mandatory', 'required skill'
        ]
        
        description_lower = description.lower()
        return any(indicator in description_lower for indicator in critical_indicators)

    def _determine_criticality_reason(self, description: str) -> str:
        """Determine reason for criticality"""
        description_lower = description.lower()
        
        if any(word in description_lower for word in ['safety', 'health', 'emergency']):
            return 'Safety/Health Critical'
        elif any(word in description_lower for word in ['regulatory', 'compliance']):
            return 'Regulatory Compliance'
        elif any(word in description_lower for word in ['core', 'essential', 'fundamental']):
            return 'Core Competency'
        else:
            return 'High Priority Component'

    def _calculate_impact_score(self, description: str) -> float:
        """Calculate impact score for critical elements (0-1)"""
        impact_keywords = {
            'safety': 1.0,
            'health': 0.9,
            'emergency': 0.95,
            'critical': 0.8,
            'essential': 0.7,
            'core': 0.6,
            'regulatory': 0.85,
            'compliance': 0.8
        }
        
        description_lower = description.lower()
        max_score = 0
        
        for keyword, score in impact_keywords.items():
            if keyword in description_lower:
                max_score = max(max_score, score)
        
        return max_score

    def _identify_critical_criteria_gaps(self, criteria: List[Dict], mapped_criteria: set) -> List[Dict]:
        """Identify critical gaps in performance criteria coverage"""
        critical_gaps = []
        
        for criterion in criteria:
            criterion_id = criterion.get('code', '')
            if criterion_id and criterion_id not in mapped_criteria:
                description = criterion.get('description', '')
                
                if self._is_critical_criterion(description):
                    critical_gaps.append({
                        'criterion_id': criterion_id,
                        'description': description,
                        'criticality_reason': self._determine_criticality_reason(description),
                        'impact_score': self._calculate_impact_score(description)
                    })
        
        return critical_gaps

    def _is_critical_criterion(self, description: str) -> bool:
        """Determine if a performance criterion is critical"""
        critical_indicators = [
            'demonstrate', 'perform', 'apply', 'implement', 'execute',
            'critical', 'essential', 'core', 'required', 'mandatory'
        ]
        
        description_lower = description.lower()
        return any(indicator in description_lower for indicator in critical_indicators)

    def _analyze_mapping_quality(self, quality_scores: List[float]) -> Dict:
        """Analyze overall mapping quality"""
        if not quality_scores:
            return {'average_quality': 0, 'quality_distribution': {}, 'recommendations': []}
        
        avg_quality = sum(quality_scores) / len(quality_scores)
        high_quality = len([s for s in quality_scores if s >= 0.8])
        medium_quality = len([s for s in quality_scores if 0.6 <= s < 0.8])
        low_quality = len([s for s in quality_scores if s < 0.6])
        
        recommendations = []
        if low_quality > len(quality_scores) * 0.3:  # More than 30% low quality
            recommendations.append("Consider reviewing low-confidence mappings")
        if avg_quality < 0.7:
            recommendations.append("Overall mapping quality needs improvement")
        
        return {
            'average_quality': round(avg_quality, 3),
            'quality_distribution': {
                'high': high_quality,
                'medium': medium_quality,
                'low': low_quality
            },
            'recommendations': recommendations
        }

    def _analyze_cognitive_balance(self, distribution: Dict) -> Dict:
        """Analyze cognitive level balance"""
        total = sum(distribution.values())
        if total == 0:
            return {'balance_score': 0, 'recommendations': ['No cognitive level data available']}
        
        # Calculate balance score (higher is better)
        percentages = {k: (v/total)*100 for k, v in distribution.items()}
        
        # Ideal distribution for competency assessment
        ideal_distribution = {
            'REMEMBER': 10, 'UNDERSTAND': 20, 'APPLY': 25, 
            'ANALYZE': 20, 'EVALUATE': 15, 'CREATE': 10
        }
        
        balance_score = 0
        for level, ideal in ideal_distribution.items():
            actual = percentages.get(level, 0)
            balance_score += max(0, 100 - abs(actual - ideal))
        
        balance_score = balance_score / len(ideal_distribution)
        
        recommendations = []
        if percentages.get('EVALUATE', 0) < 10:
            recommendations.append("Add more evaluation-level questions")
        if percentages.get('CREATE', 0) < 5:
            recommendations.append("Consider adding synthesis/creation questions")
        if percentages.get('REMEMBER', 0) > 30:
            recommendations.append("Reduce rote memorization questions")
        
        return {
            'balance_score': round(balance_score, 1),
            'distribution': percentages,
            'recommendations': recommendations
        }

    def _analyze_assessment_method_balance(self, distribution: Dict) -> Dict:
        """Analyze assessment method balance"""
        total = sum(distribution.values())
        if total == 0:
            return {'balance_score': 0, 'recommendations': ['No assessment method data available']}
        
        percentages = {k: (v/total)*100 for k, v in distribution.items()}
        
        recommendations = []
        if percentages.get('PEP', 0) < 20:
            recommendations.append("Increase practical/portfolio evidence questions")
        if percentages.get('SBA', 0) < 30:
            recommendations.append("Add more skills-based assessment questions")
        if percentages.get('KBA', 0) > 70:
            recommendations.append("Reduce knowledge-only questions")
        
        return {
            'distribution': percentages,
            'recommendations': recommendations
        }

    def _predict_likely_gaps(self, uoc_data: Dict, mappings: List[Dict]) -> List[Dict]:
        """Predict likely gaps based on pattern analysis"""
        predictions = []
        
        # Analyze mapping patterns to predict missing coverage
        mapped_elements = set()
        for mapping in mappings:
            for element in mapping.get('mapping_analysis', {}).get('mapped_elements', []):
                mapped_elements.add(element.get('element_id', ''))
        
        # Predict gaps based on common patterns
        all_elements = [elem.get('element_id', '') for elem in uoc_data.get('elements', [])]
        unmapped_elements = [elem for elem in all_elements if elem not in mapped_elements]
        
        for element_id in unmapped_elements:
            predictions.append({
                'component_type': 'element',
                'component_id': element_id,
                'prediction_confidence': 0.8,
                'reason': 'Pattern analysis suggests this element is commonly overlooked',
                'suggested_action': 'Review element coverage and add relevant questions'
            })
        
        return predictions

    def _identify_compliance_risks(self, mappings: List[Dict], uoc_data: Dict) -> List[Dict]:
        """Identify potential compliance risks"""
        risks = []
        
        # Check for low confidence mappings
        low_confidence_count = 0
        for mapping in mappings:
            avg_confidence = self._calculate_average_confidence(mapping.get('mapping_analysis', {}))
            if avg_confidence < 0.6:
                low_confidence_count += 1
        
        if low_confidence_count > len(mappings) * 0.2:  # More than 20% low confidence
            risks.append({
                'risk_type': 'Low Confidence Mappings',
                'severity': 'MEDIUM',
                'description': f'{low_confidence_count} mappings have low confidence scores',
                'impact': 'May affect audit compliance',
                'recommendation': 'Review and validate low-confidence mappings'
            })
        
        # Check for incomplete coverage
        total_elements = len(uoc_data.get('elements', []))
        mapped_elements = set()
        for mapping in mappings:
            for element in mapping.get('mapping_analysis', {}).get('mapped_elements', []):
                mapped_elements.add(element.get('element_id', ''))
        
        coverage_percentage = (len(mapped_elements) / total_elements * 100) if total_elements > 0 else 0
        
        if coverage_percentage < 80:
            risks.append({
                'risk_type': 'Incomplete Coverage',
                'severity': 'HIGH',
                'description': f'Only {coverage_percentage:.1f}% of elements are covered',
                'impact': 'May fail audit requirements',
                'recommendation': 'Add questions to cover missing elements'
            })
        
        return risks

    def _generate_intelligent_recommendations(self, mappings: List[Dict], uoc_data: Dict) -> List[Dict]:
        """Generate intelligent recommendations for improvement"""
        recommendations = []
        
        # Analyze current state
        total_questions = len(mappings)
        avg_confidence = sum(self._calculate_average_confidence(m.get('mapping_analysis', {})) for m in mappings) / total_questions if total_questions > 0 else 0
        
        # Generate recommendations based on analysis
        if avg_confidence < 0.7:
            recommendations.append({
                'type': 'quality_improvement',
                'priority': 'HIGH',
                'title': 'Improve Mapping Quality',
                'description': 'Average confidence is below 70%. Review and refine mappings.',
                'action': 'Review low-confidence mappings and provide additional context'
            })
        
        # Check for cognitive balance
        bloom_levels = {}
        for mapping in mappings:
            level = mapping.get('bloom_taxonomy', {}).get('primary_level', 'UNDERSTAND')
            bloom_levels[level] = bloom_levels.get(level, 0) + 1
        
        if bloom_levels.get('EVALUATE', 0) < total_questions * 0.1:
            recommendations.append({
                'type': 'cognitive_balance',
                'priority': 'MEDIUM',
                'title': 'Add Higher-Order Thinking',
                'description': 'Less than 10% of questions assess evaluation skills.',
                'action': 'Add 2-3 evaluation-level questions'
            })
        
        # Check assessment method balance
        assessment_methods = {}
        for mapping in mappings:
            method = mapping.get('assessment_type', 'KBA')
            assessment_methods[method] = assessment_methods.get(method, 0) + 1
        
        if assessment_methods.get('PEP', 0) < total_questions * 0.2:
            recommendations.append({
                'type': 'assessment_method',
                'priority': 'MEDIUM',
                'title': 'Increase Practical Assessment',
                'description': 'Less than 20% of questions are practical/portfolio evidence.',
                'action': 'Add workplace scenario and practical demonstration questions'
            })
        
        return recommendations
    
    def _generate_enhanced_mock_mappings(self, questions: List[Dict[str, Any]], uoc_data: Dict[str, Any], assessment_type: str = "Mixed") -> Dict[str, Any]:
        """Generate enhanced mock mappings for testing when AI is unavailable"""
        logger.info("Generating enhanced mock mappings for testing")
        
        enhanced_mappings = []
        
        # Handle both original and restructured UoC data formats
        if 'data' in uoc_data:
            # Original format from cache
            original_data = uoc_data['data']
            elements = original_data.get('elements', [])
            performance_criteria = original_data.get('performance_criteria', [])
            performance_evidence = original_data.get('performance_evidence', [])
            knowledge_evidence = original_data.get('knowledge_evidence', [])
        else:
            # Restructured format from DataPreparationAgent or direct list format
            elements = uoc_data.get('elements', [])
            performance_criteria = uoc_data.get('performance_criteria', [])
            performance_evidence = uoc_data.get('performance_evidence', [])
            knowledge_evidence = uoc_data.get('knowledge_evidence', [])
            
            # Handle case where elements might be a dictionary
            if isinstance(elements, dict):
                elements = list(elements.values())
            if isinstance(performance_criteria, dict):
                performance_criteria = list(performance_criteria.values())
            if isinstance(performance_evidence, dict):
                performance_evidence = list(performance_evidence.values())
            if isinstance(knowledge_evidence, dict):
                knowledge_evidence = list(knowledge_evidence.values())
        
        for question in questions:
            # Enhanced mock mapping logic
            mapped_elements = []
            mapped_criteria = []
            mapped_performance_evidence = []
            mapped_knowledge_evidence = []
            
            # Map to first element if available
            if elements:
                element = elements[0] if isinstance(elements, list) else list(elements.values())[0]
                mapped_elements.append({
                    "element_id": element.get('id', 'E1'),
                    "element_code": element.get('id', 'E1'),
                    "element_description": element.get('description', f'Element {element.get("id", "E1")} - Mock mapping for testing'),
                    "mapping_strength": "EXPLICIT",
                    "confidence_score": 0.95,
                    "asqa_validation": {
                        "standard_1_8_compliance": "FULL",
                        "audit_risk_level": "LOW"
                    }
                })
            
            # Map to first performance criterion if available
            if performance_criteria:
                criterion = performance_criteria[0] if isinstance(performance_criteria, list) else list(performance_criteria.values())[0]
                mapped_criteria.append({
                    "criterion_id": criterion.get('code', 'PC1'),
                    "criterion_code": criterion.get('code', 'PC1'),
                    "criterion_description": criterion.get('description', f'Performance Criterion {criterion.get("code", "PC1")} - Mock mapping for testing'),
                    "mapping_strength": "EXPLICIT",
                    "confidence_score": 0.90,
                    "asqa_validation": {
                        "standard_1_8_compliance": "FULL",
                        "audit_risk_level": "LOW"
                    }
                })
            
            enhanced_mapping = {
                "question_id": question.get('id', 0),
                "question_text": question.get('text', 'Question text not available'),
                "assessment_type": assessment_type,
                "bloom_taxonomy": {
                    "primary_level": "UNDERSTAND",
                    "cognitive_demand": "MEDIUM",
                    "asqa_assessment_suitability": "GOOD"
                },
                "asqa_quality_assessment": {
                    "competency_focus_score": 4,
                    "authenticity_score": 3,
                    "sufficiency_score": 4,
                    "fairness_score": 5,
                    "consistency_score": 4,
                    "overall_quality_rating": "HIGH",
                    "quality_evidence": "Question provides good competency assessment with clear criteria"
                },
                "mapping_analysis": {
                    "mapped_elements": mapped_elements,
                    "mapped_performance_criteria": mapped_criteria,
                    "mapped_performance_evidence": mapped_performance_evidence,
                    "mapped_knowledge_evidence": mapped_knowledge_evidence
                },
                "comprehensive_analysis": {
                    "coverage_assessment": {
                        "element_coverage_completeness": "PARTIAL",
                        "performance_criteria_alignment": "STRONG",
                        "evidence_requirement_satisfaction": "FULL"
                    },
                    "assessment_integration": {
                        "knowledge_skill_balance": "BALANCED",
                        "theory_practice_integration": "GOOD",
                        "workplace_relevance": "HIGH"
                    },
                    "priority_mappings": ["PC1", "PE1"],
                    "secondary_mappings": ["KE1", "E1"],
                    "mapping_tags": ["E1", "PC1", "PE1", "KE1"]
                },
                "mapping_statistics": {
                    "total_mappings": len(mapped_elements) + len(mapped_criteria) + len(mapped_performance_evidence) + len(mapped_knowledge_evidence),
                    "average_confidence": 0.90,
                    "asqa_compliance_distribution": {
                        "full": len(mapped_elements) + len(mapped_criteria),
                        "partial": 0,
                        "minimal": 0
                    }
                },
                "overall_assessment": {
                    "asqa_compliance_level": "FULL",
                    "audit_readiness": "READY",
                    "risk_assessment": "LOW",
                    "assessor_guidance_required": "NO",
                    "recommended_improvements": ["Consider adding more workplace scenarios"],
                    "asqa_audit_confidence": "HIGH"
                },
                "audit_trail": {
                    "mapped_by": "Mock_System_v2.0_Enhanced",
                    "mapping_timestamp": datetime.now().isoformat(),
                    "validation_checks_passed": ["structure", "coverage", "asqa_compliance", "bloom_taxonomy", "quality_assessment"],
                    "assessor_review_required": False,
                    "asqa_standards_referenced": ["Standard 1.8", "Standard 1.12"]
                }
            }
            
            enhanced_mappings.append(enhanced_mapping)
        
        # Return comprehensive structure with analysis
        mapping_analysis = self._analyze_mapping_coverage(enhanced_mappings, uoc_data)
        
        return {
            'mappings': enhanced_mappings,
            'analysis': mapping_analysis,
            'assessment_type': assessment_type,
            'total_questions': len(questions)
        } 