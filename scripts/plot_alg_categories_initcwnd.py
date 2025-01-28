import os
import pandas as pd
import matplotlib.pyplot as plt
import re
import numpy as np

# Process the given csv for the specified packet loss
def load_and_process(filename, packet_loss):
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
            if loss_val == packet_loss:
                try:
                    numeric_vals = [float(x) for x in parts[1:] if x.strip() != '']
                    median_val = pd.Series(numeric_vals).median() if numeric_vals else None
                    rows.append({'loss': loss_val, 'median': median_val})
                except ValueError:
                    continue

    return pd.DataFrame(rows).sort_values(by='loss')

# extract num using regex
def extract_number(text, prefix):
    match = re.search(rf'{prefix}([\d.]+)', text)
    return match.group(1) if match else None


def plot_for_loss(packet_loss):
    RELATIVE_DATA_DIR = 'data'
    ROLLING_WINDOW = 1 # NOTE: if results are too volatile, I may have to increase this. For now I think results look mostly fine.
    results = {}

    for initcwnd_dir in sorted(os.listdir(RELATIVE_DATA_DIR)):
        full_initcwnd_path = os.path.join(RELATIVE_DATA_DIR, initcwnd_dir)
        if os.path.isdir(full_initcwnd_path):
            initcwnd_value = extract_number(initcwnd_dir, 'initcwnd=')
            if not initcwnd_value:
                continue
            initcwnd_value = int(float(initcwnd_value))
            for latency_dir in sorted(os.listdir(full_initcwnd_path)):
                full_latency_path = os.path.join(full_initcwnd_path, latency_dir)
                if os.path.isdir(full_latency_path):
                    latency_value = extract_number(latency_dir, 'latency=')
                    if not latency_value:
                        continue
                    for filename in os.listdir(full_latency_path):
                        if filename.endswith('.csv'):
                            sig_alg, _ = filename.rsplit('.', 1)
                            if sig_alg.lower() == "sphincssha2128ssimple":
                                continue  # NOTE: as a self reminder, I am excluding this algorithm for time being due to issues
                            df = load_and_process(os.path.join(full_latency_path, filename), packet_loss)
                            if df.empty:
                                continue
                            key = (sig_alg, float(latency_value))
                            if key not in results:
                                results[key] = {}
                            results[key][initcwnd_value] = df['median'].median()

    # Categorise by standardised algs and candidate algs for plotting
    set1_prefixes = ['falcon', 'sphincs', 'mldsa']
    set2_prefixes = ['cross', 'mayo']
    set1_results = {}
    set2_results = {}

    for (sig_alg, latency), cwnd_data in results.items():
        alg_lower = sig_alg.lower()
        if any(p in alg_lower for p in set1_prefixes):
            set1_results[(sig_alg, latency)] = cwnd_data
        elif any(p in alg_lower for p in set2_prefixes):
            set2_results[(sig_alg, latency)] = cwnd_data

    def plot_grouped_results(group_results, title, packet_loss):

        # Line styling used is made to match up with base signature algorithms
        if title == 'Standardised Signature Schemes':
            line_styles = [  'x:',   's--',   'x:',    'o-',    'o-',    'o-']
            custom_colors = ['lime', 'indigo', 'darkgreen',  'red', 'gold', 'orange'] # standardised
        else:
            line_styles = ['o-', 'o-', 'o-', 'x--']
            custom_colors = ['purple', 'blue', 'red', 'green'] # candidates

        plt.figure(figsize=(8, 5))
        plot_idx = 0

        for (sig_alg, latency), cwnd_data in group_results.items():
            sorted_cwnd = sorted(cwnd_data.keys())
            median_times = [cwnd_data[c] for c in sorted_cwnd]

            # NOTE: Adding a very small amount of noise to the data was found to make graphs with lots of overlapping 
            # values slightly more readable.
            noise = np.random.normal(loc=0, scale=0.75, size=len(median_times))
            noisy_median_times = [m + n if m is not None else None for m, n in zip(median_times, noise)]
            noisy_median_series = pd.Series(noisy_median_times).rolling(window=ROLLING_WINDOW, center=True).median()

            style = line_styles[plot_idx % len(line_styles)]
            color = custom_colors[plot_idx % len(custom_colors)]

            plt.plot(
                sorted_cwnd,
                noisy_median_series,
                style,
                label=f'{sig_alg}',
                color=color,
                linewidth=2,
                markersize=6,
                alpha=0.9
            )
            plot_idx += 1

        plt.title(f'{packet_loss}% Packet Loss', fontsize=16)
        plt.xlabel('initcwnd size (MSS)', fontsize=14)
        plt.ylabel('Median Handshake Time (ms)', fontsize=14)
        plt.grid(True, alpha=0.3)

        # Sort alphabetically and force key to top-right
        handles, labels = plt.gca().get_legend_handles_labels()
        sorted_pairs = sorted(zip(labels, handles), key=lambda x: x[0])
        sorted_labels, sorted_handles = zip(*sorted_pairs)
        plt.legend(sorted_handles, sorted_labels, fontsize=14, loc='upper right')

        plt.xticks(np.arange(min(sorted_cwnd) - 5, max(sorted_cwnd) + 1, step=10))
        plt.tight_layout()

        os.makedirs('./plots', exist_ok=True)
        plot_filename = f"./plots/{title.replace(' ', '_').lower()}_{packet_loss}.png"
        plt.savefig(plot_filename)
        plt.close()
        # plt.show() # To show instead of save

    plot_grouped_results(set1_results, 'Standardised Signature Schemes', packet_loss)
    plot_grouped_results(set2_results, 'Candidate Signature Schemes', packet_loss)


# Packet loss rates to analyse
# NOTE: this can be changed. Thought these were a nice separation apart and tell a good story..
packet_loss_values = [0, 6, 12, 18]

for loss in packet_loss_values:
    print(f"\n--- Plotting for {loss}% packet loss ---")
    plot_for_loss(loss)
