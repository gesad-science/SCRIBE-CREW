# src/utils.py
"""
Utility functions for the multi-agent system.
All utilities are deterministic and do not use LLMs.
"""

import re
import json
from typing import List, Dict, Optional

def safe_json_parse(text: str) -> Optional[Dict]:
    """
    Safely parse JSON from text, handling markdown code blocks.
    
    Args:
        text: String that may contain JSON
        
    Returns:
        Parsed dict or None if parsing fails
    """
    try:
        # Remove markdown code blocks
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0]
        elif "```" in text:
            text = text.split("```")[1].split("```")[0]
        
        return json.loads(text.strip())
    except Exception as e:
        print(f"JSON parsing error: {e}")
        return None

def validate_reference_string(ref: str) -> bool:
    """
    Validate if a string looks like an academic reference.
    
    Args:
        ref: Reference string to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not ref or len(ref) < 20:
        return False
    
    # Must have at least one year (4 digits starting with 19 or 20)
    if not re.search(r'\b(19|20)\d{2}\b', ref):
        return False
    
    # Must have at least one period
    if '.' not in ref:
        return False
    
    return True

def split_references(text: str) -> List[str]:
    """
    Split text into individual reference strings.
    Assumes references are separated by numbered entries (1., 2., etc.)
    
    Args:
        text: Block of text containing multiple references
        
    Returns:
        List of reference strings
    """
    # Remove empty lines
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    
    refs = []
    buffer = ""
    
    for line in lines:
        # Detect start of new reference (number followed by period)
        if re.match(r'^\d+\.\s+', line):
            if buffer and validate_reference_string(buffer):
                refs.append(buffer.strip())
            buffer = re.sub(r'^\d+\.\s+', '', line)
        else:
            buffer += " " + line
    
    # Add last reference
    if buffer and validate_reference_string(buffer):
        refs.append(buffer.strip())
    
    return refs

def guess_title_from_reference(ref: str) -> str:
    """
    Extract probable title from a reference string.
    Usually the title is the longest sentence.
    
    Args:
        ref: Reference string
        
    Returns:
        Estimated title
    """
    # Remove common patterns at the beginning
    ref = re.sub(r'^\d+\.\s+', '', ref)
    
    # Split into sentences
    sentences = re.split(r'[.\n]', ref)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 15]
    
    if not sentences:
        return ref[:100]  # Fallback to first 100 chars
    
    # Title is usually the longest sentence
    return max(sentences, key=len)

def extract_year(ref: str) -> Optional[int]:
    """Extract year from reference"""
    years = re.findall(r'\b(19|20)\d{2}\b', ref)
    if years:
        return int(years[0])
    return None

def extract_doi(ref: str) -> Optional[str]:
    """Extract DOI from reference"""
    doi_match = re.search(r'10\.\d{4,9}/[-._;()/:A-Za-z0-9]+', ref)
    return doi_match.group(0) if doi_match else None

def extract_arxiv_id(ref: str) -> Optional[str]:
    """Extract arXiv ID from reference"""
    arxiv_match = re.search(r'arXiv[:\s]+(\d{4}\.\d{4,5})', ref, re.IGNORECASE)
    return arxiv_match.group(1) if arxiv_match else None

def clean_reference_text(ref: str) -> str:
    """
    Clean reference text by removing extra whitespace and normalizing.
    
    Args:
        ref: Raw reference text
        
    Returns:
        Cleaned reference text
    """
    # Replace multiple spaces with single space
    ref = re.sub(r'\s+', ' ', ref)
    
    # Remove leading/trailing whitespace
    ref = ref.strip()
    
    return ref

def extract_authors_simple(ref: str) -> List[str]:
    """
    Simple author extraction (names before year).
    This is a heuristic and may not be perfect.
    
    Args:
        ref: Reference string
        
    Returns:
        List of author names
    """
    # Find text before first year
    year_match = re.search(r'\b(19|20)\d{2}\b', ref)
    if not year_match:
        return []
    
    author_text = ref[:year_match.start()].strip()
    
    # Split by common separators
    authors = re.split(r'[,;&]|\band\b', author_text)
    authors = [a.strip() for a in authors if len(a.strip()) > 3]
    
    return authors[:10]  # Limit to 10 authors

def truncate_text(text: str, max_length: int = 500) -> str:
    """
    Truncate text to maximum length for logging.
    
    Args:
        text: Text to truncate
        max_length: Maximum length
        
    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text
    return text[:max_length] + "..."

def format_bibtex_entry(entry: str) -> str:
    """
    Format BibTeX entry with proper indentation.
    
    Args:
        entry: Raw BibTeX entry
        
    Returns:
        Formatted BibTeX entry
    """
    if not entry:
        return ""
    
    # Basic formatting
    lines = entry.split('\n')
    formatted = []
    
    for line in lines:
        line = line.strip()
        if line.startswith('@'):
            formatted.append(line)
        elif line:
            formatted.append('  ' + line)
    
    return '\n'.join(formatted)

import json
from typing import Any

def normalize_json(data: Any) -> Any:
    """
    Tenta extrair o primeiro valor de um objeto JSON.
    
    Se o dado for uma string JSON, converte para objeto Python.
    Se for um dicionário, retorna o primeiro valor.
    Se for uma lista, retorna o primeiro elemento.
    Caso contrário, retorna o próprio dado.
    """
    if isinstance(data, str):
        try:
            data = json.loads(data)
        except json.JSONDecodeError:
            # Se não for JSON válido, retorna a string original
            return data
    
    # Agora processamos o objeto Python (pode ser dict, list, etc)
    if isinstance(data, dict):
        if data:  # Verifica se o dicionário não está vazio
            # Pega o primeiro valor do dicionário
            return next(iter(data.values()))
        return None  # ou retorna um valor padrão
    
    elif isinstance(data, list):
        if data:  # Verifica se a lista não está vazia
            return data[0]
        return None  # ou retorna um valor padrão
    
    else:
        # Para outros tipos (int, float, bool, None), retorna o valor
        return data