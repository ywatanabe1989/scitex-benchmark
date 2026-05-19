#!/usr/bin/env python3
# Time-stamp: "2026-05-18"
# File: test_monitor.py

"""Tests for scitex_benchmark.monitor module.

Each test follows the canonical TQ shape: descriptive name (>=3 word-tokens
after `test_`), explicit `# Arrange` / `# Act` / `# Assert` markers in
order, and exactly one assertion. Multi-assertion originals are split into
one-assertion-per-test siblings that share an Arrange/Act fixture.
"""

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


@pytest.fixture
def populated_function_stats(started_monitor):
    """Record 5 metrics with increasing duration on `my_func` and return
    the function_stats dict for `my_func`."""
    for i in range(5):
        metric = PerformanceMetric(
            timestamp=time.time(),
            function="my_func",
            duration=0.1 * (i + 1),
        )
        started_monitor.record_metric(metric)
    return started_monitor.function_stats["my_func"]


@pytest.fixture
def error_tracking_stats(started_monitor):
    """Record one ok metric and one error metric on `my_func`, return its
    function_stats dict."""
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


@pytest.fixture
def two_function_stats(started_monitor):
    """Record one metric each for func1 (0.1s) and func2 (0.2s) and return
    monitor.get_stats() snapshot."""
    started_monitor.record_metric(
        PerformanceMetric(timestamp=time.time(), function="func1", duration=0.1)
    )
    started_monitor.record_metric(
        PerformanceMetric(timestamp=time.time(), function="func2", duration=0.2)
    )
    return started_monitor.get_stats()


@pytest.fixture
def single_function_stats(started_monitor):
    """Record two metrics on `my_func` (0.1s, 0.3s) and return get_stats
    for it."""
    started_monitor.record_metric(
        PerformanceMetric(timestamp=time.time(), function="my_func", duration=0.1)
    )
    started_monitor.record_metric(
        PerformanceMetric(timestamp=time.time(), function="my_func", duration=0.3)
    )
    return started_monitor.get_stats("my_func")


@pytest.fixture
def recent_metrics_window(started_monitor):
    """Record 10 metrics named func_0..func_9 and return get_recent_metrics(5)."""
    for i in range(10):
        started_monitor.record_metric(
            PerformanceMetric(
                timestamp=time.time() + i, function=f"func_{i}", duration=0.01
            )
        )
    return started_monitor.get_recent_metrics(5)


@pytest.fixture
def saved_metrics_payload(started_monitor, sample_metric, temp_dir):
    """Record sample_metric, save to disk, yield loaded JSON payload +
    file path. Yields rather than returns so the linter knows the
    fixture lifecycle is bounded (TQ005)."""
    started_monitor.record_metric(sample_metric)
    output_path = os.path.join(temp_dir, "metrics.json")
    started_monitor.save_metrics(output_path)
    with open(output_path) as f:
        data = json.load(f)
    yield {"path": output_path, "data": data}


@pytest.fixture
def slow_alerts_captured(started_monitor):
    """Configure started_monitor with a 0.1s slow_function threshold + a
    capturing callback, record a 0.5s `slow_func` metric, return the
    captured alert list."""
    alerts_received = []

    def alert_handler(alert):
        alerts_received.append(alert)

    started_monitor.alert_callbacks = [alert_handler]
    started_monitor.alerts["slow_function"] = 0.1
    started_monitor.record_metric(
        PerformanceMetric(timestamp=time.time(), function="slow_func", duration=0.5)
    )
    return alerts_received


@pytest.fixture
def memory_spike_alerts_captured(started_monitor):
    """Configure 50MB memory_spike threshold + capturing callback, record
    a 100MB `mem_func` metric, return alerts."""
    alerts_received = []

    def alert_handler(alert):
        alerts_received.append(alert)

    started_monitor.alert_callbacks = [alert_handler]
    started_monitor.alerts["memory_spike"] = 50
    started_monitor.record_metric(
        PerformanceMetric(
            timestamp=time.time(),
            function="mem_func",
            duration=0.1,
            memory_delta=100,
        )
    )
    return alerts_received


# ============================================================================
# Test PerformanceMetric
# ============================================================================


