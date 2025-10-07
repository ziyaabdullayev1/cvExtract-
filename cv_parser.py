"""
CV Parser Module
Extracts structured data from CV/Resume PDFs into organized JSON format.
"""

import re
from typing import Dict, List, Any, Optional
import pdfplumber


class CVParser:
    """Parse CV/Resume PDFs and extract structured information."""
    
    def __init__(self, pdf_path: str):
        """
        Initialize the CV parser.
        
        Args:
            pdf_path: Path to the CV PDF file
        """
        self.pdf_path = pdf_path
        self.full_text = ""
    
    def _extract_raw_text(self) -> str:
        """Extract all text from the PDF."""
        if self.full_text:
            return self.full_text
        
        # Extract text using pdfplumber
        all_text = []
        with pdfplumber.open(self.pdf_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    all_text.append(text)
        
        self.full_text = '\n'.join(all_text)
        return self.full_text
    
    def extract_name(self) -> str:
        """
        Extract candidate name from CV.
        Usually appears at the top of the CV.
        """
        text = self.full_text or self._extract_raw_text()
        lines = text.split('\n')
        
        # Special case: Look for "Contact [Name]" pattern
        for i, line in enumerate(lines[:10]):
            if line.strip().startswith('Contact '):
                # Extract name after "Contact"
                name_part = line.replace('Contact', '').strip()
                if name_part and len(name_part.split()) >= 2:
                    return name_part
        
        # Try to find name in first few lines
        for i, line in enumerate(lines[:15]):
            line = line.strip()
            
            # Skip common header words and empty lines
            if not line or len(line) < 3:
                continue
            
            # Skip lines with these keywords
            skip_keywords = ['top skills', 'summary', 'education', 'experience',
                           'objective', 'qualification', 'certification', 'it governance',
                           'it services', 'it project', 'management', 'languages']
            if any(keyword in line.lower() for keyword in skip_keywords):
                continue
            
            # Skip if it starts with common CV headers
            if line.lower().startswith(('resume', 'cv', 'curriculum', 'contact')):
                continue
            
            # Look for name pattern (2-5 words with capitals and possibly special chars like Ö, Ğ, İ)
            # Handle names like "Merve YILDIZ KÖSE"
            words = line.split()
            if 2 <= len(words) <= 5:
                # Check if it looks like a name (has uppercase letters)
                if any(c.isupper() for c in line):
                    # Avoid phone numbers, emails, URLs, or dates
                    if not any(char in line for char in ['@', '+', '/', 'www', 'http', ':', '•']):
                        # Avoid lines with too many commas or special chars
                        if line.count(',') <= 1 and line.count('-') <= 1:
                            # Check if words start with capital or are all caps
                            capital_words = [w for w in words if w and len(w) > 1 and (w[0].isupper() or w.isupper())]
                            if len(capital_words) >= 2:
                                # Make sure it's not a skill or job title line
                                if not any(word.lower() in ['skills', 'certified', 'lead', 'manager', 'analyst', 'developer'] for word in words):
                                    return line
        
        return ""
    
    def extract_contact_info(self) -> Dict[str, str]:
        """
        Extract contact information: phone, email, LinkedIn, location.
        """
        text = self.full_text or self._extract_raw_text()
        contact = {}
        lines = text.split('\n')
        
        # Email
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        email_match = re.search(email_pattern, text)
        if email_match:
            contact['email'] = email_match.group(0)
        
        # Phone (various formats)
        phone_patterns = [
            r'\+?\d{1,3}[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',  # +1-234-567-8900
            r'\+?\d{10,13}',  # +905322437822
            r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'  # (234) 567-8900
        ]
        for pattern in phone_patterns:
            phone_match = re.search(pattern, text)
            if phone_match:
                contact['phone'] = phone_match.group(0).strip()
                break
        
        # LinkedIn
        linkedin_patterns = [
            r'linkedin\.com/in/[\w-]+',
            r'www\.linkedin\.com/in/[\w-]+'
        ]
        for pattern in linkedin_patterns:
            linkedin_match = re.search(pattern, text, re.IGNORECASE)
            if linkedin_match:
                contact['linkedin'] = linkedin_match.group(0)
                break
        
        # Location - look for city-country pattern or all caps location
        # Check first 20 lines for location
        for line in lines[:20]:
            line = line.strip()
            # Pattern like "ISTANBUL-TURKEY" or "Istanbul, Turkey"
            if re.search(r'[A-Z]{2,}[-,\s]+[A-Z]{2,}', line):
                # Extract just the location part
                location_match = re.search(r'([A-Z][A-Za-z]+(?:[-\s][A-Z][A-Za-z]+)+)', line)
                if location_match:
                    contact['location'] = location_match.group(1)
                    break
            # Pattern like "Istanbul-Turkey" or "New York, USA"
            elif re.search(r'[A-Z][a-z]+[-,\s]+[A-Z][a-z]+', line) and 'Contact' not in line:
                location_match = re.search(r'([A-Z][A-Za-z]+(?:[-,\s]+[A-Z][A-Za-z]+)+)', line)
                if location_match and '@' not in line and '+' not in line:
                    contact['location'] = location_match.group(1)
                    break
        
        return contact
    
    def extract_summary(self) -> str:
        """
        Extract professional summary or objective.
        """
        text = self.full_text or self._extract_raw_text()
        lines = text.split('\n')
        
        # Find "Top Skills" section as the summary often appears after it
        summary_lines = []
        capturing = False
        
        for i, line in enumerate(lines):
            line_stripped = line.strip()
            
            # Start capturing after we see certain patterns
            if not capturing and re.search(r'(Certified|experience|years)', line_stripped, re.IGNORECASE):
                if len(line_stripped) > 20:  # Make sure it's substantial
                    capturing = True
                    summary_lines.append(line_stripped)
                    continue
            
            # If we're capturing, continue until we hit a section header
            if capturing:
                # Stop at section headers
                if re.match(r'^(Skills|Experience|Education|Certifications|Languages)[:]*$', line_stripped, re.IGNORECASE):
                    break
                
                # Add line if it's part of the summary
                if line_stripped and len(line_stripped) > 10:
                    # Skip if it starts with special chars or is a date
                    if not re.match(r'^[\-•·]', line_stripped) and not re.search(r'\d{4}', line_stripped):
                        summary_lines.append(line_stripped)
                
                # Stop after collecting enough content (around 200 words)
                if len(' '.join(summary_lines).split()) > 50:
                    break
        
        if summary_lines:
            summary = ' '.join(summary_lines)
            # Clean up
            summary = re.sub(r'\s+', ' ', summary)
            # Remove social media handles at the start
            summary = re.sub(r'^[a-z]+[a-z0-9]*\s+', '', summary)
            # Remove "Top Skills" and everything after if present
            summary = re.sub(r'\s*(Top Skills|Certifications|Languages).*', '', summary, flags=re.IGNORECASE)
            return summary.strip()
        
        return ""
    
    def extract_skills(self) -> List[str]:
        """
        Extract clean skill names from CV.
        """
        text = self.full_text or self._extract_raw_text()
        lines = text.split('\n')
        skills = []
        
        # Find "Top Skills" section or "Skills:" label
        in_skills_section = False
        skills_line_count = 0
        
        for line in lines:
            line = line.strip()
            
            # Detect start of skills section
            if re.match(r'^(Top\s+)?Skills:?$', line, re.IGNORECASE):
                in_skills_section = True
                skills_line_count = 0
                continue
            
            # Stop at next section
            if in_skills_section and re.match(r'^(Languages|Certifications|Experience|Education):?$', line, re.IGNORECASE):
                break
            
            # Extract skills from the section
            if in_skills_section:
                skills_line_count += 1
                
                # Split by comma and clean each skill
                if ',' in line:
                    parts = line.split(',')
                    for part in parts:
                        clean_skill = part.strip()
                        # Remove "in" prefix
                        clean_skill = re.sub(r'^in\s+', '', clean_skill, flags=re.IGNORECASE)
                        if clean_skill and len(clean_skill) > 2 and not clean_skill.lower().startswith(('page ', 'www.')):
                            skills.append(clean_skill)
                else:
                    # Single skill per line
                    clean_skill = re.sub(r'^in\s+', '', line, flags=re.IGNORECASE).strip()
                    if clean_skill and len(clean_skill) > 2:
                        skills.append(clean_skill)
                
                # Stop after reading ~10 lines from skills section
                if skills_line_count > 10:
                    break
        
        # If no skills section found, extract from common skill phrases
        if not skills:
            skill_patterns = [
                r'Skills?:\s*(.+)',
                r'(IT\s+\w+(?:\s+\w+){0,2})',  # IT followed by 1-3 words
                r'(Leadership|Communication|Problem-solving|Time-management)',
                r'(Team\s+(?:leader|player))',
                r'(Project\s+management|Data\s+analysis|Resource\s+management)'
            ]
            
            for pattern in skill_patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    skill = match.group(1).strip()
                    if skill and 5 < len(skill) < 60:
                        skills.append(skill)
        
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
        """
        Extract languages spoken.
        """
        text = self.full_text or self._extract_raw_text()
        
        # Look for languages section
        lang_pattern = r'Languages?[:\n]+(.+?)(?=\n\n[A-Z]|\nCertifications|\nExperience|\nEducation|$)'
        match = re.search(lang_pattern, text, re.IGNORECASE | re.DOTALL)
        
        if match:
            lang_text = match.group(1).strip()
            # Split by common delimiters
            langs = re.split(r'[,\n•·]', lang_text)
            return [lang.strip() for lang in langs if lang.strip() and len(lang.strip()) > 2][:10]
        
        return []
    
    def extract_certifications(self) -> List[str]:
        """
        Extract certifications and licenses.
        """
        text = self.full_text or self._extract_raw_text()
        
        # Look for certifications section
        cert_pattern = r'Certifications?[:\n]+(.+?)(?=\n\n[A-Z][a-z]+\s+[A-Z]|\nEducation|\nExperience|$)'
        match = re.search(cert_pattern, text, re.IGNORECASE | re.DOTALL)
        
        if match:
            cert_text = match.group(1)
            # Split by newlines
            certs = [line.strip() for line in cert_text.split('\n') if line.strip()]
            # Filter out noise
            certs = [c for c in certs if not c.lower().startswith(('page ', 'www.', 'http'))]
            return certs
        
        return []
    
    def extract_education(self) -> List[Dict[str, str]]:
        """
        Extract education history.
        """
        text = self.full_text or self._extract_raw_text()
        education = []
        
        # Look for education section
        edu_pattern = r'Education[:\n]+(.+?)(?=\nExperience|\nCertifications|$)'
        match = re.search(edu_pattern, text, re.IGNORECASE | re.DOTALL)
        
        if match:
            edu_text = match.group(1)
            lines = [line.strip() for line in edu_text.split('\n') if line.strip()]
            
            current_edu = {}
            for line in lines:
                # Check for degree patterns
                if any(keyword in line.lower() for keyword in ['bachelor', 'master', 'phd', 'degree', 'diploma']):
                    if current_edu:
                        education.append(current_edu)
                    current_edu = {'degree': line}
                # Check for year pattern
                elif re.search(r'\d{4}', line):
                    if 'period' not in current_edu:
                        current_edu['period'] = line
                # Otherwise it's likely institution name
                elif len(line) > 5 and not line.startswith('Page'):
                    if 'institution' not in current_edu:
                        current_edu['institution'] = line
                    elif 'details' not in current_edu:
                        current_edu['details'] = line
            
            if current_edu:
                education.append(current_edu)
        
        return education
    
    def extract_experience(self) -> List[Dict[str, Any]]:
        """
        Extract work experience with improved company name and duration extraction.
        Searches entire document for company names, not stopping at Education section.
        """
        text = self.full_text or self._extract_raw_text()
        lines = text.split('\n')
        experiences = []
        
        # Known company keywords to help identify companies (be specific!)
        company_keywords = ['Tobacco', 'Cosmetics', 'Coca-Cola', 'IBM', 'Bottlers', 'Icecek', 'Avon', 
                          'British American', 'BAT', 'CCI', 'Turkey']
        
        # Track the most recent company for positions that appear without a company
        last_company = None
        
        # Search entire document for companies (don't stop at Education)
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # Skip empty lines
            if not line or len(line) < 3:
                i += 1
                continue
            
            # Skip obvious non-company lines
            skip_words = ['certification', 'university', 'degree', 'page ', 'skills:', 
                         'languages:', 'toeic', 'itil', 'delf', 'dalf', 'pmp', 
                         'iso 27001', 'iso 22001', 'honors', 'lycée', 'bachelor',
                         'for turkey', 'participated:', 'markets:', 'owner,']
            if any(word in line.lower() for word in skip_words):
                i += 1
                continue
            
            # Check if this line contains a known company keyword
            # But it must be a clean match (not part of a longer project description)
            is_company = False
            for kw in company_keywords:
                if kw in line:
                    # Check if it's a simple company name (not embedded in a long description)
                    if len(line) < 50 and line.count(',') <= 1:
                        is_company = True
                        break
            
            # Additional filters for cleaner detection
            if is_company:
                # Skip if it's a location (starts with capital city name and ends with country)
                if re.match(r'^[A-Z][a-z]+,\s*[A-Z][a-z]+$', line):
                    is_company = False
                
                # Skip lines that are clearly project descriptions (contain parentheses with years)
                if re.search(r'\([12]\d{3}\)', line):
                    is_company = False
                
                # Skip lines with colons (usually descriptions, not company names)
                if ':' in line and len(line) > 25:
                    is_company = False
                
                # Skip lines with "project", "implementation", "upgrade", "module" in them (project descriptions)
                if any(word in line.lower() for word in ['project', 'implementation', 'upgrade', 'module', 'baseline']):
                    is_company = False
                
                # Skip if line contains "&" followed by more text (like "Turkey & International")
                if re.search(r'&\s+\w+', line):
                    is_company = False
            
            if is_company:
                # Clean up company name (remove project details, SAP implementations, etc.)
                company = line
                
                # If line contains SAP/implementation details, extract just the company part
                if 'SAP' in company or 'implementation' in company.lower():
                    # Try to extract just company name before "SAP" or other keywords
                    parts = re.split(r'\s+(?:SAP|implementation|&|Turkey|International)', company, flags=re.IGNORECASE)
                    if parts and len(parts[0]) > 10:
                        company = parts[0].strip()
                
                # Remove trailing special characters
                company = re.sub(r'[&\s]+$', '', company).strip()
                position = ""
                period = ""
                location = ""
                
                # Look ahead for position and date
                j = i + 1
                while j < len(lines) and j < i + 15:
                    next_line = lines[j].strip()
                    
                    if not next_line or len(next_line) < 3:
                        j += 1
                        continue
                    
                    # Skip certification/education lines
                    if any(word in next_line.lower() for word in skip_words):
                        j += 1
                        continue
                    
                    # CHECK FOR DATE FIRST (before skipping lines!)
                    date_pattern = r'([A-Z][a-z]+\s+\d{4}\s*-\s*(?:Present|[A-Z][a-z]+\s+\d{4}))'
                    date_match = re.search(date_pattern, next_line)
                    if date_match and not period:
                        period = date_match.group(1)
                        
                        # Check for duration in parentheses
                        duration_match = re.search(r'\(([0-9]+\s*(?:year|month)s?[^)]*)\)', next_line)
                        if duration_match:
                            period = date_match.group(1) + " (" + duration_match.group(1) + ")"
                        
                        j += 1
                        
                        # Check if next line is location
                        if j < len(lines):
                            loc_line = lines[j].strip()
                            # Location patterns: "Istanbul, Turkey" or "İstanbul - Turkey"
                            if re.match(r'^[A-ZİÖÜÇŞĞ][a-züğışçö]+[-,\s]+[A-Z][a-z]+$', loc_line, re.IGNORECASE):
                                location = loc_line
                                j += 1
                        break
                    
                    # Look for position (job title) if not found yet
                    if not position and len(next_line) > 5:
                        # Job titles typically contain these words or patterns
                        if re.search(r'(Manager|Analyst|Lead|Specialist|Director|Intern|Coordinator|Engineer|Developer|Owner|Officer|Tester|Performer|Solutions)', next_line, re.IGNORECASE):
                            # Make sure it's not another company name
                            if not any(kw in next_line for kw in company_keywords):
                                # Clean up position (remove parentheses with years, etc.)
                                clean_position = re.sub(r'\([12]\d{3}\)', '', next_line).strip()
                                clean_position = re.sub(r'\(.*?\)', '', clean_position).strip()
                                if clean_position:
                                    position = clean_position
                                    j += 1
                                    continue
                    
                    j += 1
                
                # Add experience if we have at least company and position
                if company and position:
                    experiences.append({
                        'company': company,
                        'position': position,
                        'period': period,
                        'location': location,
                        'responsibilities': []
                    })
                    last_company = company  # Remember this company for orphaned positions
                
                i = j
            
            # Check for orphaned positions (positions without a company before them)
            # This handles cases where position appears at top of page after company on previous page
            elif not is_company and len(line) > 10:
                # Check if this line looks like a position title
                if re.search(r'(Manager|Analyst|Lead|Specialist|Director|Intern|Coordinator|Engineer|Developer|Officer|Solutions)', line, re.IGNORECASE):
                    # Make sure it's not a description line
                    if not line.endswith(('.', ':', ';')) and not line.startswith(('For ', 'Managing', 'Supporting')):
                        orphan_position = line
                        orphan_period = ""
                        orphan_location = ""
                        
                        # Look ahead for date
                        j = i + 1
                        while j < len(lines) and j < i + 5:
                            next_line = lines[j].strip()
                            
                            # Look for date
                            date_pattern = r'([A-Z][a-z]+\s+\d{4}\s*-\s*(?:Present|[A-Z][a-z]+\s+\d{4}))'
                            date_match = re.search(date_pattern, next_line)
                            if date_match:
                                orphan_period = date_match.group(1)
                                # Check for duration
                                duration_match = re.search(r'\(([0-9]+\s*(?:year|month)s?[^)]*)\)', next_line)
                                if duration_match:
                                    orphan_period = date_match.group(1) + " (" + duration_match.group(1) + ")"
                                
                                j += 1
                                # Check for location
                                if j < len(lines):
                                    loc_line = lines[j].strip()
                                    if re.match(r'^[A-ZİÖÜÇŞĞ][a-züğışçö]+[-,\s]+[A-Z][a-z]+$', loc_line, re.IGNORECASE):
                                        orphan_location = loc_line
                                        j += 1
                                break
                            j += 1
                        
                        # If we found a date and have a last known company, add this orphaned position
                        if orphan_period and last_company:
                            # Clean up position name
                            clean_orphan_position = re.sub(r'\([12]\d{3}\)', '', orphan_position).strip()
                            clean_orphan_position = re.sub(r'\(.*?\)', '', clean_orphan_position).strip()
                            
                            if clean_orphan_position:
                                experiences.append({
                                    'company': last_company,
                                    'position': clean_orphan_position,
                                    'period': orphan_period,
                                    'location': orphan_location,
                                    'responsibilities': []
                                })
                                i = j
                                continue
                
                i += 1
            else:
                i += 1
        
        return experiences
    
    def parse(self) -> Dict[str, Any]:
        """
        Parse the CV and extract all structured information.
        
        Returns:
            Dictionary with structured CV data
        """
        import os
        
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
            'experience': self.extract_experience()
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
        import json
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
    parser = CVParser(pdf_path)
    cv_data = parser.parse()
    
    if output_path:
        parser.save_to_json(output_path)
    
    return cv_data


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python cv_parser.py <cv_pdf_file> [output_json_file]")
        sys.exit(1)
    
    cv_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else cv_file.replace('.pdf', '_parsed.json')
    
    try:
        parser = CVParser(cv_file)
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
        
    except Exception as e:
        print(f"[ERROR] Error: {e}")
        sys.exit(1)


