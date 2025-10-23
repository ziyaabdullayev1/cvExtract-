"""
Test script for LLM-enhanced CV parser
"""
import sys
from cv_parser_llm import CVParserLLM

def test_llm_parser(pdf_path, llm_model="llama3.1"):
    """Test the LLM parser with a CV"""
    print(f"\n{'='*70}")
    print(f"Testing LLM Parser with: {pdf_path}")
    print(f"Model: {llm_model}")
    print(f"{'='*70}\n")
    
    try:
        parser = CVParserLLM(pdf_path, llm_model=llm_model)
        cv_data = parser.parse()
        
        print("\n✅ Parsing successful!")
        
        # Show performance metrics
        metadata = cv_data['metadata']
        print(f"\n⏱️  Performance Metrics:")
        print(f"  PDF Extraction: {metadata['extraction_time']}s")
        print(f"  LLM Processing: {metadata['llm_processing_time']}s")
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
            for skill in cv_data['skills'][:10]:  # Show first 10
                print(f"    • {skill}")
            if len(cv_data['skills']) > 10:
                print(f"    ... and {len(cv_data['skills']) - 10} more")
        
        if cv_data['experience']:
            print(f"\n  Experience ({len(cv_data['experience'])} positions):")
            for exp in cv_data['experience'][:3]:  # Show first 3
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
            print(f"    {', '.join(cv_data['languages'][:5])}")
        
        print(f"\n  Certifications: {len(cv_data['certifications'])} found")
        if cv_data['certifications']:
            for cert in cv_data['certifications'][:3]:
                print(f"    • {cert}")
        
        if cv_data['summary']:
            print(f"\n  Summary:")
            print(f"    {cv_data['summary'][:150]}...")
        
        print(f"\n{'='*70}")
        print("✨ LLM parser test completed successfully!")
        print(f"{'='*70}\n")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_llm_parser.py <cv_pdf_file> [llm_model]")
        print("\nExamples:")
        print("  python test_llm_parser.py uploads/Merve_YILDIZ_KOSE_CV.pdf")
        print("  python test_llm_parser.py uploads/Merve_YILDIZ_KOSE_CV.pdf mistral")
        print("\nAvailable models: llama3.1, llama3, mistral, phi3, gemma2")
        print("\nNote: Make sure Ollama is running (ollama serve)")
        sys.exit(1)
    
    cv_file = sys.argv[1]
    llm_model = sys.argv[2] if len(sys.argv) > 2 else "llama3.1"
    
    test_llm_parser(cv_file, llm_model)




