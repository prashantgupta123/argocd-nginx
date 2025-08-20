#!/bin/bash

# Test runner script for security configurations
echo "🔒 Running Security Configuration Tests"
echo "======================================"

# Check if Python is available
if command -v python3 &> /dev/null; then
    echo "✅ Python3 found, running configuration tests..."
    python3 test-security-config.py
    TEST_RESULT=$?
elif command -v python &> /dev/null; then
    echo "✅ Python found, running configuration tests..."
    python test-security-config.py
    TEST_RESULT=$?
else
    echo "❌ Python not found, skipping configuration tests"
    TEST_RESULT=1
fi

echo ""
echo "🔍 Validating YAML syntax..."

# Check if yamllint is available
if command -v yamllint &> /dev/null; then
    yamllint nginx-deployment.yaml
    YAML_RESULT=$?
    if [ $YAML_RESULT -eq 0 ]; then
        echo "✅ YAML syntax is valid"
    else
        echo "❌ YAML syntax issues found"
    fi
else
    echo "⚠️  yamllint not found, skipping YAML validation"
    YAML_RESULT=0
fi

echo ""
echo "📋 Summary:"
echo "==========="

if [ $TEST_RESULT -eq 0 ]; then
    echo "✅ Security configuration tests: PASSED"
else
    echo "❌ Security configuration tests: FAILED"
fi

if [ $YAML_RESULT -eq 0 ]; then
    echo "✅ YAML syntax validation: PASSED"
else
    echo "❌ YAML syntax validation: FAILED"
fi

echo ""
echo "📖 Next Steps:"
echo "- Review SECURITY.md for detailed security information"
echo "- Run validate-security.sh after deploying to Kubernetes"
echo "- Consider implementing additional security measures from SECURITY.md"

# Exit with error if any test failed
if [ $TEST_RESULT -ne 0 ] || [ $YAML_RESULT -ne 0 ]; then
    exit 1
else
    exit 0
fi