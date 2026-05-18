#!/usr/bin/env python3
# Time-stamp: "2025-01-05"
# File: test_monitor.py

"""Tests for scitex_benchmark.monitor module."""

import json
import os
import tempfile
import threading
import time
import warnings

import pytest

from scitex_benchmark.monitor import (
    PerformanceMetric,
    PerformanceMonitor,
    add_performance_alert_handler,
    get_performance_stats,
    set_performance_alerts,
    track_performance,
)

# ============================================================================
# Test Fixtures
# ============================================================================


@pytest.fixture
def monitor():
    """Create a fresh PerformanceMonitor instance."""
    return PerformanceMonitor(max_history=100)


@pytest.fixture
def started_monitor():
    """Create a started PerformanceMonitor instance."""
    mon = PerformanceMonitor(max_history=100)
    mon.start()
    yield mon
    mon.stop()


@pytest.fixture
def sample_metric():
    """Create a sample PerformanceMetric."""
    return PerformanceMetric(
        timestamp=time.time(),
        function="test_function",
        duration=0.5,
        memory_delta=10.0,
        args_size=100,
        result_size=50,
        exception=None,
    )


@pytest.fixture
def temp_dir():
    """Create a temporary directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


# ============================================================================
# Test PerformanceMetric — all fields construction
# ============================================================================


class TestPerformanceMetricAllFields:
    """Tests for PerformanceMetric dataclass — all fields construction."""

    def test_stores_function_name_field(self, sample_metric):
        # Arrange
        metric = sample_metric
        # Act
        value = metric.function
        # Assert
        assert value == "test_function"

    def test_stores_duration_field(self, sample_metric):
        # Arrange
        metric = sample_metric
        # Act
        value = metric.duration
        # Assert
        assert value == 0.5

    def test_stores_memory_delta_field(self, sample_metric):
        # Arrange
        metric = sample_metric
        # Act
        value = metric.memory_delta
        # Assert
        assert value == 10.0

    def test_stores_args_size_field(self, sample_metric):
        # Arrange
        metric = sample_metric
        # Act
        value = metric.args_size
        # Assert
        assert value == 100

    def test_stores_result_size_field(self, sample_metric):
        # Arrange
        metric = sample_metric
        # Act
        value = metric.result_size
        # Assert
        assert value == 50

    def test_exception_defaults_to_none(self, sample_metric):
        # Arrange
        metric = sample_metric
        # Act
        value = metric.exception
        # Assert
        assert value is None


# ============================================================================
# Test PerformanceMetric — required fields only
# ============================================================================


@pytest.fixture
def minimal_metric():
    return PerformanceMetric(
        timestamp=1234567890.0,
        function="my_func",
        duration=0.1,
    )


class TestPerformanceMetricRequiredFields:
    """Tests for PerformanceMetric dataclass — required-only construction."""

    def test_stores_timestamp_field_value(self, minimal_metric):
        # Arrange
        metric = minimal_metric
        # Act
        value = metric.timestamp
        # Assert
        assert value == 1234567890.0

    def test_stores_function_name_value(self, minimal_metric):
        # Arrange
        metric = minimal_metric
        # Act
        value = metric.function
        # Assert
        assert value == "my_func"

    def test_stores_duration_field_value(self, minimal_metric):
        # Arrange
        metric = minimal_metric
        # Act
        value = metric.duration
        # Assert
        assert value == 0.1

    def test_memory_delta_defaults_to_none(self, minimal_metric):
        # Arrange
        metric = minimal_metric
        # Act
        value = metric.memory_delta
        # Assert
        assert value is None

    def test_args_size_defaults_to_none(self, minimal_metric):
        # Arrange
        metric = minimal_metric
        # Act
        value = metric.args_size
        # Assert
        assert value is None

    def test_result_size_defaults_to_none(self, minimal_metric):
        # Arrange
        metric = minimal_metric
        # Act
        value = metric.result_size
        # Assert
        assert value is None

    def test_exception_defaults_to_none(self, minimal_metric):
        # Arrange
        metric = minimal_metric
        # Act
        value = metric.exception
        # Assert
        assert value is None


# ============================================================================
# Test PerformanceMetric — with exception
# ============================================================================


class TestPerformanceMetricWithException:
    """Tests for PerformanceMetric carrying an exception string."""

    def test_exception_string_is_stored(self):
        # Arrange
        message = "ValueError: test error"
        # Act
        metric = PerformanceMetric(
            timestamp=time.time(),
            function="error_func",
            duration=0.01,
            exception=message,
        )
        # Assert
        assert metric.exception == message


# ============================================================================
# Test PerformanceMonitor — initialisation
# ============================================================================


class TestPerformanceMonitorCreation:
    """Tests for PerformanceMonitor initialization."""

    def test_max_history_is_set_to_constructor_argument(self, monitor):
        # Arrange
        m = monitor
        # Act
        value = m.max_history
        # Assert
        assert value == 100

    def test_metrics_starts_empty(self, monitor):
        # Arrange
        m = monitor
        # Act
        n = len(m.metrics)
        # Assert
        assert n == 0

    def test_is_monitoring_starts_false(self, monitor):
        # Arrange
        m = monitor
        # Act
        flag = m.is_monitoring
        # Assert
        assert flag is False

    def test_alert_callbacks_is_a_list(self, monitor):
        # Arrange
        m = monitor
        # Act
        callbacks = m.alert_callbacks
        # Assert
        assert isinstance(callbacks, list)


# ============================================================================
# Test PerformanceMonitor — start/stop
# ============================================================================


class TestPerformanceMonitorStartStop:
    """Tests for PerformanceMonitor start/stop lifecycle."""

    def test_fresh_monitor_is_not_monitoring(self, monitor):
        # Arrange
        m = monitor
        # Act
        flag = m.is_monitoring
        # Assert
        assert flag is False

    def test_start_flips_is_monitoring_to_true(self, monitor):
        # Arrange
        m = monitor
        # Act
        m.start()
        # Assert
        assert m.is_monitoring is True

    def test_stop_after_start_flips_is_monitoring_to_false(self, monitor):
        # Arrange
        m = monitor
        m.start()
        # Act
        m.stop()
        # Assert
        assert m.is_monitoring is False


# ============================================================================
# Test PerformanceMonitor — record_metric
# ============================================================================


class TestPerformanceMonitorRecordWhenActive:
    """Tests for record_metric when monitoring is active."""

    def test_recorded_metric_is_stored(self, started_monitor, sample_metric):
        # Arrange
        mon = started_monitor
        # Act
        mon.record_metric(sample_metric)
        # Assert
        assert len(mon.metrics) == 1

    def test_recording_increments_function_stats_count(
        self, started_monitor, sample_metric
    ):
        # Arrange
        mon = started_monitor
        # Act
        mon.record_metric(sample_metric)
        # Assert
        assert mon.function_stats["test_function"]["count"] == 1


class TestPerformanceMonitorRecordWhenInactive:
    """Tests for record_metric when monitoring is off."""

    def test_metric_is_not_stored_when_not_started(self, monitor, sample_metric):
        # Arrange
        m = monitor
        # Act
        m.record_metric(sample_metric)
        # Assert
        assert len(m.metrics) == 0


# ============================================================================
# Test PerformanceMonitor — function_stats accumulation
# ============================================================================


@pytest.fixture
def five_metric_stats(started_monitor):
    for i in range(5):
        started_monitor.record_metric(
            PerformanceMetric(
                timestamp=time.time(),
                function="my_func",
                duration=0.1 * (i + 1),
            )
        )
    return started_monitor.function_stats["my_func"]


class TestPerformanceMonitorFunctionStats:
    """Tests for cumulative function-stat updates."""

    def test_count_accumulates_across_metrics(self, five_metric_stats):
        # Arrange
        stats = five_metric_stats
        # Act
        value = stats["count"]
        # Assert
        assert value == 5

    def test_min_time_tracks_smallest_duration(self, five_metric_stats):
        # Arrange
        stats = five_metric_stats
        # Act
        value = stats["min_time"]
        # Assert
        assert value == 0.1

    def test_max_time_tracks_largest_duration(self, five_metric_stats):
        # Arrange
        stats = five_metric_stats
        # Act
        value = stats["max_time"]
        # Assert
        assert value == 0.5

    def test_total_time_sums_individual_durations(self, five_metric_stats):
        # Arrange
        stats = five_metric_stats
        # Act
        value = stats["total_time"]
        # Assert
        assert abs(value - 1.5) < 0.001


# ============================================================================
# Test PerformanceMonitor — error tracking
# ============================================================================


@pytest.fixture
def error_tracking_stats(started_monitor):
    started_monitor.record_metric(
        PerformanceMetric(timestamp=time.time(), function="my_func", duration=0.1)
    )
    started_monitor.record_metric(
        PerformanceMetric(
            timestamp=time.time(),
            function="my_func",
            duration=0.1,
            exception="Error!",
        )
    )
    return started_monitor.function_stats["my_func"]


class TestPerformanceMonitorErrorTracking:
    """Tests for error counting in function stats."""

    def test_total_count_includes_both_normal_and_error_metrics(
        self, error_tracking_stats
    ):
        # Arrange
        stats = error_tracking_stats
        # Act
        value = stats["count"]
        # Assert
        assert value == 2

    def test_error_count_increments_only_for_exception_metrics(
        self, error_tracking_stats
    ):
        # Arrange
        stats = error_tracking_stats
        # Act
        value = stats["errors"]
        # Assert
        assert value == 1


# ============================================================================
# Test PerformanceMonitor — max_history limit
# ============================================================================


class TestPerformanceMonitorMaxHistory:
    """Tests for max_history bounded deque."""

    def test_metrics_capped_at_max_history_length(self):
        # Arrange
        m = PerformanceMonitor(max_history=5)
        m.start()
        for _ in range(10):
            m.record_metric(
                PerformanceMetric(timestamp=time.time(), function="func", duration=0.01)
            )
        # Act
        size = len(m.metrics)
        # Assert
        m.stop()
        assert size == 5


# ============================================================================
# Test PerformanceMonitor — get_stats
# ============================================================================


@pytest.fixture
def stats_two_functions(started_monitor):
    started_monitor.record_metric(
        PerformanceMetric(timestamp=time.time(), function="func1", duration=0.1)
    )
    started_monitor.record_metric(
        PerformanceMetric(timestamp=time.time(), function="func2", duration=0.2)
    )
    return started_monitor.get_stats()


class TestPerformanceMonitorGetStatsAll:
    """Tests for get_stats() with no function filter."""

    def test_returns_entry_for_first_function(self, stats_two_functions):
        # Arrange
        stats = stats_two_functions
        # Act
        present = "func1" in stats
        # Assert
        assert present

    def test_returns_entry_for_second_function(self, stats_two_functions):
        # Arrange
        stats = stats_two_functions
        # Act
        present = "func2" in stats
        # Assert
        assert present

    def test_first_function_avg_time_matches_recorded(self, stats_two_functions):
        # Arrange
        stats = stats_two_functions
        # Act
        value = stats["func1"]["avg_time"]
        # Assert
        assert value == 0.1

    def test_second_function_avg_time_matches_recorded(self, stats_two_functions):
        # Arrange
        stats = stats_two_functions
        # Act
        value = stats["func2"]["avg_time"]
        # Assert
        assert value == 0.2


@pytest.fixture
def stats_single_function(started_monitor):
    started_monitor.record_metric(
        PerformanceMetric(timestamp=time.time(), function="my_func", duration=0.1)
    )
    started_monitor.record_metric(
        PerformanceMetric(timestamp=time.time(), function="my_func", duration=0.3)
    )
    return started_monitor.get_stats("my_func")


class TestPerformanceMonitorGetStatsSingle:
    """Tests for get_stats(function) for a specific function."""

    def test_function_field_returns_requested_name(self, stats_single_function):
        # Arrange
        stats = stats_single_function
        # Act
        value = stats["function"]
        # Assert
        assert value == "my_func"

    def test_count_is_sum_of_recorded_metrics(self, stats_single_function):
        # Arrange
        stats = stats_single_function
        # Act
        value = stats["count"]
        # Assert
        assert value == 2

    def test_avg_time_is_arithmetic_mean(self, stats_single_function):
        # Arrange
        stats = stats_single_function
        # Act
        value = stats["avg_time"]
        # Assert
        assert value == 0.2

    def test_min_time_is_smallest_recorded(self, stats_single_function):
        # Arrange
        stats = stats_single_function
        # Act
        value = stats["min_time"]
        # Assert
        assert value == 0.1

    def test_max_time_is_largest_recorded(self, stats_single_function):
        # Arrange
        stats = stats_single_function
        # Act
        value = stats["max_time"]
        # Assert
        assert value == 0.3


class TestPerformanceMonitorGetStatsUnknown:
    """Tests for get_stats() on unknown function name."""

    def test_unknown_function_returns_empty_dict(self, started_monitor):
        # Arrange
        mon = started_monitor
        # Act
        stats = mon.get_stats("unknown_func")
        # Assert
        assert stats == {}


# ============================================================================
# Test PerformanceMonitor — get_recent_metrics
# ============================================================================


@pytest.fixture
def recent_metrics(started_monitor):
    for i in range(10):
        started_monitor.record_metric(
            PerformanceMetric(
                timestamp=time.time() + i, function=f"func_{i}", duration=0.01
            )
        )
    return started_monitor.get_recent_metrics(5)


class TestPerformanceMonitorRecentMetrics:
    """Tests for get_recent_metrics()."""

    def test_returns_requested_number_of_metrics(self, recent_metrics):
        # Arrange
        result = recent_metrics
        # Act
        size = len(result)
        # Assert
        assert size == 5

    def test_first_recent_metric_is_the_correct_offset(self, recent_metrics):
        # Arrange
        result = recent_metrics
        # Act
        name = result[0].function
        # Assert
        assert name == "func_5"

    def test_last_recent_metric_is_the_most_recent(self, recent_metrics):
        # Arrange
        result = recent_metrics
        # Act
        name = result[-1].function
        # Assert
        assert name == "func_9"


# ============================================================================
# Test PerformanceMonitor — clear
# ============================================================================


@pytest.fixture
def cleared_monitor(started_monitor, sample_metric):
    started_monitor.record_metric(sample_metric)
    started_monitor.clear()
    return started_monitor


class TestPerformanceMonitorClear:
    """Tests for clear()."""

    def test_clear_empties_metrics(self, cleared_monitor):
        # Arrange
        mon = cleared_monitor
        # Act
        size = len(mon.metrics)
        # Assert
        assert size == 0

    def test_clear_empties_function_stats(self, cleared_monitor):
        # Arrange
        mon = cleared_monitor
        # Act
        size = len(mon.function_stats)
        # Assert
        assert size == 0


# ============================================================================
# Test PerformanceMonitor — save / load
# ============================================================================


@pytest.fixture
def saved_metrics_path(started_monitor, sample_metric, temp_dir):
    started_monitor.record_metric(sample_metric)
    path = os.path.join(temp_dir, "metrics.json")
    started_monitor.save_metrics(path)
    return path


class TestPerformanceMonitorSaveMetrics:
    """Tests for save_metrics()."""

    def test_save_creates_file(self, saved_metrics_path):
        # Arrange
        path = saved_metrics_path
        # Act
        exists = os.path.exists(path)
        # Assert
        assert exists

    def test_saved_payload_contains_metrics_key(self, saved_metrics_path):
        # Arrange
        with open(saved_metrics_path) as f:
            data = json.load(f)
        # Act
        present = "metrics" in data
        # Assert
        assert present

    def test_saved_payload_contains_stats_key(self, saved_metrics_path):
        # Arrange
        with open(saved_metrics_path) as f:
            data = json.load(f)
        # Act
        present = "stats" in data
        # Assert
        assert present

    def test_saved_payload_metrics_count_matches_recorded(self, saved_metrics_path):
        # Arrange
        with open(saved_metrics_path) as f:
            data = json.load(f)
        # Act
        n = len(data["metrics"])
        # Assert
        assert n == 1

    def test_saved_metric_preserves_function_name(self, saved_metrics_path):
        # Arrange
        with open(saved_metrics_path) as f:
            data = json.load(f)
        # Act
        name = data["metrics"][0]["function"]
        # Assert
        assert name == "test_function"


@pytest.fixture
def loaded_monitor(monitor, temp_dir):
    data = {
        "metrics": [
            {
                "timestamp": 123456.0,
                "function": "loaded_func",
                "duration": 0.5,
                "memory_delta": None,
                "args_size": None,
                "result_size": None,
                "exception": None,
            }
        ],
        "stats": {"loaded_func": {"count": 1, "total_time": 0.5}},
    }
    path = os.path.join(temp_dir, "metrics.json")
    with open(path, "w") as f:
        json.dump(data, f)
    monitor.load_metrics(path)
    return monitor


class TestPerformanceMonitorLoadMetrics:
    """Tests for load_metrics()."""

    def test_loaded_metrics_count_matches_payload(self, loaded_monitor):
        # Arrange
        mon = loaded_monitor
        # Act
        n = len(mon.metrics)
        # Assert
        assert n == 1

    def test_loaded_metric_preserves_function_name(self, loaded_monitor):
        # Arrange
        mon = loaded_monitor
        # Act
        name = mon.metrics[0].function
        # Assert
        assert name == "loaded_func"


# ============================================================================
# Test PerformanceMonitor — thread safety
# ============================================================================


class TestPerformanceMonitorThreadSafety:
    """Tests for thread-safe metric recording."""

    def test_concurrent_recording_preserves_total_count(self, started_monitor):
        # Arrange
        num_threads = 5
        metrics_per_thread = 100

        def record_metrics():
            for _ in range(metrics_per_thread):
                started_monitor.record_metric(
                    PerformanceMetric(
                        timestamp=time.time(),
                        function="thread_func",
                        duration=0.001,
                    )
                )

        threads = [threading.Thread(target=record_metrics) for _ in range(num_threads)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        # Act
        total = started_monitor.function_stats["thread_func"]["count"]
        # Assert
        assert total == num_threads * metrics_per_thread


# ============================================================================
# Test Alerts — slow function
# ============================================================================


@pytest.fixture
def slow_alert_capture(started_monitor):
    received = []

    def handler(alert):
        received.append(alert)

    started_monitor.alert_callbacks = [handler]
    started_monitor.alerts["slow_function"] = 0.1
    started_monitor.record_metric(
        PerformanceMetric(timestamp=time.time(), function="slow_func", duration=0.5)
    )
    return received


class TestAlertSlowFunction:
    """Tests for slow_function alert firing."""

    def test_slow_function_fires_exactly_one_alert(self, slow_alert_capture):
        # Arrange
        alerts = slow_alert_capture
        # Act
        n = len(alerts)
        # Assert
        assert n == 1

    def test_slow_function_alert_has_correct_type(self, slow_alert_capture):
        # Arrange
        alerts = slow_alert_capture
        # Act
        kind = alerts[0]["type"]
        # Assert
        assert kind == "slow_function"

    def test_slow_function_alert_includes_function_name(self, slow_alert_capture):
        # Arrange
        alerts = slow_alert_capture
        # Act
        name = alerts[0]["function"]
        # Assert
        assert name == "slow_func"


# ============================================================================
# Test Alerts — memory spike
# ============================================================================


@pytest.fixture
def memory_alert_capture(started_monitor):
    received = []

    def handler(alert):
        received.append(alert)

    started_monitor.alert_callbacks = [handler]
    started_monitor.alerts["memory_spike"] = 50
    started_monitor.record_metric(
        PerformanceMetric(
            timestamp=time.time(),
            function="mem_func",
            duration=0.1,
            memory_delta=100,
        )
    )
    return received


class TestAlertMemorySpike:
    """Tests for memory_spike alert firing."""

    def test_memory_spike_fires_exactly_one_alert(self, memory_alert_capture):
        # Arrange
        alerts = memory_alert_capture
        # Act
        n = len(alerts)
        # Assert
        assert n == 1

    def test_memory_spike_alert_has_correct_type(self, memory_alert_capture):
        # Arrange
        alerts = memory_alert_capture
        # Act
        kind = alerts[0]["type"]
        # Assert
        assert kind == "memory_spike"


# ============================================================================
# Test Alerts — below-threshold suppression
# ============================================================================


class TestAlertBelowThreshold:
    """Tests for alert suppression when metric is below threshold."""

    def test_fast_function_does_not_fire_slow_function_alert(self, started_monitor):
        # Arrange
        alerts_received = []

        def handler(alert):
            alerts_received.append(alert)

        started_monitor.alert_callbacks = [handler]
        started_monitor.alerts["slow_function"] = 1.0
        started_monitor.record_metric(
            PerformanceMetric(timestamp=time.time(), function="fast_func", duration=0.1)
        )
        # Act
        slow_alerts = [a for a in alerts_received if a["type"] == "slow_function"]
        # Assert
        assert len(slow_alerts) == 0


# ============================================================================
# Test Alerts — add_alert_callback
# ============================================================================


class TestAlertAddCallback:
    """Tests for add_alert_callback()."""

    def test_adding_callback_grows_list_by_one(self, monitor):
        # Arrange
        m = monitor
        before = len(m.alert_callbacks)

        def my_handler(alert):
            pass

        # Act
        m.add_alert_callback(my_handler)
        # Assert
        assert len(m.alert_callbacks) == before + 1


# ============================================================================
# Test track_performance decorator
# ============================================================================


class TestTrackPerformanceBasic:
    """Tests for basic track_performance decorator usage."""

    def test_decorated_function_returns_correct_value(self):
        # Arrange
        @track_performance
        def my_func(x):
            return x * 2

        # Act
        result = my_func(5)
        # Assert
        assert result == 10


class TestTrackPerformanceMetadata:
    """Tests for track_performance metadata preservation."""

    def test_decorator_preserves_function_name(self):
        # Arrange
        @track_performance
        def original_name(x):
            """Original docstring."""
            return x

        # Act
        name = original_name.__name__
        # Assert
        assert name == "original_name"

    def test_decorator_preserves_docstring(self):
        # Arrange
        @track_performance
        def original_name(x):
            """Original docstring."""
            return x

        # Act
        doc = original_name.__doc__
        # Assert
        assert doc == "Original docstring."


class TestTrackPerformanceException:
    """Tests for track_performance exception propagation."""

    def test_decorated_function_propagates_value_error(self):
        # Arrange
        @track_performance
        def error_func():
            raise ValueError("Test error")

        # Act
        raised_ctx = pytest.raises(ValueError)
        # Assert
        with raised_ctx:
            error_func()


# ============================================================================
# Test Module-Level Functions
# ============================================================================


class TestModuleFunctions:
    """Tests for module-level helper functions."""

    def test_get_performance_stats_returns_dict(self):
        # Arrange
        # (no setup needed)
        # Act
        stats = get_performance_stats()
        # Assert
        assert isinstance(stats, dict)

    def test_get_performance_stats_for_unknown_function_returns_dict(self):
        # Arrange
        # (no setup needed)
        # Act
        stats = get_performance_stats("unknown_func")
        # Assert
        assert isinstance(stats, dict)

    def test_set_performance_alerts_updates_thresholds_without_error(self):
        # Arrange
        # (no setup needed)
        # Act
        set_performance_alerts(slow_function=2.0, memory_spike=200)
        # Assert
        from scitex_benchmark.monitor import _global_monitor

        assert _global_monitor.alerts["slow_function"] == 2.0

    def test_add_performance_alert_handler_appends_callback(self):
        # Arrange
        from scitex_benchmark.monitor import _global_monitor

        before = len(_global_monitor.alert_callbacks)

        def my_handler(alert):
            pass

        # Act
        add_performance_alert_handler(my_handler)
        # Assert
        assert len(_global_monitor.alert_callbacks) == before + 1


# ============================================================================
# Test Default Alert Handler
# ============================================================================


class TestDefaultAlertHandler:
    """Tests for default alert handler."""

    def test_default_handler_issues_slow_function_warning(self):
        # Arrange
        from scitex_benchmark.monitor import _default_alert_handler

        monitor_obj = PerformanceMonitor(max_history=100)
        monitor_obj.add_alert_callback(_default_alert_handler)
        monitor_obj.start()
        monitor_obj.alerts["slow_function"] = 0.01

        try:
            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter("always")
                monitor_obj.record_metric(
                    PerformanceMetric(
                        timestamp=time.time(),
                        function="slow_func",
                        duration=0.1,
                    )
                )
                # Act
                slow_warnings = [
                    warn for warn in w if "Slow function" in str(warn.message)
                ]
                # Assert
                assert len(slow_warnings) >= 1
        finally:
            monitor_obj.stop()


# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    import os

    import pytest

    pytest.main([os.path.abspath(__file__)])

# EOF
