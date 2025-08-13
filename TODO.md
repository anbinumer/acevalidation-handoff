# Assessment Validator - TODO List

## 🎨 **UI/UX Improvements (HCD & H2A Principles)**

### **Screen 1: UoC Code Entry (`index.html`)**

#### **1. Cognitive Load Reduction**
- [ ] **Add autocomplete for UoC codes**
  - Implement datalist with common UoC codes
  - Show full titles in suggestions (e.g., "HLTINF006 - Apply basic principles...")
  - Add help text: "💡 Start typing to see suggestions"
- [ ] **Enhanced AI transparency**
  - Add "AI Capabilities Preview" section
  - List what the AI will do: fetch data, extract elements, group evidence, etc.
  - Show confidence indicators for expected data quality

#### **2. Enhanced User Feedback**
- [ ] **Real-time validation**
  - Check UoC code format as user types
  - Show loading states with progress indicators
  - Better error messages with suggested fixes

### **Screen 2: Assessment Upload (`upload_assessment.html`)**

#### **3. Enhanced Assessment Type Selection** ✅ **COMPLETED**
- [x] **Manual assessment type selection**
  - Added radio buttons for KBA, SBA, PEP
  - Visual cards with icons and descriptions
  - Form validation for assessment type
- [x] **Improved user experience**
  - Clear descriptions for each assessment type
  - Visual feedback on selection
  - Better form flow and validation

#### **4. Enhanced File Upload Experience**
- [ ] **Rich file upload with preview**
  - Drag-and-drop zone with visual feedback
  - File preview with icon, name, and statistics
  - Show page count, word count, file size
  - Remove file button with confirmation
- [ ] **Better file validation**
  - Real-time file type checking
  - Size limit warnings
  - Content preview for supported formats

### **Screen 3: Question Review (`review_questions.html`)** ✅ **COMPLETED**

#### **5. Question Review Interface** ✅ **ENHANCED**
- [x] **Comprehensive question display**
  - Shows all extracted questions with metadata
  - Question type indicators (Knowledge, Performance, Mixed)
  - Complexity levels and tags
  - Interactive filtering by question type
- [x] **Assessment summary**
  - UoC code, assessment type, question count
  - Source document information
  - Clear navigation to next step
- [x] **Human-in-the-Loop (HITL) editing** ✅ **COMPLETED**
  - Edit question text inline
  - Delete incorrect extractions
  - Save changes with visual feedback
  - Maintains human control over AI decisions
- [x] **Intelligent flagging system** ✅ **COMPLETED**
  - Confidence scores (High/Medium/Low)
  - Flag suspicious extractions
  - Visual indicators for quality issues
  - Reasoning for each extraction

### **Screen 4: Validation Dashboard (`dashboard.html`)** ✅ **COMPLETED**

#### **6. Comprehensive Validation Interface** ✅ **COMPLETED**
- [x] **Dual-panel dashboard layout**
  - Left panel: Unit structure navigation
  - Right panel: Assessment items with mappings
  - Responsive design with collapsible sections
- [x] **Interactive unit structure navigation**
  - Hierarchical display of Elements, Performance Criteria, Knowledge Evidence
  - Collapsible sections with accordion behavior
  - Component filtering and selection
  - Mapping count indicators
- [x] **Assessment item display**
  - Question cards with full text and metadata
  - Mapping confidence indicators
  - Strength assessment (EXPLICIT/IMPLICIT/PARTIAL/WEAK)
  - ASQA compliance alignment
- [x] **Advanced filtering and search**
  - Search by question text
  - Filter by component type
  - Filter by mapping strength
  - Clear filter functionality
- [x] **Tabbed interface**
  - Assessment Items tab
  - Coverage Analysis tab
  - Compliance Review tab
- [x] **Modal detail views**
  - Question mapping details modal
  - Full question text and choices display
  - Complete mapping rationale
- [x] **Validation discussion system**
  - Add comments per question
  - Comment threading with roles
  - Agreement status tracking
  - Real-time comment updates

## 🚀 **Technical Improvements**

### **Performance & Optimization**
- [x] **BeautifulSoup import handling** ✅ **COMPLETED**
  - Added top-level import with HAS_BS4 flag
  - Graceful fallback when BeautifulSoup not available
- [x] **Rate limiting for API calls** ✅ **COMPLETED**
  - Added 0.5s delay to prevent API quota exhaustion
  - Improves system reliability and cost management
- [x] **Memory optimization** ✅ **COMPLETED**
  - Truncate page content > 10,000 characters
  - Prevents token limit issues and reduces API costs
