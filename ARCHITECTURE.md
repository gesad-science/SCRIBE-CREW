# Architecture and Design Decisions

## Multi-Agent System Design

### Core Principles

1. **Separation of Concerns**: Each agent has a single, well-defined responsibility
2. **Hierarchical Coordination**: Core agent orchestrates, specialists execute
3. **Explicit Delegation**: Tools are used for inter-agent communication
4. **No Direct Agent-to-Agent**: All communication flows through the core

### Why Multiple Agents?

This architecture uses multiple specialized agents instead of a monolithic approach because:

- **Research Goal**: Demonstrate multi-agent coordination patterns
- **Modularity**: Easy to add/remove/modify individual agents
- **Specialization**: Each agent can be optimized for its specific task
- **Scalability**: New capabilities = new agents, not code rewrites
- **Fault Isolation**: Agent failures don't crash the entire system

## Critical Design Decisions

### 1. Tool-Based Delegation vs. Direct Agent Calls

**Decision**: Core agent uses tools that internally create crews for delegation.

**Why**:
```python
# ✓ CORRECT: Tool-based delegation
@tool
def delegate_to_specialist(input: str) -> str:
    task = create_task(input)
    crew = Crew(agents=[specialist_agent], tasks=[task])
    return str(crew.kickoff())

# ✗ WRONG: Direct agent interaction
specialist_result = specialist_agent.execute(input)  # Not supported
```

**Rationale**:
- CrewAI agents don't have direct execution methods
- Tools provide a clean interface for the LLM
- Crews handle task execution and error management
- Allows for independent agent testing

### 2. Separate Crews for Each Delegation

**Decision**: Each specialist agent runs in its own crew.

**Why**:
- Prevents crew nesting issues
- Isolates failures
- Allows different configurations per agent
- Cleaner separation of concerns

**Trade-off**: More overhead, but more reliable

### 3. Limited Agent Iterations

**Decision**: `MAX_AGENT_ITERATIONS = 3`

**Why**:
```python
agent = Agent(
    max_iter=3,  # Limit loops
    ...
)
```

**Rationale**:
- Prevents infinite loops
- Forces agents to be efficient
- Reduces timeout risks
- Encourages better tool design

### 4. Tools Return JSON Strings

**Decision**: All tools return JSON-formatted strings.

**Why**:
```python
@tool
def my_tool(input: str) -> str:
    result = {"status": "success", "data": [...]}
    return json.dumps(result, indent=2)  # Always JSON string
```

**Rationale**:
- LLMs understand JSON naturally
- Structured data is easier to parse
- Consistent format across all agents
- Enables better error handling

### 5. No Agent Memory

**Decision**: `ENABLE_MEMORY = False`

**Why**:
- Memory increases complexity
- Memory increases RAM usage
- Not needed for our workflow
- Easier debugging without state

**When to enable**: Only for conversational applications

### 6. Deterministic Tools + LLM Agents

**Decision**: Separate deterministic functions from agent logic.

**Architecture**:
```
User Input
    ↓
Core Agent (LLM) - decides what to do
    ↓
Tool (wrapper) - simple delegation
    ↓
Specialist Agent (LLM) - executes task
    ↓
External API (deterministic) - gets data
```

**Why**:
- LLMs for reasoning, not data processing
- Faster execution
- Easier testing
- More reliable

## Failure Points and Solutions

### Problem 1: Timeout After 600s

**Original Issue**:
```python
# Agent takes forever, times out
result = crew.kickoff()  # Hangs for 10+ minutes
```

**Root Causes**:
1. Too many nested crews
2. No iteration limits
3. Agents retrying indefinitely
4. Complex prompts

**Solutions Implemented**:

```python
# 1. Timeout configuration
llm = LLM(timeout=180)  # 3 minutes per LLM call

# 2. Iteration limits
agent = Agent(max_iter=3)  # Max 3 iterations

# 3. Clear, focused prompts
description="""
STEPS:
1. Do X
2. Do Y
3. Return result

Use each tool ONCE.
"""

# 4. Separate crews per delegation
crew = Crew(
    agents=[single_agent],  # One agent per crew
    tasks=[single_task],
    verbose=True
)
```

### Problem 2: Crews Creating Crews (Nesting)

**Original Issue**:
```python
# Reference agent creates crew
def reference_wrapper(text):
    crew = Crew(agents=[ref_agent], ...)
    
    # Which calls bibtex agent
    def call_bibtex_agent(text):
        crew = Crew(agents=[bibtex_agent], ...)  # Nested!
        return crew.kickoff()
```

**Why This Fails**:
- Exponential complexity
- Context gets lost
- Timeouts multiply
- Hard to debug

**Solution**:
```python
# Core creates plan, delegates sequentially
core_agent:
  → delegates to ref_agent (separate crew)
  ← gets result
  → delegates to bibtex_agent (separate crew)
  ← gets result
  → consolidates
```

### Problem 3: Agents as Tools

**Original Issue**:
```python
@tool
def call_agent(text: str) -> str:
    return another_agent.execute(text)  # Direct call
```

**Why This Fails**:
- Agents don't have `.execute()` method
- Breaks CrewAI's execution model
- No proper error handling

