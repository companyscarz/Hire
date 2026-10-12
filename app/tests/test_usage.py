"""Regression tests for resource metering calculations."""
import pytest

from hire_cloud.usage import (
    calculate_cpu_millicores,
    calculate_memory_bytes,
    calculate_network_bytes,
    measurement_from_docker_stats,
)


def test_cpu_millicores_for_half_a_cpu():
    assert calculate_cpu_millicores(0, 500_000_000, 0, 1_000_000_000, 1) == 500


def test_cpu_millicores_scales_with_online_cpus():
    assert calculate_cpu_millicores(0, 1_000, 0, 1_000, 4) == 4000


@pytest.mark.parametrize("values", [
    (100, 50, 100, 200, 1),
    (0, 10, 0, 0, 1),
    (0, 0, 0, 10, 1),
])
def test_cpu_counter_resets_or_empty_interval_are_zero(values):
    assert calculate_cpu_millicores(*values) == 0


@pytest.mark.parametrize("value", [-1, True, 1.5, "not-a-number"])
def test_cpu_rejects_invalid_counters(value):
    with pytest.raises(ValueError):
        calculate_cpu_millicores(value, 10, 0, 20, 1)


def test_cpu_requires_at_least_one_online_cpu():
    with pytest.raises(ValueError):
        calculate_cpu_millicores(0, 10, 0, 20, 0)


def test_memory_subtracts_inactive_file_cache():
    assert calculate_memory_bytes({
        "memory_stats": {"usage": 1000, "stats": {"inactive_file": 250}}
    }) == 750


def test_memory_falls_back_to_reported_usage_without_cache_field():
    assert calculate_memory_bytes({"memory_stats": {"usage": 123}}) == 123


def test_memory_never_goes_below_zero():
    assert calculate_memory_bytes({
        "memory_stats": {"usage": 100, "stats": {"inactive_file": 200}}
    }) == 0


def test_network_sums_interfaces_and_handles_missing_networks():
    assert calculate_network_bytes({
        "eth0": {"rx_bytes": 100, "tx_bytes": 50},
        "eth1": {"rx_bytes": 20, "tx_bytes": 10},
    }) == (120, 60)
    assert calculate_network_bytes(None) == (0, 0)


def test_network_rejects_negative_counters():
    with pytest.raises(ValueError):
        calculate_network_bytes({"eth0": {"rx_bytes": -1}})


def test_measurement_maps_sample_to_explicit_fields():
    prior = {"cpu_stats": {"cpu_usage": {"total_usage": 100}, "system_cpu_usage": 1000}}
    current = {
        "cpu_stats": {"cpu_usage": {"total_usage": 600}, "system_cpu_usage": 2000},
        "memory_stats": {"usage": 2048, "stats": {"inactive_file": 512}},
        "networks": {"eth0": {"rx_bytes": 700, "tx_bytes": 300}},
    }
    result = measurement_from_docker_stats(
        current, previous_stats=prior, online_cpus=1, storage_bytes=4096
    )
    assert result.cpu_millicores == 500
    assert result.memory_bytes == 1536
    assert result.storage_bytes == 4096
    assert result.network_rx_bytes == 700
    assert result.network_tx_bytes == 300


def test_first_sample_has_no_cpu_interval_but_keeps_other_metrics():
    current = {
        "cpu_stats": {"cpu_usage": {"total_usage": 500}, "system_cpu_usage": 1000},
        "memory_stats": {"usage": 512},
        "networks": {},
    }
    result = measurement_from_docker_stats(current, previous_stats=None, online_cpus=2)
    assert result.cpu_millicores == 0
    assert result.memory_bytes == 512
    assert result.network_rx_bytes == 0
    assert result.network_tx_bytes == 0


def test_storage_is_explicit_and_rejects_negative_values():
    with pytest.raises(ValueError):
        measurement_from_docker_stats(
            {"cpu_stats": {}, "memory_stats": {}},
            previous_stats=None,
            online_cpus=1,
            storage_bytes=-1,
        )
