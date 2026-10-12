# Hire → ScarZ Cloud: implementation plan

Status: planning baseline; implementation has not yet been verified.
Working branch: `pre-main`. Do not merge into `main` without explicit approval.

## Product decision

Keep **Hire** as the PWA/product name for now. Its new purpose is a developer-focused hosting portal operated by Company ScarZ. The portal will let customers connect a Git repository, deploy supported applications, manage permitted settings, monitor resource usage, and manage hosting subscriptions. Object/bucket storage integration is a planned capability, not part of the first release.

## Non-negotiable security principles

1. Every customer-owned record and operation must be tenant-scoped and authorized on the server.
2. Customer-facing requests must never receive unrestricted Docker, host-shell, Dokploy-owner, or server filesystem access.
3. Use per-customer or per-application credentials; never share production secrets between tenants.
4. PostgreSQL is the source of truth for users, tenants, projects, plans, subscriptions, provisioning jobs, usage snapshots, and audit events.
5. Uploaded objects and customer artifacts belong in private object storage with scoped access, not in a public bucket or the app container filesystem.
6. Git integration must use least-privilege OAuth/app installations or narrowly scoped deploy credentials. Never request a customer's personal password or store long-lived broad tokens unnecessarily.
7. Provisioning and payment processing must be idempotent, auditable, retryable, and safe under duplicate webhooks.
8. No customer workload may mount the Docker socket, privileged host paths, or access the control-plane secrets.
9. Metrics are measurements, not enforcement. CPU/RAM limits and storage quotas must be configured independently and tested.
10. Backups must be encrypted, stored off-host, access-controlled, and periodically restored in tests.

## Initial problem / solution map

| Problem | Proposed solution | Verification |
|---|---|---|
| Legacy Hire is a job-opportunity Flask app | Audit and replace/migrate intentionally; keep only reusable assets/components | Inventory routes, models, templates, dependencies, and data |
| SQLite patterns are spread across model classes | Introduce PostgreSQL through SQLAlchemy 2.x and versioned migrations | Fresh database migration and automated integration tests |
| Hardcoded secrets in legacy configuration | Rotate exposed credentials; use deployment environment/secrets management; remove secrets from tracked code | Secret scan and production configuration check |
| Customer data could cross tenant boundaries | Tenant-aware schema, server-side ownership checks, least-privilege DB roles | Cross-tenant negative tests on every resource endpoint |
| Deployments need controlled access to Dokploy | Dedicated control-plane integration and restricted provisioning worker | Verify supported API and permissions against installed Dokploy version |
| Customers need resource usage | Collect per-container CPU/RAM/network and separately account for volumes/database/object storage | Compare metrics to host/container observations |
| Shared VPS has a shared failure domain | Small restricted beta first; move customer workloads to a separate VPS before broad untrusted-code hosting | Threat-model review and isolation tests |
| Subscriptions and payments can be duplicated or fail | Subscription state machine, verified webhooks, idempotency keys, reconciliation | Duplicate, delayed, failed, and out-of-order payment tests |

## Target architecture

- **Hire PWA:** responsive customer and owner interfaces; installable manifest, icons, and service worker.
- **Flask application/API:** authentication, authorization, tenant boundaries, plans, subscriptions, audit records, and customer-facing operations.
- **PostgreSQL:** relational source of truth, managed through Alembic migrations. Production should use a separate database and restricted database role.
- **Provisioning worker:** asynchronous jobs for approved resource creation, deployment requests, quota application, and safe retries. It should not expose arbitrary shell commands to users.
- **Dokploy adapter:** narrow integration that uses documented API operations and a dedicated credential stored server-side. Confirm API capabilities against the installed version before automating user invitations or fine-grained permissions.
- **Docker/host isolation:** explicit CPU and memory limits, private service networks, no privileged customer containers, no Docker socket mounts, and customer workloads separated from the control plane.
- **Metrics:** collect CPU, memory, and network per service/container; separately measure persistent volumes, databases, logs, and object storage to avoid misleading storage totals.
- **Object storage:** private S3-compatible bucket(s), scoped upload/download access, file-size/type limits, lifecycle rules, and no public access by default.
- **Payments:** provider adapter with signature verification, idempotent webhooks, reconciliation, invoices/receipts, renewals, grace periods, and controlled suspension.
- **Owner operations:** audit logs, capacity alerts, backups, restore drills, customer support tools, and incident procedures.

