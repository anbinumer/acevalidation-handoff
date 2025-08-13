# AI-Aided Post-Validation & Mapping System for RTO ASQA Audits
## Product Requirements Document (PRD) - MVP

**Version**: 1.0  
**Date**: January 2025  
**Status**: Ready for Implementation  
**Development Time**: 4-6 hours

---

## Executive Summary

The AI-Aided Post-Validation & Mapping System is designed specifically for **Registered Training Organizations (RTOs)** preparing for **ASQA (Australian Skills Quality Authority) audits**. The MVP automates assessment question mapping to Units of Competency (UoC) components and facilitates post-validation moderation by subject matter experts, ensuring audit compliance and reducing manual mapping effort.

## Problem Statement

RTOs undergoing ASQA audits face significant challenges:
- **Manual mapping burden**: Assessors spend hours mapping assessment questions to UoC performance criteria, elements, and evidence requirements
- **Inconsistent mapping quality**: Different validators may map the same questions differently
- **Audit trail requirements**: ASQA requires clear documentation of assessment validation processes
- **Time constraints**: Limited time between assessment development and audit deadlines
- **Compliance risk**: Poorly mapped assessments can result in audit non-compliance

## Solution Overview

A computer-assisted system that:
1. **Fetches UoC components** from training.gov.au automatically
2. **Extracts questions** from assessment documents (DOCX/PDF)
3. **Maps questions to UoC components** using computer-assisted analysis with rationale
4. **Facilitates validator review** through sequential validation workflow
5. **Maintains audit trail** of all mapping decisions and validator feedback

## Target Users

**Primary Users**: RTO Assessment Validators
- **Subject Matter Experts (SMEs)**: Industry practitioners validating technical accuracy
- **Educational Experts**: Qualified trainers ensuring pedagogical soundness  
- **Compliance Officers**: RTO staff ensuring ASQA requirements are met
- **Training Managers**: Overseeing validation processes and audit preparation

**User Context**:
- Processing 5-15 assessments per audit cycle
- Working under tight audit preparation deadlines
- Require clear audit documentation trail
- May work asynchronously across different time zones

## Goals & Success Metrics

### Primary Goals
- **Speed**: Reduce mapping time from 2-4 hours to 30-45 minutes per assessment
- **Quality**: Improve mapping consistency and accuracy across validators
- **Compliance**: Generate audit-ready documentation automatically
- **Efficiency**: Enable parallel validation by multiple experts

### Key Performance Indicators (KPIs)
- **Mapping Accuracy**: 90%+ computer-generated mappings accepted or minimally modified
- **Time Reduction**: 70%+ reduction in manual mapping time
- **Validator Satisfaction**: 4.2+/5.0 rating for usefulness
- **Audit Readiness**: 100% of processed assessments have complete audit trail

### MVP Success Criteria
- [ ] Successfully processes real HLTINF006 assessment files
- [ ] Generates mappings for KBA, SBA, and PEP assessment types
- [ ] Supports sequential validator review workflow
- [ ] Produces audit-compliant documentation output
- [ ] Completes full workflow in under 1 hour per assessment

## Functional Requirements

### Core Features (Must Have)

#### 1. UoC Component Management
- **Auto-fetch from training.gov.au**: Input UoC code (e.g., `CHCDIV001`, `HLTINF006`)
- **Component extraction**: Elements, Performance Criteria (PC), Performance Evidence (PE), Knowledge Evidence (KE)
- **Local caching**: Store fetched UoC data to avoid repeated API calls
- **URL format**: `https://training.gov.au/training/details/{UoC}/unitdetails`

#### 2. Assessment Processing
- **Multi-format support**: Upload `.docx` and `.pdf` assessment files
- **Assessment categorization**: Mark as KBA (Knowledge-Based Assessment), SBA (Skills-Based Assessment), or PEP (Portfolio of Evidence Program)
- **Question extraction**: Parse questions only, ignore rubrics and existing mapping tables
- **Question numbering**: Maintain original document question numbering
- **Question typing**: Identify MCQ, short answer, scenario-based, practical demonstration questions

#### 3. Computer-Assisted Mapping Engine
- **Intelligent mapping**: Map each question to relevant PC, PE, KE, or Element components
- **Mapping strength**: Assign confidence levels (High/Medium/Low)
- **Rationale generation**: System provides explanation for each mapping decision
- **Unmapped identification**: Flag questions that cannot be mapped and UoC components not covered
- **Tag assignment**: Generate mapping tags (e.g., PE1.1, KE2.3, PC3.4)

