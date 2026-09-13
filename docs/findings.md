# Security Findings

## 1. Assessment Overview

The application and supporting infrastructure were assessed across four areas:

- SAST â€” Python application source code
- SCA â€” Python and notification-service dependencies
- Container security â€” Docker image vulnerabilities
- IaC security â€” Terraform configuration

The assessment focused on exploitable application weaknesses, dependency risk, container posture, infrastructure configuration, and the security of the shared scan-link feature introduced for this assignment.

---

## 2. Findings Summary

| ID | Finding | Severity | Source | Status | Origin |
|---|---|---|---|---|---|
| F-01 | JWT algorithm validation weakness | High | SAST/manual review | Remediated | Starter code |
| F-02 | SQL injection in scan search | Critical | SAST/manual review | Remediated | Starter code |
| F-03 | Cross-user scan access / IDOR | High | Manual security review | Remediated | Starter code |
| F-04 | Hardcoded application secrets | High | SAST/manual review | Remediated | Starter code |
| F-05 | Plaintext password logging | High | Manual review | Remediation planned | Starter code |
| F-06 | Overly permissive CORS | Medium | Manual review | Remediation planned | Starter code |
| F-07 | Detailed exception information | Medium | Manual review | Remediation planned | Starter code |
| F-08 | Shared-link password brute-force risk | High | Manual security review | Remediated | New feature |
| F-09 | Unrestricted security-group egress | Critical | IaC scan/manual review | Remediated | Starter code |
| F-10 | Public subnet exposure | High | IaC scan/manual review | Remediated | Starter code |
| F-11 | Invalid load-balancer headers accepted | High | IaC scan/manual review | Remediated | Starter code |
| F-12 | Container base-image OS vulnerabilities | High | Container scan | Residual risk | New deployment configuration |
| F-13 | Notification-service dependency vulnerabilities | High | npm audit/SCA | Residual risk | Starter code |
| F-14 | Secrets Manager not using customer-managed KMS key | Low | IaC scan | Residual risk | Deployment configuration |
| F-15 | VPC Flow Logs not enabled | Medium | IaC scan | Residual risk | Deployment configuration |

---

# 3. Detailed Findings

## F-01 â€” JWT Algorithm Validation Weakness

**Severity:** High
**Source:** SAST / manual security review
**Type:** Authentication
**Origin:** Starter code
**Status:** Remediated

The original JWT validation allowed token decoding without sufficiently restricting the accepted signing algorithm.

An attacker able to influence the token algorithm could potentially bypass intended JWT signature-validation controls.

### Business impact

Successful authentication bypass could allow an attacker to access protected application functionality or data.

### Remediation

JWT decoding was changed to explicitly use the configured signing algorithm:

```python
jwt.decode(
    token,
    SECRET_KEY,
    algorithms=[ALGORITHM],
)
