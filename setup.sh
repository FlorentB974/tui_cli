#!/bin/bash
# setup.sh - TUI CLI v1.0 setup helper

set -e

echo "🚀 TUI CLI v1.0 - Setup Helper"
echo "=================================="
echo ""

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "📝 Creating .env from template..."
    cp .env.example .env
    echo "✓ .env created"
    echo ""
    echo "⚠️  IMPORTANT: Edit .env with your API credentials:"
    echo "   nano .env"
    echo ""
fi

# Check Python
echo "🔍 Checking Python..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found"
    exit 1
fi
echo "✓ Python $(python3 --version | cut -d' ' -f2)"
echo ""

# Check virtual environment
echo "🔍 Checking virtual environment..."
if [ ! -d ".venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv .venv
    echo "✓ Virtual environment created"
fi
echo ""

# Activate venv
echo "🔌 Activating virtual environment..."
source .venv/bin/activate
echo "✓ Virtual environment activated"
echo ""

# Install dependencies
echo "📚 Installing dependencies..."
pip install -q -r requirements.txt
echo "✓ Dependencies installed"
echo ""

# Run tests
echo "🧪 Running verification tests..."
python test_project.py
echo ""

echo "=================================="
echo "✅ Setup Complete!"
echo ""
echo "📝 Next steps:"
echo "   1. Edit .env with your API credentials"
echo "   2. Run: python main.py"
echo "   3. Type /help in the app"
echo ""
echo "📖 Documentation:"
echo "   - README.md - Full documentation"
echo "   - QUICKSTART.md - Quick start guide"
echo "   - PROJECT_SUMMARY.md - Project overview"
echo ""
echo "Happy chatting! 🎉"
