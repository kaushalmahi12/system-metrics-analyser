def plot_lock_metrics(self, ax):
    df = self.metrics['locks']

    # Group by lock_address and calculate wait time statistics
    lock_stats = df.groupby('lock_address').agg({
        'wait_time': ['mean', 'max', 'count']
    }).reset_index()

    # Plot top 10 contended locks
    top_locks = lock_stats.nlargest(10, ('wait_time', 'mean'))

    bars = ax.bar(range(len(top_locks)), top_locks[('wait_time', 'mean')])
    ax.set_xticks(range(len(top_locks)))
    ax.set_xticklabels(top_locks['lock_address'], rotation=45)
    ax.set_title('Top 10 Contended Locks')
    ax.set_ylabel('Average Wait Time (ms)')

    # Add contention count annotations
    for i, bar in enumerate(bars):
        ax.text(
            bar.get_x() + bar.get_width()/2,
            bar.get_height(),
            f'Count: {int(top_locks.iloc[i][("wait_time", "count")])}',
            ha='center',
            va='bottom'
        )

def plot_thread_states(self, ax):
    df = self.metrics['threads']

    # Calculate thread state distribution over time
    thread_states = df.pivot_table(
        index='datetime',
        columns='state',
        values='thread_id',
        aggfunc='count'
    ).fillna(0)

    thread_states.plot(
        kind='area',
        stacked=True,
        ax=ax
    )
    ax.set_title('Thread States Over Time')
    ax.set_ylabel('Thread Count')
    ax.legend(title='Thread State')
