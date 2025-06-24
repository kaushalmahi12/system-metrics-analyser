# System and Java Application Metrics Analyzer

A comprehensive tool for collecting and analyzing system and Java application metrics,
with a focus on performance and lock contention analysis.

## Prerequisites

- Python 3.8+
- Java 21+
- async-profiler
- System tools (perf, sysstat)

## Quick Start

1. Setup the environment:
```bash
./setup.sh
source venv/bin/activate
```

## Start metrics collection
### For system metrics only:
```bash
python3 src/system_metrics_collector.py --output-dir ./metrics_data
```

### For Java application lock analysis:
```bash
python3 src/java_lock_metrics_collector.py --pid <JAVA_PID> --output-dir ./metrics_data
```

### For complete analysis including async-profiler:
```bash
./src/async_profiler_collector.sh <JAVA_PID> ./metrics_data 3600
```

## Generate plots from collected data
```bash
python3 src/plot_metrics.py --data-dir ./metrics_data --output system_analysis.png
```


## Collected Metrics
* System Metrics
* CPU utilization (user, system, iowait)
* Memory usage and page faults
* Disk I/O statistics
* Network I/O
* System load

## Java-specific Metrics
* Thread states and locks 
* GC metrics 
* Lock contention 
* Safepoint statistics 
* Object allocation rates

## Output Files
All metrics are stored in CSV format in the specified output directory:

* system_metrics.csv
* java_locks.csv
* java_threads.csv
* gc_metrics.csv
* async_profiler_results.html

## Configuration
Edit config/default_config.yaml to customize:
* Collection intervals
* Metrics selection
* Threshold values