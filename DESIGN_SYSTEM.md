# Assessment Validator - Design System

## 🎯 **Project Overview**

**Assessment Validator** is a computer-assisted assessment mapping tool that helps RTOs validate their assessment materials against Unit of Competency (UoC) requirements from training.gov.au.

## 🧠 **Core Design Principles**

### **1. Human-Centered Design (HCD)**
- **Clear Visual Hierarchy**: Information is organized with clear headings, sections, and visual cues
- **Intuitive Navigation**: Users can easily understand where they are and what to do next
- **Progressive Disclosure**: Information is revealed step-by-step to avoid overwhelming users
- **Consistent Patterns**: Similar actions have similar visual treatments and behaviors

### **2. Human-to-AI (H2A) Collaboration**
- **Transparency**: Users understand what the AI is doing at each step
- **Control**: Users can review, edit, and override AI decisions
- **Feedback Loops**: Clear feedback on AI performance and suggestions
- **Audit Trail**: Complete history of AI decisions and user validations

### **3. Accessibility & Compliance**
- **WCAG AA Compliance**: Focus on color contrast ratios for accessibility
- **Responsive Design**: Works seamlessly across desktop, tablet, and mobile
- **Error Prevention**: Clear validation and helpful error messages
- **Loading States**: Users always know when the system is processing

## 🚀 **User Journey & Workflow**

### **Step 1: UoC Code Entry & Data Fetching**
```
User Action: Enter UoC code (e.g., HLTINF006)
System Action: Check cache first, fetch from training.gov.au if needed
User Experience: 
- Clean, focused form with example codes
- Real-time validation and feedback
- Success confirmation with UoC summary
- Cache status indicator ("Fetched 5 days ago")
- Automatic redirect to next step
```

### **Step 2: Assessment Document Upload**
```
User Action: Upload assessment document
System Action: Process file against fetched UoC data
User Experience:
- Clear progress indicators
- UoC summary displayed for context
- File validation and preview
- Processing status with estimated time
- Checkpoint saved for multi-validator workflow
```

### **Step 3: AI Mapping & Validation**
```
User Action: Review and validate AI-generated mappings
System Action: Present mappings with confidence scores
User Experience:
- Clear mapping visualization
- Confidence indicators (high/medium/low)
- Easy approve/reject/edit actions
- Audit trail for all decisions
- State persistence for multi-validator review
```

### **Step 4: Export & Reporting**
```
User Action: Generate audit-ready reports
System Action: Create comprehensive validation reports
User Experience:
- Multiple export formats (JSON, CSV)
- Detailed audit trail with timestamps
- Quality metrics and recommendations
- Professional report formatting
- ASQA-compliant audit trail
```

### **Multi-Validator Workflow**
```
Validator 1: Enters UoC → System checks cache → Uploads file → Creates mappings → Saves checkpoint
Validator 2: Enters same UoC → System loads existing mappings → Reviews/revises → Saves changes
Validator 3: Enters same UoC → System loads final mappings → Final review → Approves
Result: Complete audit trail with minimal token usage and maximum efficiency
```

### **Intelligent Data Extraction Principles**
```
Elements & Performance Criteria: Literal extraction (preserve exact numbering and structure)
Knowledge Evidence & Performance Evidence: Intelligent analysis and grouping
- Group related concepts into broad, assessable categories
- Ignore introductory phrases like "This includes knowledge of:"
- Aim for 8-12 KE categories and 5-8 PE categories
- Each category should be substantial enough for assessment mapping
- Avoid over-granularization that would require 30+ assessment items
- Maintain professional VET terminology and language
```

## 🎨 **Visual Design System**

### **Color Palette**
```css
/* Primary Colors */
Primary: #667eea (Blue gradient start)
Secondary: #764ba2 (Purple gradient end)
Success: #28a745 (Green)
Warning: #ffc107 (Yellow)
Error: #dc3545 (Red)
Info: #17a2b8 (Cyan)

/* Neutral Colors */
Light Gray: #f8f9fa
Medium Gray: #e9ecef
Dark Gray: #6c757d
Text Primary: #333
Text Secondary: #666
```

### **Typography**
```css
/* Font Stack */
font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;

/* Font Sizes */
h1: 2.5em
h2: 2em
h3: 1.5em
body: 1em
small: 0.9em
```

### **Component Design**

#### **Cards & Containers**
```css
.card {
    background: white;
    border-radius: 15px;
    box-shadow: 0 20px 40px rgba(0,0,0,0.1);
    padding: 30px;
    margin-bottom: 20px;
}
```

#### **Buttons**
```css
.btn-primary {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border: none;
    border-radius: 8px;
    padding: 15px;
    font-weight: 600;
    transition: transform 0.2s ease;
}

.btn-primary:hover {
    transform: translateY(-2px);
}
```

#### **Form Elements**
```css
.form-input {
    width: 100%;
    padding: 12px 15px;
    border: 2px solid #e1e5e9;
    border-radius: 8px;
    font-size: 1em;
    transition: border-color 0.3s ease;
}

.form-input:focus {
    outline: none;
    border-color: #667eea;
}
```

## 📱 **Responsive Design Guidelines**

### **Breakpoints**
- **Mobile**: < 768px
- **Tablet**: 768px - 1024px
- **Desktop**: > 1024px

### **Mobile-First Approach**
- Single column layouts on mobile
- Touch-friendly button sizes (min 44px)
- Simplified navigation
- Optimized form inputs

## 🔄 **Interaction Patterns**

### **Loading States**
- **Spinner**: For short operations (< 3 seconds)
- **Progress Bar**: For longer operations with known duration
- **Skeleton Screens**: For content loading
- **Status Messages**: Clear feedback on operation state

