# Assessment Validator - Agent Guidelines

## 🎯 **Quick Reference for Computer-Assisted Agents**

### **Core Principles to Follow**
1. **Human-Centered Design (HCD)**: Always prioritize user experience
2. **Human-to-AI (H2A) Collaboration**: Make AI decisions transparent and controllable
3. **Accessibility**: Ensure WCAG AA compliance, especially color contrast
4. **Progressive Disclosure**: Reveal information step-by-step

### **User Journey (Always Follow This Order)**
1. **Step 1**: User enters UoC code → System fetches from training.gov.au
2. **Step 2**: User uploads assessment → System processes against UoC data
3. **Step 3**: User validates AI mappings → System saves audit trail
4. **Step 4**: User exports reports → System generates audit-ready documents

### **Technical Stack**
- **Frontend**: HTML5, CSS3, JavaScript ES6+
- **Backend**: Python Flask, RESTful APIs
- **AI**: Gemini API for LLM operations
- **Storage**: JSON files for session data and caching

### **File Structure**
```
rto-validation-mvp/
├── main.py                 # Main Flask application
├── agents/                 # AI agent modules
│   ├── fetch_agent.py     # Web search + LLM extraction
│   ├── extract_agent.py   # Document question extraction
│   ├── mapping_agent.py   # AI mapping generation
│   └── validation_agent.py # Validation workflow
├── templates/             # HTML templates
│   ├── index.html        # Step 1: UoC entry
│   ├── upload_assessment.html # Step 2: File upload
│   └── dashboard.html    # Step 3: Validation
├── utils/                # Utility modules
│   └── audit_export.py   # Report generation
└── storage/              # Data storage
    ├── assessments/      # Uploaded files
    ├── mappings/         # Session data
    └── cache/           # UoC data cache
```

### **Design System Rules**
- **Colors**: Primary gradient #667eea to #764ba2
- **Typography**: Segoe UI font stack
- **Cards**: White background, 15px border-radius, shadow
- **Buttons**: Gradient background, hover transform
- **Forms**: 2px border, focus state with primary color

### **API Endpoints**
- `GET /` - Step 1: UoC entry form
- `POST /fetch-uoc` - Fetch UoC data from training.gov.au
- `GET /upload-assessment` - Step 2: File upload form
- `POST /process-assessment` - Process uploaded file
- `GET /dashboard/<session_id>` - Step 3: Validation dashboard
- `POST /api/update_mapping` - Update mapping validation
- `GET /api/export/<session_id>` - Export audit report
- `GET /test` - Test all agents

### **Agent Responsibilities**

#### **FetchAgent**
- **Purpose**: Fetch UoC data from training.gov.au with intelligent caching and extraction
- **Input**: UoC code (e.g., "HLTINF006")
- **Output**: Structured UoC data (elements, performance criteria, evidence)
- **Method**: Cache-first strategy with web search + LLM extraction
- **Intelligent Extraction Rules**:
  - **Elements & PCs**: Literal extraction (preserve exact numbering and structure)
  - **KE & PE**: Intelligent grouping into broad, assessable categories
  - **Ignore**: Introductory phrases like "This includes knowledge of:"
  - **Target**: 8-12 KE categories, 5-8 PE categories
  - **Quality**: Substantial categories for assessment mapping
- **Cache**: Version-robust caching with audit trail (fetched_timestamp, source_url, data_hash)
- **TTL**: Configurable cache invalidation (3-6 months default)
- **Conflict Resolution**: Track new snapshots rather than deleting historical data

#### **ExtractAgent**
- **Purpose**: Extract questions from assessment documents
- **Input**: File path, assessment type
- **Output**: List of questions with metadata
- **Support**: PDF, DOCX, DOC files

#### **MappingAgent**
- **Purpose**: Generate AI mappings between questions and UoC elements
- **Input**: Questions, UoC data, assessment type
- **Output**: Mappings with confidence scores
- **Method**: LLM-powered semantic matching with prompt caching
- **Optimization**: Static prompt caching to reduce token usage by 50%
- **Audit**: Complete chain-of-evidence for ASQA compliance

