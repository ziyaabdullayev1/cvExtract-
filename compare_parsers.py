#!/usr/bin/env python3
"""
Parser Performance Comparison Script
Compares pdfplumber vs PyMuPDF (fitz) extraction performance.
"""

import os
import time
import json
from cv_parser import CVParser
from cv_parser_fitz import CVParserFitz

def compare_single_file(pdf_path: str) -> dict:
    """
    Compare both parsers on a single file.
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        Dictionary with comparison results
    """
    print(f"\n{'='*60}")
    print(f"Testing: {os.path.basename(pdf_path)}")
    print(f"{'='*60}")
    
    results = {
        'filename': os.path.basename(pdf_path),
        'pdfplumber': {},
        'pymupdf': {},
        'speedup': 0
    }
    
    # Test pdfplumber version
    print("\nTesting pdfplumber (original)...")
    try:
        start_time = time.time()
        parser_plumber = CVParser(pdf_path)
        data_plumber = parser_plumber.parse()
        plumber_time = time.time() - start_time
        
        results['pdfplumber'] = {
            'time': round(plumber_time, 3),
            'time_ms': round(plumber_time * 1000, 2),
            'success': True,
            'name': data_plumber['personal_info']['name'],
            'email': data_plumber['personal_info']['contact'].get('email', 'N/A'),
            'skills_count': len(data_plumber['skills']),
            'experience_count': len(data_plumber['experience']),
            'education_count': len(data_plumber['education'])
        }
        print(f"  Time: {plumber_time:.3f}s ({plumber_time*1000:.2f}ms)")
        print(f"  Extracted: {results['pdfplumber']['skills_count']} skills, {results['pdfplumber']['experience_count']} positions")
        
    except Exception as e:
        print(f"  ERROR: {e}")
        results['pdfplumber'] = {'success': False, 'error': str(e)}
    
    # Test PyMuPDF version
    print("\nTesting PyMuPDF (fitz - optimized)...")
    try:
        start_time = time.time()
        parser_fitz = CVParserFitz(pdf_path)
        data_fitz = parser_fitz.parse()
        fitz_time = time.time() - start_time
        
        results['pymupdf'] = {
            'time': round(fitz_time, 3),
            'time_ms': round(fitz_time * 1000, 2),
            'success': True,
            'name': data_fitz['personal_info']['name'],
            'email': data_fitz['personal_info']['contact'].get('email', 'N/A'),
            'skills_count': len(data_fitz['skills']),
            'experience_count': len(data_fitz['experience']),
            'education_count': len(data_fitz['education'])
        }
        print(f"  Time: {fitz_time:.3f}s ({fitz_time*1000:.2f}ms)")
        print(f"  Extracted: {results['pymupdf']['skills_count']} skills, {results['pymupdf']['experience_count']} positions")
        
    except Exception as e:
        print(f"  ERROR: {e}")
        results['pymupdf'] = {'success': False, 'error': str(e)}
    
    # Calculate speedup
    if results['pdfplumber'].get('success') and results['pymupdf'].get('success'):
        speedup = results['pdfplumber']['time'] / results['pymupdf']['time']
        results['speedup'] = round(speedup, 2)
        
        time_saved = results['pdfplumber']['time'] - results['pymupdf']['time']
        percent_faster = ((results['pdfplumber']['time'] - results['pymupdf']['time']) / results['pdfplumber']['time']) * 100
        
        print(f"\n{'='*60}")
        print(f"PERFORMANCE COMPARISON")
        print(f"{'='*60}")
        print(f"PyMuPDF is {speedup:.2f}x FASTER than pdfplumber!")
        print(f"Time saved: {time_saved:.3f}s ({percent_faster:.1f}% faster)")
        print(f"{'='*60}")
        
        # Data quality comparison
        print(f"\nDATA QUALITY COMPARISON")
        print(f"{'='*60}")
        
        name_match = results['pdfplumber']['name'] == results['pymupdf']['name']
        email_match = results['pdfplumber']['email'] == results['pymupdf']['email']
        
        print(f"Name match: {'YES' if name_match else 'NO'}")
        print(f"  pdfplumber: {results['pdfplumber']['name']}")
        print(f"  PyMuPDF:    {results['pymupdf']['name']}")
        
        print(f"\nEmail match: {'YES' if email_match else 'NO'}")
        print(f"  pdfplumber: {results['pdfplumber']['email']}")
        print(f"  PyMuPDF:    {results['pymupdf']['email']}")
        
        skills_diff = abs(results['pdfplumber']['skills_count'] - results['pymupdf']['skills_count'])
        exp_diff = abs(results['pdfplumber']['experience_count'] - results['pymupdf']['experience_count'])
        
        print(f"\nSkills: pdfplumber={results['pdfplumber']['skills_count']}, PyMuPDF={results['pymupdf']['skills_count']} (diff: {skills_diff})")
        print(f"Experience: pdfplumber={results['pdfplumber']['experience_count']}, PyMuPDF={results['pymupdf']['experience_count']} (diff: {exp_diff})")
        
        # Quality verdict
        if name_match and email_match and skills_diff <= 2 and exp_diff <= 1:
            print(f"\n{'='*60}")
            print("VERDICT: Data quality is EQUIVALENT!")
            print("PyMuPDF is faster with no loss in extraction quality.")
            print(f"{'='*60}")
        else:
            print(f"\n{'='*60}")
            print("VERDICT: Minor differences detected")
            print("Review extracted data to ensure quality meets requirements.")
            print(f"{'='*60}")
    
    return results

def compare_all_files(directory: str = 'uploads'):
    """
    Compare both parsers on all PDFs in a directory.
    
    Args:
        directory: Directory containing PDF files
    """
    pdf_files = [f for f in os.listdir(directory) if f.endswith('.pdf')]
    
    if not pdf_files:
        print(f"No PDF files found in {directory}")
        return
    
    print(f"\nFound {len(pdf_files)} PDF file(s) to test")
    
    all_results = []
    total_plumber_time = 0
    total_fitz_time = 0
    
    for pdf_file in pdf_files:
        pdf_path = os.path.join(directory, pdf_file)
        result = compare_single_file(pdf_path)
        all_results.append(result)
        
        if result['pdfplumber'].get('success'):
            total_plumber_time += result['pdfplumber']['time']
        if result['pymupdf'].get('success'):
            total_fitz_time += result['pymupdf']['time']
    
    # Overall summary
    if len(pdf_files) > 1:
        print(f"\n{'='*60}")
        print(f"OVERALL SUMMARY ({len(pdf_files)} files)")
        print(f"{'='*60}")
        print(f"Total pdfplumber time: {total_plumber_time:.3f}s")
        print(f"Total PyMuPDF time: {total_fitz_time:.3f}s")
        
        if total_fitz_time > 0:
            overall_speedup = total_plumber_time / total_fitz_time
            time_saved = total_plumber_time - total_fitz_time
            print(f"\nOverall speedup: {overall_speedup:.2f}x")
            print(f"Total time saved: {time_saved:.3f}s")
            print(f"{'='*60}")
    
    # Save results to JSON
    results_file = 'parser_comparison_results.json'
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)
    
    print(f"\nDetailed results saved to: {results_file}")

def main():
    """Main function."""
    print("PDF Parser Performance Comparison")
    print("Comparing pdfplumber vs PyMuPDF (fitz)")
    print("="*60)
    
    # Check if uploads directory exists
    if not os.path.exists('uploads'):
        print("ERROR: 'uploads' directory not found")
        print("Please create an 'uploads' directory and add PDF files")
        return
    
    # Run comparison
    compare_all_files('uploads')

if __name__ == "__main__":
    main()

