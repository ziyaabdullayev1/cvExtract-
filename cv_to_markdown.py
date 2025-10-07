"""
Convert CV data to Markdown format
"""


def cv_to_markdown(cv_data):
    """
    Convert extracted CV data to beautifully formatted Markdown.
    
    Args:
        cv_data: Dictionary containing structured CV data
        
    Returns:
        Markdown formatted string
    """
    md = []
    
    # Header
    name = cv_data.get('personal_info', {}).get('name', 'Resume')
    md.append(f"# {name}\n")
    
    # Contact Information
    contact = cv_data.get('personal_info', {}).get('contact', {})
    if contact:
        md.append("## Contact Information\n")
        if contact.get('email'):
            md.append(f"📧 **Email:** {contact['email']}  ")
        if contact.get('phone'):
            md.append(f"📱 **Phone:** {contact['phone']}  ")
        if contact.get('location'):
            md.append(f"📍 **Location:** {contact['location']}  ")
        if contact.get('linkedin'):
            md.append(f"💼 **LinkedIn:** {contact['linkedin']}  ")
        md.append("\n")
    
    # Professional Summary
    summary = cv_data.get('summary', '')
    if summary:
        md.append("## Professional Summary\n")
        md.append(f"{summary}\n\n")
    
    # Skills
    skills = cv_data.get('skills', [])
    if skills:
        md.append(f"## Skills ({len(skills)})\n")
        for skill in skills:
            md.append(f"- {skill}\n")
        md.append("\n")
    
    # Languages
    languages = cv_data.get('languages', [])
    if languages:
        md.append("## Languages\n")
        for lang in languages:
            md.append(f"- {lang}\n")
        md.append("\n")
    
    # Certifications
    certifications = cv_data.get('certifications', [])
    if certifications:
        md.append(f"## Certifications ({len(certifications)})\n")
        for cert in certifications:
            md.append(f"- {cert}\n")
        md.append("\n")
    
    # Education
    education = cv_data.get('education', [])
    if education:
        md.append("## Education\n")
        for edu in education:
            if edu.get('degree'):
                md.append(f"### {edu['degree']}\n")
            if edu.get('institution'):
                md.append(f"**Institution:** {edu['institution']}  \n")
            if edu.get('period'):
                md.append(f"**Period:** {edu['period']}  \n")
            if edu.get('details'):
                md.append(f"**Details:** {edu['details']}  \n")
            md.append("\n")
    
    # Work Experience
    experience = cv_data.get('experience', [])
    if experience:
        md.append(f"## Work Experience ({len(experience)} positions)\n")
        for exp in experience:
            position = exp.get('position', 'Position')
            company = exp.get('company', 'Company')
            md.append(f"### {position} at {company}\n")
            
            if exp.get('period'):
                md.append(f"**Period:** {exp['period']}  \n")
            if exp.get('location'):
                md.append(f"**Location:** {exp['location']}  \n")
            
            responsibilities = exp.get('responsibilities', [])
            if responsibilities:
                md.append("\n**Responsibilities:**\n")
                for resp in responsibilities:
                    md.append(f"- {resp}\n")
            md.append("\n")
    
    # Footer
    md.append("---\n")
    md.append(f"*Generated from: {cv_data.get('file_name', 'CV.pdf')}*\n")
    
    return ''.join(md)


if __name__ == "__main__":
    import json
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python cv_to_markdown.py <json_file> [output_md_file]")
        sys.exit(1)
    
    json_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else json_file.replace('.json', '.md')
    
    with open(json_file, 'r', encoding='utf-8') as f:
        cv_data = json.load(f)
    
    markdown = cv_to_markdown(cv_data)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(markdown)
    
    print(f"Markdown saved to: {output_file}")