#### 4. Sequential Validator Review Interface
- **Dashboard layout**: 
  - Left panel: UoC elements and components hierarchy
  - Right panel: Question cards with computer-generated mappings and tags
- **Validator actions**: Accept, edit, or delete computer-generated mappings
- **Comment threading**: Discussion-style comments per question
- **Sequential visibility**: Validators only see previous feedback after completing their own review
- **Role attribution**: Track validator role (SME, Industry Expert, Educational Expert)

#### 5. Audit Trail & Documentation
- **Complete logging**: All validator actions timestamped and attributed
- **Filtering capabilities**: Filter by validator, mapping tag, question type
- **Export functionality**: Generate audit-ready reports and documentation
- **Version control**: Track changes to mappings over time

### Nice to Have (Future Releases)
- Integration with Learning Management Systems (LMS)
- Bulk processing of multiple assessments
- Custom UoC component templates
- Advanced analytics and mapping insights
- SSO integration for larger RTO teams

## Technical Requirements

### Architecture & Technology Stack
- **AI Framework**: Cursor AI for development assistance
- **LLM Provider**: Google Gemini 2.0 Flash via cURL API
- **Development Approach**: Modular Agentic Workflow with PocketFlow principles
- **Backend**: Python with modular agent architecture
- **Frontend**: Simple web UI (HTML/JavaScript)
- **Storage**: Local file system or SQLite for MVP
- **Document Processing**: python-docx, PyMuPDF for file parsing

### Agent Architecture
```
FetchAgent → ExtractAgent → MappingAgent → ValidationAgent → ThreadAgent
     ↓            ↓             ↓              ↓             ↓
  UoC Cache → Questions → AI Mappings → Validator UI → Audit Trail
```

### Performance Requirements
- **UoC Fetch**: Complete within 5 seconds
- **Question Extraction**: Process 50+ questions within 10 seconds
- **AI Mapping**: Generate mappings within 30 seconds per assessment
- **Concurrent Users**: Support 3-5 validators simultaneously
- **File Size**: Handle assessment documents up to 5MB

### Security & Compliance
- **Data Privacy**: No persistent storage of sensitive assessment content
- **Audit Compliance**: Full traceability of all mapping decisions
- **Access Control**: Basic role-based access (SME, Educational Expert, Compliance)
- **Data Integrity**: Immutable audit trail once validator review is complete

## User Experience Requirements

### Human-AI Interaction Design
1. **Transparency**: Clear indication of AI-generated mappings vs. human modifications
2. **Explainability**: Rationale provided for every AI mapping decision
3. **Control**: Validators can override any AI decision with full edit capabilities
4. **Trust**: Confidence levels and uncertainty indicators for AI suggestions
5. **Efficiency**: Streamlined workflow optimized for audit preparation timelines

### Validator Workflow
1. **Setup**: Upload assessment file and specify UoC code and assessment type
2. **Processing**: System fetches UoC components and extracts questions
3. **AI Mapping**: Review AI-generated mappings with rationale
4. **Validation**: Accept, modify, or reject mappings with comments
5. **Collaboration**: Sequential review by additional validators
6. **Documentation**: Export audit-ready mapping documentation

## Implementation Plan

### Agent Development Tasks

#### Phase 1: Core Infrastructure (2 hours)
- [ ] **FetchAgent**: Scrape UoC components from training.gov.au
- [ ] **ExtractAgent**: Parse DOCX/PDF files and extract questions
- [ ] **Storage setup**: Local caching system for UoC data
- [ ] **Basic web interface**: File upload and progress indicators

#### Phase 2: AI Integration (2 hours)
- [ ] **MappingAgent**: Integrate Gemini API for question mapping
- [ ] **Prompt engineering**: Optimize prompts for accurate UoC mapping
- [ ] **Rationale generation**: Ensure AI provides clear mapping explanations
- [ ] **Unmapped detection**: Identify questions/components that can't be mapped

#### Phase 3: Validation Interface (1.5 hours)
- [ ] **ValidationAgent**: Build dashboard with question cards
- [ ] **Comment threading**: Implement discussion system per question
- [ ] **Sequential review**: Gate visibility of previous validator feedback
- [ ] **Role attribution**: Track and display validator roles and actions

#### Phase 4: Testing & Polish (0.5 hours)
- [ ] **End-to-end testing**: Use real HLTINF006 + sample KBA file
- [ ] **UI refinement**: Apply HCD principles for validator experience
- [ ] **Export functionality**: Generate audit documentation
- [ ] **Performance optimization**: Ensure sub-30-second mapping times

### Test Cases & Validation

