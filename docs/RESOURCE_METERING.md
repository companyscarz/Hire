# Hire Cloud resource metering

Status: first pure calculation layer added; provider collection and enforcement are not connected yet.

## Documentation used

- Docker resource constraints: https://docs.docker.com/engine/containers/resource_constraints/
- Docker container stats: https://docs.docker.com/reference/cli/docker/container/stats/
- Dokploy API: https://docs.dokploy.com/docs/api
- Dokploy multi-tenancy: https://docs.dokploy.com/docs/core/multi-tenancy

Docker distinguishes reporting usage from enforcing limits. Hire Cloud must do both independently: metrics show consumption, while Docker/Dokploy configuration imposes CPU and memory ceilings.

## Measurement contract

The hire_cloud.usage module transforms trusted Docker Engine stats into the existing UsageSnapshot model's units:

- cpu_millicores: average CPU consumption across a sample interval; 1000 millicores represents one fully used logical CPU.
- memory_bytes: reported memory usage minus a recognised inactive/cache field when available, clamped at zero.
- storage_bytes: supplied explicitly by a trusted volume/database/storage collector. Container CPU stats do not measure persistent storage.
- network_rx_bytes and network_tx_bytes: cumulative interface counters. Sum interfaces for each sample; calculate interval traffic from counter differences in a separate aggregation layer.

The first CPU sample has no previous interval, so its CPU reading is zero rather than a fabricated estimate. Counter resets and zero-length intervals also produce zero. Invalid or negative counters are rejected.

## Security boundaries

1. Never expose the Docker socket, host shell, host filesystem, or unrestricted Dokploy credentials to a browser or customer API.
2. The future collector runs as a trusted server-side worker using a narrowly scoped control-plane identity.
3. Resolve a service/container from a database-owned project-to-service mapping. Never use a customer-supplied container ID or provider resource ID directly.
4. Authorize tenant and project ownership before reading usage snapshots. Every query must include tenant scope.
5. Persist snapshots with UTC measurement timestamps and service identifiers, and record collector failures separately from zero usage.
6. Metrics are not a billing ledger yet. Do not charge users from these samples until retention, aggregation, counter resets, restarts, missing samples, plan boundaries, and reconciliation are tested.
7. Apply Docker/Dokploy CPU, memory, and storage limits separately from sampling. Do not assume a reported usage value enforces a limit.

## Next implementation steps

1. Verify the installed Dokploy version and available metrics API/permissions.
2. Implement a server-side collector using supported provider interfaces and controlled service mappings.
3. Persist UsageSnapshot rows with tenant/project scoping and collector-health metadata.
4. Add aggregation endpoints for customer and owner dashboards with authorization tests.
5. Configure and verify real resource limits against container observations.
6. Only then design plan allowances and billing-period usage aggregation.
