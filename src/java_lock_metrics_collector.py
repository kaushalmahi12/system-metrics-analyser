#!/usr/bin/env python3

import subprocess
import time
import csv
import os
from datetime import datetime
import threading
import re

from src.system_metrics_collector import load_config


class JavaLockMetricsCollector:
    def __init__(self, pid, output_dir, interval=1):
        self.pid = pid
        self.output_dir = output_dir
        self.interval = interval
        self.running = True

        # Verify it's a Java process
        self._verify_java_process()

        # Initialize files
        self.files = {
            'locks': open(f'{output_dir}/java_locks.csv', 'a'),
            'threads': open(f'{output_dir}/java_threads.csv', 'a'),
            'gc': open(f'{output_dir}/gc_metrics.csv', 'a'),
            'safepoint': open(f'{output_dir}/safepoint_metrics.csv', 'a')
        }

        self.writers = {
            'locks': csv.writer(self.files['locks']),
            'threads': csv.writer(self.files['threads']),
            'gc': csv.writer(self.files['gc']),
            'safepoint': csv.writer(self.files['safepoint'])
        }

        self._write_headers()

    def _verify_java_process(self):
        try:
            cmd = f"ps -p {self.pid} -o comm="
            process_name = subprocess.check_output(cmd, shell=True).decode().strip()
            if 'java' not in process_name.lower():
                raise ValueError(f"Process {self.pid} is not a Java process")
        except subprocess.CalledProcessError:
            raise ValueError(f"Process {self.pid} not found")

    def _write_headers(self):
        headers = {
            'locks': ['timestamp', 'datetime', 'thread_name', 'lock_class', 'lock_id', 'wait_time', 'owner_thread'],
            'threads': ['timestamp', 'datetime', 'thread_name', 'state', 'waited_count', 'blocked_count', 'blocked_time'],
            'gc': ['timestamp', 'datetime', 'gc_type', 'duration_ms', 'young_size', 'old_size'],
            'safepoint': ['timestamp', 'datetime', 'operation', 'duration_ms', 'threads_wait_time']
        }

        for metric_type, header in headers.items():
            if os.path.getsize(f'{self.output_dir}/{metric_type}.csv') == 0:
                self.writers[metric_type].writerow(header)

    def collect_thread_dump(self):
        try:
            cmd = f"jstack -l {self.pid}"
            return subprocess.check_output(cmd, shell=True).decode()
        except subprocess.CalledProcessError as e:
            print(f"Error collecting thread dump: {e}")
            return None

    def collect_gc_stats(self):
        try:
            cmd = f"jstat -gc {self.pid}"
            return subprocess.check_output(cmd, shell=True).decode()
        except subprocess.CalledProcessError as e:
            print(f"Error collecting GC stats: {e}")
            return None

    def parse_thread_dump(self, thread_dump):
        threads_info = []
        current_thread = None
        lock_info = []

        for line in thread_dump.split('\n'):
            if '"' in line and 'nid=' in line:  # Thread line
                thread_match = re.match(r'"([^"]+)".*prio=(\d+).*tid=(\w+).*nid=(\w+).*state=(\w+)', line)
                if thread_match:
                    current_thread = {
                        'name': thread_match.group(1),
                        'state': thread_match.group(5),
                        'waited_count': 0,
                        'blocked_count': 0,
                        'blocked_time': 0
                    }
                    threads_info.append(current_thread)

            elif current_thread and 'waiting on' in line:
                lock_match = re.search(r'waiting on <(\w+)> \(a ([\w\.]+)\)', line)
                if lock_match:
                    lock_info.append({
                        'thread_name': current_thread['name'],
                        'lock_id': lock_match.group(1),
                        'lock_class': lock_match.group(2),
                        'owner_thread': None
                    })

            elif current_thread and 'waiting to lock' in line:
                lock_match = re.search(r'waiting to lock <(\w+)> \(a ([\w\.]+)\)', line)
                if lock_match:
                    lock_info.append({
                        'thread_name': current_thread['name'],
                        'lock_id': lock_match.group(1),
                        'lock_class': lock_match.group(2),
                        'owner_thread': None
                    })

        return threads_info, lock_info

    def collect_lock_metrics(self):
        while self.running:
            try:
                timestamp = time.time()
                datetime_str = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')

                thread_dump = self.collect_thread_dump()
                if thread_dump:
                    threads_info, lock_info = self.parse_thread_dump(thread_dump)

                    for lock in lock_info:
                        self.writers['locks'].writerow([
                            timestamp,
                            datetime_str,
                            lock['thread_name'],
                            lock['lock_class'],
                            lock['lock_id'],
                            0,  # wait_time (needs JFR for accurate timing)
                            lock['owner_thread']
                        ])

                    for thread in threads_info:
                        self.writers['threads'].writerow([
                            timestamp,
                            datetime_str,
                            thread['name'],
                            thread['state'],
                            thread['waited_count'],
                            thread['blocked_count'],
                            thread['blocked_time']
                        ])

                self.files['locks'].flush()
                self.files['threads'].flush()
                time.sleep(self.interval)

            except Exception as e:
                print(f"Error in lock metrics collection: {e}")

    def collect_gc_metrics(self):
        while self.running:
            try:
                timestamp = time.time()
                datetime_str = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')

                gc_stats = self.collect_gc_stats()
                if gc_stats:
                    # Parse jstat output
                    lines = gc_stats.strip().split('\n')
                    if len(lines) >= 2:
                        headers = lines[0].split()
                        values = lines[1].split()
                        gc_data = dict(zip(headers, values))

                        self.writers['gc'].writerow([
                            timestamp,
                            datetime_str,
                            'Unknown',  # gc_type needs JFR for accurate type
                            gc_data.get('GCT', 0),  # GC time
                            gc_data.get('EU', 0),   # Eden usage
                            gc_data.get('OU', 0)    # Old usage
                        ])

                self.files['gc'].flush()
                time.sleep(self.interval)

            except Exception as e:
                print(f"Error in GC metrics collection: {e}")

    def start_collection(self):
        self.threads = [
            threading.Thread(target=self.collect_lock_metrics, name="locks"),
            threading.Thread(target=self.collect_gc_metrics, name="gc")
        ]

        for thread in self.threads:
            thread.daemon = True
            thread.start()

        return self.threads

    def stop_collection(self):
        self.running = False
        for thread in self.threads:
            thread.join()
        for file in self.files.values():
            file.close()

def main():
    import argparse
    config = load_config()
    parser = argparse.ArgumentParser(description='Collect Java metrics')
    parser.add_argument('--pid', type=int, required=True)
    parser.add_argument('--output-dir', default='metrics_data')
    parser.add_argument('--interval', type=float,
                    default=config['collection']['java']['interval'])
    args = parser.parse_args()
    collector = JavaLockMetricsCollector(args.pid, args.output_dir, args.interval)

    try:
        threads = collector.start_collection()
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        collector.stop_collection()

if __name__ == "__main__":
    main()
