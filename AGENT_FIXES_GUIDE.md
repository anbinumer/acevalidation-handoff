# Agent Fixes & Integration Guide

## 🚀 Overview

This guide documents the comprehensive fixes applied to the ExtractAgent and MappingAgent, along with the new robust integration system that ties them together.

## 🔧 Key Fixes Implemented

### 1. ExtractAgent Improvements

#### ✅ **Proper API Key Handling**
```python
# OLD: No API key parameter
extract_agent = ExtractAgent()

# NEW: Proper API key handling
extract_agent = ExtractAgent(api_key="your_api_key")
```

#### ✅ **Enhanced Error Handling**
- All methods now have comprehensive try-catch blocks
- Graceful fallbacks when operations fail
- Detailed error logging with context
- No more undefined variable references

#### ✅ **Robust File Extraction**
- Better handling of DOCX, PDF, and DOC files
- Proper file existence checks
- Safe text extraction with error recovery
- Support for tables and complex formatting

#### ✅ **Improved LLM Integration**
- Simplified JSON structure to avoid parsing issues
- Multiple fallback methods for JSON extraction
- Better prompt engineering for consistent responses
- Reduced token limits for more reliable completion

#### ✅ **Fallback Mechanisms**
- Always falls back to pattern-based extraction if LLM fails
- Multiple extraction strategies
- Graceful degradation when AI services are unavailable

### 2. MappingAgent Enhancements

#### ✅ **Testing Mode**
```python
# NEW: Testing mode with failure detection
mapping_agent = MappingAgent(
    api_key="your_api_key",
    testing_mode=True  # Stops after 2 consecutive failures
)
```

#### ✅ **Better Logging**
- Clear progress indicators with emojis
- Detailed error messages with context
- Step-by-step operation tracking
- Debug information for troubleshooting

#### ✅ **Robust JSON Parsing**
- Multiple fallback methods for cleaning AI responses
- JSON structure validation
- Automatic fixing of common JSON issues
- Graceful handling of malformed responses

#### ✅ **Improved Data Structure Handling**
- Better support for different UoC data formats
- Automatic conversion between dict and list formats
- Validation of required fields
- Default value handling

## 🎯 Integration Pattern

### **Recommended Usage**

Instead of calling agents directly, use the integration function:

```python
from main import run_assessment_analysis

# File-based analysis
results = run_assessment_analysis(
    file_path="path/to/assessment.docx",
    uoc_data=your_uoc_data,
    api_key="your_api_key"
)

# Text-based analysis
results = run_assessment_analysis(
    text_content="Your assessment text here...",
    uoc_data=your_uoc_data,
    api_key="your_api_key"
)
```

### **Agent Initialization**

```python
# ExtractAgent
from agents.extract_agent import ExtractAgent
extract_agent = ExtractAgent(api_key="your_api_key")

# MappingAgent
from agents.mapping_agent import MappingAgent
mapping_agent = MappingAgent(
    api_key="your_api_key",
    testing_mode=True  # Will stop after 2 failures for debugging
)
```

## 📊 Expected Results

### ✅ **Success Response**
```json
{
    "success": true,
    "questions": [
        {
            "id": "Q1",
            "text": "Question text here",
            "type": "mcq",
            "choices": ["A", "B", "C", "D"]
        }
    ],
    "mappings": {
        "mappings": [...],
        "analysis": {...}
    },
    "statistics": {
        "total_questions": 5,
        "total_mappings": 5,
        "assessment_type": "KBA"
    }
}
```

### ❌ **Error Response**
```json
{
    "success": false,
    "error": "No questions could be extracted from the document",
    "questions": [],
    "mappings": {"mappings": [], "analysis": {}}
}
```

## 🔍 Common Issues & Solutions

### **Issue: "No questions extracted"**
**Cause:** Document doesn't contain recognizable question patterns
**Solutions:**
- Check if document has numbered questions (1., 2., etc.)
- Ensure document is in supported format (DOCX, PDF, DOC)
- Try text paste method instead of file upload