class TestPerformanceMetric:
    """Tests for PerformanceMetric dataclass."""

    def test_metric_with_all_fields_stores_function_name(self, sample_metric):
        """PerformanceMetric.function preserves the supplied function name."""
        # Arrange
        # (sample_metric fixture builds the metric)
        # Act
        actual = sample_metric.function
        # Assert
        assert actual == "test_function"

    def test_metric_with_all_fields_stores_duration(self, sample_metric):
        """PerformanceMetric.duration preserves the supplied duration."""
        # Arrange
        # Act
        actual = sample_metric.duration
        # Assert
        assert actual == 0.5

    def test_metric_with_all_fields_stores_memory_delta(self, sample_metric):
        """PerformanceMetric.memory_delta preserves the supplied delta."""
        # Arrange
        # Act
        actual = sample_metric.memory_delta
        # Assert
        assert actual == 10.0

    def test_metric_with_all_fields_stores_args_size(self, sample_metric):
        """PerformanceMetric.args_size preserves the supplied args_size."""
        # Arrange
        # Act
        actual = sample_metric.args_size
        # Assert
        assert actual == 100

    def test_metric_with_all_fields_stores_result_size(self, sample_metric):
        """PerformanceMetric.result_size preserves the supplied result_size."""
        # Arrange
        # Act
        actual = sample_metric.result_size
        # Assert
        assert actual == 50

    def test_metric_with_all_fields_has_no_exception(self, sample_metric):
        """PerformanceMetric.exception defaults to None when not set."""
        # Arrange
        # Act
        actual = sample_metric.exception
        # Assert
        assert actual is None

    def test_metric_with_required_fields_only_keeps_timestamp(self):
        """Constructing with only required fields preserves timestamp."""
        # Arrange
        ts = 1234567890.0
        # Act
        metric = PerformanceMetric(timestamp=ts, function="my_func", duration=0.1)
        # Assert
        assert metric.timestamp == ts

    def test_metric_with_required_fields_only_keeps_function(self):
        """Constructing with only required fields preserves function name."""
        # Arrange
        # Act
        metric = PerformanceMetric(
            timestamp=1234567890.0, function="my_func", duration=0.1
        )
        # Assert
        assert metric.function == "my_func"

    def test_metric_with_required_fields_only_keeps_duration(self):
        """Constructing with only required fields preserves duration."""
        # Arrange
        # Act
        metric = PerformanceMetric(
            timestamp=1234567890.0, function="my_func", duration=0.1
        )
        # Assert
        assert metric.duration == 0.1

    def test_metric_with_required_fields_only_defaults_memory_delta_none(self):
        """memory_delta defaults to None when not supplied."""
        # Arrange
        # Act
        metric = PerformanceMetric(
            timestamp=1234567890.0, function="my_func", duration=0.1
        )
        # Assert
        assert metric.memory_delta is None

    def test_metric_with_required_fields_only_defaults_args_size_none(self):
        """args_size defaults to None when not supplied."""
        # Arrange
        # Act
        metric = PerformanceMetric(
            timestamp=1234567890.0, function="my_func", duration=0.1
        )
        # Assert
        assert metric.args_size is None

    def test_metric_with_required_fields_only_defaults_result_size_none(self):
        """result_size defaults to None when not supplied."""
        # Arrange
        # Act
        metric = PerformanceMetric(
            timestamp=1234567890.0, function="my_func", duration=0.1
        )
        # Assert
        assert metric.result_size is None

    def test_metric_with_required_fields_only_defaults_exception_none(self):
        """exception defaults to None when not supplied."""
        # Arrange
        # Act
        metric = PerformanceMetric(
            timestamp=1234567890.0, function="my_func", duration=0.1
        )
        # Assert
        assert metric.exception is None

    def test_metric_with_exception_stores_exception_message(self):
        """Supplied exception text is stored verbatim on the metric."""
        # Arrange
        msg = "ValueError: test error"
        # Act
        metric = PerformanceMetric(
            timestamp=time.time(),
            function="error_func",
            duration=0.01,
            exception=msg,
        )
        # Assert
        assert metric.exception == msg


# ============================================================================
# Test PerformanceMonitor
# ============================================================================


