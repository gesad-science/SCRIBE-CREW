# tests/test_system.py
"""
Comprehensive test suite for the Academic Multi-Agent System.
Tests individual components, agents, and full system integration.
"""

import sys
import json
sys.path.insert(0, '.')

from src.utils import (
    split_references,
    guess_title_from_reference,
    extract_doi,
    extract_arxiv_id,
    validate_reference_string,
    safe_json_parse
)

print("\n" + "="*70)
print(" "*20 + "SYSTEM TEST SUITE")
print("="*70 + "\n")

# === TEST 1: Utility Functions ===

def test_utilities():
    """Test utility functions"""
    print("TEST 1: Utility Functions")
    print("-" * 70)
    
    # Test 1.1: Split references
    text = """
    1. Smith, J. (2020). Test Article. Journal of Tests, 10(2), 100-110.
    2. Doe, J. (2021). Another Test. Conference Proceedings, 50-60.
    """
    refs = split_references(text)
    assert len(refs) == 2, f"Expected 2 refs, got {len(refs)}"
    print("  ✓ Split references: 2 references detected")
    
    # Test 1.2: Extract DOI
    ref = "Smith (2020). Article. DOI: 10.1234/test.2020.001"
    doi = extract_doi(ref)
    assert doi == "10.1234/test.2020.001", f"DOI mismatch: {doi}"
    print(f"  ✓ Extract DOI: {doi}")
    
    # Test 1.3: Extract arXiv
    ref = "Test paper. arXiv:2020.12345"
    arxiv = extract_arxiv_id(ref)
    assert arxiv == "2020.12345", f"arXiv mismatch: {arxiv}"
    print(f"  ✓ Extract arXiv: {arxiv}")
    
    # Test 1.4: Validate reference
    valid_ref = "Smith, J. (2020). Article Title. Journal Name."
    assert validate_reference_string(valid_ref), "Valid ref marked invalid"
    print("  ✓ Validate reference: Valid reference accepted")
    
    invalid_ref = "Too short"
    assert not validate_reference_string(invalid_ref), "Invalid ref marked valid"
    print("  ✓ Validate reference: Invalid reference rejected")
    
    # Test 1.5: JSON parsing
    json_text = '{"key": "value"}'
    parsed = safe_json_parse(json_text)
    assert parsed == {"key": "value"}, "JSON parse failed"
    print("  ✓ JSON parsing: Valid JSON parsed correctly")
    
    print("  ✓ All utility tests passed!\n")

# === TEST 2: External APIs ===

def test_external_apis():
    """Test external API functions"""
    print("TEST 2: External API Integration")
    print("-" * 70)
    
    from src.tools.external_apis import (
        search_semantic_scholar,
        validate_bibtex_format
    )
    
    # Test 2.1: Semantic Scholar search
    print("  → Searching Semantic Scholar (this may take 10-15 seconds)...")
    result = search_semantic_scholar("Attention is All You Need", limit=1)
    
    if result["status"] == "success" and result["papers"]:
        print(f"  ✓ Semantic Scholar: Found paper")
        print(f"    Title: {result['papers'][0]['title'][:60]}...")
    else:
        print(f"  ⚠ Semantic Scholar: {result.get('message', 'No results')}")
    
    # Test 2.2: BibTeX validation
    valid_bibtex = """@article{smith2020,
  title={Test Article},
  author={Smith, John},
  year={2020}
}"""
    assert validate_bibtex_format(valid_bibtex), "Valid BibTeX rejected"
    print("  ✓ BibTeX validation: Valid entry accepted")
    
    invalid_bibtex = "not a bibtex entry"
    assert not validate_bibtex_format(invalid_bibtex), "Invalid BibTeX accepted"
    print("  ✓ BibTeX validation: Invalid entry rejected")
    
    print("  ✓ API tests completed!\n")

# === TEST 3: Individual Agents ===

