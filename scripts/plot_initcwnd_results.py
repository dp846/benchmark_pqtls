import os
import pandas as pd
import matplotlib.pyplot as plt
import re
import numpy as np

# Set of initcwnd values to include
# NOTE: an exponential scale was used because the thresholds can be quite widely spaced for each alg.
allowed_initcwnds = {5, 10, 20, 40, 80}

# Option to add very minute random variation to plots to make ones that overlap more visible
def add_random_variation(series, percent=0.035):
    noise = np.random.uniform(1 - percent, 1 + percent, size=len(series))
    return series * noise

# Process the given csv
def load_and_process(filename):
    rows = []

    with open(filename, 'r') as f:
        for line in f:
            if not line.strip():
                continue
            parts = line.strip().split(',')
            try:
                loss_val = float(parts[0])
            except ValueError:
                continue

            try:
                numeric_vals = [float(x) for x in parts[1:] if x.strip() != '']
            except ValueError:
                continue

            median_val = pd.Series(numeric_vals).median() if numeric_vals else None
            pct90_val = pd.Series(numeric_vals).quantile(0.90) if numeric_vals else None

            rows.append({'loss': loss_val, 'median': median_val, '90thpercentile': pct90_val})

    return pd.DataFrame(rows).sort_values(by='loss')

# extract num using regex
def extract_number(text, prefix):
    match = re.search(rf'{prefix}([\d.]+)', text)
    return match.group(1) if match else None

# Root data directory relative to the script execution location.
# NOTE: expected to be in the format:
# - initcwnd=X1/
#   - latency=Y1
#   - latency=Y2
# - initcwnd=X2/
#   - latency=Y1
#   - latency=Y2
# - ...

RELATIVE_DATA_DIR = 'data'
results = {}

# Loop over initcwnd directories (top-level)
for initcwnd_dir in sorted(os.listdir(RELATIVE_DATA_DIR)):
    full_initcwnd_path = os.path.join(RELATIVE_DATA_DIR, initcwnd_dir)
    if os.path.isdir(full_initcwnd_path):
        # Extract initcwnd value, e.g. from "initcwnd=10'
        initcwnd_value = extract_number(initcwnd_dir, 'initcwnd=')
        if not initcwnd_value:
            continue
        # loop over latency directories inside initcwnd directory
        for latency_dir in sorted(os.listdir(full_initcwnd_path)):
            full_latency_path = os.path.join(full_initcwnd_path, latency_dir)
            if os.path.isdir(full_latency_path):
                # Extract latency value, e.g. from "latency=20.000ms"
                latency_value = extract_number(latency_dir, 'latency=')
                if not latency_value:
                    continue
                # Process each CSV file in latency directory
                for filename in os.listdir(full_latency_path):
                    if filename.endswith('.csv'):
                        # NOTE: assumes filename format: <sig_alg>.csv
                        sig_alg, _ = filename.rsplit('.', 1)
                        df = load_and_process(os.path.join(full_latency_path, filename))
                        key = (sig_alg, latency_value)
                        if key not in results:
                            results[key] = {}
                        # Store dataframe keyed by an integer initcwnd value
                        results[key][int(float(initcwnd_value))] = df

# Plot results for each (signature algorithm, latency) - MEDIAN HANDSHAKE TIME 
for (sig_alg, latency), cwnd_data in results.items():
    plt.figure(figsize=(8, 5))

    line_styles = ['o-', 's-', 'd-', 'x-', '^-']
    custom_colors = ['red', 'orange', 'gold', 'lime', 'green']

    style_idx = 0  # Separate index style counter for initcwnd values

    for initcwnd, df in sorted(cwnd_data.items()):
        if initcwnd in allowed_initcwnds:
            plt.plot(df['loss'], add_random_variation(df['median']), 
                     line_styles[style_idx % len(line_styles)],
                     label=f'initcwnd = {initcwnd}', 
                     color=custom_colors[style_idx % len(custom_colors)],
                     linewidth=2.5, markersize=7, alpha=0.7)
            style_idx += 1

        
    plt.xlabel('Packet Loss (%)', fontsize=14)
    plt.ylabel('Handshake Time (ms)', fontsize=14)
    plt.title(f'{sig_alg} - Median Handshake Time', fontsize=16)
    plt.grid(True, alpha=0.3)

    all_medians = []
    for initcwnd, df in cwnd_data.items():
        if initcwnd in allowed_initcwnds:
            all_medians.extend(df['median'].values)
    if all_medians:
        max_median = max(all_medians)
        plt.ylim(0, max_median * 1.1)
    
    plt.legend(fontsize=14)

    plt.xticks(ticks=list(range(0, 21, 2)))
    plt.tight_layout()
    
    # save plot to ./plots/
    os.makedirs("plots", exist_ok=True)
    filename = f"plots/{sig_alg.lower()}_median.png"
    plt.savefig(filename)
    plt.close()
    plt.show()

# Now plot results for each (sig algorithm, latency) - 90th PERCENTILE HANSHAKE TIME
for (sig_alg, latency), cwnd_data in results.items():
    plt.figure(figsize=(8, 5))

    line_styles = ['o-', 's-', 'd-', 'x-', '^-']
    custom_colors = ['red', 'orange', 'gold', 'lime', 'green']

    style_idx = 0

    for initcwnd, df in sorted(cwnd_data.items()):
        if initcwnd in allowed_initcwnds:
            plt.plot(df['loss'], df['90thpercentile'], 
                     line_styles[style_idx % len(line_styles)],
                     label=f'initcwnd = {initcwnd}', 
                     color=custom_colors[style_idx % len(custom_colors)],
                     linewidth=2.5, markersize=7, alpha=0.7)
            style_idx += 1

    plt.title(f'{sig_alg} - 90th Percentile Handshake Time', fontsize=16)
    plt.xlabel('Packet Loss (%)', fontsize=14)
    plt.ylabel('Handshake Time (ms)', fontsize=14)
    plt.grid(True, alpha=0.3)
    plt.legend(fontsize=14)

    plt.xticks(ticks=list(range(0, 19, 2)))
    plt.tight_layout()
    
    # save plot to ./plots/
    os.makedirs("plots", exist_ok=True)
    filename = f"plots/{sig_alg.lower()}_90th.png"
    plt.savefig(filename)
    plt.close()
    # plt.show()
