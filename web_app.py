"""
Web Application for CV Data Extraction
Flask-based UI for extracting structured data from CV PDFs
"""

import os
import json
import time
from flask import Flask, render_template, request, jsonify, send_from_directory, Response
from flask_cors import CORS
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
    """Handle file upload and extraction"""
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
    """Results page showing PDF preview and extracted data"""
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
    """Download extracted JSON data"""
    result_filename = filename.replace('.pdf', '_extracted.json')
    return send_from_directory(app.config['RESULTS_FOLDER'], 
                              result_filename, 
                              as_attachment=True)


@app.route('/results/<filename>/download/markdown')
def download_markdown(filename):
    """Download extracted data as Markdown"""
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

