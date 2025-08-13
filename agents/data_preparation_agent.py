#!/usr/bin/env python3
"""
Data Preparation Agent
Structures and prepares UoC and assessment data for optimal AI processing
"""

import json
from typing import Dict, List, Any
from datetime import datetime

class DataPreparationAgent:
    """Agent that prepares structured data for AI mapping and validation"""
    
    def __init__(self):
        self.name = "DataPreparationAgent"
    
    def execute(self, uoc_data: Dict, questions: List[Dict], assessment_type: str) -> Dict:
        """
        Prepare structured data for AI processing
        
        Args:
            uoc_data: Raw UoC data from fetch_agent
            questions: Raw questions from extract_agent
            assessment_type: KBA, SBA, or PEP
            
        Returns:
            Structured data optimized for AI processing
        """
        print(f"🔧 DataPreparationAgent: Structuring data for {assessment_type} assessment")
        
        # Step 1: Structure UoC data for AI consumption
        structured_uoc = self._structure_uoc_data(uoc_data)
        
        # Step 2: Categorize and tag questions
        categorized_questions = self._categorize_questions(questions, assessment_type)
        
        # Step 3: Create mapping-ready data structure
        ai_ready_data = self._create_ai_ready_structure(structured_uoc, categorized_questions, assessment_type)
        
        return ai_ready_data
    
    def _structure_uoc_data(self, uoc_data: Dict) -> Dict:
        """Structure UoC data for optimal AI processing"""
        
        structured = {
            "metadata": {
                "uoc_code": uoc_data.get('uoc_code', ''),
                "title": uoc_data.get('title', ''),
                "total_elements": len(uoc_data.get('elements', [])),
                "total_performance_criteria": len(uoc_data.get('performance_criteria', [])),
                "total_performance_evidence": len(uoc_data.get('performance_evidence', [])),
                "total_knowledge_evidence": len(uoc_data.get('knowledge_evidence', []))
            },
            "elements": {},
            "performance_criteria": {},
            "performance_evidence": {},
            "knowledge_evidence": {},
            "mapping_targets": []
        }
        
        # Structure elements with their criteria
        for element in uoc_data.get('elements', []):
            element_id = element.get('id', '')
            structured['elements'][element_id] = {
                "description": element.get('description', ''),
                "performance_criteria": [],
                "mapping_opportunities": []
            }
        
        # Structure performance criteria by element
        for pc in uoc_data.get('performance_criteria', []):
            pc_code = pc.get('code', '')
            element_id = pc_code.split('.')[0] if '.' in pc_code else '1'
            
            pc_data = {
                "code": pc_code,
                "description": pc.get('description', ''),
                "element_id": element_id,
                "mapping_opportunities": []
            }
            
            structured['performance_criteria'][pc_code] = pc_data
            
            # Add to element's criteria list
            if element_id in structured['elements']:
                structured['elements'][element_id]['performance_criteria'].append(pc_data)
        
        # Structure evidence requirements
        for pe in uoc_data.get('performance_evidence', []):
            pe_code = pe.get('code', '')
            structured['performance_evidence'][pe_code] = {
                "code": pe_code,
                "description": pe.get('description', ''),
                "evidence_type": "performance",
                "mapping_opportunities": []
            }
        
        for ke in uoc_data.get('knowledge_evidence', []):
            ke_code = ke.get('code', '')
            structured['knowledge_evidence'][ke_code] = {
                "code": ke_code,
                "description": ke.get('description', ''),
                "evidence_type": "knowledge",
                "mapping_opportunities": []
            }
        
        # Create mapping targets (what the AI should map to)
        structured['mapping_targets'] = self._create_mapping_targets(structured)
        
        return structured
    
    def _categorize_questions(self, questions: List[Dict], assessment_type: str) -> Dict:
        """Categorize and tag questions for optimal mapping"""
        
        categorized = {
            "metadata": {
                "total_questions": len(questions),
                "assessment_type": assessment_type,
                "categorization_timestamp": datetime.now().isoformat()
            },
            "questions_by_type": {
                "knowledge_based": [],
                "performance_based": [],
                "mixed": [],
                "uncategorized": []
            },
            "questions_by_complexity": {
                "basic": [],
                "intermediate": [],
                "advanced": []
            },
            "questions_with_tags": []
        }
        
        for i, question in enumerate(questions):
            question_text = question.get('text', '').lower()
            
            # Determine question type
            question_type = self._determine_question_type(question_text, assessment_type)
            
            # Determine complexity
            complexity = self._determine_complexity(question_text)
            
            # Add tags
            tags = self._extract_tags(question_text)
            
            # Enhanced question structure
            enhanced_question = {
                "id": f"Q{i+1}",
                "original_text": question.get('text', ''),
                "question_type": question_type,
                "complexity": complexity,
                "tags": tags,
                "mapping_suggestions": [],
                "confidence_score": 0.0
            }
            
            # Add to appropriate categories
            categorized['questions_by_type'][question_type].append(enhanced_question)
            categorized['questions_by_complexity'][complexity].append(enhanced_question)
            categorized['questions_with_tags'].append(enhanced_question)
        
        return categorized
    
    def _determine_question_type(self, question_text: str, assessment_type: str) -> str:
        """Determine if question is knowledge-based, performance-based, or mixed"""
        
        knowledge_indicators = [
            'explain', 'describe', 'define', 'what is', 'list', 'identify',
            'theory', 'concept', 'knowledge', 'understand', 'know', 'state',
            'outline', 'summarize', 'compare', 'contrast', 'analyze'
        ]
        
        performance_indicators = [
            'demonstrate', 'perform', 'show', 'practice', 'apply',
            'practical', 'skill', 'procedure', 'technique', 'method',
            'complete', 'conduct', 'execute', 'carry out', 'implement'
        ]
        
        knowledge_score = sum(1 for indicator in knowledge_indicators if indicator in question_text)
        performance_score = sum(1 for indicator in performance_indicators if indicator in question_text)
        
        if knowledge_score > performance_score:
            return "knowledge_based"
        elif performance_score > knowledge_score:
            return "performance_based"
        else:
            return "mixed"
    
    def _determine_complexity(self, question_text: str) -> str:
        """Determine question complexity level"""
        
        basic_indicators = ['list', 'identify', 'state', 'name', 'what is']
        advanced_indicators = ['analyze', 'evaluate', 'critique', 'synthesize', 'design', 'create']
        
        if any(indicator in question_text for indicator in advanced_indicators):
            return "advanced"
        elif any(indicator in question_text for indicator in basic_indicators):
            return "basic"
        else:
            return "intermediate"
    
    def _extract_tags(self, question_text: str) -> List[str]:
        """Extract relevant tags from question text"""
        
        tags = []
        
        # Content area tags
        if any(word in question_text for word in ['safety', 'infection', 'hygiene']):
            tags.append('safety')
        if any(word in question_text for word in ['communication', 'interpersonal']):
            tags.append('communication')
        if any(word in question_text for word in ['documentation', 'record']):
            tags.append('documentation')
        if any(word in question_text for word in ['equipment', 'tools']):
            tags.append('equipment')
        if any(word in question_text for word in ['procedure', 'protocol']):
            tags.append('procedures')
        
        # Question format tags
        if '?' in question_text:
            tags.append('question')
        if any(word in question_text for word in ['scenario', 'case study']):
            tags.append('scenario')
        if any(word in question_text for word in ['multiple choice', 'mcq']):
            tags.append('multiple_choice')
        
        return tags
    
    def _create_mapping_targets(self, structured_uoc: Dict) -> List[Dict]:
        """Create prioritized mapping targets for AI"""
        
        targets = []
        
        # Priority 1: Performance Criteria (most specific)
        for pc_code, pc_data in structured_uoc['performance_criteria'].items():
            targets.append({
                "type": "performance_criteria",
                "code": pc_code,
                "description": pc_data['description'],
                "priority": "high",
                "element_id": pc_data['element_id'],
                "mapping_opportunities": []
            })
        
        # Priority 2: Knowledge Evidence (for KBA assessments)
        for ke_code, ke_data in structured_uoc['knowledge_evidence'].items():
            targets.append({
                "type": "knowledge_evidence",
                "code": ke_code,
                "description": ke_data['description'],
                "priority": "medium",
                "mapping_opportunities": []
            })
        
        # Priority 3: Performance Evidence (for SBA assessments)
        for pe_code, pe_data in structured_uoc['performance_evidence'].items():
            targets.append({
                "type": "performance_evidence",
                "code": pe_code,
                "description": pe_data['description'],
                "priority": "medium",
                "mapping_opportunities": []
            })
        
        # Priority 4: Elements (broadest level)
        for element_id, element_data in structured_uoc['elements'].items():
            targets.append({
                "type": "element",
                "code": element_id,
                "description": element_data['description'],
                "priority": "low",
                "mapping_opportunities": []
            })
        
        return targets
    
    def _create_ai_ready_structure(self, structured_uoc: Dict, categorized_questions: Dict, assessment_type: str) -> Dict:
        """Create final AI-ready data structure"""
        
        return {
            "metadata": {
                "preparation_timestamp": datetime.now().isoformat(),
                "assessment_type": assessment_type,
                "total_questions": categorized_questions['metadata']['total_questions'],
                "total_mapping_targets": len(structured_uoc['mapping_targets'])
            },
            "uoc_data": structured_uoc,
            "questions": categorized_questions,
            "mapping_instructions": self._generate_mapping_instructions(assessment_type),
            "validation_criteria": self._generate_validation_criteria(assessment_type)
        }
    
    def _generate_mapping_instructions(self, assessment_type: str) -> Dict:
        """Generate AI-specific mapping instructions"""
        
        if assessment_type == "KBA":
            return {
                "primary_focus": "knowledge_evidence",
                "secondary_focus": "performance_criteria",
                "mapping_strategy": "Match questions to knowledge requirements",
                "confidence_threshold": 0.7
            }
        elif assessment_type == "SBA":
            return {
                "primary_focus": "performance_evidence",
                "secondary_focus": "performance_criteria",
                "mapping_strategy": "Match simulation scenarios to performance requirements",
                "confidence_threshold": 0.8
            }
        elif assessment_type == "PEP":
            return {
                "primary_focus": "performance_evidence",
                "secondary_focus": "performance_criteria",
                "mapping_strategy": "Match workplace activities to performance requirements",
                "confidence_threshold": 0.8
            }
        else:  # Mixed
            return {
                "primary_focus": "balanced",
                "secondary_focus": "all_evidence_types",
                "mapping_strategy": "Match questions to appropriate evidence types",
                "confidence_threshold": 0.75
            }
    
    def _generate_validation_criteria(self, assessment_type: str) -> Dict:
        """Generate validation criteria for the assessment type"""
        
        return {
            "coverage_requirements": {
                "min_elements_covered": 0.8,  # 80% of elements
                "min_performance_criteria_covered": 0.7,  # 70% of PCs
                "min_evidence_covered": 0.6  # 60% of evidence requirements
            },
            "quality_requirements": {
                "min_question_quality": 0.6,
                "min_mapping_confidence": 0.7,
                "max_duplicate_mappings": 0.2  # Max 20% duplicate mappings
            },
            "assessment_type_specific": {
                "kba_focus": assessment_type == "KBA",
                "sba_focus": assessment_type == "SBA",
                "pep_focus": assessment_type == "PEP",
                "mixed_balance": assessment_type == "Mixed"
            }
        } 