- [x] **File size validation** ✅ **COMPLETED**
  - Added 16MB file size limit
  - Prevents server crashes from large files
  - Clear error messages for users
- [x] **Session cleanup** ✅ **COMPLETED**
  - Automatic cleanup of old session files (>24 hours)
  - Prevents disk space issues
  - Runs before each request
- [ ] **Implement autocomplete API**
  - Create endpoint for UoC code suggestions
  - Cache common UoC codes
  - Fuzzy search for partial matches
- [ ] **Enhanced caching strategy**
  - Cache UoC data with version tracking
  - Implement cache warming for popular UoCs
  - Add cache invalidation based on training.gov.au updates

### **AI Enhancement**
- [x] **Structured data preparation** ✅ **COMPLETED**
  - Created DataPreparationAgent for optimal AI processing
  - Categorizes questions by type and complexity
  - Structures UoC data with mapping targets
  - Provides AI-specific instructions and validation criteria
  - Updated to use correct VET assessment types: KBA, SBA, PEP
- [x] **Enhanced document extraction** ✅ **COMPLETED**
  - Fixed DOCX table extraction (was only reading paragraphs)
  - Now extracts text from both paragraphs and tables
  - Improved question detection from complex document formats
  - Resolved issue where 0 questions were being extracted
- [x] **Hierarchical question extraction** ✅ **COMPLETED**
  - Added support for main questions (1., 2., 3., etc.)
  - Added support for sub-questions (5.1, 5.2, 20.1, 20.2, etc.)
  - Proper grouping of main questions with their sub-questions
  - Enhanced UI to display hierarchical structure
- [x] **Question type classification** ✅ **COMPLETED**
  - Enhanced question type detection (MCQ, SAQ, Essay, Scenario, Practical)
  - Updated filters to show question types instead of assessment types
  - Better categorization for mapping and validation
- [x] **MCQ choice extraction** ✅ **COMPLETED**
  - Extract and display MCQ choices (A, B, C, D or 1, 2, 3, 4)
  - Visual display of choices with letter/number indicators
  - Essential for proper mapping and validation
- [x] **LLM-powered question analysis** ✅ **COMPLETED**
  - Intelligent question type classification (MCQ, SAQ, Essay, etc.)
  - Enhanced question grouping and structure analysis
  - MCQ choice extraction with context
  - Quality assessment and confidence scoring
- [x] **Enhanced MCQ choice extraction** ✅ **COMPLETED**
  - Improved table content handling for MCQ choices
  - Context-aware choice extraction from surrounding text
  - Better pattern matching for various choice formats
  - Document context extraction for choices in separate sections
  - Intelligent filtering to exclude incorrect choices
- [x] **Question type editing** ✅ **COMPLETED**
  - User can edit question types to correct LLM mistakes
  - Dropdown selection for all question types including "Unknown"
  - Real-time filtering updates after type changes
  - H2A principle: Human oversight of AI classifications
- [x] **Unknown question type filter** ✅ **COMPLETED**
  - Added "Unknown" filter for unclassified questions
  - Helps identify questions that need manual classification
  - Improves transparency of AI extraction quality
- [x] **ASQA-Focused AI mapping** ✅ **COMPLETED**
  - Enhanced MappingAgent with ASQA compliance focus
  - Mapping strength assessment (EXPLICIT/IMPLICIT/PARTIAL/WEAK)
  - ASQA compliance alignment (FULL/PARTIAL/MINIMAL)
  - Clear audit justification for each mapping
  - Audit trail documentation and risk assessment
  - Coverage analysis to identify mapping gaps
  - ASQA-focused statistics and compliance tracking
- [x] **Alternative text paste extraction** ✅ **COMPLETED**
    - Added "Paste Text" option as alternative to file upload
    - Direct text input for complex document structures
    - LLM-based intelligent extraction from raw text
    - Universal compatibility with any document format
    - Better handling of complex table structures and mixed formatting
    - Enhanced prompt for accurate choice extraction from pasted text
    - Improved chunking for large texts (splits by questions, preserves Q&A groups)
    - Token limit management (3500 chars per chunk)
- [x] **Bulk question renumbering** ✅ **COMPLETED**
    - Added renumbering modal with table interface
    - Bulk editing of question numbers
    - Auto-renumbering functionality
    - Duplicate number validation
    - Scalable for large assessments
    - HITL-friendly interface
- [ ] **Confidence scoring system**
    - Score extracted data quality (1-10)
    - Show confidence indicators in UI
    - Flag incomplete or low-quality extractions
- [ ] **Process transparency**
  - Add detailed logging of AI decisions
  - Show extraction progress in real-time
  - Provide explanations for AI mappings

