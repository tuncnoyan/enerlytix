# Deployment Approval Process

Production deployments must be approved before release.

## Required checks

- Code review completed
- Security sign-off completed
- Database migration impact reviewed
- Secrets and environment variables verified
- Rollback plan confirmed

## Admin access changes

New admin accounts may only be created after approval from the appropriate owner or reviewer.

## Release expectation

- No direct production deployment without approval
- Use a controlled deployment workflow for every production change
