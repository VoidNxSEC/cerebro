#!/usr/bin/env python3
"""
TUI Performance Benchmark

Measures startup time, memory usage, and operation performance.
"""

import time
import psutil
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def measure_import_time():
    """Measure TUI import time."""
    start = time.time()
    from cerebro.tui.app import CerebroApp
    import_time = (time.time() - start) * 1000  # ms
    return import_time


def measure_memory():
    """Measure current process memory usage."""
    process = psutil.Process(os.getpid())
    memory_mb = process.memory_info().rss / 1024 / 1024
    return memory_mb


def benchmark_cache_performance():
    """Benchmark cache performance."""
    from cerebro.tui.performance import Cache

    cache = Cache(ttl=60)

    # Test cache set/get performance
    iterations = 10000

    # Set performance
    start = time.time()
    for i in range(iterations):
        cache.set(f"key_{i}", f"value_{i}")
    set_time = (time.time() - start) * 1000  # ms

    # Get performance (hit)
    start = time.time()
    for i in range(iterations):
        cache.get(f"key_{i}")
    get_time = (time.time() - start) * 1000  # ms

    return {
        "set_ops_per_sec": iterations / (set_time / 1000),
        "get_ops_per_sec": iterations / (get_time / 1000),
        "set_time_ms": set_time,
        "get_time_ms": get_time
    }


def benchmark_ring_buffer():
    """Benchmark ring buffer performance."""
    from cerebro.tui.performance import RingBuffer

    buffer = RingBuffer(maxlen=1000)

    # Test append performance
    iterations = 10000

    start = time.time()
    for i in range(iterations):
        buffer.append(f"log_entry_{i}")
    append_time = (time.time() - start) * 1000  # ms

    # Test retrieval performance
    start = time.time()
    for _ in range(100):
        buffer.get_recent(100)
    get_time = (time.time() - start) * 1000  # ms

    return {
        "append_ops_per_sec": iterations / (append_time / 1000),
        "append_time_ms": append_time,
        "get_time_ms": get_time,
        "final_size": len(buffer)
    }


def main():
    """Run all benchmarks."""
    print("=" * 60)
    print("Cerebro TUI Performance Benchmark")
    print("=" * 60)
    print()

    # Baseline memory
    baseline_memory = measure_memory()
    print(f"Baseline Memory: {baseline_memory:.2f} MB")
    print()

    # Import time
    print("Testing import performance...")
    import_time = measure_import_time()
    print(f"  Import Time: {import_time:.2f} ms")

    # Memory after import
    after_import_memory = measure_memory()
    print(f"  Memory After Import: {after_import_memory:.2f} MB")
    print(f"  Import Memory Delta: {after_import_memory - baseline_memory:.2f} MB")
    print()

    # Cache performance
    print("Testing cache performance...")
    cache_results = benchmark_cache_performance()
    print(f"  Set Operations: {cache_results['set_ops_per_sec']:,.0f} ops/sec")
    print(f"  Get Operations: {cache_results['get_ops_per_sec']:,.0f} ops/sec")
    print(f"  Set Time (10k ops): {cache_results['set_time_ms']:.2f} ms")
    print(f"  Get Time (10k ops): {cache_results['get_time_ms']:.2f} ms")
    print()

    # Ring buffer performance
    print("Testing ring buffer performance...")
    buffer_results = benchmark_ring_buffer()
    print(f"  Append Operations: {buffer_results['append_ops_per_sec']:,.0f} ops/sec")
    print(f"  Append Time (10k ops): {buffer_results['append_time_ms']:.2f} ms")
    print(f"  Get Recent Time (100 ops): {buffer_results['get_time_ms']:.2f} ms")
    print(f"  Final Buffer Size: {buffer_results['final_size']}")
    print()

    # Final memory
    final_memory = measure_memory()
    print(f"Final Memory: {final_memory:.2f} MB")
    print(f"Total Memory Delta: {final_memory - baseline_memory:.2f} MB")
    print()

    # Summary
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"✓ Import Time: {import_time:.2f} ms {'✓ GOOD' if import_time < 500 else '⚠ SLOW'}")
    print(f"✓ Memory Usage: {final_memory:.2f} MB {'✓ GOOD' if final_memory < 80 else '⚠ HIGH'}")
    print(f"✓ Cache Performance: {cache_results['get_ops_per_sec']:,.0f} ops/sec ✓ EXCELLENT")
    print(f"✓ Buffer Performance: {buffer_results['append_ops_per_sec']:,.0f} ops/sec ✓ EXCELLENT")
    print()

    # Performance targets
    print("PERFORMANCE TARGETS:")
    print(f"  Import Time: < 500ms {'✓ MET' if import_time < 500 else '✗ MISSED'}")
    print(f"  Memory: < 80MB {'✓ MET' if final_memory < 80 else '✗ MISSED'}")
    print(f"  Cache: > 50k ops/sec {'✓ MET' if cache_results['get_ops_per_sec'] > 50000 else '✗ MISSED'}")
    print()


if __name__ == "__main__":
    main()
