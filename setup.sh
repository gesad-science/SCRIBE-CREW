#!/bin/bash
# setup.sh - Quick setup script for Academic Multi-Agent System

set -e  # Exit on error

echo "========================================================================"
echo "        Academic Multi-Agent System - Setup Script"
echo "========================================================================"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check Python version
echo -e "${YELLOW}[1/7]${NC} Checking Python version..."
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
REQUIRED_VERSION="3.10"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" = "$REQUIRED_VERSION" ]; then 
    echo -e "${GREEN}✓${NC} Python $PYTHON_VERSION detected"
else
    echo -e "${RED}✗${NC} Python 3.10+ required, found $PYTHON_VERSION"
    exit 1
fi

# Create virtual environment
echo -e "\n${YELLOW}[2/7]${NC} Creating virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo -e "${GREEN}✓${NC} Virtual environment created"
else
    echo -e "${GREEN}✓${NC} Virtual environment already exists"
fi

# Activate virtual environment
echo -e "\n${YELLOW}[3/7]${NC} Activating virtual environment..."
source venv/bin/activate
echo -e "${GREEN}✓${NC} Virtual environment activated"

# Install dependencies
echo -e "\n${YELLOW}[4/7]${NC} Installing dependencies..."
pip install --upgrade pip -q
pip install -r requirements.txt -q
echo -e "${GREEN}✓${NC} Dependencies installed"

# Create .env file
echo -e "\n${YELLOW}[5/7]${NC} Creating .env configuration..."
if [ ! -f ".env" ]; then
    cat > .env << EOF
# === Telemetry Settings ===
OTEL_SDK_DISABLED=true
CREWAI_TELEMETRY_ENABLED=false

# === LLM Configuration ===
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2:3b

# === Timeouts (in seconds) ===
LLM_TIMEOUT=180
CORE_AGENT_TIMEOUT=300

# === Agent Configuration ===
MAX_AGENT_ITERATIONS=3
MAX_RPM=20
ENABLE_MEMORY=false
VERBOSE=true
EOF
    echo -e "${GREEN}✓${NC} .env file created"
else
    echo -e "${GREEN}✓${NC} .env file already exists"
fi

# Check Ollama
echo -e "\n${YELLOW}[6/7]${NC} Checking Ollama..."
if command -v ollama &> /dev/null; then
    echo -e "${GREEN}✓${NC} Ollama is installed"
    
    # Check if Ollama is running
    if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} Ollama is running"
    else
        echo -e "${YELLOW}⚠${NC} Ollama is not running"
        echo "  Start it with: ollama serve"
    fi
    
    # Check if model exists
    if ollama list | grep -q "llama3.2:3b"; then
        echo -e "${GREEN}✓${NC} Model llama3.2:3b is available"
    else
        echo -e "${YELLOW}⚠${NC} Model llama3.2:3b not found"
        echo "  Pull it with: ollama pull llama3.2:3b"
        read -p "  Pull now? [y/N]: " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            ollama pull llama3.2:3b
            echo -e "${GREEN}✓${NC} Model downloaded"
        fi
    fi
else
    echo -e "${RED}✗${NC} Ollama is not installed"
    echo "  Download from: https://ollama.ai"
    exit 1
fi

# Run tests
echo -e "\n${YELLOW}[7/7]${NC} Running quick tests..."
read -p "Run system tests? [y/N]: " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    python tests/test_system.py
else
    echo -e "${YELLOW}⊘${NC} Tests skipped"
fi

# Summary
echo ""
echo "========================================================================"
echo -e "${GREEN}✓ Setup Complete!${NC}"
echo "========================================================================"
echo ""
echo "Next steps:"
echo "  1. Activate virtual environment:"
echo "     $ source venv/bin/activate"
echo ""
echo "  2. Start Ollama (if not running):"
echo "     $ ollama serve"
echo ""
echo "  3. Run the system:"
echo "     $ python src/main.py 'Your reference here'"
echo ""
echo "  4. Or run tests:"
echo "     $ python tests/test_system.py"
echo ""
echo "For help, see README.md and TROUBLESHOOTING.md"
echo "========================================================================"