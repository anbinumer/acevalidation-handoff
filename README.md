# Assessment Validator

A comprehensive testing and validation tool for RTO (Registered Training Organisation) assessment mapping using computer-assisted agents.

## 📚 **Documentation**

- **[Design System](DESIGN_SYSTEM.md)** - Complete UI/UX guidelines and design principles
- **[Agent Guidelines](AGENT_GUIDELINES.md)** - Quick reference for AI agents and developers
- **[Architecture & Caching](ARCHITECTURE_CACHING.md)** - Intelligent caching and incremental workflow system
- **[Implementation Status](IMPLEMENTATION_STATUS.md)** - Current project status and roadmap

## 🚀 Quick Start

### 1. Local Development Setup

```bash
# 1. Create project structure
mkdir rto-validation-mvp
cd rto-validation-mvp

# 2. Set up Python environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Create environment file
cp .env.example .env  # Create your own .env file
```

### 2. Environment Configuration

Create a `.env` file with the following variables:

```env
# API Configuration
GEMINI_API_KEY=your_gemini_api_key_here
RTO_API_BASE_URL=https://training.gov.au/api/v1

# Application Settings
DEBUG=True
SECRET_KEY=your-secret-key-here

# File Storage
UPLOAD_FOLDER=storage/uploads
```

### 3. Run the Application

```bash
# Start the Flask development server
python app.py

# Visit http://localhost:5001 to access the testing dashboard
```

## 🧪 Testing Strategy

### Phase 1: FetchAgent Test (30 minutes)

Test the agent that fetches Unit of Competency data from training.gov.au:

```bash
python test_fetch_agent.py
```

**Expected Output:**
```
🧪 Testing FetchAgent...
✅ FetchAgent initialized successfully
📡 Fetching data for UoC: HLTINF006
✅ FetchAgent working - Retrieved 2 elements and 2 performance criteria
📋 Unit Title: Mock Unit: HLTINF006
🔢 Elements found: 2
📊 Performance Criteria found: 2
🎉 FetchAgent test completed successfully!
```

### Phase 2: ExtractAgent Test (45 minutes)

Test the agent that extracts questions from assessment documents:

```bash
# Create a test document first
python -c "
from docx import Document
doc = Document()
doc.add_heading('Test Assessment', 0)
doc.add_paragraph('1. What are infection control procedures?')
doc.add_paragraph('2. Describe standard precautions.')
doc.save('test_assessment.docx')
"

# Test the ExtractAgent
python -c "
from agents.extract_agent import ExtractAgent
agent = ExtractAgent()
questions = agent.execute('test_assessment.docx')
print('Questions extracted:', len(questions))
"
```

### Phase 3: MappingAgent Test (60 minutes)

Test the AI-powered mapping agent:

```bash
python -c "
from agents.mapping_agent import MappingAgent
from agents.fetch_agent import FetchAgent
from agents.extract_agent import ExtractAgent

# Get UoC data
fetch_agent = FetchAgent()
uoc_data = fetch_agent.execute('HLTINF006')

# Get questions
extract_agent = ExtractAgent()
questions = extract_agent.execute('test_assessment.docx')

# Generate mappings
mapping_agent = MappingAgent(api_key='your_gemini_key')
mappings = mapping_agent.execute(questions, uoc_data)
print('Mappings generated:', len(mappings))
"
```

### Phase 4: Full Pipeline Test (90 minutes)

Test the complete pipeline:

```bash
python test_pipeline.py
```

## 🏗️ Architecture

### Agent System

The MVP consists of three specialized agents:

1. **FetchAgent**: Intelligent extraction of UoC data from training.gov.au
   - **Elements & PCs**: Literal extraction preserving exact numbering
   - **KE & PE**: Intelligent grouping into broad, assessable categories (8-12 KE, 5-8 PE)
   - **Quality**: Substantial categories for practical assessment mapping
2. **ExtractAgent**: Extracts questions from uploaded assessment documents (DOCX, PDF, DOC)
3. **MappingAgent**: Uses AI to map assessment questions to UoC elements and performance criteria

