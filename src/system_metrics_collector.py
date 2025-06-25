#!/usr/bin/env python3

import yaml
from pathlib import Path
import time
import csv
import os
import psutil
import argparse
from datetime import datetime
import threading
import signal
import sys



# Load configuration
def load_config():
    config_path = Path(__file__).parent.parent / 'config' / 'default_config.yaml'
    with open(config_path) as f:
        return yaml.safe_load(f)


class MetricsCollector:
    def __init__(self, output_dir, interval=1):
        self.output_dir = output_dir
        self.interval = interval
        self.running = True
        os.makedirs(output_dir, exist_ok=True)

        # Initialize file handlers with fixed names
        self.files = {
            'cpu': open(f'{output_dir}/cpu_metrics.csv', 'a'),
            'memory': open(f'{output_dir}/memory_metrics.csv', 'a'),
            'io': open(f'{output_dir}/io_metrics.csv', 'a'),
            'network': open(f'{output_dir}/network_metrics.csv', 'a')
        }

        # Initialize CSV writers
        self.writers = {
            'cpu': csv.writer(self.files['cpu']),
            'memory': csv.writer(self.files['memory']),
            'io': csv.writer(self.files['io']),
            'network': csv.writer(self.files['network'])
        }

        # Write headers only if files are empty
        self._write_headers_if_empty()

    def _write_headers_if_empty(self):
        headers = {
            'cpu': ['timestamp', 'datetime', 'cpu_percent', 'user', 'system', 'iowait'],
            'memory': ['timestamp', 'datetime', 'total', 'available', 'used', 'free', 'cached', 'buffers'],
            'io': ['timestamp', 'datetime', 'read_bytes', 'write_bytes', 'read_count', 'write_count', 'read_time', 'write_time'],
            'network': ['timestamp', 'datetime', 'bytes_sent', 'bytes_recv', 'packets_sent', 'packets_recv', 'errin', 'errout']
        }

        for metric_type, header in headers.items():
            if os.path.getsize(f'{self.output_dir}/{metric_type}_metrics.csv') == 0:
                self.writers[metric_type].writerow(header)

    def collect_cpu_stats(self):
        while self.running:
            try:
                timestamp = time.time()
                datetime_str = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
                cpu_times = psutil.cpu_times_percent()
                cpu_percent = psutil.cpu_percent()

                self.writers['cpu'].writerow([
                    timestamp,
                    datetime_str,
                    cpu_percent,
                    cpu_times.user,
                    cpu_times.system,
                    cpu_times.iowait
                ])
                self.files['cpu'].flush()
                time.sleep(self.interval)
            except Exception as e:
                print(f"Error collecting CPU stats: {e}")

    def collect_memory_stats(self):
        while self.running:
            try:
                timestamp = time.time()
                datetime_str = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
                mem = psutil.virtual_memory()

                self.writers['memory'].writerow([
                    timestamp,
                    datetime_str,
                    mem.total,
                    mem.available,
                    mem.used,
                    mem.free,
                    mem.cached,
                    mem.buffers if hasattr(mem, 'buffers') else 0
                ])
                self.files['memory'].flush()
                time.sleep(self.interval)
            except Exception as e:
                print(f"Error collecting memory stats: {e}")

    def collect_io_stats(self):
        while self.running:
            try:
                timestamp = time.time()
                datetime_str = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
                io = psutil.disk_io_counters()

                self.writers['io'].writerow([
                    timestamp,
                    datetime_str,
                    io.read_bytes,
                    io.write_bytes,
                    io.read_count,
                    io.write_count,
                    io.read_time,
                    io.write_time
                ])
                self.files['io'].flush()
                time.sleep(self.interval)
            except Exception as e:
                print(f"Error collecting I/O stats: {e}")

    def collect_network_stats(self):
        while self.running:
            try:
                timestamp = time.time()
                datetime_str = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
                net = psutil.net_io_counters()

                self.writers['network'].writerow([
                    timestamp,
                    datetime_str,
                    net.bytes_sent,
                    net.bytes_recv,
                    net.packets_sent,
                    net.packets_recv,
                    net.errin,
                    net.errout
                ])
                self.files['network'].flush()
                time.sleep(self.interval)
            except Exception as e:
                print(f"Error collecting network stats: {e}")

    def start_collection(self):
        self.threads = [
            threading.Thread(target=self.collect_cpu_stats, name="cpu"),
            threading.Thread(target=self.collect_memory_stats, name="memory"),
            threading.Thread(target=self.collect_io_stats, name="io"),
            threading.Thread(target=self.collect_network_stats, name="network")
        ]

        for thread in self.threads:
            thread.daemon = True
            thread.start()

        return self.threads

    def stop_collection(self):
        print("\nStopping metrics collection...")
        self.running = False
        for thread in self.threads:
            thread.join()
        for file in self.files.values():
            file.close()

def signal_handler(signum, frame):
    print(f"\nReceived signal {signum}")
    if collector:
        collector.stop_collection()
    sys.exit(0)

def main():
    config = load_config()
    parser = argparse.ArgumentParser(description='Collect system metrics')
    parser.add_argument('--output-dir', default='metrics_data')
    parser.add_argument('--duration', default=10, type=int)
    parser.add_argument('--interval', type=float,
                        default=config['collection']['system']['interval'])
    args = parser.parse_args()

    global collector
    collector = MetricsCollector(args.output_dir, args.interval)

    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    print(f"Starting metrics collection. Data will be saved in {args.output_dir}/")
    print("Press Ctrl+C to stop collection")

    threads = collector.start_collection()

    try:
        if args.duration > 0:
            time.sleep(args.duration)
            collector.stop_collection()
        else:
            while True:
                time.sleep(1)
    except KeyboardInterrupt:
        collector.stop_collection()



if __name__ == "__main__":
    main()
