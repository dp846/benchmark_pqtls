### --- Imports --- ###

import csv
import os
import subprocess
import sys
from multiprocessing import Pool

### --- Config --- ###

POOL_SIZE = 40
MEASUREMENTS_PER_TIMER = 150
TIMERS = 4

def run_subprocess(command, working_dir='.'):
    """
    Run a subprocess command and return its stdout  as a string.
    """

    result = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=working_dir
    )

    if result.stderr:
        print(result.stderr.decode('utf-8'))

    # Raise exception if return code is nonzero
    result.check_returncode()  

    return result.stdout.decode('utf-8')

def change_qdisc(ns, dev, pkt_loss, delay):
    """
    Change traffic control (qdisc) settings for a given network namespace and device.
    """

    base_cmd = ['ip', 'netns', 'exec', ns, 'tc', 'qdisc', 'change',
                'dev', dev, 'root', 'netem', 'limit', '1000']
    
    # Only add the packet loss param if non zero
    if pkt_loss != 0:
        base_cmd.extend(['loss', f'{pkt_loss}%'])

    base_cmd.extend(['delay', delay, 'rate', '1000mbit'])

    print(" > " + " ".join(base_cmd))
    run_subprocess(base_cmd)

def time_handshake(sig_alg, measurements):
    """
    Run the C executable 'time_handshake' in the client namespace with the given
    signature algorithm and measurement count.
    The command output is expected to be a comma-separated list of handshake timings.
    """

    command = [
        'ip', 'netns', 'exec', 'client_namespace',
        './src/build/time_handshake', sig_alg, str(measurements)
    ]
    print(" > " + " ".join(command))
    result = run_subprocess(command)
    # Parse the comma-separated float values
    return [float(x) for x in result.strip().split(',') if x]

def run_timers(sig_alg, timer_pool, timers, measurements):
    """
    Launch multiple handshake measurements concurrently and flatten the results.
    """
    results_nested = timer_pool.starmap(time_handshake, [(sig_alg, measurements)] * timers)
    return [item for sublist in results_nested for item in sublist]

def main():
    # Argument parsing
    if len(sys.argv) < 4:
        print(f"Usage: {sys.argv[0]} <signature_algorithm> <value> <mode: initcwnd|mtu>")
        sys.exit(1)
    
    sig_alg = sys.argv[1]
    experiment_value = sys.argv[2]  # Could be initcwnd or MTU value
    mode = sys.argv[3].lower()

    if mode not in ["initcwnd", "mtu"]:
        print("Error: mode must be either 'initcwnd' or 'mtu'")
        sys.exit(1)

    timer_pool = Pool(processes=POOL_SIZE)

    for latency_ms in ['20.000ms']:  # Can be expanded to use more latencies - 

        # Create directory depending on experiment mode
        if mode == "initcwnd":
            output_dir = f"data/initcwnd={experiment_value}/latency={latency_ms}"
        elif mode == "mtu":
            output_dir = f"data/mtu={experiment_value}/latency={latency_ms}"

        os.makedirs(output_dir, exist_ok=True)

        # Set qdisc with no loss initially
        change_qdisc('client_namespace', 'client_veth', 0, delay=latency_ms)
        change_qdisc('server_namespace', 'server_veth', 0, delay=latency_ms)

        csv_filename = f"{output_dir}/{sig_alg}.csv"
        with open(csv_filename, 'w', newline='') as csvfile:
            csv_out = csv.writer(csvfile)

            for pkt_loss in [0, 0.1, 1, 2]:
                change_qdisc('client_namespace', 'client_veth', pkt_loss, delay=latency_ms)
                change_qdisc('server_namespace', 'server_veth', pkt_loss, delay=latency_ms)
                results = run_timers(sig_alg, timer_pool, timers=4, measurements=50)
                results.insert(0, pkt_loss)
                csv_out.writerow(results)

            for pkt_loss in [4, 6, 8, 10]:
                change_qdisc('client_namespace', 'client_veth', pkt_loss, delay=latency_ms)
                change_qdisc('server_namespace', 'server_veth', pkt_loss, delay=latency_ms)
                results = run_timers(sig_alg, timer_pool, timers=4, measurements=200)
                results.insert(0, pkt_loss)
                csv_out.writerow(results)

            for pkt_loss in [12, 14]:
                change_qdisc('client_namespace', 'client_veth', pkt_loss, delay=latency_ms)
                change_qdisc('server_namespace', 'server_veth', pkt_loss, delay=latency_ms)
                results = run_timers(sig_alg, timer_pool, timers=4, measurements=300)
                results.insert(0, pkt_loss)
                csv_out.writerow(results)

            for pkt_loss in [16, 18]:
                change_qdisc('client_namespace', 'client_veth', pkt_loss, delay=latency_ms)
                change_qdisc('server_namespace', 'server_veth', pkt_loss, delay=latency_ms)
                results = run_timers(sig_alg, timer_pool, timers=4, measurements=400)
                results.insert(0, pkt_loss)
                csv_out.writerow(results)


    timer_pool.close()
    timer_pool.join()


if __name__ == '__main__':
    main()