### Web Interface

- **Modern, responsive design** with real-time testing capabilities
- **Phase-by-phase testing** with visual progress indicators
- **Comprehensive results display** with detailed logging
- **File upload support** for assessment documents

### Testing Features

- **Unit Testing**: Individual agent testing with detailed output
- **Integration Testing**: Full pipeline validation
- **Web Interface Testing**: Interactive dashboard for manual testing
- **Mock Data Support**: Fallback mechanisms when APIs are unavailable

## 📁 Project Structure

```
rto-validation-mvp/
├── agents/                 # AI agents
│   ├── __init__.py
│   ├── fetch_agent.py     # UoC data fetching
│   ├── extract_agent.py   # Question extraction
│   └── mapping_agent.py   # AI-powered mapping
├── ui/                    # Web interface
│   ├── __init__.py
│   └── routes.py
├── templates/             # HTML templates
│   └── index.html
├── storage/              # File storage
│   └── uploads/
├── tests/                # Test files
├── main.py               # Flask application
├── config.py             # Configuration
├── requirements.txt      # Dependencies
├── test_fetch_agent.py  # FetchAgent unit test
├── test_pipeline.py     # Full pipeline test
└── README.md            # This file
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `GEMINI_API_KEY` | Google Gemini API key for AI mapping | Required |
| `RTO_API_BASE_URL` | Training.gov.au API base URL | `https://training.gov.au/api/v1` |
| `DEBUG` | Enable debug mode | `True` |
| `SECRET_KEY` | Flask secret key | Auto-generated |
| `UPLOAD_FOLDER` | File upload directory | `storage/uploads` |

### Supported File Types

- **DOCX**: Microsoft Word documents
- **PDF**: Portable Document Format
- **DOC**: Legacy Word documents (basic support)

## 🚀 Deployment

### Development

```bash
# Run with auto-reload
python main.py

# Or use Flask CLI
export FLASK_APP=main.py
export FLASK_ENV=development
flask run
```

### Production

```bash
# Set production environment
export FLASK_ENV=production
export DEBUG=False

# Use a production WSGI server
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 main:app
```

## 🧪 Testing Commands

### Quick Tests

```bash
# Test individual components
python test_fetch_agent.py
python test_pipeline.py

# Test via web interface
python app.py
# Visit http://localhost:5001
```

### Manual Testing

1. **FetchAgent**: Click "Test FetchAgent" to verify UoC data retrieval
2. **ExtractAgent**: Upload a document and click "Test ExtractAgent"
3. **MappingAgent**: Run after FetchAgent and ExtractAgent to test AI mapping
4. **Full Pipeline**: Upload document, enter UoC code, and test complete workflow

## 📊 Expected Results

### Successful Test Output

```
✅ FetchAgent: Retrieved 2 elements and 2 performance criteria
✅ ExtractAgent: Extracted 3 questions from document
✅ MappingAgent: Generated 3 mappings with 85% average confidence
✅ Full Pipeline: Complete workflow successful
```

### Performance Metrics

- **FetchAgent**: < 5 seconds for UoC data retrieval
- **ExtractAgent**: < 10 seconds for document processing
- **MappingAgent**: < 30 seconds for AI mapping (per question)
- **Full Pipeline**: < 2 minutes for complete workflow

## 🔍 Troubleshooting

### Common Issues

1. **API Key Missing**: Set `GEMINI_API_KEY` in your `.env` file
2. **File Upload Errors**: Check file permissions and supported formats
3. **Network Issues**: Verify internet connection for API calls
4. **Memory Issues**: Large documents may require more memory

### Debug Mode

Enable debug mode for detailed error messages:

```bash
export DEBUG=True
python main.py
```

## 📈 Next Steps

1. **Production Deployment**: Configure production environment
2. **API Integration**: Connect to real training.gov.au API
3. **Advanced AI**: Implement more sophisticated mapping algorithms
4. **User Management**: Add authentication and user roles
5. **Reporting**: Generate detailed validation reports
6. **Bulk Processing**: Support for multiple documents

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details. 