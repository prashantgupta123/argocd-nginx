#!/usr/bin/env python3
"""
Unit tests for nginx-deployment.yaml security configurations
This script validates that all required security parameters are present
"""

import yaml
import sys
import os

def load_yaml_file(file_path):
    """Load and parse YAML file"""
    try:
        with open(file_path, 'r') as file:
            documents = list(yaml.safe_load_all(file))
        return documents
    except Exception as e:
        print(f"❌ Error loading YAML file: {e}")
        return None

def test_service_account(documents):
    """Test service account configuration"""
    print("🔍 Testing Service Account configuration...")
    
    service_account = None
    for doc in documents:
        if doc and doc.get('kind') == 'ServiceAccount':
            service_account = doc
            break
    
    if not service_account:
        print("❌ ServiceAccount not found")
        return False
    
    # Check service account name
    if service_account.get('metadata', {}).get('name') != 'nginx-service-account':
        print("❌ ServiceAccount name is not 'nginx-service-account'")
        return False
    
    # Check automountServiceAccountToken
    if service_account.get('automountServiceAccountToken') is not False:
        print("❌ automountServiceAccountToken should be false")
        return False
    
    print("✅ Service Account configuration is correct")
    return True

def test_deployment_security(documents):
    """Test deployment security configurations"""
    print("🔍 Testing Deployment security configuration...")
    
    deployment = None
    for doc in documents:
        if doc and doc.get('kind') == 'Deployment':
            deployment = doc
            break
    
    if not deployment:
        print("❌ Deployment not found")
        return False
    
    spec = deployment.get('spec', {})
    template = spec.get('template', {})
    pod_spec = template.get('spec', {})
    
    # Test service account reference
    if pod_spec.get('serviceAccountName') != 'nginx-service-account':
        print("❌ serviceAccountName not set to nginx-service-account")
        return False
    
    # Test pod security context
    pod_security_context = pod_spec.get('securityContext', {})
    
    required_pod_security = {
        'runAsNonRoot': True,
        'runAsUser': 101,
        'runAsGroup': 101,
        'fsGroup': 101
    }
    
    for key, expected_value in required_pod_security.items():
        if pod_security_context.get(key) != expected_value:
            print(f"❌ Pod securityContext.{key} should be {expected_value}")
            return False
    
    # Test seccomp profile
    if pod_security_context.get('seccompProfile', {}).get('type') != 'RuntimeDefault':
        print("❌ Pod seccompProfile should be RuntimeDefault")
        return False
    
    print("✅ Deployment security configuration is correct")
    return True

def test_container_security(documents):
    """Test container security configurations"""
    print("🔍 Testing Container security configuration...")
    
    deployment = None
    for doc in documents:
        if doc and doc.get('kind') == 'Deployment':
            deployment = doc
            break
    
    if not deployment:
        print("❌ Deployment not found")
        return False
    
    containers = deployment.get('spec', {}).get('template', {}).get('spec', {}).get('containers', [])
    
    if not containers:
        print("❌ No containers found")
        return False
    
    nginx_container = containers[0]  # Assuming first container is nginx
    
    # Test image
    image = nginx_container.get('image', '')
    if not image.startswith('nginx:1.25.3-alpine'):
        print(f"❌ Image should be nginx:1.25.3-alpine, got: {image}")
        return False
    
    # Test imagePullPolicy
    if nginx_container.get('imagePullPolicy') != 'Always':
        print("❌ imagePullPolicy should be Always")
        return False
    
    # Test container security context
    container_security_context = nginx_container.get('securityContext', {})
    
    required_container_security = {
        'allowPrivilegeEscalation': False,
        'readOnlyRootFilesystem': True,
        'runAsNonRoot': True,
        'runAsUser': 101,
        'runAsGroup': 101
    }
    
    for key, expected_value in required_container_security.items():
        if container_security_context.get(key) != expected_value:
            print(f"❌ Container securityContext.{key} should be {expected_value}")
            return False
    
    # Test capabilities
    capabilities = container_security_context.get('capabilities', {})
    if capabilities.get('drop') != ['ALL']:
        print("❌ Capabilities drop should be ['ALL']")
        return False
    
    if capabilities.get('add') != ['NET_BIND_SERVICE']:
        print("❌ Capabilities add should be ['NET_BIND_SERVICE']")
        return False
    
    print("✅ Container security configuration is correct")
    return True

def test_resource_limits(documents):
    """Test resource limits configuration"""
    print("🔍 Testing Resource limits configuration...")
    
    deployment = None
    for doc in documents:
        if doc and doc.get('kind') == 'Deployment':
            deployment = doc
            break
    
    containers = deployment.get('spec', {}).get('template', {}).get('spec', {}).get('containers', [])
    nginx_container = containers[0]
    
    resources = nginx_container.get('resources', {})
    
    # Test requests
    requests = resources.get('requests', {})
    if requests.get('memory') != '64Mi' or requests.get('cpu') != '50m':
        print(f"❌ Resource requests should be memory: 64Mi, cpu: 50m")
        return False
    
    # Test limits
    limits = resources.get('limits', {})
    if limits.get('memory') != '128Mi' or limits.get('cpu') != '100m':
        print(f"❌ Resource limits should be memory: 128Mi, cpu: 100m")
        return False
    
    print("✅ Resource limits configuration is correct")
    return True

