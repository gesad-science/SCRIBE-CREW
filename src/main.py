# src/main.py
"""
Main entry point for the Academic Multi-Agent System.
"""

import sys
import json
from src.config import validate_llm_connection
from agents.core_agent.core_agent import process_references

def print_banner():
    """Print system banner"""
    print("\n" + "="*70)
    print(" "*15 + "ACADEMIC MULTI-AGENT SYSTEM")
    print(" "*20 + "Reference Processor v2.0")
    print("="*70)
    print("\nSpecialized Agents:")
    print("  • Reference Finder    - Searches for academic papers")
    print("  • BibTeX Generator    - Creates BibTeX entries")
    print("  • Reference Validator - Validates data quality")
    print("  • Governance Agent    - Ensures policy compliance")
    print("  • Core Orchestrator   - Coordinates all agents")
    print("="*70 + "\n")

def validate_system():
    """Validate system is ready"""
    print("System Check:")
    print("  [1/2] Checking Ollama connection...", end=" ")
    
    try:
        validate_llm_connection()
        print("✓ OK")
    except Exception as e:
        print("✗ FAILED")
        print(f"\nError: {e}")
        print("\nTroubleshooting:")
        print("  1. Make sure Ollama is running:")
        print("     $ ollama serve")
        print("  2. Pull the required model:")
        print("     $ ollama pull llama3.2:3b")
        print("  3. Test the model:")
        print("     $ ollama run llama3.2:3b 'Hello'")
        return False
    
    print("  [2/2] Checking dependencies...", end=" ")
    try:
        import crewai
        import requests
        print("✓ OK\n")
        return True
    except ImportError as e:
        print("✗ FAILED")
        print(f"\nMissing dependency: {e}")
        print("\nInstall with:")
        print("  $ pip install -r requirements.txt")
        return False

def get_user_input():
    """Get input from user"""
    
    # Check for command line arguments
    if len(sys.argv) > 1:
        return " ".join(sys.argv[1:])
    
    # Interactive mode
    print("Enter your academic references below.")
    print("You can paste multiple references (one per line or numbered).")
    print("Press Ctrl+D (Linux/Mac) or Ctrl+Z (Windows) when done.\n")
    print("-" * 70)
    
    try:
        lines = []
        while True:
            line = input()
            lines.append(line)
    except EOFError:
        pass
    
    print("-" * 70 + "\n")
    
    return "\n".join(lines)

def format_output(result: str):
    """Format and print the output"""
    print("\n" + "="*70)
    print(" "*25 + "PROCESSING RESULTS")
    print("="*70 + "\n")
    
    # Try to parse as JSON for better formatting
    try:
        data = json.loads(result)
        print(json.dumps(data, indent=2, ensure_ascii=False))
    except:
        # If not JSON, print as-is
        print(result)
    
    print("\n" + "="*70 + "\n")

def main():
    """Main execution function"""
    
    # Print banner
    print_banner()
    
    # Validate system
    if not validate_system():
        sys.exit(1)
    
    # Get user input
    try:
        user_input = get_user_input()
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
        sys.exit(0)
    
    if not user_input.strip():
        print("Error: No input provided.")
        print("\nUsage:")
        print("  Interactive: $ python src/main.py")
        print("  Command:     $ python src/main.py 'Your reference here'")
        print("  File:        $ python src/main.py \"$(cat refs.txt)\"")
        sys.exit(1)
    
    # Process references
    print("Processing references...")
    print("This may take a few minutes depending on the number of references.\n")
    
    try:
        result = process_references(user_input)
        format_output(result)
        
    except KeyboardInterrupt:
        print("\n\n⚠ Processing interrupted by user.")
        sys.exit(0)
        
    except Exception as e:
        print(f"\n✗ Fatal Error: {e}")
        print("\nStack trace:")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()