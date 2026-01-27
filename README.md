# SCRIBE System

## 🎯 Research Objective

A multi-agent system for processing academic references using specialized AI agents coordinated by a core orchestrator. This architecture follows the LLM-native style and demonstrates agent collaboration, task delegation, and hierarchical planning in an academic context.

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

#### Native agents

##### **Core Orchestrator Agent** 🎯
- **Role**: Main coordinator
- **Responsibilities**:
  - Receives user requests
  - Creates execution plans
  - Delegates tasks to specialized agents
  - Consolidates results
  - Manages workflow
- **Tools**: Delegation functions for each specialized agent

##### **Governance Agent** 🛡️
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

#### Domain agents

##### 1. **Reference Finder Agent** 🔍
- **Role**: Paper search specialist
- **Responsibilities**:
  - Extract identifiers (DOI, arXiv) from references
  - Search Semantic Scholar API
  - Extract paper metadata
- **Tools**:
  - `search_paper_by_title`
  - `extract_identifiers_from_reference`
  - `guess_title_tool`

##### 2. **BibTeX Generator Agent** 📝
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

##### 3. **Reference Validator Agent** ✅
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

## 🔄 Workflow

### Step-by-Step Process

```
1. User submits a request
         ↓
2. Core Agent receives request
         ↓
3. Core creates execution plan
         ↓
4. Governance validates plan
         ↓
5. Core executes plan:
         ↓
6. Core consolidates results
         ↓
7. User receives final output
```

### Example Execution Flow

For input: " Give more information about Smith, J. (2020). AI Research. Conference."

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
cd SCRIBE-CREW

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows

# Also can use anaconda

# 3. Install dependencies
pip install -r requirements.txt

# 4. (If using an external API) Create .env file (IMPORTANT!)
cat > .env << EOF
API_KEY = # your key here
EOF

# 5. (If using ollama) Setup Ollama
# Download from: https://ollama.ai
ollama pull llama3.2:3b

# 6. Start Ollama
ollama serve
```

## 📖 Usage

### Command Line

```bash
# Single reference
python -m test.py
### and set your input.
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

## ⚙️ Configuration (`config.py`)

### LLM Settings 

> USE_OLLAMA 
enables or disables the use of the Ollama backend for model execution.

> MODEL 
specifies the language model to be used by the system.

>TIMEOUT
defines the maximum time (in seconds) allowed for a single model request before it is aborted.

> TEMPERATURE 
controls the randomness of the model’s responses. Lower values make outputs more deterministic, while higher values increase creativity.

> MAX_RETRIES
sets how many times the system will retry a failed model request.

> VERBOSE
enables detailed logging, useful for debugging and understanding internal execution flow.

### Core Configuration

> CORE_CONFIG
groups settings related to the internal agent system.

> AVALIABLE_AGENTS
defines which agents are enabled and can participate in the execution pipeline. The order may matter depending on the orchestration logic.

> PLAN_OUTPUT
defines the format or style of the generated plans produced by the planning agent.

### Governance Configuration

> POLICIES
the system policies that governance agent will use to validate information.

### Model Recommendations

| Model | RAM | Speed | Accuracy |
|-------|-----|-------|----------|
| llama3.2:3b | 2GB | Fast | Good |
| llama3.1:8b | 5GB | Medium | Better |
| mistral:7b | 4GB | Medium | Good |


## 📝 Extending the System

### Adding a New Agent

--- not implemented yet ---


## 📚 Dependencies

- **crewai**: Multi-agent framework
- **litellm**: LLM interface
- **requests**: HTTP client
- **doi2bib3**: DOI to BibTeX converter
- **beautifulsoup4**: HTML parsing
- **bibtexparser**: BibTeX parser

Verify the file `requirements.txt` to know more

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