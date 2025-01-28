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

# MTU values to experiment with
MTU_VALUES=(1500 3000 9000)

# Corresponding INITCWND values, following inverse proportional relationship with MTU
INITCWND_VALS=(12 6 2)

### --- Setup --- ###

# Make sure nginx isn't running from previous run
ip netns exec server_namespace "${NGINX_APP}" -s stop || true

# TCP configuration to avoid cached metrics
ip netns exec client_namespace sysctl net.ipv4.tcp_no_metrics_save=1

# Build the handshake timing binary
cd src
cmake -B build && cmake --build build
cd ..

### --- Experiment Loop --- ###

for idx in ${!MTU_VALUES[@]}; do
    MTU=${MTU_VALUES[$idx]}
    INITCWND_VAL=${INITCWND_VALS[$idx]}

    echo "Setting initcwnd value to: $INITCWND_VAL"
    echo "Setting MTU value to: $MTU"

    # Set MTU in both namespaces
    ip netns exec client_namespace ip link set dev client_veth mtu $MTU
    ip netns exec server_namespace ip link set dev server_veth mtu $MTU

    # Setting the new initcwnd value for the route
    # NOTE: I set them on both the client and the server here but the server is the one it matters for
    ip netns exec client_namespace ip route change 10.0.0.0/24 dev client_veth proto kernel scope link src 10.0.0.2 initcwnd $INITCWND_VAL
    ip netns exec server_namespace ip route change 10.0.0.0/24 dev server_veth proto kernel scope link src 10.0.0.1 initcwnd $INITCWND_VAL

    # Now loop through every signature algorithm
    for SIG in "mldsa44" "mldsa65" "mldsa87" "sphincssha2128fsimple" "falcon512" "falcon1024" "mayo1" "mayo3" "mayo5" "CROSSrsdp128balanced"; do

        # Update nginx config using the certificate
        sed "s|??SERVER_CERT??|certs/${SIG}_fullchain.crt|g; \
             s|??SERVER_KEY??|certs/${SIG}_server.key|g" \
            nginx.conf > "${NGINX_CONF_DIR}/nginx.conf"

        # Start nginx in server namespce
        ip netns exec server_namespace "${NGINX_APP}"
        $OPENSSL_BIN list -providers -verbose

        # Begin experiment timings in python script
        python3 scripts/time_handshakes.py "${SIG}" "${MTU}" mtu

        # Cleanup
        ip netns exec server_namespace "${NGINX_APP}" -s stop
        rm "${NGINX_CONF_DIR}/nginx.conf"
        
        sleep 1

    done
done

exit