### **Security & Validation**
- [x] **File size validation** ✅ **COMPLETED**
  - Added 16MB file size limit
  - Prevents server crashes from large files
  - Clear error messages for users
- [x] **Session cleanup** ✅ **COMPLETED**
  - Automatic cleanup of old session files (>24 hours)
  - Prevents disk space issues
  - Runs before each request
- [ ] **File type validation**
  - Add file type validation (PDF, DOCX, DOC)
  - Add virus scanning for uploaded files
- [ ] **Session timeout**
  - Implement session timeout
  - Secure session storage

## 📋 **Documentation Updates**

### **User Guides**
- [ ] **Create user onboarding flow**
  - Step-by-step tutorial for first-time users
  - Tooltips for complex features
  - Help documentation with examples
- [ ] **Add video tutorials**
  - Screen recording of complete workflow
  - Troubleshooting guide
  - Best practices for assessment mapping

## 🎯 **Priority Order**

### **High Priority (Next Sprint)**
1. ✅ **AI Transparency** - Show users what the AI will do before processing
2. ✅ **Confidence Scoring** - Implement detailed confidence indicators
3. ~~Add autocomplete for UoC codes~~ - **CIRCLE BACK LATER**
4. ~~Rich file upload with preview~~ - **REMOVED: Using paste-only approach**

### **Medium Priority (Following Sprint)**
1. ~~Enhanced data visualization with previews~~ - **REMOVED: Not needed**
2. ~~AI process transparency flow~~ - **COMPLETED: Part of AI Transparency**
3. ~~Real-time validation improvements~~ - **REMOVED: Not needed**
4. ~~Performance optimizations~~ - **REMOVED: Not needed**

### **Low Priority (Future)**
1. Video tutorials and onboarding
2. ~~Advanced caching strategies~~ - **REMOVED: Not needed**
3. ~~Detailed AI confidence scoring~~ - **MOVED TO HIGH PRIORITY**
4. ~~Accessibility improvements (WCAG AA)~~ - **REMOVED: Not needed**
5. **Export Functionality** - **ON HOLD: Waiting for sample documentation**

## 📊 **Success Metrics**

### **User Experience**
- [ ] Reduce time to complete UoC entry by 50%
- [ ] ~~Increase file upload success rate to 95%~~ - **REMOVED: Using paste-only**
- [ ] Achieve 90% user satisfaction score
- [ ] Reduce support requests by 30%

### **Technical Performance**
- [ ] ~~Achieve sub-2-second page load times~~ - **REMOVED: Not needed**
- [ ] Implement 99.9% uptime for core features
- [ ] ~~Reduce API calls by 40% through caching~~ - **REMOVED: Not needed**
- [ ] Achieve 95% test coverage

## ✅ **Recently Completed Features**

### **Major UI/UX Enhancements (Completed This Session)**
- [x] **Comprehensive Validation Dashboard** ✅ **COMPLETED**
  - Full dual-panel interface with unit structure navigation
  - Interactive assessment item display with mapping details
  - Advanced filtering and search capabilities
  - Tabbed interface for different views
  - Modal detail views for comprehensive information
  - Validation discussion system with comment threading
  - Real-time updates and responsive design

### **Technical Infrastructure (Completed This Session)**
- [x] **Robust Session Management** ✅ **COMPLETED**
  - Automatic cleanup of old session files
  - File size validation and error handling
  - Comprehensive error logging and user feedback
  - Secure session storage and management

### **AI and Data Processing (Completed This Session)**
- [x] **Enhanced Document Processing** ✅ **COMPLETED**
  - Improved DOCX table extraction
  - Hierarchical question extraction with sub-questions
  - MCQ choice extraction with context awareness
  - Question type classification and editing
  - Alternative text paste extraction for complex documents
  - Bulk question renumbering functionality

### **AI Transparency and Confidence Scoring (Completed This Session)**
- [x] **AI Transparency Interface** ✅ **COMPLETED**
  - Collapsible AI capabilities preview on main page
  - Step-by-step explanation of AI processes
  - Expected confidence levels for each step
  - Visual confidence indicators with color coding
  - Clear explanation of human oversight requirements
- [x] **Enhanced Confidence Scoring** ✅ **COMPLETED**
  - Detailed confidence breakdown for each mapping
  - Mapping strength indicators (EXPLICIT/IMPLICIT/PARTIAL/WEAK)
  - ASQA compliance alignment indicators
  - Data quality percentage scores
  - Evidence level assessments (Strong/Moderate/Weak)
  - Visual confidence indicators with color-coded dots
  - Comprehensive metrics grid for easy assessment 