| Test Case | Action | Expected Result |
|-----------|---------|-----------------|
| **TC1** | Input `HLTINF006` UoC code | Fetch and cache all PC, PE, KE, Elements |
| **TC2** | Upload KBA DOCX file | Extract numbered questions with categorization |
| **TC3** | Run AI mapping on 20 questions | Generate mappings with High/Med/Low confidence |
| **TC4** | Validator A completes review | Validator B sees A's feedback after own completion |
| **TC5** | Question unmappable to UoC | AI provides clear rationale for exclusion |
| **TC6** | Export audit documentation | Generate compliant mapping report |

## Risk Assessment & Mitigation

### Technical Risks
- **Training.gov.au availability**: Site downtime or structure changes
  - *Mitigation*: Robust error handling and manual UoC input fallback
- **Gemini API limits**: Rate limiting or service disruption
  - *Mitigation*: Retry logic and batch processing optimization
- **Document parsing complexity**: Complex formatting or corrupted files
  - *Mitigation*: Multiple parsing libraries and manual text input option

### Business Risks
- **Audit non-compliance**: Incorrect mappings affecting ASQA audit
  - *Mitigation*: Clear disclaimers, human oversight requirements, validation workflow
- **User adoption**: Validators resistant to AI-assisted workflow
  - *Mitigation*: Transparent AI reasoning, full human control, training materials

## File Structure & Development Organization

```
rto-validation-mvp/
├── agents/
│   ├── fetch_agent.py          # UoC component scraping
│   ├── extract_agent.py        # Question parsing from docs
│   ├── mapping_agent.py        # AI mapping with Gemini
│   ├── validation_agent.py     # Validator review interface
│   └── thread_agent.py         # Comment management
├── ui/
│   ├── upload.html             # File upload interface
│   ├── dashboard.html          # Main validation dashboard
│   └── question_card.html      # Individual question review
├── storage/
│   ├── uoc_cache.json          # Cached UoC components
│   ├── assessments/            # Uploaded assessment files
│   └── mappings/               # Generated mappings and feedback
├── utils/
│   ├── doc_parser.py           # Document processing utilities
│   └── audit_export.py         # Generate audit reports
├── main.py                     # Application entry point
├── config.py                   # Configuration and API keys
└── README.md                   # Setup and usage instructions
```

## Success Measurement & Iteration

### Immediate Feedback Loops
- **Mapping accuracy tracking**: Percentage of AI mappings accepted vs. modified
- **Validator time logs**: Before/after implementation comparison
- **User feedback surveys**: Post-validation experience rating
- **System performance metrics**: Processing times and error rates

### Post-MVP Roadmap
1. **Integration capabilities**: LMS connectivity and bulk processing
2. **Advanced AI features**: Custom model training on RTO-specific data
3. **Collaboration enhancements**: Real-time collaborative validation
4. **Analytics dashboard**: Validation trends and quality insights
5. **Mobile support**: Tablet-optimized interface for field validators

---

## Appendices

### Appendix A: Sample UoC Structure (HLTINF006)
```json
{
  "code": "HLTINF006",
  "title": "Apply basic principles and practices of infection prevention and control",
  "elements": [
    {
      "id": "1",
      "description": "Identify and assess risks",
      "performance_criteria": ["1.1", "1.2", "1.3"],
      "performance_evidence": ["PE1.1", "PE1.2"],
      "knowledge_evidence": ["KE1.1", "KE1.2"]
    }
  ]
}
```

### Appendix B: AI Mapping Prompt Template
```
You are an expert in Australian VET competency mapping. Map this assessment question to the appropriate UoC components:

UoC: {uoc_code} - {uoc_title}
Question: {question_text}
Assessment Type: {assessment_type}

Available components:
- Elements: {elements}
- Performance Criteria: {performance_criteria}
- Performance Evidence: {performance_evidence}
- Knowledge Evidence: {knowledge_evidence}

Provide mapping with:
1. Mapped components (PC/PE/KE/Element codes)
2. Confidence level (High/Medium/Low)
3. Rationale (2-3 sentences explaining the mapping)
```

### Appendix C: Compliance Requirements
- **ASQA Standards**: Full traceability of assessment validation process
- **AQF Requirements**: Evidence of systematic assessment review
- **Audit Documentation**: Timestamped record of all validation decisions
- **Quality Assurance**: Multiple expert review and sign-off process

---

**Document Control**
- **Author**: Development Team  
- **Target Users**: RTO Assessment Teams, ASQA Auditors
- **Implementation Timeline**: 4-6 hours development + 2 hours testing
- **Next Review**: Post-implementation feedback session 