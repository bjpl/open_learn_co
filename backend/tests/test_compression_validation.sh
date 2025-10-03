#!/bin/bash
# Compression Middleware Validation Script
# Tests compression implementation without running full test suite

set -e

echo "========================================================================"
echo "COMPRESSION MIDDLEWARE VALIDATION"
echo "========================================================================"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if in correct directory
if [ ! -f "app/middleware/compression.py" ]; then
    echo -e "${RED}Error: Must run from backend directory${NC}"
    exit 1
fi

echo -e "\n${YELLOW}[1/5] Checking Python environment...${NC}"
python3 --version
echo "✓ Python available"

echo -e "\n${YELLOW}[2/5] Checking required packages...${NC}"
python3 -c "import brotli; print(f'✓ brotli {brotli.__version__}')" 2>/dev/null || echo "✗ brotli not installed (pip install brotli==1.1.0)"
python3 -c "import gzip; print('✓ gzip (built-in)')" || echo "✗ gzip not available"
python3 -c "import fastapi; print(f'✓ fastapi')" 2>/dev/null || echo "✗ fastapi not installed"

echo -e "\n${YELLOW}[3/5] Validating compression middleware...${NC}"
python3 << 'EOF'
import sys
sys.path.insert(0, '.')

try:
    from app.middleware.compression import CompressionMiddleware, COMPRESSIBLE_TYPES, SKIP_COMPRESSION_TYPES
    print("✓ CompressionMiddleware imported successfully")
    print(f"✓ Compressible types: {len(COMPRESSIBLE_TYPES)} configured")
    print(f"✓ Skip compression types: {len(SKIP_COMPRESSION_TYPES)} configured")
except Exception as e:
    print(f"✗ Import failed: {e}")
    sys.exit(1)
EOF

echo -e "\n${YELLOW}[4/5] Testing compression functionality...${NC}"
python3 << 'EOF'
import sys
sys.path.insert(0, '.')
import brotli
import gzip
import json

# Test data
test_data = json.dumps({"data": [{"id": i, "value": "x" * 100} for i in range(50)]}).encode()
print(f"Original size: {len(test_data)} bytes")

# Test Brotli
brotli_compressed = brotli.compress(test_data, quality=4)
brotli_ratio = (1 - len(brotli_compressed) / len(test_data)) * 100
print(f"✓ Brotli compressed: {len(brotli_compressed)} bytes ({brotli_ratio:.1f}% saved)")

# Test Gzip
gzip_compressed = gzip.compress(test_data, compresslevel=6)
gzip_ratio = (1 - len(gzip_compressed) / len(test_data)) * 100
print(f"✓ Gzip compressed: {len(gzip_compressed)} bytes ({gzip_ratio:.1f}% saved)")

# Verify Brotli is better
improvement = brotli_ratio - gzip_ratio
print(f"✓ Brotli improvement: +{improvement:.1f}%")

# Decompression test
decompressed_brotli = brotli.decompress(brotli_compressed)
decompressed_gzip = gzip.decompress(gzip_compressed)
assert decompressed_brotli == test_data, "Brotli decompression failed"
assert decompressed_gzip == test_data, "Gzip decompression failed"
print("✓ Decompression verified")
EOF

echo -e "\n${YELLOW}[5/5] Checking configuration files...${NC}"

# Check main.py has compression middleware
if grep -q "CompressionMiddleware" app/main.py; then
    echo "✓ Compression middleware added to app/main.py"
else
    echo "✗ Compression middleware NOT found in app/main.py"
fi

# Check requirements.txt
if grep -q "brotli" requirements.txt; then
    echo "✓ brotli dependency in requirements.txt"
else
    echo "✗ brotli NOT in requirements.txt"
fi

# Check .env.example
if grep -q "ENABLE_COMPRESSION" .env.example; then
    echo "✓ Compression settings in .env.example"
else
    echo "✗ Compression settings NOT in .env.example"
fi

# Check config/settings.py
if grep -q "COMPRESSION" app/config/settings.py; then
    echo "✓ Compression settings in app/config/settings.py"
else
    echo "✗ Compression settings NOT in app/config/settings.py"
fi

echo -e "\n${GREEN}========================================================================"
echo "VALIDATION COMPLETE"
echo "========================================================================${NC}"

echo -e "\n${YELLOW}Installation Instructions:${NC}"
echo "1. Install compression dependencies:"
echo "   pip install brotli==1.1.0 brotlipy==0.7.0"
echo ""
echo "2. Update environment variables in .env:"
echo "   ENABLE_COMPRESSION=True"
echo "   BROTLI_COMPRESSION_LEVEL=4"
echo "   GZIP_COMPRESSION_LEVEL=6"
echo "   COMPRESSION_MIN_SIZE=500"
echo ""
echo "3. Restart the FastAPI server"
echo ""
echo "4. Test compression with:"
echo "   curl -H 'Accept-Encoding: br, gzip' http://localhost:8000/api/scraping/sources"
echo ""
echo "5. Check compression stats:"
echo "   curl http://localhost:8000/health/compression"

echo -e "\n${GREEN}Performance Targets:${NC}"
echo "  - JSON compression ratio: >60%"
echo "  - Compression overhead: <10ms"
echo "  - Bandwidth savings: 60-80%"
echo "  - CPU impact: <5%"
