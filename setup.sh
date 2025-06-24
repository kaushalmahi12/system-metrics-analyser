#!/bin/bash

# Exit on any error
set -e

echo "Setting up System Metrics Analyzer..."

# Check Python version
if ! command -v python3 &> /dev/null; then
    echo "Python 3 is required but not installed."
    exit 1
fi

# Install system dependencies for Amazon Linux 2
if [ -f /etc/system-release ] && grep -q "Amazon Linux" /etc/system-release; then
    echo "Installing system dependencies..."
    sudo yum update -y
    sudo yum install -y python3-devel gcc sysstat perf java-21-openjdk-devel
fi

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Install async-profiler
if [ ! -d "/opt/async-profiler" ]; then
    echo "Installing async-profiler..."
    cd /tmp
    wget https://github.com/jvm-profiling-tools/async-profiler/releases/download/v2.9/async-profiler-2.9-linux-x64.tar.gz
    sudo tar xzf async-profiler-2.9-linux-x64.tar.gz -C /opt
    sudo ln -sf /opt/async-profiler-2.9-linux-x64 /opt/async-profiler
fi

echo "Setup completed successfully!"