**Solution**:
```python
@tool
def delegate_to_agent(text: str) -> str:
    task = Task(description=text, agent=specialist)
    crew = Crew(agents=[specialist], tasks=[task])
    return str(crew.kickoff())  # Proper delegation
```

### Problem 4: Unclear Task Instructions

**Original Issue**:
```python
Task(
    description="Process this reference somehow and do good job",
    ...
)
```

**Why This Fails**:
- LLM doesn't know what to do
- Retries multiple times
- Uses wrong tools
- Returns wrong format

**Solution**:
```python
Task(
    description="""
You received: {input}

STEPS:
1. Use tool_a to extract X
2. Use tool_b to process Y
3. Return JSON with format:
   {{"field1": "value", "field2": "value"}}

RULES:
- Use each tool ONCE
- Do NOT invent data
- Follow JSON format exactly
""",
    expected_output="JSON object with field1 and field2"
)
```

### Problem 5: No Error Boundaries

**Original Issue**:
```python
result = crew.kickoff()  # Crashes entire system if fails
```

**Solution**:
```python
try:
    result = crew.kickoff()
    return str(result)
except Exception as e:
    return json.dumps({
        "status": "error",
        "message": str(e),
        "error_type": type(e).__name__
    })
```

## Performance Optimizations

### 1. Model Selection

```python
# Fast but less capable
llm = LLM(model="ollama/llama3.2:3b")  # ~2GB RAM, ~5s per call

# Balanced
llm = LLM(model="ollama/mistral:7b")   # ~4GB RAM, ~10s per call

# Slow but more accurate
llm = LLM(model="ollama/llama3.1:70b") # ~40GB RAM, ~30s per call
```

**Recommendation**: Start with 3b, upgrade only if needed.

### 2. Rate Limiting

```python
crew = Crew(
    agents=[...],
    max_rpm=20,  # Max 20 requests per minute
    ...
)
```

**Why**: Prevents API rate limits and reduces server load.

### 3. Verbose Logging

```python
agent = Agent(verbose=True)  # Enable during development
crew = Crew(verbose=True)    # Disable in production
```

**Trade-off**: Verbose = slower but easier to debug.

## Testing Strategy

### 1. Unit Tests (No LLM)

Test deterministic functions:
```python
def test_extract_doi():
    assert extract_doi("DOI: 10.1234/test") == "10.1234/test"
```

### 2. Integration Tests (With LLM)

Test individual agents:
```python
def test_reference_agent():
    task = create_reference_task("Paper title")
    crew = Crew(agents=[reference_finder_agent], tasks=[task])
    result = crew.kickoff()
    assert "title" in str(result)
```

### 3. System Tests (Full Pipeline)

Test complete workflow:
```python
def test_full_system():
    result = process_references("Paper reference")
    assert "bibtex" in result.lower()
```

## Scalability Considerations

### Adding New Agents

1. Create agent file with tools
2. Add delegation tool in core_agent.py
3. Update core agent's tool list
4. Add to governance valid_actions
5. Document in README

### Current Limits

- **References per request**: 5-10 (more = timeout risk)
- **Concurrent requests**: 1 (no parallelization)
- **LLM calls per reference**: 6-8
- **Total time per reference**: 15-30 seconds

### Future Improvements

1. **Parallel Processing**: Process multiple references simultaneously
2. **Caching**: Cache API results to avoid duplicate calls
3. **Batch Operations**: Group similar operations
4. **Smarter Delegation**: Core decides which agents to skip

## Monitoring and Debugging

### Verbose Output Structure

```
[CORE] Starting orchestration...
  [CORE] Delegating to Reference Finder Agent...
    [TOOL] Searching for paper: Title...
    [TOOL] Extracting identifiers...
  [CORE] Delegating to BibTeX Generator Agent...
    [TOOL] Fetching BibTeX for DOI...
[CORE] Orchestration complete!
```

### Common Error Patterns

1. **"Agent failed after max iterations"**
   - Agent stuck in loop
   - Solution: Check tool outputs, simplify task

2. **"Connection timeout"**
   - Ollama not responding
   - Solution: Check `ollama ps`, restart if needed

3. **"Invalid JSON"**
   - Agent returned wrong format
   - Solution: Improve expected_output specification

4. **"Tool not found"**
   - Typo in tool name
   - Solution: Check tool names match exactly

## Research Applications

This architecture demonstrates:

1. **Hierarchical Multi-Agent Systems**: Core + specialists pattern
2. **Task Decomposition**: Breaking complex tasks into subtasks
3. **Agent Coordination**: Explicit delegation and result consolidation
4. **Policy Enforcement**: Governance layer for validation
5. **Error Handling**: Graceful degradation and error reporting

### Potential Research Questions

- How does agent specialization affect overall performance?
- What is the optimal number of agents for a given task?
- How does governance overhead impact execution time?
- Can agents learn to improve delegation strategies?
- What coordination patterns emerge in multi-agent workflows?

## Conclusion

This multi-agent architecture prioritizes:

1. **Clarity**: Each agent has a clear role
2. **Reliability**: Multiple layers of error handling
3. **Modularity**: Easy to extend and modify
4. **Research Value**: Demonstrates agent coordination patterns

The design trades raw speed for robustness and extensibility, making it suitable for research and production use cases where reliability matters more than millisecond-level performance.