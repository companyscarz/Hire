# Hire Cloud resource metering and Dokploy integration

Status: resource calculation helpers and a minimal server-side Dokploy API client exist. Automated collection, persistence, customer dashboards, user provisioning, and enforcement are not connected yet.

## Documentation used

- Dokploy API: https://docs.dokploy.com/docs/api
- Dokploy User API: https://docs.dokploy.com/docs/api/user
- Dokploy permissions: https://docs.dokploy.com/docs/core/permissions
- Dokploy multi-tenancy: https://docs.dokploy.com/docs/core/multi-tenancy
- Docker resource constraints: https://docs.docker.com/engine/containers/resource_constraints/
- Docker container stats: https://docs.docker.com/reference/cli/docker/container/stats/

Dokploy already provides organization members, roles, project/environment/service permissions, and server/container metric API operations. Hire Cloud should use Dokploy for deployment operations rather than reimplementing the deployment engine. The customer-facing account, plans, ownership, billing, and usage history remain Hire Cloud responsibilities.

## When to create a Dokploy user

A Hire Cloud account does not automatically need a separate Dokploy login. The safer default is for customers to use Hire Cloud only; Hire Cloud makes authorized, server-side calls to Dokploy and returns only resources belonging to their tenant.

Create/invite a Dokploy user when the product explicitly offers direct access to the Dokploy control panel. In that case:
- grant only the projects/environments/services that belong to that customer;
- do not grant host-wide Docker, API/CLI, SSH-key, Traefik-file, server, or Git-provider access unless the feature specifically requires it;
- never make customers organization Owners or Admins;
- keep credentials out of logs and do not reuse one shared customer password;
- provision and revoke access through a controlled, audited server-side workflow;
- confirm the installed Dokploy version's invitation and permission semantics before automating provisioning.

The current client intentionally does not create, update, or remove Dokploy users. User creation is privileged and should be implemented only alongside a tenant-to-Dokploy-project mapping and tests proving least-privilege access.

## Dokploy API client

`hire_cloud.dokploy.DokployClient` reads `DOKPLOY_BASE_URL` and `DOKPLOY_API_KEY` from the server environment. It currently supports only the documented server-metrics and user-list GET endpoints. It:
- requires HTTPS except for loopback development URLs;
- rejects embedded credentials/query strings/fragments in the base URL;
- uses a bounded timeout and response size;
- allowlists endpoint paths;
- sanitizes API/network errors so response bodies and secrets are not echoed.

The client is a foundation, not yet wired to a customer route or background worker. Do not expose the API key to JavaScript or customer responses.

## Measurement contract

The `hire_cloud.usage` module transforms trusted Docker Engine stats into the existing `UsageSnapshot` model's units:

- `cpu_millicores`: average CPU consumption across a sample interval; 1000 millicores represents one fully used logical CPU.
- `memory_bytes`: reported memory usage minus a recognised inactive/cache field when available, clamped at zero.
- `storage_bytes`: supplied explicitly by a trusted volume/database/storage collector. Container CPU stats do not measure persistent storage.
- `network_rx_bytes` and `network_tx_bytes`: cumulative interface counters. Sum interfaces for each sample; calculate interval traffic from counter differences in a separate aggregation layer.

The first CPU sample has no previous interval, so its CPU reading is zero rather than a fabricated estimate. Counter resets and zero-length intervals also produce zero. Invalid or negative counters are rejected.

## Security boundaries

1. Never expose the Docker socket, host shell, host filesystem, or unrestricted Dokploy credentials to a browser or customer API.
2. Run collection in a trusted server-side worker using a control-plane identity restricted to the required operations.
3. Resolve a service/container from a database-owned project-to-service mapping. Never use a customer-supplied container ID or provider resource ID directly.
4. Authorize tenant and project ownership before reading usage snapshots. Every query must include tenant scope.
5. Persist snapshots with UTC measurement timestamps and service identifiers, and record collector failures separately from zero usage.
6. Metrics are not a billing ledger yet. Do not charge users from these samples until retention, aggregation, counter resets, restarts, missing samples, plan boundaries, and reconciliation are tested.
7. Apply Docker/Dokploy CPU, memory, and storage limits separately from sampling. Do not assume a reported usage value enforces a limit.

## Next implementation steps

1. Verify the installed Dokploy version and response shapes for the supported metrics endpoints.
2. Add an explicit, server-owned mapping between each Hire Cloud project and its Dokploy project/services.
3. Implement a scheduled collector that uses trusted mappings and records collector health.
4. Persist `UsageSnapshot` rows with tenant/project scoping.
5. Add customer and operator dashboards with tenant-isolation tests.
6. If direct Dokploy access is a product requirement, add a separate least-privilege user provisioning/revocation workflow.
7. Configure and verify real resource limits against container observations.
8. Only then design plan allowances and billing-period usage aggregation.
