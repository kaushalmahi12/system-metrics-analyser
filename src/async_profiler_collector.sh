#!/bin/bash

PID=$1
OUTPUT_DIR=$2
DURATION=$3

# Check if async-profiler is available
ASYNC_PROFILER_HOME=${ASYNC_PROFILER_HOME:-"/opt/async-profiler"}

if [ ! -d "$ASYNC_PROFILER_HOME" ]; then
    echo "async-profiler not found. Please install it first."
    exit 1
fi

# Start profiling
$ASYNC_PROFILER_HOME/profiler.sh start -e lock -i 1ms -f $OUTPUT_DIR/lock_profile.jfr $PID

# Wait for specified duration
sleep $DURATION

# Stop profiling
$ASYNC_PROFILER_HOME/profiler.sh stop $PID

# Convert JFR to JSON for analysis
$ASYNC_PROFILER_HOME/converters/jfr2flame.sh $OUTPUT_DIR/lock_profile.jfr