class TestPerformanceMonitor:
    """Tests for PerformanceMonitor class."""

    def test_new_monitor_preserves_max_history(self, monitor):
        """PerformanceMonitor stores the max_history constructor arg."""
        # Arrange
        # Act
        actual = monitor.max_history
        # Assert
        assert actual == 100

    def test_new_monitor_starts_with_empty_metrics(self, monitor):
        """Newly-constructed monitor has zero recorded metrics."""
        # Arrange
        # Act
        actual = len(monitor.metrics)
        # Assert
        assert actual == 0

    def test_new_monitor_is_not_monitoring(self, monitor):
        """New monitor reports is_monitoring=False until .start() is called."""
        # Arrange
        # Act
        actual = monitor.is_monitoring
        # Assert
        assert actual is False

    def test_new_monitor_alert_callbacks_is_list(self, monitor):
        """alert_callbacks is initialised to a list (default handler only on global)."""
        # Arrange
        # Act
        actual = monitor.alert_callbacks
        # Assert
        assert isinstance(actual, list)

    def test_start_sets_is_monitoring_true(self, monitor):
        """Calling .start() flips is_monitoring to True."""
        # Arrange
        # Act
        monitor.start()
        # Assert
        assert monitor.is_monitoring is True

    def test_stop_sets_is_monitoring_false(self, monitor):
        """Calling .stop() after .start() flips is_monitoring back to False."""
        # Arrange
        monitor.start()
        # Act
        monitor.stop()
        # Assert
        assert monitor.is_monitoring is False

    def test_record_metric_when_monitoring_appends_metric(
        self, started_monitor, sample_metric
    ):
        """record_metric appends to .metrics while monitoring is active."""
        # Arrange
        # Act
        started_monitor.record_metric(sample_metric)
        # Assert
        assert len(started_monitor.metrics) == 1

    def test_record_metric_when_monitoring_increments_function_count(
        self, started_monitor, sample_metric
    ):
        """record_metric while monitoring bumps function_stats[fn]['count']."""
        # Arrange
        # Act
        started_monitor.record_metric(sample_metric)
        # Assert
        assert started_monitor.function_stats["test_function"]["count"] == 1

    def test_record_metric_when_not_monitoring_does_not_store(
        self, monitor, sample_metric
    ):
        """record_metric while stopped silently drops the metric."""
        # Arrange
        # Act
        monitor.record_metric(sample_metric)
        # Assert
        assert len(monitor.metrics) == 0

    def test_function_stats_count_tracks_record_calls(self, populated_function_stats):
        """Five record_metric calls produce count=5."""
        # Arrange
        stats = populated_function_stats
        # Act
        actual = stats["count"]
        # Assert
        assert actual == 5

    def test_function_stats_min_time_tracks_smallest_duration(
        self, populated_function_stats
    ):
        """min_time equals the smallest duration recorded (0.1)."""
        # Arrange
        stats = populated_function_stats
        # Act
        actual = stats["min_time"]
        # Assert
        assert actual == 0.1

    def test_function_stats_max_time_tracks_largest_duration(
        self, populated_function_stats
    ):
        """max_time equals the largest duration recorded (0.5)."""
        # Arrange
        stats = populated_function_stats
        # Act
        actual = stats["max_time"]
        # Assert
        assert actual == 0.5

    def test_function_stats_total_time_sums_durations(self, populated_function_stats):
        """total_time equals sum of recorded durations (0.1+0.2+0.3+0.4+0.5=1.5)."""
        # Arrange
        stats = populated_function_stats
        # Act
        actual = stats["total_time"]
        # Assert
        assert abs(actual - 1.5) < 0.001

    def test_error_tracking_counts_each_recorded_metric(self, error_tracking_stats):
        """One ok + one error metric -> count=2."""
        # Arrange
        stats = error_tracking_stats
        # Act
        actual = stats["count"]
        # Assert
        assert actual == 2

    def test_error_tracking_counts_only_exception_metrics_as_errors(
        self, error_tracking_stats
    ):
        """One ok + one error metric -> errors=1."""
        # Arrange
        stats = error_tracking_stats
        # Act
        actual = stats["errors"]
        # Assert
        assert actual == 1

    def test_max_history_limit_caps_stored_metrics(self):
        """A monitor with max_history=5 caps .metrics at 5 even after 10 records."""
        # Arrange
        monitor = PerformanceMonitor(max_history=5)
        monitor.start()
        for _ in range(10):
            monitor.record_metric(
                PerformanceMetric(timestamp=time.time(), function="func", duration=0.01)
            )
        # Act
        actual = len(monitor.metrics)
        monitor.stop()
        # Assert
        assert actual == 5

    def test_get_stats_all_includes_first_function(self, two_function_stats):
        """get_stats() with no args returns a dict containing func1."""
        # Arrange
        stats = two_function_stats
        # Act
        actual = "func1" in stats
        # Assert
        assert actual is True

    def test_get_stats_all_includes_second_function(self, two_function_stats):
        """get_stats() with no args returns a dict containing func2."""
        # Arrange
        stats = two_function_stats
        # Act
        actual = "func2" in stats
        # Assert
        assert actual is True

    def test_get_stats_all_avg_time_for_first_function(self, two_function_stats):
        """avg_time for func1 equals its only duration (0.1)."""
        # Arrange
        stats = two_function_stats
        # Act
        actual = stats["func1"]["avg_time"]
        # Assert
        assert actual == 0.1

    def test_get_stats_all_avg_time_for_second_function(self, two_function_stats):
        """avg_time for func2 equals its only duration (0.2)."""
        # Arrange
        stats = two_function_stats
        # Act
        actual = stats["func2"]["avg_time"]
        # Assert
        assert actual == 0.2

    def test_get_stats_single_function_includes_name(self, single_function_stats):
        """get_stats(fn) returns a dict whose 'function' key echoes fn."""
        # Arrange
        stats = single_function_stats
        # Act
        actual = stats["function"]
        # Assert
        assert actual == "my_func"

    def test_get_stats_single_function_counts_calls(self, single_function_stats):
        """get_stats(fn).count equals number of record_metric calls."""
        # Arrange
        stats = single_function_stats
        # Act
        actual = stats["count"]
        # Assert
        assert actual == 2

    def test_get_stats_single_function_computes_avg(self, single_function_stats):
        """avg_time = mean of recorded durations (0.1, 0.3) -> 0.2."""
        # Arrange
        stats = single_function_stats
        # Act
        actual = stats["avg_time"]
        # Assert
        assert actual == 0.2

    def test_get_stats_single_function_min_time(self, single_function_stats):
        """min_time = smallest duration (0.1)."""
        # Arrange
        stats = single_function_stats
        # Act
        actual = stats["min_time"]
        # Assert
        assert actual == 0.1

    def test_get_stats_single_function_max_time(self, single_function_stats):
        """max_time = largest duration (0.3)."""
        # Arrange
        stats = single_function_stats
        # Act
        actual = stats["max_time"]
        # Assert
        assert actual == 0.3

    def test_get_stats_unknown_function_returns_empty_dict(self, started_monitor):
        """get_stats('not-recorded') returns an empty dict."""
        # Arrange
        # Act
        stats = started_monitor.get_stats("unknown_func")
        # Assert
        assert stats == {}

    def test_get_recent_metrics_returns_requested_count(self, recent_metrics_window):
        """get_recent_metrics(5) returns 5 entries from a 10-metric history."""
        # Arrange
        recent = recent_metrics_window
        # Act
        actual = len(recent)
        # Assert
        assert actual == 5

    def test_get_recent_metrics_returns_window_starting_from_func_5(
        self, recent_metrics_window
    ):
        """First entry in the 5-window is func_5 (i.e. last-5 ordered)."""
        # Arrange
        recent = recent_metrics_window
        # Act
        actual = recent[0].function
        # Assert
        assert actual == "func_5"

    def test_get_recent_metrics_returns_window_ending_at_func_9(
        self, recent_metrics_window
    ):
        """Last entry in the 5-window is func_9."""
        # Arrange
        recent = recent_metrics_window
        # Act
        actual = recent[-1].function
        # Assert
        assert actual == "func_9"

    def test_clear_empties_metrics_deque(self, started_monitor, sample_metric):
        """clear() empties the .metrics deque."""
        # Arrange
        started_monitor.record_metric(sample_metric)
        # Act
        started_monitor.clear()
        # Assert
        assert len(started_monitor.metrics) == 0

    def test_clear_empties_function_stats_dict(self, started_monitor, sample_metric):
        """clear() empties the function_stats dict."""
        # Arrange
        started_monitor.record_metric(sample_metric)
        # Act
        started_monitor.clear()
        # Assert
        assert len(started_monitor.function_stats) == 0

    def test_save_metrics_writes_file_to_disk(self, saved_metrics_payload):
        """save_metrics writes a file at the requested path."""
        # Arrange
        payload = saved_metrics_payload
        # Act
        actual = os.path.exists(payload["path"])
        # Assert
        assert actual is True

    def test_save_metrics_payload_contains_metrics_key(self, saved_metrics_payload):
        """Saved JSON has a 'metrics' key."""
        # Arrange
        payload = saved_metrics_payload
        # Act
        actual = "metrics" in payload["data"]
        # Assert
        assert actual is True

    def test_save_metrics_payload_contains_stats_key(self, saved_metrics_payload):
        """Saved JSON has a 'stats' key."""
        # Arrange
        payload = saved_metrics_payload
        # Act
        actual = "stats" in payload["data"]
        # Assert
        assert actual is True

    def test_save_metrics_serialises_recorded_metric_count(self, saved_metrics_payload):
        """One recorded metric -> one entry in saved data['metrics']."""
        # Arrange
        payload = saved_metrics_payload
        # Act
        actual = len(payload["data"]["metrics"])
        # Assert
        assert actual == 1

    def test_save_metrics_serialises_function_name(self, saved_metrics_payload):
        """Saved metric carries the function name from sample_metric."""
        # Arrange
        payload = saved_metrics_payload
        # Act
        actual = payload["data"]["metrics"][0]["function"]
        # Assert
        assert actual == "test_function"

    def test_load_metrics_restores_metric_count(self, monitor, temp_dir):
        """load_metrics restores 1 entry from a 1-entry payload."""
        # Arrange
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
        input_path = os.path.join(temp_dir, "metrics.json")
        with open(input_path, "w") as f:
            json.dump(data, f)
        # Act
        monitor.load_metrics(input_path)
        # Assert
        assert len(monitor.metrics) == 1

    def test_load_metrics_restores_function_name(self, monitor, temp_dir):
        """load_metrics restores the function name onto the loaded metric."""
        # Arrange
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
        input_path = os.path.join(temp_dir, "metrics.json")
        with open(input_path, "w") as f:
            json.dump(data, f)
        # Act
        monitor.load_metrics(input_path)
        # Assert
        assert monitor.metrics[0].function == "loaded_func"

    def test_thread_safety_record_metric_counts_all_threads(self, started_monitor):
        """5 threads x 100 metrics -> function_stats['thread_func']['count']==500."""
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
        actual = started_monitor.function_stats["thread_func"]["count"]
        # Assert
        assert actual == num_threads * metrics_per_thread


