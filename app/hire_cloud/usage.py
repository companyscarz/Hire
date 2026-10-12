"""Pure, testable resource metering helpers for Hire Cloud.

This module deliberately does not connect to Docker or Dokploy. A future trusted
collector can pass service stats from the control plane into these functions.
Never accept Docker identifiers, host paths, or provider credentials from a
customer-facing request.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


@dataclass(frozen=True)
class UsageMeasurement:
    """A point-in-time measurement; network counters are cumulative bytes."""

    cpu_millicores: int
    memory_bytes: int
    storage_bytes: int
    network_rx_bytes: int
    network_tx_bytes: int


def _nonnegative_int(value: Any, field: str) -> int:
    """Parse a nonnegative integer without accepting booleans or negative values."""
    if isinstance(value, bool):
        raise ValueError(f"{field} must be a nonnegative integer")
    try:
        parsed = int(value)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError(f"{field} must be a nonnegative integer") from exc
    if parsed < 0 or (isinstance(value, float) and not value.is_integer()):
        raise ValueError(f"{field} must be a nonnegative integer")
    return parsed


def calculate_cpu_millicores(
    previous_cpu_total: int,
    current_cpu_total: int,
    previous_system_total: int,
    current_system_total: int,
    online_cpus: int,
) -> int:
    """Calculate average CPU millicores between two Docker stats samples.

    The ratio of CPU-time delta to system CPU-time delta is multiplied by the
    online CPU count. 1000 millicores represents one fully occupied logical CPU.
    """
    previous_cpu = _nonnegative_int(previous_cpu_total, "previous_cpu_total")
    current_cpu = _nonnegative_int(current_cpu_total, "current_cpu_total")
    previous_system = _nonnegative_int(previous_system_total, "previous_system_total")
    current_system = _nonnegative_int(current_system_total, "current_system_total")
    cpus = _nonnegative_int(online_cpus, "online_cpus")
    if cpus < 1:
        raise ValueError("online_cpus must be at least 1")
    cpu_delta = current_cpu - previous_cpu
    system_delta = current_system - previous_system
    if cpu_delta <= 0 or system_delta <= 0:
        return 0
    return max(0, round((cpu_delta / system_delta) * cpus * 1000))


def calculate_memory_bytes(stats: Mapping[str, Any]) -> int:
    """Return working memory, subtracting a recognised cache field when present."""
    memory = stats.get("memory_stats") or {}
    usage = _nonnegative_int(memory.get("usage", 0), "memory usage")
    stats_map = memory.get("stats") or {}
    cache = stats_map.get("inactive_file")
    if cache is None:
        cache = stats_map.get("total_inactive_file")
    if cache is None:
        cache = stats_map.get("cache", 0)
    cache_bytes = _nonnegative_int(cache, "memory cache")
    return max(0, usage - cache_bytes)


def calculate_network_bytes(networks: Mapping[str, Any] | None) -> tuple[int, int]:
    """Sum RX/TX counters across interfaces, tolerating no interfaces."""
    rx_total = 0
    tx_total = 0
    for name, counters in (networks or {}).items():
        if not isinstance(counters, Mapping):
            raise ValueError(f"network counters for {name!r} must be an object")
        rx_total += _nonnegative_int(counters.get("rx_bytes", 0), "rx_bytes")
        tx_total += _nonnegative_int(counters.get("tx_bytes", 0), "tx_bytes")
    return rx_total, tx_total


def measurement_from_docker_stats(
    stats: Mapping[str, Any],
    *,
    previous_stats: Mapping[str, Any] | None,
    online_cpus: int,
    storage_bytes: int = 0,
) -> UsageMeasurement:
    """Convert a Docker stats sample into normalised, non-billing usage fields.

    storage_bytes must come from a trusted volume/database measurement. Docker
    live stats do not measure persistent volume consumption.
    """
    storage = _nonnegative_int(storage_bytes, "storage_bytes")
    cpu = stats.get("cpu_stats") or {}
    cpu_usage = cpu.get("cpu_usage") or {}
    current_cpu = _nonnegative_int(cpu_usage.get("total_usage", 0), "cpu total usage")
    current_system = _nonnegative_int(cpu.get("system_cpu_usage", 0), "system cpu usage")
    prior_cpu = 0
    prior_system = 0
    if previous_stats is not None:
        prior = previous_stats.get("cpu_stats") or {}
        prior_usage = prior.get("cpu_usage") or {}
        prior_cpu = _nonnegative_int(prior_usage.get("total_usage", 0), "previous cpu total usage")
        prior_system = _nonnegative_int(prior.get("system_cpu_usage", 0), "previous system cpu usage")
    rx, tx = calculate_network_bytes(stats.get("networks"))
    return UsageMeasurement(
        cpu_millicores=calculate_cpu_millicores(
            prior_cpu, current_cpu, prior_system, current_system, online_cpus
        ),
        memory_bytes=calculate_memory_bytes(stats),
        storage_bytes=storage,
        network_rx_bytes=rx,
        network_tx_bytes=tx,
    )
