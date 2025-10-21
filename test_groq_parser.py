"""
Test script for Groq LLM-enhanced CV parser
"""
import sys
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from cv_parser_groq import CVParserGroq

def test_groq_parser(pdf_path, model="llama-3.3-70b-versatile"):
    """Test the Groq parser with a CV"""
    print(f"\n{'='*70}")
    print(f"Testing Groq LLM Parser with: {pdf_path}")
    print(f"Model: {model}")
    print(f"{'='*70}\n")
    
    try:
        parser = CVParserGroq(pdf_path, model=model)
        cv_data = parser.parse()
        
        print("\n✅ Parsing successful!")
        
        # Show performance metrics
        metadata = cv_data['metadata']
        print(f"\n⏱️  Performance Metrics:")
        print(f"  PDF Extraction: {metadata['extraction_time']}s")
        print(f"  Groq Processing: {metadata['llm_processing_time']}s ⚡")
        print(f"  Total Time: {metadata['total_time']}s")
        print(f"  Parser: {metadata['parser']}")
        
        # Show extracted data
        print(f"\n📋 Extracted Data:")
        print(f"  Name: {cv_data['personal_info']['name']}")
        print(f"  Email: {cv_data['personal_info']['contact'].get('email', 'N/A')}")
        print(f"  Phone: {cv_data['personal_info']['contact'].get('phone', 'N/A')}")
        print(f"  Location: {cv_data['personal_info']['contact'].get('location', 'N/A')}")
        
        if cv_data['skills']:
            print(f"\n  Skills ({len(cv_data['skills'])} found):")
            for skill in cv_data['skills'][:10]:
                print(f"    • {skill}")
            if len(cv_data['skills']) > 10:
                print(f"    ... and {len(cv_data['skills']) - 10} more")
        
        if cv_data['experience']:
            print(f"\n  Experience ({len(cv_data['experience'])} positions):")
            for exp in cv_data['experience']:
                print(f"    • {exp.get('position', 'N/A')} at {exp.get('company', 'N/A')}")
                if exp.get('period'):
                    print(f"      Period: {exp['period']}")
        
        if cv_data['education']:
            print(f"\n  Education ({len(cv_data['education'])} entries):")
            for edu in cv_data['education']:
                print(f"    • {edu.get('degree', 'N/A')}")
                if edu.get('institution'):
                    print(f"      {edu['institution']}")
        
        print(f"\n  Languages: {len(cv_data['languages'])} found")
        if cv_data['languages']:
            for lang in cv_data['languages']:
                print(f"    • {lang}")
        
        print(f"\n  Certifications: {len(cv_data['certifications'])} found")
        if cv_data['certifications']:
            for cert in cv_data['certifications'][:5]:
                print(f"    • {cert}")
            if len(cv_data['certifications']) > 5:
                print(f"    ... and {len(cv_data['certifications']) - 5} more")
        
        if cv_data['summary']:
            print(f"\n  Summary:")
            summary = cv_data['summary']
            if len(summary) > 200:
                print(f"    {summary[:200]}...")
            else:
                print(f"    {summary}")
        
        print(f"\n{'='*70}")
        print("✨ Groq parser test completed successfully!")
        print(f"{'='*70}\n")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_groq_parser.py <cv_pdf_file> [model]")
        print("\nExamples:")
        print("  python test_groq_parser.py uploads/Merve_YILDIZ_KOSE_CV.pdf")
        print("  python test_groq_parser.py uploads/Merve_YILDIZ_KOSE_CV.pdf llama-3.3-70b-versatile")
        print("\nAvailable Groq models:")
        print("  - llama-3.3-70b-versatile (Recommended, newest & most accurate)")
        print("  - llama3-70b-8192 (Good quality)")
        print("  - mixtral-8x7b-32768 (Good alternative)")
        print("  - llama3-8b-8192 (Faster, lighter)")
        sys.exit(1)
    
    cv_file = sys.argv[1]
    model = sys.argv[2] if len(sys.argv) > 2 else "llama-3.3-70b-versatile"
    
    test_groq_parser(cv_file, model)

