# Usage Examples

## Basic Usage

### Example 1: Single Reference

**Input:**
```bash
python src/main.py "Vaswani, A., et al. (2017). Attention is All You Need. NeurIPS."
```

**Expected Output:**
```json
{
  "total_references": 1,
  "successful": 1,
  "failed": 0,
  "results": [
    {
      "reference": "Vaswani, A., et al. (2017)...",
      "status": "success",
      "metadata": {
        "title": "Attention is All You Need",
        "authors": ["Ashish Vaswani", "Noam Shazeer", ...],
        "year": 2017,
        "url": "https://arxiv.org/abs/1706.03762"
      },
      "bibtex": "@inproceedings{vaswani2017attention,\n  title={Attention is all you need},\n  author={Vaswani, Ashish and ...},\n  booktitle={Advances in neural information processing systems},\n  pages={5998--6008},\n  year={2017}\n}"
    }
  ]
}
```

### Example 2: Multiple References

**Input:**
```bash
python src/main.py "$(cat references.txt)"
```

**references.txt:**
```
1. Devlin, J., Chang, M. W., Lee, K., & Toutanova, K. (2019). 
   BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding.

2. Brown, T., Mann, B., Ryder, N., et al. (2020). 
   Language Models are Few-Shot Learners. NeurIPS.

3. Radford, A., Wu, J., Child, R., et al. (2019). 
   Language Models are Unsupervised Multitask Learners.
```

**Expected Workflow:**
```
Core Agent:
├─ Detects 3 references
├─ Creates plan with 6 steps (find + bibtex for each)
├─ Validates plan with Governance
└─ Executes:
   ├─ Reference 1: Found ✓, BibTeX ✓
   ├─ Reference 2: Found ✓, BibTeX ✓
   └─ Reference 3: Found ✓, BibTeX ✓
```

### Example 3: Reference with DOI

**Input:**
```bash
python src/main.py "Smith, J. (2020). Example Paper. DOI: 10.1234/example.2020"
```

**Workflow:**
```
Reference Finder Agent:
├─ Extracts DOI: 10.1234/example.2020
├─ Searches Semantic Scholar
└─ Returns metadata ✓

BibTeX Generator Agent:
├─ Detects DOI present
├─ Fetches BibTeX directly from DOI
└─ Returns authoritative BibTeX ✓
```

### Example 4: Reference with arXiv

**Input:**
```bash
python src/main.py "Neural Networks. arXiv:2020.12345"
```

**Workflow:**
```
Reference Finder Agent:
├─ Extracts arXiv ID: 2020.12345
├─ Searches using title
└─ Returns metadata ✓

BibTeX Generator Agent:
├─ Detects arXiv ID present
├─ Fetches BibTeX from arXiv
└─ Returns BibTeX ✓
```

## Advanced Usage

### Example 5: Interactive Mode

**Session:**
```bash
$ python src/main.py

=======================================================================
              ACADEMIC MULTI-AGENT SYSTEM
                Reference Processor v2.0
=======================================================================

Specialized Agents:
  • Reference Finder    - Searches for academic papers
  • BibTeX Generator    - Creates BibTeX entries
  • Reference Validator - Validates data quality
  • Governance Agent    - Ensures policy compliance
  • Core Orchestrator   - Coordinates all agents
=======================================================================

System Check:
  [1/2] Checking Ollama connection... ✓ OK
  [2/2] Checking dependencies... ✓ OK

Enter your academic references below.
You can paste multiple references (one per line or numbered).
Press Ctrl+D (Linux/Mac) or Ctrl+Z (Windows) when done.

----------------------------------------------------------------------
Vaswani et al. 2017. Attention is All You Need.
[Ctrl+D]
----------------------------------------------------------------------

Processing references...
This may take a few minutes depending on the number of references.

[CORE] Starting orchestration...
...
[CORE] Orchestration complete!

=======================================================================
                    PROCESSING RESULTS
=======================================================================

{
  "total_references": 1,
  "successful": 1,
  ...
}

=======================================================================
```

### Example 6: From File

