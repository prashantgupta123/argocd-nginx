# Security Enhancements for Nginx Deployment

This document outlines the security improvements implemented in the nginx-deployment.yaml file to follow Kubernetes security best practices.

## Security Enhancements Implemented

### 1. Service Account Security
- **Created dedicated service account**: `nginx-service-account`
- **Disabled automatic token mounting**: `automountServiceAccountToken: false`
- **Principle of least privilege**: Minimal permissions for the nginx workload

### 2. Container Security Context
- **Non-root execution**: `runAsNonRoot: true`, `runAsUser: 101` (nginx user)
- **Read-only root filesystem**: `readOnlyRootFilesystem: true`
- **Privilege escalation prevention**: `allowPrivilegeEscalation: false`
- **Capability restrictions**: Dropped all capabilities, only added `NET_BIND_SERVICE`
- **Seccomp profile**: Applied `RuntimeDefault` seccomp profile

### 3. Pod Security Context
- **User and group settings**: `runAsUser: 101`, `runAsGroup: 101`, `fsGroup: 101`
- **Non-root enforcement**: `runAsNonRoot: true`
- **Seccomp profile**: Applied at pod level for additional security

### 4. Resource Management
- **CPU limits**: 100m limit, 50m request
- **Memory limits**: 128Mi limit, 64Mi request
- **Prevents resource exhaustion attacks**

### 5. Health Monitoring
- **Liveness probe**: HTTP check on port 80, path "/"
- **Readiness probe**: HTTP check with faster intervals for traffic routing
- **Proper timing configuration**: Appropriate delays and thresholds

### 6. Image Security
- **Specific version**: Changed from `nginx:latest` to `nginx:1.25.3-alpine`
- **Image pull policy**: Set to `Always` for consistency
- **Alpine base**: Smaller attack surface with alpine-based image

### 7. Volume Mounts for Read-Only Filesystem
- **nginx-cache**: `/var/cache/nginx` - For nginx cache files
- **nginx-run**: `/var/run` - For runtime files and PID
- **nginx-tmp**: `/tmp` - For temporary files
- **EmptyDir volumes**: Ephemeral storage that doesn't persist

### 8. Network Security
- **Named ports**: Using named port "http" for better service mesh integration
- **Protocol specification**: Explicit TCP protocol declaration

## Security Annotations

### Seccomp Profile
```yaml
seccomp.security.alpha.kubernetes.io/pod: runtime/default
```
Applied at both pod and container level for system call filtering.

## Validation and Testing

### 1. Security Validation Commands

```bash
# Check if containers are running as non-root
kubectl exec -it deployment/nginx-deployment -- id

# Verify read-only filesystem
kubectl exec -it deployment/nginx-deployment -- touch /test-file
# Should fail with "Read-only file system"

# Check capabilities
kubectl exec -it deployment/nginx-deployment -- capsh --print

# Verify resource limits
kubectl describe pod -l app=nginx
```

### 2. Functional Testing

```bash
# Test HTTP connectivity
kubectl port-forward service/nginx-service 8080:80
curl http://localhost:8080

# Check health probes
kubectl get pods -l app=nginx -o wide
kubectl describe pod -l app=nginx | grep -A 10 "Liveness\|Readiness"
```

### 3. Security Scanning

```bash
# Use tools like:
# - kube-score for Kubernetes security scoring
# - kube-bench for CIS Kubernetes Benchmark
# - Falco for runtime security monitoring
```

## Compliance and Standards

This configuration addresses several security frameworks:

- **CIS Kubernetes Benchmark**: Multiple controls addressed
- **NIST Cybersecurity Framework**: Protect function implementation
- **Pod Security Standards**: Restricted profile compliance
- **OWASP Kubernetes Top 10**: Several vulnerabilities mitigated

## Monitoring and Alerting

### Recommended Monitoring
1. **Resource usage**: Monitor CPU/memory against limits
2. **Health probe failures**: Alert on probe failures
3. **Security events**: Monitor for privilege escalation attempts
4. **Image vulnerabilities**: Regular scanning of nginx:1.25.3-alpine

### Log Monitoring
- Monitor nginx access logs for suspicious patterns
- Watch for security context violations
- Track resource limit breaches

## Maintenance

### Regular Updates
1. **Image updates**: Regularly update nginx version for security patches
2. **Resource tuning**: Adjust limits based on actual usage patterns
3. **Security scanning**: Regular vulnerability assessments
4. **Probe tuning**: Adjust health check parameters based on performance

### Security Reviews
- Quarterly review of security configurations
- Annual penetration testing
- Regular compliance audits

## Troubleshooting

### Common Issues

1. **Container fails to start**
   - Check if nginx user (101) exists in the image
   - Verify volume mounts are accessible
   - Check resource limits aren't too restrictive

2. **Health probes failing**
   - Verify nginx is listening on port 80
   - Check if probe timing is appropriate
   - Ensure nginx serves content at "/"

3. **Permission denied errors**
   - Verify volume mounts for writable directories
   - Check if additional capabilities are needed
   - Ensure file permissions are correct

### Debug Commands

```bash
# Check pod events
kubectl describe pod -l app=nginx

# View container logs
kubectl logs -l app=nginx

# Execute into container for debugging
kubectl exec -it deployment/nginx-deployment -- /bin/sh

# Check security context
kubectl get pod -l app=nginx -o yaml | grep -A 20 securityContext
```

## Future Enhancements

1. **Network Policies**: Implement network segmentation
2. **Pod Security Policies/Pod Security Standards**: Enforce at namespace level
3. **Service Mesh**: Integrate with Istio/Linkerd for mTLS
4. **Admission Controllers**: Use OPA Gatekeeper for policy enforcement
5. **Runtime Security**: Implement Falco rules for runtime monitoring

## References

- [Kubernetes Security Best Practices](https://kubernetes.io/docs/concepts/security/)
- [Pod Security Standards](https://kubernetes.io/docs/concepts/security/pod-security-standards/)
- [CIS Kubernetes Benchmark](https://www.cisecurity.org/benchmark/kubernetes)
- [NIST Container Security Guide](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-190.pdf)