### **Issue: "JSON parsing failed"**
**Cause:** API response format issues
**Solutions:**
- Will automatically fallback to mock data
- Check API key validity
- Verify network connectivity

### **Issue: "No mappings generated"**
**Cause:** UoC data format issues
**Solutions:**
- Check UoC data structure has required fields
- Ensure elements and performance_criteria are present
- Verify data format compatibility

### **Issue: "API call failed"**
**Cause:** Invalid API key or network issues
**Solutions:**
- Verify API key is correct
- Check network connectivity
- Will use fallback mappings automatically

## 🛠️ Debugging Tips

### **Enable Detailed Logging**
```python
import logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

### **Check UoC Data Structure**
```python
# Ensure your UoC data has this structure:
uoc_data = {
    'uoc_code': 'CHCAGE011',
    'title': 'Unit Title',
    'elements': [
        {'id': 'E1', 'description': 'Element description'}
    ],
    'performance_criteria': [
        {'code': 'PC1.1', 'description': 'Criterion description'}
    ],
    'performance_evidence': [],
    'knowledge_evidence': []
}
```

### **Test Individual Components**
```python
# Test extraction only
questions = extract_agent.execute("path/to/file.docx")
print(f"Extracted {len(questions)} questions")

# Test mapping only
mappings = mapping_agent.execute(questions, uoc_data, "KBA")
print(f"Generated {len(mappings.get('mappings', []))} mappings")
```

## 🚀 Web Interface Usage

### **Start the Application**
```bash
python app.py
```

### **Access Points**
- **Main Interface:** http://localhost:5001
- **Test Endpoint:** http://localhost:5001/test
- **Dashboard:** http://localhost:5001/dashboard/{session_id}

### **Workflow**
1. Enter UoC code on main page
2. Upload assessment file or paste text
3. Review results in dashboard
4. Export audit report if needed

## 📈 Performance Improvements

### **Before Fixes**
- ❌ Frequent crashes on malformed JSON
- ❌ No fallback when AI fails
- ❌ Poor error messages
- ❌ Inconsistent data structures

### **After Fixes**
- ✅ Robust error handling with fallbacks
- ✅ Clear progress indicators
- ✅ Detailed error messages
- ✅ Consistent data structures
- ✅ Multiple extraction strategies
- ✅ Comprehensive validation

## 🔧 Configuration

### **Environment Variables**
```bash
# Required
GEMINI_API_KEY=your_api_key_here

# Optional
FLASK_ENV=development
FLASK_DEBUG=True
```

### **File Structure**
```
rto-validation-mvp/
├── agents/
│   ├── extract_agent.py      # ✅ Fixed
│   ├── mapping_agent.py      # ✅ Fixed
│   └── ...
├── main.py                   # ✅ New integration
├── app.py                    # ✅ Updated Flask app
└── ...
```

## 🎯 Best Practices

1. **Always use the integration function** instead of calling agents directly
2. **Enable detailed logging** for debugging
3. **Validate UoC data structure** before processing
4. **Test with small samples** before processing large documents
5. **Monitor the logs** for any issues
6. **Use testing_mode=True** during development

## 🚨 Troubleshooting Checklist

- [ ] API key is valid and has sufficient quota
- [ ] Document contains recognizable question patterns
- [ ] UoC data has required fields (elements, performance_criteria)
- [ ] Network connectivity is stable
- [ ] File format is supported (DOCX, PDF, DOC)
- [ ] File size is within limits (16MB)
- [ ] Logging is enabled for debugging

## 📞 Support

If you encounter issues:

1. **Check the logs** for detailed error messages
2. **Verify your data** matches expected formats
3. **Test with the `/test` endpoint** to verify components
4. **Use the integration function** instead of direct agent calls
5. **Enable debug logging** for more detailed information

The enhanced agents are now much more resilient and will provide clear guidance when issues occur! 