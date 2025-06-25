#!/usr/bin/env python3

import pandas as pd
import matplotlib.pyplot as plt
import glob
import os
import argparse

class MetricsAnalyzer:
    def __init__(self, data_dir):
        self.data_dir = data_dir
        self.metrics = {}
        self.load_data()

    def load_data(self):
        metric_types = ['cpu', 'memory', 'io', 'network']

        for metric in metric_types:
            files = glob.glob(f"{self.data_dir}/{metric}_*.csv")
            if files:
                latest_file = max(files, key=os.path.getctime)
                self.metrics[metric] = pd.read_csv(latest_file)
                # Convert timestamp to datetime
                self.metrics[metric]['datetime'] = pd.to_datetime(self.metrics[metric]['timestamp'], unit='s')

    def plot_cpu_metrics(self, ax):
        df = self.metrics['cpu']
        ax.plot(df['datetime'], df['cpu_percent'], label='CPU %')
        ax.plot(df['datetime'], df['user'], label='User %')
        ax.plot(df['datetime'], df['system'], label='System %')
        ax.plot(df['datetime'], df['iowait'], label='IO Wait %')
        ax.set_title('CPU Utilization')
        ax.set_ylabel('Percentage')
        ax.legend()

    def plot_memory_metrics(self, ax):
        df = self.metrics['memory']
        # Convert to GB
        for col in ['total', 'available', 'used', 'free', 'cached', 'buffers']:
            df[f'{col}_gb'] = df[col] / (1024 ** 3)

        ax.plot(df['datetime'], df['used_gb'], label='Used')
        ax.plot(df['datetime'], df['cached_gb'], label='Cached')
        ax.plot(df['datetime'], df['buffers_gb'], label='Buffers')
        ax.set_title('Memory Usage (GB)')
        ax.set_ylabel('GB')
        ax.legend()

    def plot_io_metrics(self, ax):
        df = self.metrics['io']
        # Calculate rates
        df['read_mb_s'] = df['read_bytes'].diff() / (df['timestamp'].diff() * 1024 * 1024)
        df['write_mb_s'] = df['write_bytes'].diff() / (df['timestamp'].diff() * 1024 * 1024)

        ax.plot(df['datetime'], df['read_mb_s'], label='Read MB/s')
        ax.plot(df['datetime'], df['write_mb_s'], label='Write MB/s')
        ax.set_title('Disk I/O')
        ax.set_ylabel('MB/s')
        ax.legend()

    def plot_network_metrics(self, ax):
        df = self.metrics['network']
        # Calculate rates
        df['sent_mb_s'] = df['bytes_sent'].diff() / (df['timestamp'].diff() * 1024 * 1024)
        df['recv_mb_s'] = df['bytes_recv'].diff() / (df['timestamp'].diff() * 1024 * 1024)

        ax.plot(df['datetime'], df['sent_mb_s'], label='Sent MB/s')
        ax.plot(df['datetime'], df['recv_mb_s'], label='Received MB/s')
        ax.set_title('Network I/O')
        ax.set_ylabel('MB/s')
        ax.legend()

    def plot_all_metrics(self):
        fig, axes = plt.subplots(4, 1, figsize=(15, 20))
        fig.suptitle('System Metrics Overview')

        self.plot_cpu_metrics(axes[0])
        self.plot_memory_metrics(axes[1])
        self.plot_io_metrics(axes[2])
        self.plot_network_metrics(axes[3])

        plt.tight_layout()
        return fig

def main():
    parser = argparse.ArgumentParser(description='Plot system metrics')
    parser.add_argument('--data-dir', default='metrics_data', help='Directory containing metrics data')
    parser.add_argument('--output', default='system_metrics.png', help='Output file name')

    args = parser.parse_args()

    analyzer = MetricsAnalyzer(args.data_dir)
    fig = analyzer.plot_all_metrics()
    plt.savefig(args.output)
    print(f"Plot saved as {args.output}")

if __name__ == "__main__":
    main()
