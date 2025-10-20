"""
CV Parser Module - LLM Enhanced Version
Uses PyMuPDF for fast text extraction + LLM (Ollama) for intelligent data structuring.
"""

import re
import json
import time
from typing import Dict, List, Any, Optional
import os

class CVParserLLM:
    """Parse CV/Resume PDFs using PyMuPDF + LLM for intelligent extraction."""
    
    def __init__(self, pdf_path: str, llm_model: str = "llama3.1", llm_base_url: str = "http://localhost:11434"):
        """
        Initialize the LLM-enhanced CV parser.
        
        Args:
            pdf_path: Path to the CV PDF file
            llm_model: Ollama model to use (default: llama3.1)
            llm_base_url: Ollama API base URL (default: http://localhost:11434)
        """
        self.pdf_path = pdf_path
        self.llm_model = llm_model
        self.llm_base_url = llm_base_url
        self.full_text = ""
        self.page_count = 0
        self.extraction_time = 0
        self.llm_processing_time = 0
    
    def _extract_raw_text(self) -> str:
        """Extract text from PDF using PyMuPDF (fast)."""
        if self.full_text:
            return self.full_text
        
        import fitz
        
        start_time = time.time()
        all_text = []
        doc = fitz.open(self.pdf_path)
        self.page_count = doc.page_count
        
        for page in doc:
            text = page.get_text("text")
            if text:
                all_text.append(text)
        
        doc.close()
        self.full_text = '\n'.join(all_text)
        self.extraction_time = time.time() - start_time
        
        print(f"INFO: Extracted text using PyMuPDF in {self.extraction_time:.2f}s")
        return self.full_text
    
    def _call_ollama(self, prompt: str) -> str:
        """Call Ollama API to process text with LLM."""
        try:
            import requests
            
            url = f"{self.llm_base_url}/api/generate"
            
            payload = {
                "model": self.llm_model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.1,  # Low temperature for more consistent output
                    "top_p": 0.9,
                }
            }
            
            response = requests.post(url, json=payload, timeout=120)
            response.raise_for_status()
            
            result = response.json()
            return result.get('response', '').strip()
            
        except requests.exceptions.ConnectionError:
            raise Exception("Cannot connect to Ollama. Make sure Ollama is running (ollama serve)")
        except Exception as e:
            raise Exception(f"Ollama API error: {str(e)}")
    
    def _extract_with_llm(self) -> Dict[str, Any]:
        """Use LLM to intelligently extract structured CV data."""
        text = self.full_text or self._extract_raw_text()
        
        prompt = f"""Extract structured information from this CV/Resume text and return ONLY valid JSON (no markdown, no explanations, no code blocks).

CV Text:
{text}

Extract and return JSON with this exact structure:
{{
  "name": "candidate's full name",
  "email": "email address",
  "phone": "phone number",
  "location": "city, country",
  "linkedin": "linkedin URL if present",
  "summary": "professional summary or objective",
  "skills": ["skill1", "skill2", "skill3"],
  "languages": ["language1 - proficiency", "language2 - proficiency"],
  "certifications": ["cert1", "cert2"],
  "education": [
    {{
      "degree": "degree name",
      "institution": "university/school name",
      "period": "start - end year"
    }}
  ],
  "experience": [
    {{
      "company": "company name",
      "position": "job title",
      "period": "start - end date",
      "location": "city, country",
      "responsibilities": ["responsibility1", "responsibility2"]
    }}
  ]
}}

Rules:
1. Extract ONLY information that is present in the CV
2. For missing fields, use empty string "" or empty array []
3. Fix any obvious typos or formatting issues
4. Separate skills from certifications properly
5. Identify spoken languages (NOT programming languages)
6. Return ONLY the JSON object, nothing else"""

        print(f"INFO: Processing CV with LLM ({self.llm_model})...")
        start_time = time.time()
        
        try:
            llm_response = self._call_ollama(prompt)
            self.llm_processing_time = time.time() - start_time
            print(f"INFO: LLM processing completed in {self.llm_processing_time:.2f}s")
            
            # Clean the response - remove markdown code blocks if present
            llm_response = llm_response.strip()
            if llm_response.startswith('```'):
                # Remove markdown code blocks
                llm_response = re.sub(r'^```json\s*', '', llm_response)
                llm_response = re.sub(r'^```\s*', '', llm_response)
                llm_response = re.sub(r'\s*```$', '', llm_response)
                llm_response = llm_response.strip()
            
            # Parse JSON
            cv_data = json.loads(llm_response)
            return cv_data
            
        except json.JSONDecodeError as e:
            print(f"WARNING: LLM returned invalid JSON: {str(e)}")
            print(f"Response preview: {llm_response[:200]}")
            # Fallback to basic extraction
            return self._fallback_extraction()
        except Exception as e:
            print(f"WARNING: LLM processing failed: {str(e)}")
            return self._fallback_extraction()
    
    def _fallback_extraction(self) -> Dict[str, Any]:
        """Fallback to basic pattern-based extraction if LLM fails."""
        print("INFO: Using fallback extraction method")
        text = self.full_text
        
        # Basic email extraction
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        email_match = re.search(email_pattern, text)
        email = email_match.group(0) if email_match else ""
        
        # Basic phone extraction
        phone_patterns = [
            r'\+?\d{1,3}[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',
            r'\+?\d{10,13}',
        ]
        phone = ""
        for pattern in phone_patterns:
            phone_match = re.search(pattern, text)
            if phone_match:
                phone = phone_match.group(0).strip()
                break
        
        return {
            "name": "",
            "email": email,
            "phone": phone,
            "location": "",
            "linkedin": "",
            "summary": "",
            "skills": [],
            "languages": [],
            "certifications": [],
            "education": [],
            "experience": []
        }
    
    def parse(self) -> Dict[str, Any]:
        """
        Parse the CV and extract all structured information using LLM.
        
        Returns:
            Dictionary with structured CV data
        """
        # Extract raw text first
        self._extract_raw_text()
        
        # Use LLM to extract structured data
        cv_data = self._extract_with_llm()
        
        # Build final response with metadata
        result = {
            'file_name': os.path.basename(self.pdf_path),
            'personal_info': {
                'name': cv_data.get('name', ''),
                'contact': {
                    'email': cv_data.get('email', ''),
                    'phone': cv_data.get('phone', ''),
                    'location': cv_data.get('location', ''),
                    'linkedin': cv_data.get('linkedin', '')
                }
            },
            'summary': cv_data.get('summary', ''),
            'skills': cv_data.get('skills', []),
            'languages': cv_data.get('languages', []),
            'certifications': cv_data.get('certifications', []),
            'education': cv_data.get('education', []),
            'experience': cv_data.get('experience', []),
            'metadata': {
                'page_count': self.page_count,
                'parser': f'LLM ({self.llm_model})',
                'extraction_time': round(self.extraction_time, 2),
                'llm_processing_time': round(self.llm_processing_time, 2),
                'total_time': round(self.extraction_time + self.llm_processing_time, 2)
            }
        }
        
        return result
    
    def save_to_json(self, output_path: str, indent: int = 2) -> str:
        """
        Parse CV and save to JSON file.
        
        Args:
            output_path: Path for the output JSON file
            indent: JSON indentation (default: 2)
            
        Returns:
            Path to the created JSON file
        """
        from pathlib import Path
        
        cv_data = self.parse()
        
        output_file = Path(output_path)
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(cv_data, f, indent=indent, ensure_ascii=False)
        
        return str(output_file)


