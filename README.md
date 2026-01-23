# Academic Multi-Agent Reference System

## 🎯 Research Objective

A multi-agent system for processing academic references using specialized AI agents coordinated by a core orchestrator. This architecture demonstrates agent collaboration, task delegation, and hierarchical planning in an academic context.

## 🏗️ Multi-Agent Architecture

### Agent Hierarchy

```
                    ┌─────────────────────┐
                    │  Core Orchestrator  │
                    │    (Main Agent)     │
                    └──────────┬──────────┘
                               │
                   ┌───────────┴───────────┐
                   │     Delegates to      │
                   └───────────┬───────────┘
                               │
         ┌─────────────────────┼─────────────────────┐
         │                     │                     │
         ▼                     ▼                     ▼
┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐
│   Reference     │   │     BibTeX      │   │   Validator     │
│  Finder Agent   │   │ Generator Agent │   │     Agent       │
└─────────────────┘   └─────────────────┘   └─────────────────┘
         │                     │                     │
         └─────────────────────┴─────────────────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │  Governance Agent   │
                    │  (Policy Enforcer)  │
                    └─────────────────────┘
```

### Specialized Agents

#### 1. **Core Orchestrator Agent** 🎯
- **Role**: Main coordinator
- **Responsibilities**:
  - Receives user requests
  - Creates execution plans
  - Delegates tasks to specialized agents
  - Consolidates results
  - Manages workflow
- **Tools**: Delegation functions for each specialized agent

#### 2. **Reference Finder Agent** 🔍
- **Role**: Paper search specialist
- **Responsibilities**:
  - Extract identifiers (DOI, arXiv) from references
  - Search Semantic Scholar API
  - Extract paper metadata
- **Tools**:
  - `search_paper_by_title`
  - `extract_identifiers_from_reference`
  - `guess_title_tool`

#### 3. **BibTeX Generator Agent** 📝
- **Role**: Bibliography entry creator
- **Responsibilities**:
  - Fetch BibTeX from DOI/arXiv
  - Construct BibTeX manually when needed
  - Validate BibTeX format
- **Tools**:
  - `fetch_bibtex_from_doi`
  - `fetch_bibtex_from_arxiv`
  - `create_bibtex_manually`
  - `validate_bibtex`

#### 4. **Reference Validator Agent** ✅
- **Role**: Quality control specialist
- **Responsibilities**:
  - Check metadata completeness
  - Validate BibTeX entries
  - Cross-check consistency
  - Provide quality reports
- **Tools**:
  - `check_metadata_completeness`
  - `check_bibtex_validity`
  - `cross_check_metadata_bibtex`

#### 5. **Governance Agent** 🛡️
- **Role**: Policy enforcer
- **Responsibilities**:
  - Validate execution plans
  - Detect PII in data
  - Ensure policy compliance
  - Check plan efficiency
- **Tools**:
  - `get_system_policies`
  - `validate_plan_structure`
  - `detect_pii`
  - `check_plan_efficiency`

## 🔄 Workflow

### Step-by-Step Process

```
1. User submits references
         ↓
2. Core Agent receives request
         ↓
3. Core creates execution plan
         ↓
4. Governance validates plan
         ↓
5. Core executes plan:
   ├─→ Reference Finder searches papers
   ├─→ BibTeX Generator creates entries
   └─→ Validator checks quality
         ↓
6. Core consolidates results
         ↓
7. User receives final output
```

### Example Execution Flow

For input: "Smith, J. (2020). AI Research. Conference."

```
Core Agent:
  ├─ Creates Plan: [find_reference, generate_bibtex, validate]
  ├─ Delegates to Governance: validate plan
  │   └─ Governance: ✓ Plan approved
  ├─ Delegates to Reference Finder: search "Smith AI Research 2020"
  │   └─ Reference Finder: ✓ Found paper metadata
  ├─ Delegates to BibTeX Generator: create BibTeX
  │   └─ BibTeX Generator: ✓ Generated BibTeX entry
  ├─ Delegates to Validator: validate data
  │   └─ Validator: ✓ Quality check passed
  └─ Returns: Complete reference with BibTeX
```

## 🚀 Installation

```bash
# 1. Clone repository
git clone <repository-url>
cd academic-multiagent

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Create .env file (IMPORTANT!)
cat > .env << EOF
OTEL_SDK_DISABLED=true
CREWAI_TELEMETRY_ENABLED=false
OLLAMA_MODEL=llama3.2:3b
EOF

# 5. Setup Ollama
# Download from: https://ollama.ai
ollama pull llama3.2:3b

# 6. Start Ollama
ollama serve
```

## 📖 Usage

### Command Line

```bash
# Single reference
python src/main.py "Vaswani et al. 2017. Attention is All You Need."

# Multiple references
python src/main.py "$(cat references.txt)"
```

### Interactive Mode

```bash
python src/main.py
# Paste references, then Ctrl+D
```

### Example Input

```
1. Vaswani, A., Shazeer, N., Parmar, N., et al. (2017). 
   Attention is All You Need. In NeurIPS.

2. Devlin, J., Chang, M. W., Lee, K., & Toutanova, K. (2019). 
   BERT: Pre-training of Deep Bidirectional Transformers. In NAACL.
```

### Example Output

```json
{
  "total_references": 2,
  "successful": 2,
  "failed": 0,
  "results": [
    {
      "reference": "Vaswani, A., Shazeer, N...",
      "status": "success",
      "metadata": {
        "title": "Attention is All You Need",
        "authors": ["Ashish Vaswani", "Noam Shazeer", ...],
        "year": 2017,
        "url": "https://..."
      },
      "bibtex": "@inproceedings{vaswani2017attention,...}"
    },
    ...
  ]
}
```

