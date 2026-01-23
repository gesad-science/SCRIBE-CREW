# Troubleshooting Guide

## Common Issues and Solutions

### Issue 1: Telemetry Connection Timeout

**Error Message:**
```
HTTPSConnectionPool(host='telemetry.crewai.com', port=4319): Max retries exceeded
```

**Cause:**
CrewAI tries to send telemetry data to their servers, which can timeout or fail if you don't have internet or their server is slow.

**Solution:**

1. **Create/Update `.env` file** in the project root:
```bash
# .env
OTEL_SDK_DISABLED=true
CREWAI_TELEMETRY_ENABLED=false
```

2. **Set environment variables directly** (alternative):
```bash
export OTEL_SDK_DISABLED=true
export CREWAI_TELEMETRY_ENABLED=false

# Then run your script
python tests/test_system.py
```

3. **In code** (if .env doesn't work):
```python
# At the very top of config.py, BEFORE importing crewai
import os
os.environ["OTEL_SDK_DISABLED"] = "true"
os.environ["CREWAI_TELEMETRY_ENABLED"] = "false"
```

4. **Install python-dotenv** (if not installed):
```bash
pip install python-dotenv
```

**Verification:**
```bash
# Check if variables are set
echo $OTEL_SDK_DISABLED
echo $CREWAI_TELEMETRY_ENABLED

# Should both print "true" or "false"
```

---

### Issue 2: Ollama Connection Refused

**Error Message:**
```
Cannot connect to Ollama. ConnectionError
```

**Solutions:**

1. **Check if Ollama is running:**
```bash
ollama ps
```

2. **Start Ollama:**
```bash
ollama serve
```

3. **Test model directly:**
```bash
ollama run llama3.2:3b "Hello"
```

4. **Pull model if missing:**
```bash
ollama pull llama3.2:3b
```

---

### Issue 3: Agent Timeout (180s)

**Error Message:**
```
litellm.Timeout: Connection timed out after 180.0 seconds
```

**Cause:**
Agent taking too long to respond.

**Solutions:**

1. **Increase timeout in `.env`:**
```bash
LLM_TIMEOUT=300
CORE_AGENT_TIMEOUT=600
```

2. **Use smaller model:**
```bash
OLLAMA_MODEL=llama3.2:3b  # Instead of larger models
```

3. **Reduce references per request:**
```bash
# Instead of 10 references at once
python src/main.py "$(head -n 3 references.txt)"
```

4. **Check system resources:**
```bash
htop  # or top on macOS
# Make sure CPU/RAM not maxed out
```

---

### Issue 4: Max Iterations Exceeded

**Error Message:**
```
Agent failed after max iterations (3)
```

**Cause:**
Agent stuck in loop, retrying failed operations.

**Solutions:**

1. **Check verbose output** for the loop:
```python
# In agent code, look for repeated tool calls
```

2. **Increase max iterations** (temporary):
```bash
# .env
MAX_AGENT_ITERATIONS=5
```

3. **Simplify task description:**
```python
# Make prompt more explicit about using tools ONCE
```

4. **Check tool outputs:**
- Are tools returning errors?
- Is tool output format wrong?

---

### Issue 5: Invalid JSON Output

**Error Message:**
```
JSONDecodeError: Expecting value: line 1 column 1
```

**Cause:**
Agent returned text instead of JSON.

**Solutions:**

1. **Check expected_output in task:**
```python
Task(
    expected_output="Valid JSON object with fields: x, y, z"
)
```

2. **Use safe_json_parse:**
```python
from src.utils import safe_json_parse
result = safe_json_parse(agent_output)
```

3. **Improve prompt:**
```python
description="""
OUTPUT FORMAT (JSON ONLY, NO MARKDOWN):
{
  "field": "value"
}
"""
```

---

### Issue 6: Reference Not Found

**Error Message:**
```
"status": "not_found"
```

**Cause:**
Paper doesn't exist in Semantic Scholar database.

**Solutions:**

1. **Check if paper exists:**
- Visit https://www.semanticscholar.org/
- Search manually

2. **Try with DOI or arXiv:**
```bash
python src/main.py "Paper Title. DOI: 10.1234/example"
```

3. **Check reference format:**
```
# Good:
Smith, J. (2020). Title. Journal.

# Bad:
Smith 2020 Title Journal
```

---

### Issue 7: Import Errors

**Error Message:**
```
ModuleNotFoundError: No module named 'crewai'
```

**Solutions:**

1. **Activate virtual environment:**
```bash
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Check Python version:**
```bash
python --version  # Should be 3.10+
```

---

### Issue 8: Memory Leak / High RAM Usage

**Symptoms:**
- System slows down
- Process uses 8GB+ RAM

**Solutions:**

1. **Use smaller model:**
```bash
# .env
OLLAMA_MODEL=llama3.2:3b  # 2GB RAM
# Instead of llama3.1:70b  # 40GB RAM
```

2. **Disable memory:**
```bash
# .env
ENABLE_MEMORY=false
```

3. **Process fewer references:**
```bash
# Split into batches
python src/main.py "$(head -n 2 refs.txt)"
python src/main.py "$(tail -n 2 refs.txt)"
```

4. **Restart Ollama:**
```bash
ollama stop
ollama serve
```

---

### Issue 9: Semantic Scholar API Rate Limit

**Error Message:**
```
"status": "error", "message": "HTTP 429"
```

**Cause:**
Too many requests to Semantic Scholar API.

**Solutions:**

1. **Add delays between requests:**
```python
import time
time.sleep(2)  # Wait 2 seconds between requests
```

2. **Reduce MAX_RPM:**
```bash
# .env
MAX_RPM=10  # Instead of 20
```

3. **Use batch processing with delays:**
```python
for ref in references:
    result = process_references(ref)
    time.sleep(5)  # Wait between references
```

---

### Issue 10: CrewAI Version Incompatibility

**Error Message:**
```
AttributeError: 'Agent' object has no attribute 'max_iter'
```

**Solutions:**

1. **Check CrewAI version:**
```bash
pip show crewai
```

2. **Update to latest:**
```bash
pip install --upgrade crewai
```

3. **Install specific version:**
```bash
pip install crewai==0.70.0
```

---

## Quick Diagnostic Commands

```bash
# 1. Check Python
python --version

# 2. Check virtual environment
which python

# 3. Check Ollama
ollama ps
ollama list

# 4. Check dependencies
pip list | grep crewai
pip list | grep litellm

# 5. Check environment variables
printenv | grep CREW
printenv | grep OTEL

# 6. Test Ollama directly
ollama run llama3.2:3b "test"

# 7. Check port
netstat -an | grep 11434  # Linux
lsof -i :11434            # macOS
```

---

## Getting Help

If issues persist:

1. **Enable verbose mode:**
```bash
# .env
VERBOSE=true
```

2. **Check logs in detail:**
```bash
python src/main.py "test" 2>&1 | tee debug.log
```

3. **Test components individually:**
```bash
# Test utilities only
python -c "from src.utils import split_references; print(split_references('test'))"

# Test API
python -c "from src.tools.external_apis import search_semantic_scholar; print(search_semantic_scholar('AI'))"
```

4. **Run minimal test:**
```python
# minimal_test.py
from src.config import llm
print("LLM configured:", llm.model)

from src.agents.reference_agent import reference_finder_agent
print("Agent created:", reference_finder_agent.role)
```

---

## Environment Setup Checklist

Before running the system:

- [ ] Python 3.10+ installed
- [ ] Virtual environment activated
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] Ollama running (`ollama ps`)
- [ ] Model pulled (`ollama list`)
- [ ] `.env` file configured
- [ ] Telemetry disabled (`OTEL_SDK_DISABLED=true`)
- [ ] Test passed (`python tests/test_system.py`)

---

## Performance Tips

1. **Use smaller models for development:**
```bash
OLLAMA_MODEL=llama3.2:3b  # 2GB, fast
```

2. **Increase timeouts for production:**
```bash
LLM_TIMEOUT=300
CORE_AGENT_TIMEOUT=600
```

3. **Disable verbose in production:**
```bash
VERBOSE=false
```

4. **Process references in batches:**
```python
# 5 at a time instead of 50
```

5. **Monitor resources:**
```bash
watch -n 1 'ps aux | grep ollama'
```