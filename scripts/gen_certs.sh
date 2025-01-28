#!/bin/bash
set -ex

ROOT_DIR=$(pwd)
FINAL_BUILD_DIR="${ROOT_DIR}/provider_build"
NGINX_CONF_DIR="${FINAL_BUILD_DIR}/nginx/conf"
OPENSSL="${FINAL_BUILD_DIR}/bin/openssl"

# Set environment vars for OQS provider
export OPENSSL_CONF="${FINAL_BUILD_DIR}/ssl/openssl.cnf"
export OPENSSL_MODULES="${FINAL_BUILD_DIR}/lib"

# Create certificate directory
mkdir -p "${NGINX_CONF_DIR}/certs"

# Generate certificates for each algorithm
for SIG in "mldsa44" "mldsa65" "mldsa87" "sphincssha2128fsimple" "falcon512" "falcon1024" "mayo1" "mayo3" "mayo5" "CROSSrsdp128balanced"; do
    # Generate Root CA (self-signed)
    "${OPENSSL}" req -x509 -new \
        -newkey "${SIG}" \
        -keyout "${NGINX_CONF_DIR}/certs/${SIG}_RootCA.key" \
        -out "${NGINX_CONF_DIR}/certs/${SIG}_RootCA.crt" \
        -nodes \
        -subj "/CN=OQS Root CA ${SIG}" \
        -days 730

    # Generate intermediate CA CSR
    "${OPENSSL}" req -new \
        -newkey "${SIG}" \
        -keyout "${NGINX_CONF_DIR}/certs/${SIG}_IntermediateCA.key" \
        -out "${NGINX_CONF_DIR}/certs/${SIG}_IntermediateCA.csr" \
        -nodes \
        -subj "/CN=OQS Intermediate CA ${SIG}"

    # Sign intermediate CA with Root CA
    "${OPENSSL}" x509 -req \
        -in "${NGINX_CONF_DIR}/certs/${SIG}_IntermediateCA.csr" \
        -out "${NGINX_CONF_DIR}/certs/${SIG}_IntermediateCA.crt" \
        -CA "${NGINX_CONF_DIR}/certs/${SIG}_RootCA.crt" \
        -CAkey "${NGINX_CONF_DIR}/certs/${SIG}_RootCA.key" \
        -CAcreateserial \
        -days 730 \
        -extfile <(printf "basicConstraints=CA:TRUE\nkeyUsage=keyCertSign,cRLSign")

    # Generate server csr
    "${OPENSSL}" req -new \
        -newkey "${SIG}" \
        -keyout "${NGINX_CONF_DIR}/certs/${SIG}_server.key" \
        -out "${NGINX_CONF_DIR}/certs/${SIG}_server.csr" \
        -nodes \
        -subj "/CN=OQS Server ${SIG}"

    # Sign server cert with intermediaet CA
    "${OPENSSL}" x509 -req \
        -in "${NGINX_CONF_DIR}/certs/${SIG}_server.csr" \
        -out "${NGINX_CONF_DIR}/certs/${SIG}_server.crt" \
        -CA "${NGINX_CONF_DIR}/certs/${SIG}_IntermediateCA.crt" \
        -CAkey "${NGINX_CONF_DIR}/certs/${SIG}_IntermediateCA.key" \
        -CAcreateserial \
        -days 365 \
        -extfile <(printf "extendedKeyUsage=serverAuth")

    # Create a certificate chain file (server cert + intermediat cert + root cert)
    cat \
        "${NGINX_CONF_DIR}/certs/${SIG}_server.crt" \
        "${NGINX_CONF_DIR}/certs/${SIG}_IntermediateCA.crt" \
        "${NGINX_CONF_DIR}/certs/${SIG}_RootCA.crt" \
        > "${NGINX_CONF_DIR}/certs/${SIG}_fullchain.crt"

done
