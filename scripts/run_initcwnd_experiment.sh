#!/bin/bash
set -ex

### --- Setting variables --- ###

# Paths
ROOT_DIR=$(pwd)
FINAL_BUILD_DIR="${ROOT_DIR}/provider_build"
NGINX_APP="${FINAL_BUILD_DIR}/nginx/sbin/nginx"
NGINX_CONF_DIR="${FINAL_BUILD_DIR}/nginx/conf"
OPENSSL_BIN="${FINAL_BUILD_DIR}/bin/openssl"

# Inherited env vars (saves passing around provider paths all the time)
export OPENSSL_CONF="${FINAL_BUILD_DIR}/ssl/openssl.cnf"
export OPENSSL_MODULES="${FINAL_BUILD_DIR}/lib"

# Controls the initcwnd value range in experiments 
MAX_INITCWND=100
INTERVAL=5
STARTING_VAL=5

### --- Setup --- ###

# Network namespace setup
ip netns exec server_namespace "${NGINX_APP}" -s stop || true

# TCP configuration
ip netns exec client_namespace sysctl net.ipv4.tcp_no_metrics_save=1

# Build C handshake executable (will be run from the client namespace)
cd src
cmake -B build && cmake --build build
cd ..

### --- Experiment logic --- ###

# Loop over all initcwnd values
for initcwnd_val in $(seq "$STARTING_VAL" "$INTERVAL" "$MAX_INITCWND"); do
    
    # Setting the new initcwnd value for the route
    # NOTE: I set them on both the client and the server here but the server is the one it matters for
    echo "Setting initcwnd value to: $initcwnd_val"
    ip netns exec client_namespace ip route change 10.0.0.0/24 dev client_veth proto kernel scope link src 10.0.0.2 initcwnd $initcwnd_val
    ip netns exec server_namespace ip route change 10.0.0.0/24 dev server_veth proto kernel scope link src 10.0.0.1 initcwnd $initcwnd_val

    # Now loop through every signature algorithm
    for SIG in "mldsa44" "mldsa65" "mldsa87" "sphincssha2128fsimple" "falcon512" "falcon1024" "mayo1" "mayo3" "mayo5" "CROSSrsdp128balanced"; do

        # Update nginx config using the certificate
        sed "s|??SERVER_CERT??|certs/${SIG}_fullchain.crt|g; \
            s|??SERVER_KEY??|certs/${SIG}_server.key|g" \
            nginx.conf > "${NGINX_CONF_DIR}/nginx.conf"

        # Start nginx in server namespace
        echo "OPENSSL_CONF=$OPENSSL_CONF"
        echo "OPENSSL_MODULES=$OPENSSL_MODULES"
        ip netns exec server_namespace "${NGINX_APP}"
        $OPENSSL_BIN list -providers -verbose

        sleep 3
        
        # Begin experiment timings in python script (takes in a signature alg and an initcwnd value)
        python3 scripts/time_handshakes.py "${SIG}" $initcwnd_val initcwnd

        sleep 3

        # Cleanup
        ip netns exec server_namespace "${NGINX_APP}" -s stop
        rm "${NGINX_CONF_DIR}/nginx.conf"

    done
done

exit