def test_health_probes(documents):
    """Test health probes configuration"""
    print("🔍 Testing Health probes configuration...")
    
    deployment = None
    for doc in documents:
        if doc and doc.get('kind') == 'Deployment':
            deployment = doc
            break
    
    containers = deployment.get('spec', {}).get('template', {}).get('spec', {}).get('containers', [])
    nginx_container = containers[0]
    
    # Test liveness probe
    liveness_probe = nginx_container.get('livenessProbe', {})
    if not liveness_probe:
        print("❌ Liveness probe not configured")
        return False
    
    liveness_http = liveness_probe.get('httpGet', {})
    if liveness_http.get('path') != '/' or liveness_http.get('port') != 'http':
        print("❌ Liveness probe HTTP configuration incorrect")
        return False
    
    # Test readiness probe
    readiness_probe = nginx_container.get('readinessProbe', {})
    if not readiness_probe:
        print("❌ Readiness probe not configured")
        return False
    
    readiness_http = readiness_probe.get('httpGet', {})
    if readiness_http.get('path') != '/' or readiness_http.get('port') != 'http':
        print("❌ Readiness probe HTTP configuration incorrect")
        return False
    
    print("✅ Health probes configuration is correct")
    return True

def test_volume_mounts(documents):
    """Test volume mounts for read-only filesystem"""
    print("🔍 Testing Volume mounts configuration...")
    
    deployment = None
    for doc in documents:
        if doc and doc.get('kind') == 'Deployment':
            deployment = doc
            break
    
    pod_spec = deployment.get('spec', {}).get('template', {}).get('spec', {})
    containers = pod_spec.get('containers', [])
    nginx_container = containers[0]
    
    # Test volume mounts
    volume_mounts = nginx_container.get('volumeMounts', [])
    expected_mounts = {
        'nginx-cache': '/var/cache/nginx',
        'nginx-run': '/var/run',
        'nginx-tmp': '/tmp'
    }
    
    mount_dict = {mount['name']: mount['mountPath'] for mount in volume_mounts}
    
    for name, path in expected_mounts.items():
        if mount_dict.get(name) != path:
            print(f"❌ Volume mount {name} should be mounted at {path}")
            return False
    
    # Test volumes
    volumes = pod_spec.get('volumes', [])
    volume_names = [vol['name'] for vol in volumes]
    
    for expected_name in expected_mounts.keys():
        if expected_name not in volume_names:
            print(f"❌ Volume {expected_name} not found")
            return False
    
    print("✅ Volume mounts configuration is correct")
    return True

def test_service_configuration(documents):
    """Test service configuration"""
    print("🔍 Testing Service configuration...")
    
    service = None
    for doc in documents:
        if doc and doc.get('kind') == 'Service':
            service = doc
            break
    
    if not service:
        print("❌ Service not found")
        return False
    
    # Test service name
    if service.get('metadata', {}).get('name') != 'nginx-service':
        print("❌ Service name should be nginx-service")
        return False
    
    # Test port configuration
    ports = service.get('spec', {}).get('ports', [])
    if not ports:
        print("❌ No ports configured in service")
        return False
    
    port_config = ports[0]
    if (port_config.get('name') != 'http' or 
        port_config.get('port') != 80 or 
        port_config.get('targetPort') != 'http'):
        print("❌ Service port configuration incorrect")
        return False
    
    print("✅ Service configuration is correct")
    return True

def main():
    """Main test function"""
    print("🔒 Starting Security Configuration Tests")
    print("=" * 50)
    
    # Load YAML file
    file_path = 'nginx-deployment.yaml'
    if not os.path.exists(file_path):
        print(f"❌ File {file_path} not found")
        sys.exit(1)
    
    documents = load_yaml_file(file_path)
    if not documents:
        sys.exit(1)
    
    # Run all tests
    tests = [
        test_service_account,
        test_deployment_security,
        test_container_security,
        test_resource_limits,
        test_health_probes,
        test_volume_mounts,
        test_service_configuration
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test(documents):
                passed += 1
            print()  # Empty line for readability
        except Exception as e:
            print(f"❌ Test failed with error: {e}")
            print()
    
    # Summary
    print("=" * 50)
    print(f"🔒 Security Configuration Test Results: {passed}/{total} passed")
    
    if passed == total:
        print("✅ All security configurations are correct!")
        sys.exit(0)
    else:
        print("❌ Some security configurations need attention")
        sys.exit(1)

if __name__ == "__main__":
    main()