## First release scope

### Include
- Account registration, email verification, login, password reset, and owner-only administration.
- PostgreSQL models and migrations for tenants, users/memberships, projects, plans, subscriptions, deployments, provisioning jobs, usage snapshots, payment events, and audit events.
- Customer dashboard with applications, subscription status, usage, and deployment state.
- Git-connected deployment for a small set of supported project types after security review.
- Owner-mediated provisioning at first; automate only after the workflow and Dokploy API permissions are verified.
- Basic CPU, memory, and network monitoring; storage accounting for supported volumes and databases.
- PWA manifest, valid icons, installability checks, responsive UI, health endpoint, structured logs, and tests.

### Defer until the safe core works
- Arbitrary Dockerfiles and untrusted arbitrary code on the same VPS as ScarZ's own projects.
- Customer-managed Docker, host shell, SSH keys, or unrestricted Dokploy API/CLI.
- Usage-based overage billing, automatic destructive cleanup, multi-region hosting, and Kubernetes.
- Public buckets and direct access to shared storage credentials.
- Fully automated customer invitations/permissions until the installed Dokploy API is verified.

## Delivery sequence

1. Rotate exposed legacy credentials and stop tracking secrets.
2. Inventory the existing app, identify sensitive routes and data, and confirm the deployment/database facts.
3. Build the new PostgreSQL-backed app structure and migration/test baseline on `pre-main`.
4. Implement authentication and tenant authorization, including negative cross-tenant tests.
5. Implement plans/subscriptions as database state before connecting real payment processing.
6. Build the owner dashboard and customer usage dashboard with test fixtures.
7. Add metrics collection and enforce CPU/RAM/storage policies.
8. Add Git integration and a restricted provisioning worker; verify Dokploy API permissions from official docs and the installed instance.
9. Add private object storage integration and scoped access.
10. Run security, functional, restore, and load checks; launch a small invite-only beta.
11. Separate customer workloads from the existing ScarZ projects before opening public self-service to untrusted developers.

## Acceptance gates

- No known live secrets committed; exposed credentials have been rotated.
- A customer cannot enumerate, read, mutate, deploy into, or view metrics for another tenant.
- No customer account can access host administration, Docker socket, internal monitoring endpoints, or other tenants' secrets.
- Resource limits are applied and tested; usage collection is labelled with its measurement method and known limitations.
- PostgreSQL migrations run from an empty database and upgrade a prior schema reproducibly.
- Payment/webhook events are verified and idempotent; unpaid accounts cannot obtain paid resources.
- Backup restoration is demonstrated before storing important customer data.
- Tests and security checks pass before deployment; no merge to `main` without owner approval.

## Documentation references

- Dokploy API: https://docs.dokploy.com/docs/api
- Dokploy multi-tenancy: https://docs.dokploy.com/docs/core/multi-tenancy
- Dokploy permissions: https://docs.dokploy.com/docs/core/permissions
- Dokploy project API: https://docs.dokploy.com/docs/api/project
- Docker resource constraints: https://docs.docker.com/engine/containers/resource_constraints/
- Docker security: https://docs.docker.com/engine/security/
- Flask-SQLAlchemy: https://flask-sqlalchemy.palletsprojects.com/
- Alembic: https://alembic.sqlalchemy.org/
- PWA installability: https://developer.mozilla.org/en-US/docs/Web/Progressive_web_apps/Guides/Making_PWAs_installable

These references guide the design; the installed Dokploy version, Hostinger plan/terms, and actual production environment still need verification.
