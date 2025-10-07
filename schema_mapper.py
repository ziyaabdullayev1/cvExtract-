"""
Map CV data to custom JSON schema
"""

import json
import re


def map_to_schema(cv_data, schema):
    """
    Map extracted CV data to a custom user-defined schema.
    
    Args:
        cv_data: Dictionary containing extracted CV data
        schema: Dictionary or string containing the target schema
        
    Returns:
        Dictionary with data mapped to the custom schema
    """
    if isinstance(schema, str):
        try:
            schema = json.loads(schema)
        except json.JSONDecodeError:
            raise ValueError("Invalid JSON schema provided")
    
    def map_value(schema_value, cv_data, is_array_item=False):
        """Recursively map schema to CV data"""
        if isinstance(schema_value, dict):
            result = {}
            for key, value in schema_value.items():
                result[key] = map_value(value, cv_data, is_array_item)
            return result
        elif isinstance(schema_value, list):
            if len(schema_value) > 0:
                # If schema has array with template, use it for CV data arrays
                template = schema_value[0]
                array_data = get_array_data(cv_data)
                return [map_value(template, item, is_array_item=True) for item in array_data]
            return []
        elif isinstance(schema_value, str):
            # Map schema placeholder to actual CV data
            return get_cv_field(schema_value, cv_data, is_array_item)
        else:
            return schema_value
    
    return map_value(schema, cv_data)


def get_cv_field(field_type, cv_data, is_array_item=False):
    """
    Get CV field based on type hint in schema.
    
    Common mappings:
    - "string" -> empty string or first available text
    - "number" -> 0 or first available number
    - "email" -> extracted email
    - "phone" -> extracted phone
    - "name" -> candidate name
    - etc.
    
    Args:
        field_type: The field type from schema
        cv_data: CV data or experience item (if is_array_item=True)
        is_array_item: Whether we're mapping an array item (experience entry)
    """
    field_lower = field_type.lower()
    
    # If this is an array item (experience entry), cv_data is the experience dict
    if is_array_item:
        if "company" in field_lower or "employer" in field_lower:
            return cv_data.get('company', '')
        if "position" in field_lower or "role" in field_lower or "title" in field_lower:
            return cv_data.get('position', '')
        if "duration" in field_lower or "period" in field_lower or "date" in field_lower or "time" in field_lower:
            # Try period first, if empty, construct from other fields
            period = cv_data.get('period', '')
            if not period:
                # Check if there's a date field or other time info
                period = cv_data.get('date', '')
            return period
        if "location" in field_lower or "city" in field_lower:
            return cv_data.get('location', '')
        if "responsibility" in field_lower or "responsibilities" in field_lower or "duty" in field_lower or "duties" in field_lower:
            responsibilities = cv_data.get('responsibilities', [])
            # If it's a list, join first 3 items
            if isinstance(responsibilities, list) and responsibilities:
                return '; '.join(responsibilities[:3])
            return responsibilities if responsibilities else ''
        if field_lower == "string":
            return ""
        if field_lower == "number":
            return 0
        return field_type
    
    # Standard CV data mapping
    if field_lower == "name" or "name" in field_lower:
        return cv_data.get('personal_info', {}).get('name', '')
    
    if field_lower == "email" or "email" in field_lower:
        return cv_data.get('personal_info', {}).get('contact', {}).get('email', '')
    
    if field_lower == "phone" or "phone" in field_lower:
        return cv_data.get('personal_info', {}).get('contact', {}).get('phone', '')
    
    if field_lower == "location" or "address" in field_lower:
        return cv_data.get('personal_info', {}).get('contact', {}).get('location', '')
    
    if field_lower == "linkedin" or "profile" in field_lower:
        return cv_data.get('personal_info', {}).get('contact', {}).get('linkedin', '')
    
    if "summary" in field_lower or "objective" in field_lower:
        return cv_data.get('summary', '')
    
    if "skill" in field_lower:
        skills = cv_data.get('skills', [])
        if isinstance(skills, list) and skills:
            # Clean up and return all skills
            clean_skills = [s.strip() for s in skills if s.strip()]
            return ', '.join(clean_skills)
        return ''
    
    if "language" in field_lower:
        languages = cv_data.get('languages', [])
        if isinstance(languages, list) and languages:
            # Extract only actual language names (skip descriptive text)
            clean_langs = []
            common_langs = ['english', 'french', 'turkish', 'spanish', 'german', 'italian', 'portuguese', 
                          'russian', 'chinese', 'japanese', 'arabic', 'hindi', 'korean']
            for lang in languages:
                lang_lower = lang.lower().strip()
                # Check if it's an actual language name
                for common_lang in common_langs:
                    if common_lang in lang_lower:
                        clean_langs.append(common_lang.capitalize())
            # Remove duplicates while preserving order
            seen = set()
            result_langs = []
            for lang in clean_langs:
                if lang not in seen:
                    seen.add(lang)
                    result_langs.append(lang)
            return ', '.join(result_langs) if result_langs else ''
        return ''
    
    if "education" in field_lower or "degree" in field_lower:
        education = cv_data.get('education', [])
        if education and len(education) > 0:
            return education[0].get('degree', '')
        return ''
    
    if "experience" in field_lower or "position" in field_lower or "job" in field_lower:
        experience = cv_data.get('experience', [])
        if experience and len(experience) > 0:
            return experience[0].get('position', '')
        return ''
    
    if "company" in field_lower or "employer" in field_lower:
        experience = cv_data.get('experience', [])
        if experience and len(experience) > 0:
            return experience[0].get('company', '')
        return ''
    
    # Type-based defaults
    if field_lower == "string":
        return ""
    elif field_lower == "number":
        return 0
    elif field_lower == "boolean":
        return False
    elif field_lower == "array":
        return []
    
    return field_type  # Return as-is if no mapping found


def get_array_data(cv_data):
    """Get array data from CV (skills, experience, etc.)"""
    # Return experience as the most common array type
    return cv_data.get('experience', [])


# Sample CV schema templates
SAMPLE_SCHEMAS = {
    "invoice": """{
  "invoice_number": "string",
  "customer_name": "string",
  "total_amount": "number",
  "date": "string",
  "items": [
    {
      "description": "string",
      "quantity": "number",
      "price": "number"
    }
  ]
}""",
    
    "resume": """{
  "candidate_name": "name",
  "contact_email": "email",
  "contact_phone": "phone",
  "location": "location",
  "professional_summary": "summary",
  "skills": "skills",
  "work_experience": [
    {
      "company": "company",
      "position": "position",
      "duration": "string",
      "responsibilities": "string"
    }
  ],
  "education": [
    {
      "degree": "degree",
      "institution": "string",
      "year": "string"
    }
  ]
}""",

    "simple": """{
  "full_name": "name",
  "email": "email",
  "phone": "phone",
  "summary": "summary"
}"""
}


if __name__ == "__main__":
    # Test with sample data
    cv_data = {
        "personal_info": {
            "name": "John Doe",
            "contact": {
                "email": "john@example.com",
                "phone": "+1234567890"
            }
        },
        "summary": "Experienced developer",
        "skills": ["Python", "JavaScript"],
        "experience": [
            {
                "company": "Tech Corp",
                "position": "Senior Developer",
                "period": "2020-2023"
            }
        ]
    }
    
    schema = {
        "name": "name",
        "email": "email",
        "skills": "skills"
    }
    
    result = map_to_schema(cv_data, schema)
    print(json.dumps(result, indent=2))

