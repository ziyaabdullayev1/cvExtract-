# CVExtract Pro - AI-Powered Resume Parser

A beautiful, modern web application for extracting structured data from CV/Resume PDFs with multiple output formats and custom schema support.

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Start the Web Server

```bash
python web_app.py
```

### 3. Open Your Browser

Navigate to: **http://localhost:5000**

---

## ✨ Features

### 🎯 Multiple Output Formats

1. **Flat JSON** - Standard structured data with all CV fields extracted automatically
2. **Structured JSON** - Define your own custom schema to extract data in your desired format
3. **Markdown** - Formatted text with headers & lists, great for documentation

### 📤 Upload Interface

- **Drag & Drop** - Simply drag your PDF or click to select
- **File Validation** - Only valid PDF files accepted
- **Modern UI** - Clean, professional design with custom branding
- **Real-time Processing** - See progress with loading indicators

### 📊 Results Screen

- **Split View Layout**:
  - **Left Panel**: Live PDF preview
  - **Right Panel**: Extracted structured data
- **Two Display Modes**:
  - **Preview**: Beautifully formatted view of extracted data
  - **Raw**: Syntax-highlighted JSON
- **Action Buttons**:
  - 📥 Download JSON file
  - 📝 Download Markdown file
  - 📋 Copy JSON to clipboard
  - ← Back to upload

---

## 📋 What Gets Extracted

The app intelligently extracts:

- ✅ **Personal Info**: Name, email, phone, location, LinkedIn
- ✅ **Professional Summary**: Career overview and objectives
- ✅ **Skills**: Technical and soft skills (with count badges)
- ✅ **Languages**: Spoken languages with proficiency
- ✅ **Certifications**: Professional certifications and licenses
- ✅ **Education**: Degrees, institutions, graduation dates
- ✅ **Work Experience**: Companies, positions, durations, responsibilities

---

## 🔧 Custom Schema Format

### How to Use Structured JSON

1. Select **"Structured JSON"** format
2. Define your schema using field type hints:

```json
{
  "candidate_name": "name",
  "contact_email": "email",
  "contact_phone": "phone",
  "location": "location",
  "professional_summary": "summary",
  "skills": "skills",
  "languages": "languages",
  "work_experience": [
    {
      "company": "company",
      "position": "position",
      "duration": "period"
    }
  ]
}
```

### Available Field Types

**Personal Information:**
- `name` - Candidate's full name
- `email` - Email address
- `phone` - Phone number
- `location` - City/Country
- `linkedin` - LinkedIn profile

**Profile:**
- `summary` - Professional summary/objective
- `skills` - Technical and soft skills
- `languages` - Spoken languages

**Experience & Education:**
- `experience` - Work experience
- `position` - Job title/role
- `company` - Company/employer name
- `period` - Duration/dates
- `education` - Education history
- `degree` - Degree/qualification

**Data Types:**
- `string` - Empty string
- `number` - Zero
- `boolean` - False
- `array` - Empty array

---

## 📁 File Structure

```
test/
├── web_app.py              # Flask web server
├── cv_parser.py            # CV extraction logic
├── schema_mapper.py        # Custom schema mapping
├── cv_to_markdown.py       # Markdown converter
├── templates/
│   ├── index.html          # Upload page
│   └── results.html        # Results page
├── static/
│   └── logo.jpg            # Application logo
├── uploads/                # Uploaded PDFs (auto-created)
├── results/                # Extracted files (auto-created)
├── requirements.txt        # Python dependencies
└── README.md              # This file
```

---

## 💻 Usage Examples

### Basic Usage

1. **Start the server**:
   ```bash
   python web_app.py
   ```

2. **Upload a CV**:
   - Go to http://localhost:5000
   - Drag & drop your PDF or click "Select File"
   - Choose output format (Flat JSON, Structured JSON, or Markdown)
   - Click "Extract Content"