# ============================================================================
# Test Alerts
# ============================================================================


class TestAlerts:
    """Tests for performance alerts."""

    def test_slow_function_alert_fires_one_alert(self, slow_alerts_captured):
        """0.5s metric against 0.1s threshold triggers exactly one alert."""
        # Arrange
        alerts = slow_alerts_captured
        # Act
        actual = len(alerts)
        # Assert
        assert actual == 1

    def test_slow_function_alert_type_is_slow_function(self, slow_alerts_captured):
        """The triggered alert has type='slow_function'."""
        # Arrange
        alerts = slow_alerts_captured
        # Act
        actual = alerts[0]["type"]
        # Assert
        assert actual == "slow_function"

    def test_slow_function_alert_carries_function_name(self, slow_alerts_captured):
        """The triggered alert names the function that was slow."""
        # Arrange
        alerts = slow_alerts_captured
        # Act
        actual = alerts[0]["function"]
        # Assert
        assert actual == "slow_func"

    def test_memory_spike_alert_fires_one_alert(self, memory_spike_alerts_captured):
        """100MB delta against 50MB threshold triggers exactly one alert."""
        # Arrange
        alerts = memory_spike_alerts_captured
        # Act
        actual = len(alerts)
        # Assert
        assert actual == 1

    def test_memory_spike_alert_type_is_memory_spike(
        self, memory_spike_alerts_captured
    ):
        """The triggered alert has type='memory_spike'."""
        # Arrange
        alerts = memory_spike_alerts_captured
        # Act
        actual = alerts[0]["type"]
        # Assert
        assert actual == "memory_spike"

    def test_no_alert_when_duration_below_slow_function_threshold(
        self, started_monitor
    ):
        """A fast metric does not fire a slow_function alert."""
        # Arrange
        alerts_received = []

        def alert_handler(alert):
            alerts_received.append(alert)

        started_monitor.alert_callbacks = [alert_handler]
        started_monitor.alerts["slow_function"] = 1.0
        started_monitor.record_metric(
            PerformanceMetric(timestamp=time.time(), function="fast_func", duration=0.1)
        )
        # Act
        slow_alerts = [a for a in alerts_received if a["type"] == "slow_function"]
        # Assert
        assert len(slow_alerts) == 0

    def test_add_alert_callback_appends_handler(self, monitor):
        """add_alert_callback adds exactly one handler to alert_callbacks."""
        # Arrange
        initial_count = len(monitor.alert_callbacks)

        def my_handler(alert):
            pass

        # Act
        monitor.add_alert_callback(my_handler)
        # Assert
        assert len(monitor.alert_callbacks) == initial_count + 1