### **Error Handling**
- **Inline Validation**: Real-time form validation
- **Error Messages**: Clear, actionable error descriptions
- **Recovery Options**: Suggested fixes and alternatives
- **Graceful Degradation**: System works even with partial failures

### **Success Feedback**
- **Confirmation Messages**: Clear success indicators
- **Progress Updates**: Step-by-step completion status
- **Next Steps**: Clear guidance on what to do next

## 🎯 **User Experience Guidelines**

### **Information Architecture**
1. **Progressive Disclosure**: Show only what's needed when it's needed
2. **Contextual Help**: Help text appears when users need it
3. **Breadcrumbs**: Users always know where they are
4. **Consistent Navigation**: Same navigation patterns throughout

### **Content Strategy**
1. **Clear Language**: Avoid jargon, use plain English
2. **Action-Oriented**: Button text describes the action
3. **Scannable**: Use headings, lists, and visual hierarchy
4. **Accessible**: High contrast, readable fonts, keyboard navigation

### **Performance Guidelines**
1. **Fast Loading**: Pages load in under 3 seconds
2. **Responsive**: Interface responds immediately to user actions
3. **Caching**: Intelligent caching to reduce API calls
4. **Progressive Enhancement**: Core functionality works without JavaScript

## 🔧 **Technical Implementation Rules**

### **Frontend Standards**
- **HTML5 Semantic**: Use proper semantic elements
- **CSS Grid/Flexbox**: Modern layout techniques
- **JavaScript ES6+**: Modern JavaScript features
- **Progressive Web App**: Installable, offline-capable

### **Backend Standards**
- **RESTful APIs**: Consistent API design
- **Error Handling**: Comprehensive error management
- **Logging**: Detailed logging for debugging
- **Security**: Input validation, CSRF protection

### **Intelligent Caching & Incremental Workflow Architecture**

#### **Unit Metadata Caching: Version-Robust & Audit-Safe**
- **Cache-First Strategy**: Check local cache before external API calls
- **Version Tracking**: Store fetched_timestamp, source_url, data_hash for audit traceability
- **TTL Management**: Invalidate cache after configurable timeframe (3-6 months)
- **Conflict Resolution**: Track new snapshots rather than deleting historical data

#### **Incremental State Awareness: Checkpoints & Flow Idempotency**
- **Task Checkpoints**: Define clear state boundaries
  1. Unit metadata retrieved
  2. Assessment files uploaded + mapping initiated
- **State Persistence**: System remembers each state for seamless continuation
- **Multi-Validator Support**: Validators can pick up where others left off
- **UI State Indicators**: "Mapping needed" vs "Review pending" status

#### **Token-Rich LLM Calls with Prompt Caching**
- **Static Prompt Caching**: Cache system prompts (schema, mapping rules, rationale templates)
- **Dynamic Content Appending**: Only context-specific data appended to cached prompts
- **Cost Optimization**: Reduce token usage by 50% through intelligent caching
- **Audit Compliance**: Maintain complete chain-of-evidence for ASQA

### **Data Flow**
1. **User Input** → **Validation** → **Processing** → **Feedback**
2. **API Calls** → **Loading State** → **Success/Error** → **UI Update**
3. **File Upload** → **Progress** → **Processing** → **Results**
4. **Cache Check** → **Fetch if Needed** → **Store with Metadata** → **Serve Cached**

## 📊 **Quality Assurance**

### **Usability Testing**
- **Task Completion**: Users can complete key tasks successfully
- **Error Rate**: Low error rates in common workflows
- **Time on Task**: Efficient completion of tasks
- **User Satisfaction**: High satisfaction scores

### **Accessibility Testing**
- **Screen Reader**: Compatible with screen readers
- **Keyboard Navigation**: Full keyboard accessibility
- **Color Contrast**: WCAG AA compliant contrast ratios
- **Focus Management**: Clear focus indicators

### **Performance Testing**
- **Page Load Time**: < 3 seconds
- **API Response Time**: < 1 second
- **File Upload**: Progress indication for large files
- **Error Recovery**: Graceful handling of network issues

## 🚀 **Future Enhancements**

### **Planned Features**
1. **Advanced Analytics**: Detailed usage analytics with cache performance metrics
2. **Bulk Processing**: Multiple file upload and processing with intelligent caching
3. **Collaborative Validation**: Multi-user validation workflows with state persistence
4. **Integration APIs**: Connect with other RTO systems and external data sources
5. **ASQA Compliance Dashboard**: Real-time audit trail monitoring and reporting

### **Design Evolution**
1. **Dark Mode**: Optional dark theme with accessibility considerations
2. **Customization**: User-configurable interface with validator preferences
3. **Advanced Filtering**: Sophisticated search and filter options with cached results
4. **Real-time Collaboration**: Live collaboration features with conflict resolution
5. **Smart Caching UI**: Visual indicators for cache status and optimization opportunities

---

## 📝 **Documentation Standards**

### **Code Comments**
- **Purpose**: Explain why, not what
- **Context**: Provide business context for complex logic
- **Examples**: Include usage examples for APIs
- **Updates**: Keep comments in sync with code changes

### **User Documentation**
- **Getting Started**: Clear onboarding guide
- **Feature Guides**: Step-by-step instructions
- **Troubleshooting**: Common issues and solutions
- **Best Practices**: Recommended workflows

### **API Documentation**
- **OpenAPI/Swagger**: Comprehensive API documentation
- **Examples**: Real-world usage examples
- **Error Codes**: Complete error code reference
- **Rate Limits**: Clear rate limiting information

---

*This design system ensures consistency, accessibility, and user satisfaction across all aspects of the Assessment Validator. All agents and developers should refer to this document when making design or implementation decisions.* 