3. **View & Download Results**:
   - Browse extracted data in preview mode
   - Switch to raw JSON view
   - Download JSON or Markdown format
   - Copy data to clipboard

### Advanced: Custom Schema

1. Select **"Structured JSON"** format
2. Modify the schema in the editor:
   ```json
   {
     "applicant_name": "name",
     "contact_email": "email",
     "residence": "location",
     "technical_skills": "skills",
     "current_position": "position"
   }
   ```
3. Extract - data will match your custom structure!

---

## 🌐 API Endpoints

The web app exposes these endpoints:

- `GET /` - Upload page
- `POST /upload` - Upload and extract CV (supports `format` and `schema` parameters)
- `GET /results/<filename>` - View extraction results
- `GET /uploads/<filename>` - Serve PDF file
- `GET /results/<filename>/download` - Download JSON
- `GET /results/<filename>/download/markdown` - Download Markdown

---

## 🎨 Customization

### Modify Extraction Logic

Edit `cv_parser.py` to:
- Adjust pattern matching for different CV formats
- Add new data fields to extract
- Modify parsing rules
- Enhance extraction accuracy

### Customize UI

Edit `templates/index.html` and `templates/results.html` to:
- Change colors and styling
- Add new features
- Modify layout
- Update branding

### Add Output Formats

Create new converters like `cv_to_markdown.py` to support additional formats.

---

## 📱 Browser Support

- ✅ Chrome (recommended)
- ✅ Firefox
- ✅ Safari
- ✅ Edge

---

## 🐛 Troubleshooting

**Q: Server won't start**  
A: Make sure port 5000 is not in use. Change the port in `web_app.py` if needed.

**Q: PDF preview not showing**  
A: Some browsers may block PDF rendering. Try Chrome or check browser console for errors.

**Q: Upload fails**  
A: Ensure the file is a valid PDF and not corrupted. Max file size is 16MB.

**Q: Name or location extracted incorrectly**  
A: Some CVs have non-standard formats. The parser uses pattern matching and may need tuning for specific formats.

**Q: Custom schema not working**  
A: Validate your JSON syntax. Use the sample schemas as templates.

**Q: Browser storage error**  
A: Clear browser cache: Chrome DevTools → Application → Clear storage → Clear site data

---

## 🔒 Security Notes

- Files are stored locally in `uploads/` and `results/` folders
- For production use, implement proper file cleanup and security measures
- Consider adding authentication for multi-user environments
- Use HTTPS in production
- Implement rate limiting to prevent abuse

---

## 🎯 Production Deployment

For production deployment:

1. **Disable Debug Mode**:
   ```python
   app.run(debug=False, host='0.0.0.0', port=5000)
   ```

2. **Use Production Server**:
   ```bash
   pip install gunicorn
   gunicorn -w 4 -b 0.0.0.0:5000 web_app:app
   ```

3. **Add Security Features**:
   - Implement user authentication
   - Add rate limiting
   - Use HTTPS/SSL certificates
   - Implement automatic file cleanup
   - Add virus scanning for uploads
   - Set up logging and monitoring

---

## 📊 Performance

- **Typical extraction time**: 2-5 seconds per CV
- **Supported file size**: Up to 16MB
- **Optimal CV length**: 1-10 pages
- **Concurrent uploads**: Supports multiple users

---

## 🛠️ Dependencies

- **Flask** - Web framework
- **pdfplumber** - PDF text extraction
- **pypdf** - PDF metadata
- **Werkzeug** - File handling
- **Jinja2** - Template engine

See `requirements.txt` for complete list with versions.

---

## 🤝 Support

For issues or questions:
1. Check the terminal/console for error messages
2. Ensure all dependencies are installed correctly
3. Verify PDF file is not corrupted or password-protected
4. Try with a different CV/Resume PDF
5. Check browser console (F12) for frontend errors

---

**Transform resumes into structured data in seconds!** 🎉

CVExtract Pro - Your AI-powered resume parsing solution.