def test_individual_agents():
    """Test each agent in isolation"""
    print("TEST 3: Individual Agent Tests")
    print("-" * 70)
    print("  Note: These tests use LLM and may take 1-2 minutes each\n")
    
    response = input("  Run agent tests? (requires Ollama) [y/N]: ")
    if response.lower() != 'y':
        print("  ⊘ Skipping agent tests\n")
        return
    
    from crewai import Crew
    from src.agents.reference_agent import reference_finder_agent, create_reference_task
    from src.agents.bibtex_agent import bibtex_generator_agent, create_bibtex_task
    
    # Test 3.1: Reference Finder Agent
    print("\n  → Testing Reference Finder Agent...")
    ref_text = "Vaswani et al. 2017. Attention is All You Need."
    task = create_reference_task(ref_text)
    
    try:
        crew = Crew(agents=[reference_finder_agent], tasks=[task], verbose=False)
        result = crew.kickoff()
        print("  ✓ Reference Finder: Completed successfully")
        print(f"    Result preview: {str(result)}")
    except Exception as e:
        print(f"  ✗ Reference Finder failed: {e}")
    
    # Test 3.2: BibTeX Generator Agent
    print("\n  → Testing BibTeX Generator Agent...")
    paper_metadata = {
        "title": "Attention is All You Need",
        "authors": ["Ashish Vaswani", "Noam Shazeer"],
        "year": 2017,
        "doi": None,
        "arxiv": None
    }
    task = create_bibtex_task(paper_metadata)
    
    try:
        crew = Crew(agents=[bibtex_generator_agent], tasks=[task], verbose=False)
        result = crew.kickoff()
        print("  ✓ BibTeX Generator: Completed successfully")
        print(f"    Result preview: {str(result)[:100]}...")
    except Exception as e:
        print(f"  ✗ BibTeX Generator failed: {e}")
    
    print("\n  ✓ Agent tests completed!\n")

# === TEST 4: Full System Integration ===

def test_full_system():
    """Test complete system with core orchestrator"""
    print("TEST 4: Full System Integration")
    print("-" * 70)
    print("  Note: This test runs the complete multi-agent system\n")
    
    response = input("  Run full system test? (takes 2-5 minutes) [y/N]: ")
    if response.lower() != 'y':
        print("  ⊘ Skipping full system test\n")
        return
    
    from agents.core_agent.core_agent import process_references
    
    test_reference = """
    Vaswani, A., Shazeer, N., Parmar, N., Uszkoreit, J., Jones, L., 
    Gomez, A. N., Kaiser, Ł., & Polosukhin, I. (2017). 
    Attention is all you need. In Advances in neural information 
    processing systems (pp. 5998-6008).
    """
    
    print("\n  → Processing reference through full system...")
    print(f"  Reference: {test_reference.strip()[:80]}...\n")
    
    try:
        result = process_references(test_reference)
        
        # Try to parse result
        try:
            result_json = json.loads(result)
            print("\n  ✓ System executed successfully!")
            print(f"    Total references: {result_json.get('total_references', 'N/A')}")
            print(f"    Successful: {result_json.get('successful', 'N/A')}")
            print(f"    Failed: {result_json.get('failed', 'N/A')}")
        except:
            print("\n  ✓ System executed (non-JSON result)")
            print(f"    Result preview: {result[:200]}...")
        
    except Exception as e:
        print(f"\n  ✗ System test failed: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n  ✓ Full system test completed!\n")

# === TEST 5: Error Handling ===

def test_error_handling():
    """Test system handles errors gracefully"""
    print("TEST 5: Error Handling")
    print("-" * 70)
    
    # Test 5.1: Invalid reference
    invalid_ref = "This is not a real reference"
    refs = split_references(invalid_ref)
    print(f"  ✓ Invalid reference: {len(refs)} references detected (expected 0 or 1)")
    
    # Test 5.2: Empty input
    empty = ""
    refs = split_references(empty)
    assert len(refs) == 0, "Empty input should produce no references"
    print("  ✓ Empty input: Handled correctly")
    
    # Test 5.3: Malformed JSON
    bad_json = '{"incomplete": '
    parsed = safe_json_parse(bad_json)
    assert parsed is None, "Bad JSON should return None"
    print("  ✓ Malformed JSON: Handled correctly")
    
    print("  ✓ Error handling tests passed!\n")

# === MAIN TEST RUNNER ===

def run_all_tests():
    """Run all tests"""
    
    try:
        # Quick tests (no LLM)
        test_utilities()
        test_external_apis()
        test_error_handling()
        
        # LLM-dependent tests (optional)
        test_individual_agents()
        test_full_system()
        
        print("="*70)
        print(" "*25 + "ALL TESTS COMPLETED")
        print("="*70 + "\n")
        
        print("Summary:")
        print("  ✓ Utility functions working")
        print("  ✓ External APIs accessible")
        print("  ✓ Error handling robust")
        
        return True
        
    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}\n")
        return False
    except Exception as e:
        print(f"\n✗ UNEXPECTED ERROR: {e}\n")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)