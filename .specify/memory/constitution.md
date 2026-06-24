<!--
Sync Impact Report
Version change: 1.0.0 -> 1.0.1
Modified principles: none
Added sections: none
Removed sections: none
Templates requiring updates: ✅ Reviewed, no changes required: .specify/templates/plan-template.md
✅ Reviewed, no changes required: .specify/templates/spec-template.md
✅ Reviewed, no changes required: .specify/templates/tasks-template.md
Follow-up TODOs: none
-->

# Enerlytix Constitution

## Core Principles

### I. Windows-Native Platform Alignment
The application MUST be designed as a Windows-native web property where client and deployment assumptions reflect Windows compatibility first.
- Native Windows support is mandatory for the application runtime and the local maintenance tooling.
- The design MUST avoid platform abstractions that would force non-Windows host assumptions or require elevated system access.
- User experience, installation, and support guidance MUST target Windows deployment and operations.

### II. Least-Privilege Development & Operations
Development, maintenance, and daily operations MUST be performed without administrator privileges.
- Build, test, and deployment tooling MUST run under standard user accounts.
- Administrative access MUST be restricted to explicit approval processes.
- Runtime and maintenance operations MUST not require elevated privileges except for controlled, documented exceptions.

### III. Data Security and Database Isolation
Data protection is critical and MUST be enforced at every application layer.
- The database layer MUST prevent unauthorized access from external and local actors.
- Sensitive data MUST be encrypted at rest and in transit when moving between application components.
- Access controls MUST be role-based, auditable, and enforced consistently across the app and database.
- Log data and audit records MUST preserve security and privacy, with only approved viewers able to access them.

### IV. Approval-Governed Production Operations
Production deployments and administrative account changes MUST require explicit approval.
- All production deployments MUST be reviewed and approved before execution.
- New administrative accounts or privilege escalations MUST be granted only after approval by authorized owners.
- Emergency changes MUST be documented, justified, and retroactively reviewed.

### V. Containerized Maintainability & Observability
The application MUST be containerized natively and built for maintainable, observable operation.
- Containerization MUST be the standard packaging and deployment model for application components.
- Containers MUST be configured so the app can be deployed, maintained, and operated without admin privileges.
- Operational observability MUST include structured logging, health checks, and security event monitoring.

## Additional Constraints
- The product MUST behave as a business-focused web application for electricity, gas, and water usage analysis.
- The application MUST support Windows-native hosting and maintenance without depending on admin-level system changes.
- Deployment tooling and runtime packaging MUST be container-native and compatible with Windows container ecosystems.
- Data security requirements MUST include database hardening, secure configuration management, and protection from unauthorized external access.
- API keys, secrets, and similar runtime parameters MUST be sourced from `.env` during development and test environments.
- Production MAY also use `.env` if the deployment platform provides no stronger secret management mechanism, but a platform-native secure secret store MUST be preferred when available.
- Any external integration or API usage MUST be vetted for secure access and data privacy.

## Development Workflow & Approval
- All code changes MUST be reviewed against these constitution principles before merging.
- Security, deployment, and administrative privilege changes MUST be documented with defined approval owners.
- Production release candidates MUST pass an approval gate before deployment.
- Admin account creation and privileged role changes MUST be processed through a documented approval workflow.
- Compliance with security and least-privilege rules MUST be verified during planning, implementation, and deployment reviews.

## Governance
This constitution supersedes ad hoc preferences and is the authoritative source for platform, security, and workflow decisions.
- All work MUST map to one or more constitution principles.
- Amendments MUST be documented, reviewed, and approved by the project’s governance owners before they are accepted.
- Changes to this constitution MUST include a clear rationale, impact analysis, and version update.
- Regular compliance review SHOULD occur whenever the project’s platform, security, or deployment context changes.

**Version**: 1.0.1 | **Ratified**: 2026-06-23 | **Last Amended**: 2026-06-24