# ============================================================================
# Test track_performance decorator
# ============================================================================


class TestTrackPerformance:
    """Tests for track_performance decorator."""

    def test_track_performance_basic_returns_function_result(self):
        """A @track_performance-decorated `x*2` function returns 10 for x=5."""
        # Arrange

        @track_performance
        def my_func(x):
            return x * 2

        # Act
        result = my_func(5)
        # Assert
        assert result == 10

    def test_track_performance_preserves_function_name(self):
        """@track_performance preserves __name__ on the wrapped function."""
        # Arrange

        @track_performance
        def original_name(x):
            """Original docstring."""
            return x

        # Act
        actual = original_name.__name__
        # Assert
        assert actual == "original_name"

    def test_track_performance_preserves_function_docstring(self):
        """@track_performance preserves __doc__ on the wrapped function."""
        # Arrange

        @track_performance
        def original_name(x):
            """Original docstring."""
            return x

        # Act
        actual = original_name.__doc__
        # Assert
        assert actual == "Original docstring."

    def test_track_performance_propagates_exception_from_wrapped(self):
        """@track_performance re-raises ValueError from the wrapped function."""
        # Arrange

        @track_performance
        def error_func():
            raise ValueError("Test error")

        # Act
        ctx = pytest.raises(ValueError)
        # Assert
        with ctx:
            error_func()


