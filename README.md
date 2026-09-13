# Security Automation Engineer – Take-Home Assignment

This repository contains the completed Security Automation Engineer take-home assignment.

## Architecture

The project contains:

- `app/` – Python FastAPI REST API
- `notify/` – Node.js notification service
- `tests/` – Python API tests
- `reports/` – SAST, SCA, container, and IaC security reports
- `terraform/` – AWS deployment infrastructure
- `docs/` – Security findings, remediation plan, and executive summary
- `Dockerfile` – Production-oriented application container

## Requirements

- Python 3.11
- Node.js 20+
- Docker
- Terraform
- Git

## Configuration

The application requires a `SECRET_KEY` environment variable.

Example:

```text
SECRET_KEY=replace-with-a-long-random-secret