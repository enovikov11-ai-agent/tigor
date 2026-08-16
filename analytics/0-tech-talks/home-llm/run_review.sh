#!/bin/bash
# Wrapper script to run presentation review automation

echo "🚀 Presentation Review Automation"
echo "=================================="
echo ""

# Check if API key is provided as argument
if [ -n "$1" ]; then
    export ANTHROPIC_API_KEY="$1"
    echo "✅ Using provided API key"
elif [ -n "$ANTHROPIC_API_KEY" ]; then
    echo "✅ Using existing ANTHROPIC_API_KEY from environment"
else
    echo "⚠️  No ANTHROPIC_API_KEY provided"
    echo "   Screenshots will be taken but evaluation will be skipped"
    echo ""
    echo "Usage:"
    echo "   ./run_review.sh [ANTHROPIC_API_KEY]"
    echo "   or"
    echo "   export ANTHROPIC_API_KEY='your-key' && ./run_review.sh"
    echo ""
fi

echo ""
echo "📂 Working directory: $(pwd)"
echo "📄 Presentation: ru.html"
echo "📁 Screenshots will be saved to: screenshots/"
echo ""
read -p "Press Enter to start or Ctrl+C to cancel..."
echo ""

# Run the automation
python3 review_slides.py

echo ""
echo "✅ Automation complete!"
echo "📁 Check screenshots/ directory for results"