**references.txt:**
```
1. LeCun, Y., Bengio, Y., & Hinton, G. (2015). 
   Deep learning. Nature, 521(7553), 436-444.

2. Krizhevsky, A., Sutskever, I., & Hinton, G. E. (2012). 
   Imagenet classification with deep convolutional neural networks. 
   NeurIPS.

3. He, K., Zhang, X., Ren, S., & Sun, J. (2016). 
   Deep residual learning for image recognition. CVPR.
```

**Command:**
```bash
python src/main.py "$(cat references.txt)"
```

**Or with redirection:**
```bash
python src/main.py < references.txt
```

### Example 7: With Validation

**Custom validation workflow:**
```python
# custom_workflow.py
from src.agents.core_agent import process_references
from src.agents.validator_agent import reference_validator_agent, create_validation_task
from crewai import Crew
import json

# Process references
result_str = process_references("Your reference here")
result = json.loads(result_str)

# Additional validation
for ref in result["results"]:
    validation_task = create_validation_task(ref)
    crew = Crew(agents=[reference_validator_agent], tasks=[validation_task])
    validation = crew.kickoff()
    print(f"Validation: {validation}")
```

## Error Handling Examples

### Example 8: Reference Not Found

**Input:**
```bash
python src/main.py "Nonexistent Paper by Nobody (2099)"
```

**Output:**
```json
{
  "total_references": 1,
  "successful": 0,
  "failed": 1,
  "results": [
    {
      "reference": "Nonexistent Paper by Nobody (2099)",
      "status": "not_found",
      "message": "Paper not found in databases",
      "metadata": null,
      "bibtex": null
    }
  ]
}
```

### Example 9: Malformed Reference

**Input:**
```bash
python src/main.py "This is not a reference"
```

**Output:**
```json
{
  "total_references": 0,
  "message": "No valid references detected in input"
}
```

### Example 10: Network Error

**Output when APIs fail:**
```json
{
  "reference": "Smith (2020). Paper.",
  "status": "error",
  "message": "Semantic Scholar API timeout",
  "metadata": null,
  "bibtex": null
}
```

## Testing Examples

### Example 11: Unit Tests

```bash
$ python tests/test_system.py

=======================================================================
                      SYSTEM TEST SUITE
=======================================================================

TEST 1: Utility Functions
----------------------------------------------------------------------
  ✓ Split references: 2 references detected
  ✓ Extract DOI: 10.1234/test.2020.001
  ✓ Extract arXiv: 2020.12345
  ✓ Validate reference: Valid reference accepted
  ✓ Validate reference: Invalid reference rejected
  ✓ JSON parsing: Valid JSON parsed correctly
  ✓ All utility tests passed!

TEST 2: External API Integration
----------------------------------------------------------------------
  → Searching Semantic Scholar (this may take 10-15 seconds)...
  ✓ Semantic Scholar: Found paper
    Title: Attention is All You Need
  ✓ BibTeX validation: Valid entry accepted
  ✓ BibTeX validation: Invalid entry rejected
  ✓ API tests completed!

...
```

### Example 12: Individual Agent Test

```python
# test_single_agent.py
from src.agents.reference_agent import reference_finder_agent, create_reference_task
from crewai import Crew

ref = "Attention is All You Need"
task = create_reference_task(ref)
crew = Crew(agents=[reference_finder_agent], tasks=[task], verbose=True)

result = crew.kickoff()
print(result)
```

## Configuration Examples

### Example 13: Different Models

```python
# config.py

# Option 1: Fast and lightweight
llm = LLM(model="ollama/llama3.2:3b", timeout=120)

# Option 2: Balanced
llm = LLM(model="ollama/mistral:7b", timeout=180)

# Option 3: High accuracy
llm = LLM(model="ollama/llama3.1:70b", timeout=300)
```

### Example 14: Custom Timeout

```python
# config.py

# Shorter timeout for fast responses
llm = LLM(model="ollama/llama3.2:3b", timeout=60)

# Longer timeout for complex references
llm = LLM(model="ollama/llama3.2:3b", timeout=300)
```

### Example 15: Adjust Agent Iterations

```python
# config.py

# Conservative (faster but may fail)
MAX_AGENT_ITERATIONS = 2

# Standard
MAX_AGENT_ITERATIONS = 3

# Permissive (slower but more robust)
MAX_AGENT_ITERATIONS = 5
```

