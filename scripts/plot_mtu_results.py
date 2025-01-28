import os
import pandas as pd
import matplotlib.pyplot as plt
import re
import numpy as np

# Only MTU values to include
allowed_mtus = {1500, 3000, 4500, 6000, 7500, 9000}

def add_random_variation(series, percent=0.02):
    """
    Apply a small random variation to make overlapping lines easier to read.
    """
    noise = np.random.uniform(1 - percent, 1 + percent, size=len(series))
    return series * noise

def extract_number(text, prefix):
    match = re.search(rf'{prefix}([\d.]+)', text)
    return match.group(1) if match else None

def load_data():
    results = {}

    RELATIVE_DATA_DIR = 'data'

    for mtu_dir in sorted(os.listdir(RELATIVE_DATA_DIR)):
        full_mtu_path = os.path.join(RELATIVE_DATA_DIR, mtu_dir)
        mtu_val = extract_number(mtu_dir, 'mtu=')
        if not mtu_val or not os.path.isdir(full_mtu_path):
            continue
        mtu_val = int(float(mtu_val))

        for latency_dir in os.listdir(full_mtu_path):
            full_latency_path = os.path.join(full_mtu_path, latency_dir)
            if not os.path.isdir(full_latency_path):
                continue

            for filename in os.listdir(full_latency_path):
                if not filename.endswith('.csv'):
                    continue
                sig_alg, _ = filename.rsplit('.', 1)
                if sig_alg.lower() == "sphincssha2128ssimple":
                    continue # NOTE: as a self reminder, I am excluding this algorithm for time being due to issues
                filepath = os.path.join(full_latency_path, filename)

                with open(filepath, 'r') as f:
                    for line in f:
                        if not line.strip():
                            continue
                        parts = line.strip().split(',')
                        try:
                            pkt_loss = float(parts[0])
                            times = [float(x) for x in parts[1:] if x.strip()]
                            median = pd.Series(times).median() if times else None
                            pct90 = pd.Series(times).quantile(0.90) if times else None
                        except ValueError:
                            continue

                        key = (sig_alg, pkt_loss)
                        if key not in results:
                            results[key] = {}
                        if mtu_val not in results[key]:
                            results[key][mtu_val] = {'median': None, '90th': None}
                        results[key][mtu_val]['median'] = median
                        results[key][mtu_val]['90th'] = pct90

    return results

def plot_by_signature(results, metric='median'):
    # Organise by sig algorithm
    grouped = {}
    for (sig_alg, pkt_loss), mtu_data in results.items():
        if sig_alg not in grouped:
            grouped[sig_alg] = {}
        grouped[sig_alg][pkt_loss] = mtu_data

    mtu_to_initcwnd = {
        1500: 12,
        3000: 6,
        9000: 2,
    }

    for sig_alg, pkt_loss_data in grouped.items():
        plt.figure(figsize=(8, 5))

        line_styles = ['o-', 's--', 'd:']
        custom_colors = ['red', 'green', 'blue']
        style_idx = 0

        for mtu in sorted(mtu_to_initcwnd.keys()):
            x_vals = []
            y_vals = []

            for pkt_loss in sorted(pkt_loss_data.keys()):
                mtu_data = pkt_loss_data[pkt_loss]
                if mtu in mtu_data and mtu_data[mtu][metric] is not None:
                    x_vals.append(pkt_loss)
                    y_vals.append(mtu_data[mtu][metric])

            if x_vals and y_vals:
                if metric == 'median':
                    series = pd.Series(add_random_variation(pd.Series(y_vals)))
                else:
                    series = pd.Series(y_vals)  # No jitter needed for 90th perc
                plt.plot(
                    x_vals, series,
                    line_styles[style_idx % len(line_styles)],
                    label=f'MTU={mtu} (initcwnd={mtu_to_initcwnd[mtu]})',
                    color=custom_colors[style_idx % len(custom_colors)],
                    linewidth=2.5,
                    markersize=7,
                    alpha=0.75
                )
                style_idx += 1

        plt.xlabel('Packet Loss (%)', fontsize=14)
        plt.ylabel('Handshake Time (ms)', fontsize=14)
        title_metric = "Median" if metric == 'median' else "90th Percentile"
        plt.title(f'{sig_alg} - {title_metric} Handshake Time', fontsize=16)
        plt.grid(True, alpha=0.3)
        plt.legend(fontsize=15, loc='upper left')
        plt.xticks(list(range(0, 21, 2)))
        plt.tight_layout()

        os.makedirs("plots", exist_ok=True)
        plt.savefig(f"plots/{sig_alg.lower()}_mtu_{metric}.png")
        plt.close()

def main():
    results = load_data()
    plot_by_signature(results, metric='median')
    plot_by_signature(results, metric='90th')

if __name__ == '__main__':
    main()
