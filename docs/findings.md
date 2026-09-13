\# Security Findings



\## Overview



Security testing was performed across the Python application source code, third-party dependencies, container image, and Terraform infrastructure configuration.



The analysis focused on identifying vulnerabilities that could affect confidentiality, integrity, availability, authentication, authorization, and deployment security.



\## Findings Summary



| ID | Tool / Scan | Finding | Severity | Source | Business Impact | Status |

|---|---|---|---|---|---|---|

| F-01 | Bandit / SAST | JWT algorithm was not restricted during token validation | High | Starter code | An attacker could potentially bypass authentication if an unsigned or unexpected JWT algorithm were accepted | Remediated |

| F-02 | Manual review | SQL injection in scan search functionality | Critical | Starter code | Could allow unauthorized database queries and exposure or modification of application data | Remediated |

| F-03 | Manual review | Missing ownership check when accessing scan results | High | Starter code | An authenticated user could potentially access another user's scan result | Remediated |

| F-04 | Manual review | Hardcoded application/database secrets | High | Starter code | Secrets stored in source code could be exposed through source control or application distribution | Remediated |

| F-05 | Manual review | Plaintext password included in login logging | High | Starter code | Credentials could be exposed through application logs and subsequently accessed by unauthorized users | Remediation planned |

| F-06 | Manual review | Overly permissive CORS configuration | Medium | Starter code | Untrusted web origins could interact with the API and increase the risk of unauthorized browser-based requests | Remediation planned |

| F-07 | Manual review | Detailed exception/traceback information exposed by the global error handler | Medium | Starter code | Internal implementation details could be disclosed to attackers and assist further attacks | Remediation planned |

| F-08 | pip-audit / SCA | ecdsa dependency has a known timing-attack vulnerability with no available upstream fix | Medium | Third-party dependency | Under specific cryptographic signing/key-generation use cases, timing information could potentially expose private-key information | Residual risk |

| F-09 | Trivy / IaC | Security group rules allowed unrestricted public egress | Critical | Starter infrastructure configuration | Compromised workloads could communicate with arbitrary external destinations | Remediated |

| F-10 | Trivy / IaC | Public subnet allowed public IP assignment | High | Starter infrastructure configuration | Resources could become directly reachable from the internet | Remediated |

| F-11 | Trivy / IaC | Application Load Balancer accepted invalid headers | High | Infrastructure configuration | Invalid headers could be forwarded to backend services and increase request-processing attack surface | Remediated |

| F-12 | Trivy / Container | No Critical or High severity findings identified in the application container image | Informational | Container image | No Critical/High container vulnerability was identified during the scan | Reviewed |



\## Detailed Findings



\### F-01 — JWT Algorithm Validation



\*\*Severity:\*\* High

\*\*Source:\*\* Starter code

\*\*Type:\*\* Authentication



The JWT validation logic did not explicitly restrict the accepted signing algorithm.



An attacker able to provide a token using an unexpected or unsigned algorithm could potentially bypass authentication.



\*\*Remediation:\*\* JWT decoding was changed to explicitly allow the configured signing algorithm.



```python

payload = jwt.decode(

&#x20;   token,

&#x20;   SECRET\_KEY,

&#x20;   algorithms=\[ALGORITHM],

)