def parse_cv(pdf_path: str, output_path: Optional[str] = None, llm_model: str = "llama3.1") -> Dict[str, Any]:
    """
    Convenience function to parse CV from PDF using LLM.
    
    Args:
        pdf_path: Path to the CV PDF file
        output_path: Path for output JSON file (optional)
        llm_model: Ollama model to use (default: llama3.1)
        
    Returns:
        Dictionary containing structured CV data
    """
    parser = CVParserLLM(pdf_path, llm_model=llm_model)
    cv_data = parser.parse()
    
    if output_path:
        parser.save_to_json(output_path)
    
    return cv_data


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python cv_parser_llm.py <cv_pdf_file> [output_json_file] [llm_model]")
        print("\nExamples:")
        print("  python cv_parser_llm.py cv.pdf")
        print("  python cv_parser_llm.py cv.pdf output.json")
        print("  python cv_parser_llm.py cv.pdf output.json llama3.1")
        print("\nAvailable Ollama models: llama3.1, llama3, mistral, phi3, gemma2")
        sys.exit(1)
    
    cv_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else cv_file.replace('.pdf', '_llm_parsed.json')
    llm_model = sys.argv[3] if len(sys.argv) > 3 else "llama3.1"
    
    try:
        print(f"\n{'='*60}")
        print(f"CV Parser - LLM Enhanced (Model: {llm_model})")
        print(f"{'='*60}\n")
        
        parser = CVParserLLM(cv_file, llm_model=llm_model)
        output_path = parser.save_to_json(output_file)
        
        # Show summary
        cv_data = parser.parse()
        metadata = cv_data['metadata']
        
        print(f"\n{'='*60}")
        print(f"[SUCCESS] Successfully parsed CV to JSON: {output_path}")
        print(f"{'='*60}\n")
        
        print(f"Performance Metrics:")
        print(f"  PDF Extraction: {metadata['extraction_time']}s")
        print(f"  LLM Processing: {metadata['llm_processing_time']}s")
        print(f"  Total Time: {metadata['total_time']}s")
        print(f"  Parser: {metadata['parser']}\n")
        
        print(f"Extracted Data:")
        print(f"  Name: {cv_data['personal_info']['name']}")
        print(f"  Email: {cv_data['personal_info']['contact'].get('email', 'N/A')}")
        print(f"  Phone: {cv_data['personal_info']['contact'].get('phone', 'N/A')}")
        print(f"  Skills: {len(cv_data['skills'])} found")
        print(f"  Experience: {len(cv_data['experience'])} positions")
        print(f"  Education: {len(cv_data['education'])} entries")
        print(f"  Certifications: {len(cv_data['certifications'])} found")
        print(f"  Languages: {len(cv_data['languages'])} found")
        
    except Exception as e:
        print(f"\n[ERROR] Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)