# ============================================================================
# Test Module-Level Functions
# ============================================================================


class TestModuleFunctions:
    """Tests for module-level functions."""

    def test_get_performance_stats_returns_dict(self):
        """get_performance_stats() returns a dict instance."""
        # Arrange
        # Act
        stats = get_performance_stats()
        # Assert
        assert isinstance(stats, dict)

    def test_get_performance_stats_for_unknown_function_returns_dict(self):
        """get_performance_stats('unknown_func') still returns a dict (possibly empty)."""
        # Arrange
        # Act
        stats = get_performance_stats("unknown_func")
        # Assert
        assert isinstance(stats, dict)

    def test_set_performance_alerts_updates_slow_function_threshold(self):
        """set_performance_alerts(slow_function=2.0) updates the global threshold."""
        # Arrange
        from scitex_benchmark.monitor import _global_monitor

        original = dict(_global_monitor.alerts)
        # Act
        set_performance_alerts(slow_function=2.0, memory_spike=200)
        try:
            actual = _global_monitor.alerts["slow_function"]
        finally:
            _global_monitor.alerts.clear()
            _global_monitor.alerts.update(original)
        # Assert
        assert actual == 2.0

    def test_add_performance_alert_handler_appends_to_global_callbacks(self):
        """add_performance_alert_handler appends one handler to the global monitor."""
        # Arrange
        from scitex_benchmark.monitor import _global_monitor

        before = len(_global_monitor.alert_callbacks)

        def my_handler(alert):
            pass

        # Act
        try:
            add_performance_alert_handler(my_handler)
            after = len(_global_monitor.alert_callbacks)
        finally:
            _global_monitor.alert_callbacks.remove(my_handler)
        # Assert
        assert after == before + 1


# ============================================================================
# Test Default Alert Handler
# ============================================================================


class TestDefaultAlertHandler:
    """Tests for default alert handler."""

    def test_default_handler_issues_slow_function_warning(self):
        """_default_alert_handler emits a warning containing 'Slow function' for a slow metric."""
        # Arrange
        from scitex_benchmark.monitor import _default_alert_handler

        monitor = PerformanceMonitor(max_history=100)
        monitor.add_alert_callback(_default_alert_handler)
        monitor.start()
        monitor.alerts["slow_function"] = 0.01
        try:
            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter("always")
                # Act
                monitor.record_metric(
                    PerformanceMetric(
                        timestamp=time.time(), function="slow_func", duration=0.1
                    )
                )
                slow_warnings = [
                    warning for warning in w if "Slow function" in str(warning.message)
                ]
        finally:
            monitor.stop()
        # Assert
        assert len(slow_warnings) >= 1


# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    import os

    import pytest

    pytest.main([os.path.abspath(__file__)])
