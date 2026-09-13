# Remediation Plan

## Purpose

This document tracks security findings that remain unresolved after the security assessment.

High-impact application and infrastructure findings identified during the assessment were remediated where practical. The remaining items are documented with residual risk, remediation effort, and compensating controls.

---

## Remaining Findings

| Finding | Severity | Residual Risk | Remediation | Effort | Compensating Controls |
|---|---|---|---|---|---|
| Plaintext password logging | High | Credentials could be exposed through application logs if sensitive values continue to be logged | Remove password values from authentication logs and retain only non-sensitive authentication metadata | Low | Restrict access to application logs and monitor authentication events |
| Overly permissive CORS | Medium | Untrusted browser origins may interact with the API | Replace permissive origins with an explicit trusted-origin allowlist | Low | API authentication and server-side authorization |
| Detailed exception information | Medium | Internal implementation details may be disclosed through error responses | Return generic production errors and retain detailed diagnostics only in protected server-side logs | Low | Restrict application logs and avoid exposing internal errors to clients |
| Container base-image OS vulnerabilities | High | Vulnerable operating-system packages may increase container attack surface | Rebuild regularly and move to patched upstream Python/Debian base images when fixes become available | Medium | Non-root container user, read-only root filesystem, dropped capabilities, restricted network access, regular vulnerability scanning |
| Notification-service dependency vulnerabilities | High | Vulnerable third-party packages may expose the notification service to dependency-specific attacks | Review and upgrade Express/UUID and related dependencies, regenerate the lock file, and run the complete test suite | Medium | Limit notification-service exposure and continuously monitor dependency vulnerabilities |
| Secrets Manager without customer-managed KMS key | Low | Reduced customer control over encryption-key lifecycle and auditing | Use a customer-managed KMS key for production secrets | Medium | AWS Secrets Manager encryption and restricted IAM access |
| VPC Flow Logs not enabled | Medium | Reduced visibility into rejected network traffic can make investigation harder | Enable VPC Flow Logs for rejected traffic and send logs to protected CloudWatch Logs | Low | Security-group restrictions and load-balancer monitoring |

---

## Completed Remediations

The following high-impact findings were remediated during the assessment:

- JWT algorithm validation was restricted to the configured algorithm.
- SQL injection in scan search was remediated using parameterized database queries.
- Cross-user scan access was prevented through ownership checks.
- Hardcoded secrets were moved to environment variables.
- Shared-link password brute-force protection was implemented.
- Unrestricted security-group egress was restricted.
- Public application subnets were removed.
- Application workloads were configured without public IP addresses.
- The Application Load Balancer was configured to drop invalid headers.
- The container was configured to run as a non-root user.
- The ECS task definition uses a read-only root filesystem.
- Linux capabilities are dropped from the ECS application container.
- Python dependency vulnerabilities identified by the current SCA scan were remediated.

---

## Priority 1 — Container and Dependency Risk

The container scan continues to report High-severity operating-system package findings for the Debian base layer.

The notification service also has High-severity dependency findings reported by `npm audit`.

These should be addressed before production deployment where compatible fixed versions are available.

### Actions

1. Monitor upstream Debian/Python image security updates.
2. Rebuild the container regularly.
3. Re-run the container vulnerability scan for every release.
4. Review notification-service dependency upgrades.
5. Upgrade dependencies after compatibility testing.
6. Re-run the complete notification-service test suite after dependency changes.

---

## Priority 2 — Credential Protection

Remove any remaining plaintext password logging.

### Actions

1. Identify authentication logging statements.
2. Remove credential values from log messages.
3. Retain only non-sensitive authentication metadata.
4. Review centralized logging permissions.

---

## Priority 3 — API Boundary and Monitoring Hardening

The remaining API and infrastructure hardening items are CORS restrictions, safer production error responses, and network-flow visibility.

### Actions

1. Restrict CORS to trusted origins.
2. Return generic production error responses.
3. Retain detailed diagnostic information only in protected logs.
4. Enable VPC Flow Logs for rejected traffic.

---

## Priority 4 — Secrets Encryption

The infrastructure currently relies on AWS-managed encryption for the Secrets Manager secret.

### Actions

1. Create a customer-managed KMS key.
2. Apply a least-privilege KMS key policy.
3. Configure the production secret to use the customer-managed key.
4. Enable appropriate key rotation and monitoring.

---

## Residual Risk

The current residual risks are primarily associated with:

- Container operating-system vulnerabilities for which the current scanner reports no fixed package versions.
- Notification-service dependency vulnerabilities that require compatibility-tested upgrades.
- Application logging, CORS, and production error-handling hardening.
- Network-flow visibility.
- Customer-managed encryption-key requirements.

These risks are documented rather than hidden from the security assessment.

The container and dependency risks should be reassessed whenever new upstream security fixes become available.

---

## Compensating Controls

Until the remaining findings are remediated, the following controls reduce exposure:

- Authentication is required for protected API operations.
- JWT validation is restricted to the configured algorithm.
- Scan ownership is enforced server-side.
- Shared-link passwords are hashed.
- Shared-link password guessing is rate-limited through temporary lockout.
- Application workloads run without public IP addresses.
- Security-group access is restricted between application components.
- The container runs as a non-root user.
- The container root filesystem is configured as read-only in ECS.
- Linux capabilities are dropped from the application container.
- CI performs automated testing and security scanning.
- Security scan reports are retained under `reports/`.

---

## Reassessment

The remediation plan should be reviewed:

- Before production deployment.
- After major dependency upgrades.
- After base-image updates.
- After significant authentication or authorization changes.
- When new security advisories affect application or infrastructure dependencies.