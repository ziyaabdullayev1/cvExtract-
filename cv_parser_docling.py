"""
CV Parser Module - Docling Version
Extracts structured data from CV/Resume PDFs using IBM Docling library.
Docling provides advanced document understanding and layout analysis.
"""

import re
import json
from typing import Dict, List, Any, Optional
import os

class CVParserDocling:
    """Parse CV/Resume PDFs and extract structured information using Docling."""
    
    def __init__(self, pdf_path: str):
        """
        Initialize the CV parser with Docling.
        
        Args:
            pdf_path: Path to the CV PDF file
        """
        self.pdf_path = pdf_path
        self.full_text = ""
        self.page_count = 0
        self.docling_doc = None
        self.actually_used_parser = "Docling"  # Track which parser was actually used
        
        # Precompile regex patterns for better performance
        self._email_pattern = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
        self._phone_patterns = [
            re.compile(r'\+?\d{1,3}[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'),
            re.compile(r'\+?\d{10,13}'),
            re.compile(r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}')
        ]
        self._linkedin_patterns = [
            re.compile(r'linkedin\.com/in/[\w-]+', re.IGNORECASE),
            re.compile(r'www\.linkedin\.com/in/[\w-]+', re.IGNORECASE)
        ]
        self._date_pattern = re.compile(r'([A-Z][a-z]+\s+\d{4}\s*-\s*(?:Present|[A-Z][a-z]+\s+\d{4}))')
    
    def _extract_raw_text(self) -> str:
        """Extract all text from the PDF using Docling."""
        if self.full_text:
            return self.full_text
        
        try:
            # Try to import and use Docling
            from docling.document_converter import DocumentConverter
            
            print("INFO: Using Docling for PDF extraction...")
            
            # Initialize Docling converter
            converter = DocumentConverter()
            
            # Convert the PDF document
            result = converter.convert(self.pdf_path)
            
            # Store the document object for later use
            self.docling_doc = result.document
            
            # Extract text content - prefer plain text over markdown for better parsing
            if hasattr(result.document, 'export_to_text'):
                # Use plain text export for better compatibility with extraction logic
                self.full_text = result.document.export_to_text()
                print("INFO: Successfully extracted text using Docling (text)")
            elif hasattr(result.document, 'export_to_markdown'):
                # If only markdown is available, convert it to plain text
                markdown_text = result.document.export_to_markdown()
                # Clean markdown syntax
                import re
                self.full_text = self._clean_markdown(markdown_text)
                print("INFO: Successfully extracted text using Docling (markdown->text)")
            else:
                # Fallback: extract text from pages
                all_text = []
                for page in result.document.pages:
                    if hasattr(page, 'text'):
                        all_text.append(page.text)
                    elif hasattr(page, 'export_to_text'):
                        all_text.append(page.export_to_text())
                self.full_text = '\n'.join(all_text)
                print("INFO: Successfully extracted text using Docling (pages)")
            
            # Get page count
            if hasattr(result.document, 'pages'):
                self.page_count = len(result.document.pages)
            
        except ImportError as e:
            # Fallback to PyMuPDF if Docling is not installed
            print(f"WARNING: Docling not installed ({e}). Falling back to PyMuPDF.")
            self._fallback_to_pymupdf()
        
        except Exception as e:
            error_msg = str(e)
            print(f"WARNING: Docling extraction failed: {error_msg[:200]}")
            
            # Check for specific errors and provide helpful messages
            if "transformers" in error_msg.lower() or "rt_detr" in error_msg.lower():
                print("HINT: Docling requires transformers>=4.40.0. Run: pip install --upgrade transformers")
            elif "torch" in error_msg.lower():
                print("HINT: Docling requires PyTorch. Run: pip install torch")
            
            print("INFO: Falling back to PyMuPDF for text extraction...")
            self._fallback_to_pymupdf()
        
        return self.full_text
    
    def _clean_markdown(self, markdown_text: str) -> str:
        """Convert markdown to plain text by removing markdown syntax."""
        text = markdown_text
        
        # Remove HTML comments
        text = re.sub(r'<!--.*?-->', '', text, flags=re.DOTALL)
        
        # Remove markdown headers (##, ###, etc.) - keep the text
        text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
        
        # Replace HTML entities
        text = text.replace('&amp;', '&')
        text = text.replace('&lt;', '<')
        text = text.replace('&gt;', '>')
        text = text.replace('&quot;', '"')
        
        # Remove markdown bold/italic (* or _)
        text = re.sub(r'\*\*([^\*]+)\*\*', r'\1', text)  # **bold**
        text = re.sub(r'\*([^\*]+)\*', r'\1', text)      # *italic*
        text = re.sub(r'__([^_]+)__', r'\1', text)       # __bold__
        text = re.sub(r'_([^_]+)_', r'\1', text)         # _italic_
        
        # Clean up bullet points
        text = re.sub(r'^\s*[-\*+]\s+--', '- ', text, flags=re.MULTILINE)
        text = re.sub(r'^\s*[-\*+]\s+', '- ', text, flags=re.MULTILINE)
        
        # Clean up extra whitespace
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        return text.strip()
    
    def _fallback_to_pymupdf(self):
        """Fallback method to extract text using PyMuPDF."""
        import fitz
        all_text = []
        doc = fitz.open(self.pdf_path)
        self.page_count = doc.page_count
        
        for page in doc:
            text = page.get_text("text")
            if text:
                all_text.append(text)
        
        doc.close()
        self.full_text = '\n'.join(all_text)
        self.actually_used_parser = "PyMuPDF (Docling fallback)"
        print(f"INFO: Successfully extracted text using PyMuPDF fallback ({self.page_count} pages)")
    
    def extract_name(self) -> str:
        """Extract candidate name from CV."""
        text = self.full_text or self._extract_raw_text()
        lines = text.split('\n')
        
        # Special case: Look for "Contact [Name]" pattern
        for i, line in enumerate(lines[:10]):
            if line.strip().startswith('Contact '):
                name_part = line.replace('Contact', '').strip()
                if name_part and len(name_part.split()) >= 2:
                    return name_part
        
        # Try to find name in first few lines
        for i, line in enumerate(lines[:15]):
            line = line.strip()
            
            if not line or len(line) < 3:
                continue
            
            skip_keywords = ['top skills', 'summary', 'education', 'experience',
                           'objective', 'qualification', 'certification', 'it governance',
                           'it services', 'it project', 'management', 'languages']
            if any(keyword in line.lower() for keyword in skip_keywords):
                continue
            
            if line.lower().startswith(('resume', 'cv', 'curriculum', 'contact')):
                continue
            
            words = line.split()
            if 2 <= len(words) <= 5:
                if any(c.isupper() for c in line):
                    if not any(char in line for char in ['@', '+', '/', 'www', 'http', ':', '•']):
                        if line.count(',') <= 1 and line.count('-') <= 1:
                            capital_words = [w for w in words if w and len(w) > 1 and (w[0].isupper() or w.isupper())]
                            if len(capital_words) >= 2:
                                if not any(word.lower() in ['skills', 'certified', 'lead', 'manager', 'analyst', 'developer'] for word in words):
                                    return line
        
        return ""
    
    def extract_contact_info(self) -> Dict[str, str]:
        """Extract contact information: phone, email, LinkedIn, location."""
        text = self.full_text or self._extract_raw_text()
        contact = {}
        lines = text.split('\n')
        
        # Email
        email_match = self._email_pattern.search(text)
        if email_match:
            contact['email'] = email_match.group(0)
        
        # Phone
        for pattern in self._phone_patterns:
            phone_match = pattern.search(text)
            if phone_match:
                contact['phone'] = phone_match.group(0).strip()
                break
        
        # LinkedIn
        for pattern in self._linkedin_patterns:
            linkedin_match = pattern.search(text)
            if linkedin_match:
                contact['linkedin'] = linkedin_match.group(0)
                break
        
        # Location
        for line in lines[:20]:
            line_stripped = line.strip()
            
            name = self.extract_name()
            if line_stripped == name or name in line_stripped and len(line_stripped) < len(name) + 5:
                continue
            
            if '|' in line:
                segments = [s.strip() for s in line.split('|')]
                for segment in segments:
                    city_country_match = re.match(r'^([A-Z][a-zA-Z\s]+,\s*[A-Z][a-zA-Z]+)$', segment)
                    if city_country_match:
                        location = city_country_match.group(1).strip()
                        common_locations = ['Turkey', 'USA', 'UK', 'Germany', 'France', 'Spain', 'Italy',
                                          'Istanbul', 'Ankara', 'New York', 'London', 'Paris', 'Berlin',
                                          'California', 'Texas', 'Canada', 'Australia', 'India', 'China']
                        if any(word in location for word in common_locations):
                            contact['location'] = location
                            break
                if 'location' in contact:
                    break
            
            city_country_match = re.match(r'^([A-Z][a-zA-Z\s]+,\s*[A-Z][a-zA-Z]+)$', line_stripped)
            if city_country_match:
                location = city_country_match.group(1).strip()
                common_locations = ['Turkey', 'USA', 'UK', 'Germany', 'France', 'Spain', 'Italy',
                                  'Istanbul', 'Ankara', 'New York', 'London', 'Paris', 'Berlin']
                if any(word in location for word in common_locations):
                    contact['location'] = location
                    break
        
        return contact
    
    def extract_summary(self) -> str:
        """Extract professional summary or objective."""
        text = self.full_text or self._extract_raw_text()
        lines = text.split('\n')
        
        summary_lines = []
        capturing = False
        
        for i, line in enumerate(lines):
            line_stripped = line.strip()
            
            if not capturing and re.search(r'(Certified|experience|years)', line_stripped, re.IGNORECASE):
                if len(line_stripped) > 20:
                    capturing = True
                    summary_lines.append(line_stripped)
                    continue
            
            if capturing:
                if re.match(r'^(Skills|Experience|Education|Certifications|Languages)[:]*$', line_stripped, re.IGNORECASE):
                    break
                
                if line_stripped and len(line_stripped) > 10:
                    if not re.match(r'^[\-•·]', line_stripped) and not re.search(r'\d{4}', line_stripped):
                        summary_lines.append(line_stripped)
                
                if len(' '.join(summary_lines).split()) > 50:
                    break
        
        if summary_lines:
            summary = ' '.join(summary_lines)
            summary = re.sub(r'\s+', ' ', summary)
            summary = re.sub(r'^[a-z]+[a-z0-9]*\s+', '', summary)
            summary = re.sub(r'\s*(Top Skills|Certifications|Languages).*', '', summary, flags=re.IGNORECASE)
            return summary.strip()
        
        return ""
    
    def extract_skills(self) -> List[str]:
        """Extract clean skill names from CV."""
        text = self.full_text or self._extract_raw_text()
        lines = text.split('\n')
        skills = []
        
        in_skills_section = False
        skills_line_count = 0
        
        for line in lines:
            line = line.strip()
            
            if re.match(r'^(Top\s+)?Skills:?$', line, re.IGNORECASE):
                in_skills_section = True
                skills_line_count = 0
                continue
            
            if in_skills_section and re.match(r'^(Languages|Certifications|Experience|Education):?$', line, re.IGNORECASE):
                break
            
            if in_skills_section:
                skills_line_count += 1
                
                if ',' in line:
                    parts = line.split(',')
                    for part in parts:
                        clean_skill = part.strip()
                        clean_skill = re.sub(r'^in\s+', '', clean_skill, flags=re.IGNORECASE)
                        if clean_skill and len(clean_skill) > 2 and not clean_skill.lower().startswith(('page ', 'www.')):
                            skills.append(clean_skill)
                else:
                    clean_skill = re.sub(r'^in\s+', '', line, flags=re.IGNORECASE).strip()
                    if clean_skill and len(clean_skill) > 2:
                        skills.append(clean_skill)
                
                if skills_line_count > 10:
                    break
        
        # Remove duplicates
        seen = set()
        unique_skills = []
        for skill in skills:
            skill_lower = skill.lower().strip()
            if skill_lower not in seen and len(skill) > 2:
                seen.add(skill_lower)
                unique_skills.append(skill)
        
        return unique_skills[:25]
    
    def extract_languages(self) -> List[str]:
        """Extract spoken languages (NOT programming languages)."""
        text = self.full_text or self._extract_raw_text()
        
        programming_langs = ['java', 'python', 'c#', 'c++', '.net', 'javascript', 'html', 'css', 
                           'php', 'ruby', 'go', 'rust', 'swift', 'kotlin', 'typescript', 'sql']
        
        spoken_lang_keywords = ['English', 'Turkish', 'Spanish', 'French', 'German', 'Italian', 
                               'Portuguese', 'Russian', 'Chinese', 'Japanese', 'Korean', 'Arabic']
        
        for lang_match in re.finditer(r'LANGUAGES', text, re.IGNORECASE):
            start_pos = lang_match.end()
            next_section = re.search(r'\n([A-Z][A-Z\s]+)\n', text[start_pos:start_pos+500])
            if next_section:
                lang_text = text[start_pos:start_pos + next_section.start()].strip()
            else:
                lang_text = text[start_pos:start_pos+500].strip()
            
            has_proficiency = any(word in lang_text for word in ['Native', 'Fluent', 'Intermediate', 'Basic', 'Beginner', 'Upper', 'Advanced', 'A1', 'A2', 'B1', 'B2', 'C1', 'C2'])
            has_spoken_lang = any(lang in lang_text for lang in spoken_lang_keywords)
            has_programming = any(prog in lang_text.lower() for prog in programming_langs[:5])
            
            if (has_proficiency or has_spoken_lang) and not has_programming:
                langs = re.split(r'[,\n•·]', lang_text)
                cleaned_langs = []
                for lang in langs:
                    lang = lang.strip()
                    if not lang or len(lang) < 3:
                        continue
                    if any(prog == lang.lower() for prog in programming_langs):
                        continue
                    if lang.upper() in ['LANGUAGES', 'ADDITIONAL INFORMATION', 'PROGRAMMING LANGUAGES', 'CERTIFICATIONS']:
                        continue
                    if lang.lower().startswith(('for full', 'page ', 'www.', 'http')):
                        continue
                    lang = re.sub(r'\s*[–-]\s*', ' - ', lang)
                    cleaned_langs.append(lang)
                
                if cleaned_langs:
                    return cleaned_langs[:10]
        
        return []
    
    def extract_certifications(self) -> List[str]:
        """Extract certifications and licenses."""
        text = self.full_text or self._extract_raw_text()
        
        patterns = [
            r'Certifications?[:\s]*\n(.+?)(?=\nLANGUAGES|\nADDITIONAL|\nEDUCATION|\nEXPERIENCE|$)',
            r'CERTIFICATIONS[:\s]*\n(.+?)(?=\nLANGUAGES|\nADDITIONAL|\nEDUCATION|\nEXPERIENCE|$)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                cert_text = match.group(1)
                certs = [line.strip() for line in cert_text.split('\n') if line.strip()]
                filtered_certs = []
                for cert in certs:
                    if cert.lower().startswith(('page ', 'www.', 'http', 'for full list')):
                        continue
                    if len(cert) < 5:
                        continue
                    if cert.upper() in ['LANGUAGES', 'ADDITIONAL INFORMATION', 'EDUCATION', 'EXPERIENCE']:
                        break
                    filtered_certs.append(cert)
                return filtered_certs
        
        return []
    
    def extract_education(self) -> List[Dict[str, str]]:
        """Extract education history."""
        text = self.full_text or self._extract_raw_text()
        education = []
        
        patterns = [
            r'Education[:\s]*\n(.+?)(?=\nEXPERIENCE|\nCERTIFICATIONS|\nSKILLS|$)',
            r'EDUCATION[:\s]*\n(.+?)(?=\nEXPERIENCE|\nCERTIFICATIONS|\nSKILLS|$)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                edu_text = match.group(1)
                lines = [line.strip() for line in edu_text.split('\n') if line.strip()]
                
                current_edu = {}
                for line in lines:
                    if line.upper() in ['EXPERIENCE', 'CERTIFICATIONS', 'SKILLS', 'LANGUAGES']:
                        break
                    
                    if line.lower().startswith(('page ', 'www.', 'http')):
                        continue
                    
                    if any(keyword in line.lower() for keyword in ['bachelor', 'master', 'phd', 'degree', 'diploma']):
                        if current_edu:
                            education.append(current_edu)
                        current_edu = {'degree': line}
                    elif re.search(r'\d{4}', line) and not current_edu.get('period'):
                        current_edu['period'] = line
                    elif len(line) > 5:
                        if 'institution' not in current_edu:
                            current_edu['institution'] = line
                        elif 'details' not in current_edu and 'period' in current_edu:
                            current_edu['details'] = line
                
                if current_edu:
                    education.append(current_edu)
                
                if education:
                    return education
        
        return education
    
    def extract_experience(self) -> List[Dict[str, Any]]:
        """Extract work experience."""
        text = self.full_text or self._extract_raw_text()
        lines = text.split('\n')
        experiences = []
        
        # Try to find EXPERIENCE section explicitly
        exp_section_match = re.search(r'EXPERIENCE[:\s]*\n(.+?)(?=\nEDUCATION|\nCERTIFICATIONS|\nSKILLS|$)', text, re.IGNORECASE | re.DOTALL)
        if exp_section_match:
            exp_text = exp_section_match.group(1)
            exp_lines = [l.strip() for l in exp_text.split('\n') if l.strip()]
            
            current_exp = {}
            for i, line in enumerate(exp_lines):
                if re.search(r'(Specialist|Engineer|Developer|Manager|Analyst|Lead|Consultant|Intern|QA|Tester)', line, re.IGNORECASE):
                    if not any(word in line.lower() for word in ['testing', 'reported', 'performed', 'developed']):
                        if current_exp:
                            experiences.append(current_exp)
                        current_exp = {'position': line, 'company': '', 'period': '', 'location': '', 'responsibilities': []}
                
                elif ',' in line and len(line) < 100:
                    if 'company' not in current_exp or not current_exp['company']:
                        current_exp['company'] = line
                
                elif re.search(r'(20\d{2}|Present|January|February|March|April|May|June|July|August|September|October|November|December)', line, re.IGNORECASE):
                    if 'period' not in current_exp or not current_exp['period']:
                        current_exp['period'] = line
                
                elif line.startswith('•') or line.startswith('�'):
                    if current_exp:
                        current_exp['responsibilities'].append(line.lstrip('•�').strip())
            
            if current_exp:
                experiences.append(current_exp)
            
            if experiences:
                return experiences
        
        return experiences
    
    def parse(self) -> Dict[str, Any]:
        """
        Parse the CV and extract all structured information.
        
        Returns:
            Dictionary with structured CV data
        """
        # Extract raw text first
        self._extract_raw_text()
        
        # Extract all sections
        cv_data = {
            'file_name': os.path.basename(self.pdf_path),
            'personal_info': {
                'name': self.extract_name(),
                'contact': self.extract_contact_info()
            },
            'summary': self.extract_summary(),
            'skills': self.extract_skills(),
            'languages': self.extract_languages(),
            'certifications': self.extract_certifications(),
            'education': self.extract_education(),
            'experience': self.extract_experience(),
            'metadata': {
                'page_count': self.page_count,
                'parser': self.actually_used_parser
            }
        }
        
        return cv_data
    
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


def parse_cv(pdf_path: str, output_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Convenience function to parse CV from PDF.
    
    Args:
        pdf_path: Path to the CV PDF file
        output_path: Path for output JSON file (optional)
        
    Returns:
        Dictionary containing structured CV data
    """
    parser = CVParserDocling(pdf_path)
    cv_data = parser.parse()
    
    if output_path:
        parser.save_to_json(output_path)
    
    return cv_data


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python cv_parser_docling.py <cv_pdf_file> [output_json_file]")
        sys.exit(1)
    
    cv_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else cv_file.replace('.pdf', '_parsed.json')
    
    try:
        parser = CVParserDocling(cv_file)
        output_path = parser.save_to_json(output_file)
        print(f"[SUCCESS] Successfully parsed CV to JSON: {output_path}")
        
        # Show summary
        cv_data = parser.parse()
        print(f"\nExtracted Data:")
        print(f"  Name: {cv_data['personal_info']['name']}")
        print(f"  Email: {cv_data['personal_info']['contact'].get('email', 'N/A')}")
        print(f"  Skills: {len(cv_data['skills'])} found")
        print(f"  Experience: {len(cv_data['experience'])} positions")
        print(f"  Education: {len(cv_data['education'])} entries")
        print(f"  Certifications: {len(cv_data['certifications'])} found")
        print(f"  Parser: {cv_data['metadata']['parser']}")
        
    except Exception as e:
        print(f"[ERROR] Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

