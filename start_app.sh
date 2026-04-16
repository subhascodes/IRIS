#!/bin/bash
# Start the Guidewire Streamlit app
# Usage: bash start_app.sh

set -e

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "🚀 Starting Guidewire Agentic Governance System..."
echo ""

# Check if venv exists
if [ ! -d "$REPO_DIR/venv" ]; then
    echo "❌ Virtual environment not found at $REPO_DIR/venv"
    echo "   Please run: python3 -m venv venv"
    exit 1
fi

# Activate venv
source "$REPO_DIR/venv/bin/activate"

# Check if streamlit is installed
if ! command -v streamlit &> /dev/null; then
    echo "📦 Installing dependencies..."
    pip install -q -r "$REPO_DIR/requirements.txt"
fi

# Start app
echo "📡 Streamlit server starting..."
echo "   → Open: http://localhost:8501"
echo "   → Login with: admin / admin"
echo "   → Select: 'Agent' mode for autonomous rule evaluation"
echo ""
echo "Press Ctrl+C to stop"
echo ""

cd "$REPO_DIR"
streamlit run app.py
