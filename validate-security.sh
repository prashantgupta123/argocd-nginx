#!/bin/bash

# Security Validation Script for Nginx Deployment
# This script validates that all security configurations are properly applied

set -e

echo "🔒 Starting Security Validation for Nginx Deployment"
echo "=================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print status
print_status() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✅ $2${NC}"
    else
        echo -e "${RED}❌ $2${NC}"
    fi
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# Check if kubectl is available
if ! command -v kubectl &> /dev/null; then
    echo -e "${RED}❌ kubectl is not installed or not in PATH${NC}"
    exit 1
fi

# Check if deployment exists
echo "1. Checking if nginx deployment exists..."
if kubectl get deployment nginx-deployment &> /dev/null; then
    print_status 0 "Nginx deployment found"
else
    print_status 1 "Nginx deployment not found"
    exit 1
fi

# Check if service account exists
echo "2. Checking service account..."
if kubectl get serviceaccount nginx-service-account &> /dev/null; then
    print_status 0 "Service account nginx-service-account exists"
else
    print_status 1 "Service account nginx-service-account not found"
fi

# Wait for pods to be ready
echo "3. Waiting for pods to be ready..."
kubectl wait --for=condition=ready pod -l app=nginx --timeout=60s
if [ $? -eq 0 ]; then
    print_status 0 "Pods are ready"
else
    print_status 1 "Pods are not ready within timeout"
    exit 1
fi

# Get pod name for testing
POD_NAME=$(kubectl get pods -l app=nginx -o jsonpath='{.items[0].metadata.name}')
echo "Using pod: $POD_NAME"

# Test 1: Check if running as non-root
echo "4. Testing non-root execution..."
USER_ID=$(kubectl exec $POD_NAME -- id -u 2>/dev/null || echo "failed")
if [ "$USER_ID" = "101" ]; then
    print_status 0 "Container running as user 101 (non-root)"
else
    print_status 1 "Container not running as expected user (got: $USER_ID)"
fi

# Test 2: Check read-only filesystem
echo "5. Testing read-only filesystem..."
kubectl exec $POD_NAME -- touch /test-readonly-file &> /dev/null
if [ $? -ne 0 ]; then
    print_status 0 "Root filesystem is read-only"
else
    print_status 1 "Root filesystem is writable (security risk)"
fi

# Test 3: Check if nginx is serving content
echo "6. Testing HTTP connectivity..."
kubectl exec $POD_NAME -- curl -s http://localhost:80 > /dev/null
if [ $? -eq 0 ]; then
    print_status 0 "Nginx is serving HTTP requests"
else
    print_status 1 "Nginx is not responding to HTTP requests"
fi

# Test 4: Check resource limits
echo "7. Checking resource limits..."
MEMORY_LIMIT=$(kubectl get pod $POD_NAME -o jsonpath='{.spec.containers[0].resources.limits.memory}')
CPU_LIMIT=$(kubectl get pod $POD_NAME -o jsonpath='{.spec.containers[0].resources.limits.cpu}')

if [ "$MEMORY_LIMIT" = "128Mi" ] && [ "$CPU_LIMIT" = "100m" ]; then
    print_status 0 "Resource limits are properly configured"
else
    print_status 1 "Resource limits not as expected (Memory: $MEMORY_LIMIT, CPU: $CPU_LIMIT)"
fi

# Test 5: Check security context
echo "8. Checking security context..."
RUN_AS_NON_ROOT=$(kubectl get pod $POD_NAME -o jsonpath='{.spec.securityContext.runAsNonRoot}')
RUN_AS_USER=$(kubectl get pod $POD_NAME -o jsonpath='{.spec.securityContext.runAsUser}')

if [ "$RUN_AS_NON_ROOT" = "true" ] && [ "$RUN_AS_USER" = "101" ]; then
    print_status 0 "Pod security context is properly configured"
else
    print_status 1 "Pod security context not as expected"
fi

# Test 6: Check container security context
echo "9. Checking container security context..."
ALLOW_PRIV_ESC=$(kubectl get pod $POD_NAME -o jsonpath='{.spec.containers[0].securityContext.allowPrivilegeEscalation}')
READ_ONLY_FS=$(kubectl get pod $POD_NAME -o jsonpath='{.spec.containers[0].securityContext.readOnlyRootFilesystem}')

if [ "$ALLOW_PRIV_ESC" = "false" ] && [ "$READ_ONLY_FS" = "true" ]; then
    print_status 0 "Container security context is properly configured"
else
    print_status 1 "Container security context not as expected"
fi

# Test 7: Check health probes
echo "10. Checking health probes..."
LIVENESS_PATH=$(kubectl get pod $POD_NAME -o jsonpath='{.spec.containers[0].livenessProbe.httpGet.path}')
READINESS_PATH=$(kubectl get pod $POD_NAME -o jsonpath='{.spec.containers[0].readinessProbe.httpGet.path}')

if [ "$LIVENESS_PATH" = "/" ] && [ "$READINESS_PATH" = "/" ]; then
    print_status 0 "Health probes are configured"
else
    print_status 1 "Health probes not properly configured"
fi

# Test 8: Check image version
echo "11. Checking image version..."
IMAGE=$(kubectl get pod $POD_NAME -o jsonpath='{.spec.containers[0].image}')
if [[ "$IMAGE" == *"nginx:1.25.3-alpine"* ]]; then
    print_status 0 "Using specific nginx version (not latest)"
else
    print_status 1 "Not using expected nginx version (got: $IMAGE)"
fi

# Test 9: Check service connectivity
echo "12. Testing service connectivity..."
kubectl get service nginx-service &> /dev/null
if [ $? -eq 0 ]; then
    print_status 0 "Service nginx-service exists"
    
    # Port forward test (background process)
    kubectl port-forward service/nginx-service 8080:80 &> /dev/null &
    PF_PID=$!
    sleep 2
    
    # Test connectivity
    curl -s http://localhost:8080 > /dev/null 2>&1
    if [ $? -eq 0 ]; then
        print_status 0 "Service is accessible via port-forward"
    else
        print_status 1 "Service is not accessible"
    fi
    
    # Clean up port-forward
    kill $PF_PID 2>/dev/null || true
else
    print_status 1 "Service nginx-service not found"
fi

# Summary
echo ""
echo "🔒 Security Validation Complete"
echo "================================"

# Additional security recommendations
echo ""
echo "📋 Additional Security Recommendations:"
echo "- Regularly update the nginx image version"
echo "- Implement network policies for network segmentation"
echo "- Use Pod Security Standards at namespace level"
echo "- Monitor with security tools like Falco"
echo "- Regular vulnerability scanning of container images"
echo "- Implement admission controllers for policy enforcement"

echo ""
echo "For more details, see SECURITY.md"