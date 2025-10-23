"""
Web Application for CV Data Extraction
Flask-based UI for extracting structured data from CV PDFs
"""

import os
import json
import time
from flask import Flask, render_template, request, jsonify, send_from_directory, Response
from flask_cors import CORS
from flasgger import Swagger, swag_from
from werkzeug.utils import secure_filename
from cv_parser import CVParser
from cv_parser_fitz import CVParserFitz
from cv_parser_groq import CVParserGroq
from cv_to_markdown import cv_to_markdown
from schema_mapper import map_to_schema
import base64

# Optional imports for advanced parsers (may not be installed)
try:
    from cv_parser_docling import CVParserDocling
except ImportError:
    CVParserDocling = None

try:
    from cv_parser_llm import CVParserLLM
except ImportError:
    CVParserLLM = None

app = Flask(__name__)

# Enable CORS for cross-origin requests (when frontend is on different server)
CORS(app, resources={
    r"/*": {
        "origins": "*",  # Allow all origins - change this in production to specific domains
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

# Swagger configuration
swagger_config = {
    "headers": [],
    "specs": [
        {
            "endpoint": 'apispec',
            "route": '/apispec.json',
            "rule_filter": lambda rule: True,
            "model_filter": lambda tag: True,
        }
    ],
    "static_url_path": "/flasgger_static",
    "swagger_ui": True,
    "specs_route": "/docs"
}

swagger_template = {
    "swagger": "2.0",
    "info": {
        "title": "CV Parser API - PyMuPDF + Groq AI",
        "description": """
# CV Parser API - Integration Guide

AI-powered CV/Resume parsing API with multiple extraction engines. **Recommended: PyMuPDF + Groq AI** for best results.

## 🚀 Quick Start

**Base URL:** `http://192.168.1.114:5000`

### Example Request (JavaScript)

```javascript
const formData = new FormData();
formData.append('file', pdfFile);
formData.append('parser_type', 'groq');
formData.append('groq_model', 'llama-3.3-70b-versatile');

const response = await fetch('http://192.168.1.114:5000/upload', {
  method: 'POST',
  body: formData
});

const result = await response.json();
console.log(result.data); // Extracted CV data
```

### Example Request (Python)

```python
import requests

def extract_cv(pdf_path):
    url = 'http://192.168.1.114:5000/upload'
    with open(pdf_path, 'rb') as f:
        files = {'file': f}
        data = {'parser_type': 'groq'}
        response = requests.post(url, files=files, data=data)
    return response.json()['data']
```

### Example Request (cURL)

```bash
curl -X POST http://192.168.1.114:5000/upload \\
  -F "file=@cv.pdf" \\
  -F "parser_type=groq"
```

## 📊 Parser Options

| Parser | Speed | Accuracy | Best For |
|--------|-------|----------|----------|
| **groq** (Recommended) | 2-5s | 95% | Production, best accuracy |
| fast | 0.5-1s | 75% | Quick scans |
| original | 1-3s | 80% | Fallback |
| llm | 10-30s | 90% | Privacy (local) |
| docling | 5-10s | 92% | Complex layouts |

## 📋 Response Format

```json
{
  "success": true,
  "data": {
    "personal_info": {
      "name": "John Doe",
      "contact": {
        "email": "john@email.com",
        "phone": "+1234567890",
        "location": "San Francisco, CA"
      }
    },
    "skills": ["Python", "JavaScript", "Docker"],
    "experience": [...],
    "education": [...],
    "metadata": {
      "parser": "Groq (llama-3.3-70b-versatile)",
      "total_time": 2.76
    }
  }
}
```

## 🔑 Authentication

API key is configured server-side in `.env` file:
```bash
GROQ_API_KEY=your_groq_api_key
```

## 🌐 CORS

CORS is enabled for all origins. Safe for cross-origin requests.

## 📚 More Examples

See full integration examples for JavaScript, Python, PHP, C#, Java, and more in the documentation.
        """,
        "version": "1.0.0",
        "contact": {
            "name": "API Support",
            "url": "http://192.168.1.114:5000",
        }
    },
    "host": "192.168.1.114:5000",  # Change this to your server address
    "basePath": "/",
    "schemes": ["http", "https"],
    "consumes": ["multipart/form-data", "application/json"],
    "produces": ["application/json"],
    "externalDocs": {
        "description": "Full API Integration Guide",
        "url": "https://github.com/yourusername/cv-parser-api"
    }
}

swagger = Swagger(app, config=swagger_config, template=swagger_template)

app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['RESULTS_FOLDER'] = 'results'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Create necessary folders
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['RESULTS_FOLDER'], exist_ok=True)
os.makedirs('static', exist_ok=True)

ALLOWED_EXTENSIONS = {'pdf'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
def index():
    """Main upload page"""
    return render_template('index.html')


@app.route('/upload', methods=['POST'])
def upload_file():
    """
    Upload and extract CV/Resume data
    
    Extract structured data from CV/Resume PDFs using AI-powered parsers.
    
    **Recommended Setup:** Use `parser_type=groq` with `groq_model=llama-3.3-70b-versatile` for best results.
    
    ## Quick Examples:
    
    ### JavaScript (Fetch)
    ```javascript
    const formData = new FormData();
    formData.append('file', pdfFile);
    formData.append('parser_type', 'groq');
    
    fetch('http://192.168.1.114:5000/upload', {
      method: 'POST',
      body: formData
    }).then(r => r.json()).then(data => console.log(data));
    ```
    
    ### Python (Requests)
    ```python
    import requests
    files = {'file': open('cv.pdf', 'rb')}
    data = {'parser_type': 'groq'}
    r = requests.post('http://192.168.1.114:5000/upload', files=files, data=data)
    print(r.json()['data'])
    ```
    
    ### cURL
    ```bash
    curl -X POST http://192.168.1.114:5000/upload \\
      -F "file=@cv.pdf" \\
      -F "parser_type=groq"
    ```
    
    ## Response Time:
    - **groq**: 2-5 seconds (Recommended)
    - **fast**: 0.5-1 seconds
    - **original**: 1-3 seconds
    
    ---
    tags:
      - CV Extraction
    consumes:
      - multipart/form-data
    parameters:
      - name: file
        in: formData
        type: file
        required: true
        description: |
          PDF file of the CV/Resume to parse.
          
          **Requirements:**
          - Format: PDF only
          - Max size: 16MB
          - Recommended: 1-10 pages
          
          **Supported CV formats:** Any standard CV/Resume layout
      - name: parser_type
        in: formData
        type: string
        required: false
        default: original
        enum: [original, fast, groq, llm, docling]
        description: |
          Parser engine to use:
          
          - **groq** (Recommended): AI-powered, 95% accuracy, 2-5s
          - **fast**: PyMuPDF, 75% accuracy, 0.5-1s
          - **original**: pdfplumber, 80% accuracy, 1-3s
          - **llm**: Ollama local, 90% accuracy, 10-30s
          - **docling**: IBM AI, 92% accuracy, 5-10s
      - name: format
        in: formData
        type: string
        required: false
        default: flat-json
        enum: [flat-json, structured-json, markdown]
        description: |
          Output format:
          
          - **flat-json**: Standard structured JSON (default)
          - **structured-json**: Custom schema mapping
          - **markdown**: Formatted text document
      - name: groq_model
        in: formData
        type: string
        required: false
        default: llama-3.3-70b-versatile
        enum: [llama-3.3-70b-versatile, llama3-70b-8192, mixtral-8x7b-32768, llama3-8b-8192]
        description: |
          Groq AI model (only for parser_type=groq):
          
          - **llama-3.3-70b-versatile**: Best quality (Recommended)
          - **llama3-70b-8192**: Good quality
          - **mixtral-8x7b-32768**: Alternative model
          - **llama3-8b-8192**: Fastest, lighter
      - name: llm_model
        in: formData
        type: string
        required: false
        default: llama3.1
        description: |
          Ollama model name (only for parser_type=llm).
          
          Examples: llama3.1, llama3, mistral, phi3, gemma2
          
          **Note:** Model must be installed in Ollama
      - name: schema
        in: formData
        type: string
        required: false
        description: |
          Custom JSON schema (only for format=structured-json).
          
          Example:
          ```json
          {
            "candidate_name": "name",
            "contact_email": "email",
            "skills": "skills"
          }
          ```
    responses:
      200:
        description: |
          Successfully extracted CV data
          
          **Example Response:**
          ```json
          {
            "success": true,
            "filename": "John_Doe_CV.pdf",
            "data": {
              "personal_info": {
                "name": "John Doe",
                "contact": {
                  "email": "john.doe@email.com",
                  "phone": "+1-555-0123",
                  "location": "San Francisco, CA",
                  "linkedin": "linkedin.com/in/johndoe"
                }
              },
              "summary": "Experienced software engineer with 10+ years...",
              "skills": ["Python", "JavaScript", "Docker", "AWS", "React"],
              "languages": ["English - Native", "Spanish - Intermediate"],
              "certifications": ["AWS Certified Solutions Architect"],
              "education": [
                {
                  "degree": "B.S. Computer Science",
                  "institution": "Stanford University",
                  "period": "2010-2014"
                }
              ],
              "experience": [
                {
                  "company": "Tech Corp",
                  "position": "Senior Software Engineer",
                  "period": "2020-Present",
                  "location": "San Francisco, CA",
                  "responsibilities": [
                    "Led team of 5 developers",
                    "Architected microservices platform"
                  ]
                }
              ],
              "metadata": {
                "page_count": 2,
                "parser": "Groq (llama-3.3-70b-versatile)",
                "extraction_time": 0.45,
                "llm_processing_time": 2.31,
                "total_time": 2.76
              }
            },
            "processing_time": 2.76,
            "page_count": 2,
            "parser_used": "Groq (llama-3.3-70b-versatile)"
          }
          ```
          
          **How to use the response:**
          
          ```javascript
          // Access extracted data
          const name = result.data.personal_info.name;
          const email = result.data.personal_info.contact.email;
          const skills = result.data.skills;
          const experience = result.data.experience;
          ```
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            filename:
              type: string
              example: "John_Doe_CV.pdf"
            result_file:
              type: string
              example: "John_Doe_CV_extracted.json"
            data:
              type: object
              properties:
                file_name:
                  type: string
                personal_info:
                  type: object
                  properties:
                    name:
                      type: string
                      example: "John Doe"
                    contact:
                      type: object
                      properties:
                        email:
                          type: string
                          example: "john.doe@email.com"
                        phone:
                          type: string
                          example: "+1-555-0123"
                        location:
                          type: string
                          example: "San Francisco, CA"
                        linkedin:
                          type: string
                          example: "linkedin.com/in/johndoe"
                summary:
                  type: string
                  example: "Experienced software engineer..."
                skills:
                  type: array
                  items:
                    type: string
                  example: ["Python", "JavaScript", "Docker"]
                experience:
                  type: array
                  items:
                    type: object
                  example: [{"company": "Tech Corp", "position": "Senior Engineer"}]
                education:
                  type: array
                  items:
                    type: object
                  example: [{"degree": "B.S. Computer Science", "institution": "Stanford"}]
                metadata:
                  type: object
                  example: {"parser": "Groq", "total_time": 2.76}
            processing_time:
              type: number
              example: 2.45
            processing_time_ms:
              type: number
              example: 2450
            page_count:
              type: integer
              example: 2
            format:
              type: string
              example: "flat-json"
            parser_used:
              type: string
              example: "Groq (llama-3.3-70b-versatile)"
      400:
        description: |
          Bad request - Invalid input or missing required fields
          
          **Common causes:**
          - No file provided
          - File is not a PDF
          - File exceeds 16MB
          - Invalid schema format
          - Missing Groq API key
        schema:
          type: object
          properties:
            error:
              type: string
              example: "No file provided"
        examples:
          no_file:
            value:
              error: "No file provided"
          invalid_file:
            value:
              error: "Only PDF files are allowed"
          missing_key:
            value:
              error: "Groq API key not configured"
      500:
        description: |
          Internal server error - Processing failed
          
          **Possible causes:**
          - PDF parsing error
          - API timeout
          - Server error
          
          **Solution:** Retry the request or contact support
        schema:
          type: object
          properties:
            error:
              type: string
              example: "Processing error: [details]"
    """
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    output_format = request.form.get('format', 'flat-json')  # Get selected format
    custom_schema = request.form.get('schema', None)  # Get custom schema if provided
    use_fast_parser = request.form.get('use_fast_parser', 'false').lower() == 'true'  # Get parser choice
    
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': 'Only PDF files are allowed'}), 400
    
    try:
        # Save uploaded file
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Start timing
        start_time = time.time()
        
        # Extract CV data - choose parser based on user selection
        parser_type = request.form.get('parser_type', 'original')  # Get parser type choice
        
        if parser_type == 'groq':
            # Get API key from: 1) Environment variable, 2) Request parameter
            groq_api_key = os.environ.get('GROQ_API_KEY') or request.form.get('groq_api_key')
            
            if not groq_api_key:
                return jsonify({'error': 'Groq API key not configured. Please set GROQ_API_KEY environment variable.'}), 400
            
            groq_model = request.form.get('groq_model', 'llama-3.3-70b-versatile')
            parser = CVParserGroq(filepath, api_key=groq_api_key, model=groq_model)
            parser_used = f'Groq ({groq_model})'
        elif parser_type == 'llm':
            if CVParserLLM is None:
                return jsonify({'error': 'LLM parser not installed'}), 400
            llm_model = request.form.get('llm_model', 'llama3.1')
            parser = CVParserLLM(filepath, llm_model=llm_model)
            parser_used = f'LLM ({llm_model})'
        elif parser_type == 'docling':
            if CVParserDocling is None:
                return jsonify({'error': 'Docling parser not installed'}), 400
            parser = CVParserDocling(filepath)
            parser_used = 'Docling (Advanced)'
        elif parser_type == 'fast' or use_fast_parser:
            parser = CVParserFitz(filepath)
            parser_used = 'PyMuPDF (Fast)'
        else:
            parser = CVParser(filepath)
            parser_used = 'pdfplumber (Original)'
        
        cv_data = parser.parse()
        
        # Calculate processing time
        elapsed_time = time.time() - start_time
        processing_time = round(elapsed_time, 2)
        processing_time_ms = round(elapsed_time * 1000, 2)
        
        # Prepare output data based on format
        output_data = cv_data
        
        # If structured JSON, map to custom schema
        if output_format == 'structured-json' and custom_schema:
            try:
                output_data = map_to_schema(cv_data, custom_schema)
                # Save the custom schema for reference
                schema_filename = filename.replace('.pdf', '_schema.json')
                schema_path = os.path.join(app.config['RESULTS_FOLDER'], schema_filename)
                with open(schema_path, 'w', encoding='utf-8') as f:
                    f.write(custom_schema)
            except Exception as e:
                return jsonify({'error': f'Schema mapping error: {str(e)}'}), 400
        
        # Get page count FIRST (before saving metadata)
        page_count = 0
        try:
            if 'metadata' in cv_data and 'page_count' in cv_data['metadata']:
                page_count = cv_data['metadata']['page_count']
            else:
                # Try to get from PDF directly
                from pypdf import PdfReader
                reader = PdfReader(filepath)
                page_count = len(reader.pages)
        except Exception as e:
            # If all else fails, default to 0
            page_count = 0
        
        # Save extracted data in JSON
        result_filename = filename.replace('.pdf', '_extracted.json')
        result_path = os.path.join(app.config['RESULTS_FOLDER'], result_filename)
        
        with open(result_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        # Save metadata (processing time, page count, etc.)
        metadata_filename = filename.replace('.pdf', '_metadata.json')
        metadata_path = os.path.join(app.config['RESULTS_FOLDER'], metadata_filename)
        metadata = {
            'processing_time': processing_time,
            'processing_time_ms': processing_time_ms,
            'page_count': page_count,
            'filename': filename,
            'format': output_format,
            'parser_used': parser_used
        }
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2)
        
        # Also save in Markdown if requested
        if output_format == 'markdown':
            markdown_filename = filename.replace('.pdf', '_extracted.md')
            markdown_path = os.path.join(app.config['RESULTS_FOLDER'], markdown_filename)
            markdown_content = cv_to_markdown(cv_data)  # Use original CV data for markdown
            with open(markdown_path, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
        
        return jsonify({
            'success': True,
            'filename': filename,
            'result_file': result_filename,
            'data': output_data,  # Return the formatted data
            'processing_time': processing_time,
            'processing_time_ms': processing_time_ms,
            'page_count': page_count,
            'format': output_format,
            'parser_used': parser_used
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/results/<filename>')
def results(filename):
    """
    Get extraction results page
    ---
    tags:
      - Results
    parameters:
      - name: filename
        in: path
        type: string
        required: true
        description: Original PDF filename
      - name: format
        in: query
        type: string
        required: false
        description: Output format used during extraction
    responses:
      200:
        description: Results page HTML
      404:
        description: Results not found
    """
    result_filename = filename.replace('.pdf', '_extracted.json')
    result_path = os.path.join(app.config['RESULTS_FOLDER'], result_filename)
    
    if not os.path.exists(result_path):
        return "Results not found", 404
    
    with open(result_path, 'r', encoding='utf-8') as f:
        cv_data = json.load(f)
    
    # Load metadata if exists
    metadata_filename = filename.replace('.pdf', '_metadata.json')
    metadata_path = os.path.join(app.config['RESULTS_FOLDER'], metadata_filename)
    processing_time = 0
    processing_time_ms = 0
    page_count = 0
    parser_used = 'Unknown'
    
    if os.path.exists(metadata_path):
        with open(metadata_path, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
            processing_time = metadata.get('processing_time', 0)
            processing_time_ms = metadata.get('processing_time_ms', 0)
            page_count = metadata.get('page_count', 0)
            parser_used = metadata.get('parser_used', 'Unknown')
    
    # Check if this is structured JSON (custom schema)
    # Structured JSON won't have the standard 'personal_info' field
    is_structured = 'personal_info' not in cv_data
    output_format = request.args.get('format', 'flat-json')
    
    return render_template('results.html', 
                         filename=filename,
                         cv_data=cv_data,
                         cv_data_json=json.dumps(cv_data, indent=2, ensure_ascii=False),
                         is_structured=is_structured,
                         output_format=output_format,
                         processing_time=processing_time,
                         processing_time_ms=processing_time_ms,
                         page_count=page_count,
                         parser_used=parser_used)


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    """Serve uploaded PDF files"""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@app.route('/results/<filename>/download')
def download_result(filename):
    """
    Download extracted data as JSON
    ---
    tags:
      - Download
    parameters:
      - name: filename
        in: path
        type: string
        required: true
        description: Original PDF filename
    responses:
      200:
        description: JSON file download
        content:
          application/json:
            schema:
              type: object
      404:
        description: File not found
    """
    result_filename = filename.replace('.pdf', '_extracted.json')
    return send_from_directory(app.config['RESULTS_FOLDER'], 
                              result_filename, 
                              as_attachment=True)


@app.route('/results/<filename>/download/markdown')
def download_markdown(filename):
    """
    Download extracted data as Markdown
    ---
    tags:
      - Download
    parameters:
      - name: filename
        in: path
        type: string
        required: true
        description: Original PDF filename
    responses:
      200:
        description: Markdown file download
        content:
          text/markdown:
            schema:
              type: string
      404:
        description: File not found
    """
    # Load JSON data
    result_filename = filename.replace('.pdf', '_extracted.json')
    result_path = os.path.join(app.config['RESULTS_FOLDER'], result_filename)
    
    with open(result_path, 'r', encoding='utf-8') as f:
        cv_data = json.load(f)
    
    # Convert to Markdown
    markdown_content = cv_to_markdown(cv_data)
    
    # Return as downloadable file
    return Response(
        markdown_content,
        mimetype='text/markdown',
        headers={'Content-Disposition': f'attachment;filename={filename.replace(".pdf", "_extracted.md")}'}
    )


if __name__ == '__main__':
    print("\n" + "="*70)
    print("CV DATA EXTRACTION WEB APP")
    print("="*70)
    print("\nStarting web server...")
    print("Open your browser and go to: http://localhost:5000")
    print("\nFeatures:")
    print("   - Upload CV/Resume PDFs")
    print("   - Extract structured data (JSON)")
    print("   - Preview PDF and extracted data side-by-side")
    print("\nPress Ctrl+C to stop the server\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000)