## Integration Examples

### Example 16: Python Script

```python
# my_script.py
from src.agents.core_agent import process_references
import json

references = """
1. Paper One (2020)
2. Paper Two (2021)
"""

result_str = process_references(references)
result = json.loads(result_str)

for ref in result["results"]:
    if ref["status"] == "success":
        print(f"Title: {ref['metadata']['title']}")
        print(f"BibTeX:\n{ref['bibtex']}\n")
```

### Example 17: Web API Wrapper

```python
# api.py
from flask import Flask, request, jsonify
from src.agents.core_agent import process_references
import json

app = Flask(__name__)

@app.route('/process', methods=['POST'])
def process():
    references = request.json.get('references', '')
    result_str = process_references(references)
    result = json.loads(result_str)
    return jsonify(result)

if __name__ == '__main__':
    app.run(port=5000)
```

**Usage:**
```bash
curl -X POST http://localhost:5000/process \
  -H "Content-Type: application/json" \
  -d '{"references": "Vaswani et al. 2017. Attention is All You Need."}'
```

### Example 18: Batch Processing

```python
# batch_process.py
from src.agents.core_agent import process_references
import json
import glob

# Process all .txt files in a directory
for file_path in glob.glob("references/*.txt"):
    print(f"Processing {file_path}...")
    
    with open(file_path, 'r') as f:
        references = f.read()
    
    result_str = process_references(references)
    result = json.loads(result_str)
    
    # Save output
    output_path = file_path.replace('.txt', '_output.json')
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)
    
    print(f"Saved to {output_path}")
```

## Troubleshooting Examples

### Example 19: Verbose Debugging

```python
# debug_run.py
from src.config import llm
from src.agents.core_agent import core_orchestrator_agent
from crewai import Task, Crew

# Enable maximum verbosity
task = Task(
    description="Find: Attention is All You Need",
    agent=core_orchestrator_agent,
    expected_output="Paper metadata"
)

crew = Crew(
    agents=[core_orchestrator_agent],
    tasks=[task],
    verbose=True  # See all agent reasoning
)

result = crew.kickoff()
```

### Example 20: Error Recovery

```python
# robust_processing.py
from src.agents.core_agent import process_references
import json
import time

def process_with_retry(references, max_retries=3):
    """Process references with automatic retry"""
    
    for attempt in range(max_retries):
        try:
            result_str = process_references(references)
            result = json.loads(result_str)
            
            if result.get("status") != "fatal_error":
                return result
            
            print(f"Attempt {attempt + 1} failed, retrying...")
            time.sleep(5)
            
        except Exception as e:
            print(f"Error on attempt {attempt + 1}: {e}")
            if attempt < max_retries - 1:
                time.sleep(5)
            else:
                raise
    
    return {"status": "failed_all_retries"}

# Usage
result = process_with_retry("Your reference here")
```

## Performance Examples

### Example 21: Timing Analysis

```python
# benchmark.py
import time
from src.agents.core_agent import process_references

references = [
    "Paper 1 (2020)",
    "Paper 2 (2021)",
    "Paper 3 (2022)"
]

for ref in references:
    start = time.time()
    result = process_references(ref)
    elapsed = time.time() - start
    print(f"Processed in {elapsed:.2f} seconds")
```

### Example 22: Memory Profiling

```python
# memory_test.py
import tracemalloc
from src.agents.core_agent import process_references

tracemalloc.start()

result = process_references("Attention is All You Need")

current, peak = tracemalloc.get_traced_memory()
print(f"Current memory: {current / 1024 / 1024:.2f} MB")
print(f"Peak memory: {peak / 1024 / 1024:.2f} MB")

tracemalloc.stop()
```

---

## Summary

These examples demonstrate:

- ✓ Basic single/multiple reference processing
- ✓ Advanced features (DOI, arXiv, validation)
- ✓ Error handling and recovery
- ✓ Configuration and customization
- ✓ Integration with other systems
- ✓ Testing and debugging
- ✓ Performance optimization

For more information, see README.md and ARCHITECTURE.md.