#### **ValidationAgent**
- **Purpose**: Handle validation workflow and audit trail
- **Input**: Session data, user actions
- **Output**: Updated mappings with validation history
- **Features**: Multi-role validation, audit trail, export
- **State Management**: Incremental state awareness with checkpoints
- **Multi-Validator**: Support for seamless validator handoffs
- **Conflict Resolution**: Track changes without losing audit trail

### **Error Handling Guidelines**
1. **User-Friendly Messages**: Clear, actionable error descriptions
2. **Graceful Degradation**: System works even with partial failures
3. **Recovery Options**: Suggest fixes and alternatives
4. **Logging**: Detailed logs for debugging

### **Token Management & Context Optimization**
1. **Cache-First Strategy**: Always check cache before making LLM calls
2. **Prompt Caching**: Cache static prompt components to reduce token usage
3. **Content Truncation**: Limit page content to 8000 characters for LLM processing
4. **Focused Extraction**: Use targeted prompts rather than sending entire page content
5. **Batch Processing**: Group related operations to minimize API calls
6. **maxOutputTokens**: Set to 4000 for comprehensive but controlled responses
7. **Temperature**: Use 0.1 for consistent, structured extraction
8. **Audit Trail**: Track token usage for cost optimization

### **Performance Guidelines**
1. **Fast Loading**: Pages load in < 3 seconds
2. **Responsive**: Interface responds immediately to user actions
3. **Intelligent Caching**: Cache-first strategy with version tracking
4. **Token Optimization**: Reduce LLM costs by 50% through prompt caching
5. **Progress Indicators**: Show loading states for all operations
6. **State Persistence**: Seamless continuation across validator sessions

### **Security Considerations**
1. **Input Validation**: Validate all user inputs
2. **File Upload**: Secure file handling and validation
3. **Session Management**: Secure session handling
4. **API Security**: Rate limiting and error handling

### **Testing Requirements**
1. **Unit Tests**: Test individual agent functions
2. **Integration Tests**: Test complete workflows
3. **User Acceptance**: Test with real RTO scenarios
4. **Performance Tests**: Ensure fast response times

### **Documentation Standards**
1. **Code Comments**: Explain business logic, not syntax
2. **API Documentation**: Clear endpoint descriptions
3. **User Guides**: Step-by-step instructions
4. **Troubleshooting**: Common issues and solutions

### **Quality Assurance**
1. **Accessibility**: WCAG AA compliance
2. **Responsive Design**: Works on all devices
3. **Error Recovery**: Graceful handling of failures
4. **User Satisfaction**: High usability scores

---

## 🚨 **Critical Rules for Agents**

### **Always Follow These Rules**
1. **Never break the user journey flow** - Steps must be sequential
2. **Always provide feedback** - Users must know what's happening
3. **Always handle errors gracefully** - Never crash the application
4. **Always maintain audit trails** - All decisions must be logged
5. **Always prioritize accessibility** - WCAG AA compliance is mandatory
6. **Always check cache first** - Reduce API calls and improve performance
7. **Always preserve state** - Support multi-validator workflows seamlessly
8. **Always optimize tokens** - Use prompt caching to reduce LLM costs

### **When Making Changes**
1. **Test the complete workflow** - End-to-end testing required
2. **Update documentation** - Keep docs in sync with changes
3. **Consider backward compatibility** - Don't break existing functionality
4. **Follow the design system** - Maintain visual consistency

### **When Adding Features**
1. **Follow the established patterns** - Use existing components
2. **Consider the user journey** - How does this fit into the workflow?
3. **Plan for scalability** - Will this work with larger datasets?
4. **Document the changes** - Update relevant documentation

---

*This guide ensures all computer-assisted agents work consistently and maintain the high quality standards of the Assessment Validator project.* 