## 🧪 Testing

```bash
# Run full test suite
python tests/test_system.py

# Test individual agents
python src/agents/reference_agent.py
python src/agents/bibtex_agent.py
python src/agents/validator_agent.py
```

## ⚙️ Configuration

### LLM Settings (`src/config.py`)

```python
llm = LLM(
    model="ollama/llama3.2:3b",  # Smaller = faster
    timeout=180,  # 3 minutes per call
    temperature=0.3  # More deterministic
)
```

### Agent Limits

```python
MAX_AGENT_ITERATIONS = 3  # Max iterations per agent
MAX_RPM = 20             # Max requests per minute
```

### Model Recommendations

| Model | RAM | Speed | Accuracy |
|-------|-----|-------|----------|
| llama3.2:3b | 2GB | Fast | Good |
| llama3.1:8b | 5GB | Medium | Better |
| mistral:7b | 4GB | Medium | Good |

## 🐛 Troubleshooting

### Telemetry Connection Timeout

**Problem**: `HTTPSConnectionPool(host='telemetry.crewai.com'): Max retries exceeded`

**Solution**: Create `.env` file in project root:
```bash
OTEL_SDK_DISABLED=true
CREWAI_TELEMETRY_ENABLED=false
```

See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for complete guide.

### Connection Timeout

```bash
# Check Ollama is running
ollama ps

# Test model directly
ollama run llama3.2:3b "test"

# Increase timeout in config.py
llm = LLM(timeout=300)
```

### Agent Failures

**Symptom**: "Agent failed after max iterations"

**Solution**:
- Simplify input (fewer references at once)
- Use smaller model
- Check tool errors in verbose output

### Governance Rejection

**Symptom**: "Plan rejected by governance"

**Solution**:
- Check verbose output for policy violations
- Ensure plan has valid JSON structure
- Remove any PII from input

### Memory Issues

**Symptom**: System runs out of memory

**Solution**:
```python
# Use smaller model
llm = LLM(model="ollama/llama3.2:3b")

# Disable memory
ENABLE_MEMORY = False
```

## 📊 System Metrics

### Performance

| Metric | Value |
|--------|-------|
| Average time per reference | 15-30s |
| LLM calls per reference | 6-8 |
| Success rate | 85-95% |
| Memory usage | 2-4GB |

### Agent Communication

- **Core → Specialist**: Task delegation via tools
- **Specialist → Core**: JSON-formatted results
- **Core ↔ Governance**: Plan validation
- **No direct**: Specialist ↔ Specialist communication

## 🔬 Research Applications

This architecture is suitable for research on:

1. **Multi-Agent Coordination**: Hierarchical task delegation
2. **Specialized Agents**: Domain-specific agent design
3. **Plan Validation**: Governance in multi-agent systems
4. **Error Handling**: Fault tolerance in agent workflows
5. **Tool Usage**: Agent-tool interaction patterns

## 📝 Extending the System

### Adding a New Agent

```python
# 1. Create agent file: src/agents/new_agent.py
new_agent = Agent(
    role="New Specialist",
    goal="Specific task",
    tools=[tool1, tool2],
    llm=llm
)

# 2. Add delegation tool in core_agent.py
@tool
def delegate_to_new_agent(input: str) -> str:
    task = create_new_task(input)
    crew = Crew(agents=[new_agent], tasks=[task])
    return str(crew.kickoff())

# 3. Add tool to core agent
core_orchestrator_agent = Agent(
    tools=[..., delegate_to_new_agent]
)
```

### Adding a New Tool

```python
# In respective agent file
@tool
def my_new_tool(input: str) -> str:
    """Tool description for the agent"""
    result = some_function(input)
    return json.dumps(result)
```

## 🛡️ System Policies

Current governance policies:

1. All plans must be valid JSON
2. Each step must have: step, action, input
3. Valid actions: find_reference, generate_bibtex, validate_reference
4. No PII (emails, phone numbers, SSN, credit cards)
5. Plans should be efficient (no redundant steps)

## 📄 Project Structure

```
academic-multiagent/
├── src/
│   ├── config.py                    # System configuration
│   ├── utils.py                     # Utility functions
│   ├── main.py                      # Entry point
│   ├── tools/
│   │   └── external_apis.py         # API integrations
│   └── agents/
│       ├── core_agent.py            # Core orchestrator
│       ├── reference_agent.py       # Reference finder
│       ├── bibtex_agent.py          # BibTeX generator
│       ├── validator_agent.py       # Quality validator
│       └── governance_agent.py      # Policy enforcer
├── tests/
│   └── test_system.py               # Test suite
├── requirements.txt
└── README.md
```

## 📚 Dependencies

- **crewai**: Multi-agent framework
- **litellm**: LLM interface
- **requests**: HTTP client
- **doi2bib3**: DOI to BibTeX converter
- **beautifulsoup4**: HTML parsing
- **bibtexparser**: BibTeX parser

## 📜 License

MIT License - Free for research and educational use

## 🤝 Contributing

This is a research project. Contributions welcome:
- New specialized agents
- Improved tools
- Better governance policies
- Performance optimizations

## 📞 Support

For issues or questions about the multi-agent architecture:
1. Check verbose output (`VERBOSE=True`)
2. Test individual agents
3. Review agent logs
4. Check Ollama connection

---

**Note**: This system is designed for academic research on multi-agent coordination. The architecture prioritizes agent specialization and clear delegation patterns over raw performance.