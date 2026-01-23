
import re
import json
from typing import List, Dict, Optional

def safe_json_parse(text: str) -> Optional[Dict]:
    try:
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0]
        elif "```" in text:
            text = text.split("```")[1].split("```")[0]
        
        return json.loads(text.strip())
    except Exception as e:
        print(f"JSON parsing error: {e}")
        return None

def validate_reference_string(ref: str) -> bool:
    if not ref or len(ref) < 20:
        return False
    
    if not re.search(r'\b(19|20)\d{2}\b', ref):
        return False
    
    if '.' not in ref:
        return False
    
    return True

def split_references(text: str) -> List[str]:
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    
    refs = []
    buffer = ""
    
    for line in lines:
        if re.match(r'^\d+\.\s+', line):
            if buffer and validate_reference_string(buffer):
                refs.append(buffer.strip())
            buffer = re.sub(r'^\d+\.\s+', '', line)
        else:
            buffer += " " + line
    
    if buffer and validate_reference_string(buffer):
        refs.append(buffer.strip())
    
    return refs

def guess_title_from_reference(ref: str) -> str:
    ref = re.sub(r'^\d+\.\s+', '', ref)
    
    sentences = re.split(r'[.\n]', ref)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 15]
    
    if not sentences:
        return ref[:100]  
    
    return max(sentences, key=len)

def extract_year(ref: str) -> Optional[int]:
    years = re.findall(r'\b(19|20)\d{2}\b', ref)
    if years:
        return int(years[0])
    return None

def extract_doi(ref: str) -> Optional[str]:
    doi_match = re.search(r'10\.\d{4,9}/[-._;()/:A-Za-z0-9]+', ref)
    return doi_match.group(0) if doi_match else None

def extract_arxiv_id(ref: str) -> Optional[str]:
    arxiv_match = re.search(r'arXiv[:\s]+(\d{4}\.\d{4,5})', ref, re.IGNORECASE)
    return arxiv_match.group(1) if arxiv_match else None

def clean_reference_text(ref: str) -> str:
    ref = re.sub(r'\s+', ' ', ref)
    
    ref = ref.strip()
    
    return ref

def extract_authors_simple(ref: str) -> List[str]:
    year_match = re.search(r'\b(19|20)\d{2}\b', ref)
    if not year_match:
        return []
    
    author_text = ref[:year_match.start()].strip()
    
    authors = re.split(r'[,;&]|\band\b', author_text)
    authors = [a.strip() for a in authors if len(a.strip()) > 3]
    
    return authors[:10]  

def truncate_text(text: str, max_length: int = 500) -> str:
    if len(text) <= max_length:
        return text
    return text[:max_length] + "..."

def format_bibtex_entry(entry: str) -> str:
    if not entry:
        return ""
    
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
    if isinstance(data, str):
        try:
            data = json.loads(data)
        except json.JSONDecodeError:
            return data
    
    if isinstance(data, dict):
        if data:  
            return next(iter(data.values()))
        return None  
    
    elif isinstance(data, list):
        if data:  
            return data[0]
        return None  
    
    else:
        return data