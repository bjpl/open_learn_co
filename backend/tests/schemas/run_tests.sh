#!/bin/bash
# Test runner for validation schemas
# Install dependencies first: pip install -r requirements.txt

cd "$(dirname "$0")/../.."

echo "Running validation schema tests..."
python -m pytest tests/schemas/test_validation.py -v --tb=short

echo ""
echo "Test Summary:"
python -m pytest tests/schemas/test_validation.py --collect-only -q
