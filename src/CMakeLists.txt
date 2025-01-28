cmake_minimum_required(VERSION 3.20)
project(time_handshake C)

### --- Custom OpenSSL path using the installed provider build --- ###

set(OPENSSL_CUSTOM_DIR "${CMAKE_SOURCE_DIR}/../provider_build")
set(OPENSSL_INCLUDE_DIR "${OPENSSL_CUSTOM_DIR}/include")
set(OPENSSL_LIB_DIR "${OPENSSL_CUSTOM_DIR}/lib")

# Manually specify libraries
# TODO: there is probably a better future-proof way of doing this but this will do for the time being
set(OPENSSL_SSL_LIB "${OPENSSL_LIB_DIR}/libssl.a")
set(OPENSSL_CRYPTO_LIB "${OPENSSL_LIB_DIR}/libcrypto.a")

# Verify files exist
if(NOT EXISTS ${OPENSSL_SSL_LIB} OR NOT EXISTS ${OPENSSL_CRYPTO_LIB})
    message(FATAL_ERROR "OpenSSL libraries not found in ${OPENSSL_LIB_DIR}")
endif()

### --- Create executable --- ###

add_executable(time_handshake time_handshake.c)

# Include directories
target_include_directories(time_handshake PRIVATE ${OPENSSL_INCLUDE_DIR})

# Link directories and libraries
target_link_directories(time_handshake PRIVATE ${OPENSSL_LIB_DIR})
target_link_libraries(time_handshake PRIVATE ${OPENSSL_SSL_LIB} ${OPENSSL_CRYPTO_LIB})

# Check libs
message(STATUS "Using OpenSSL from: ${OPENSSL_CUSTOM_DIR}")
message(STATUS "OpenSSL includes: ${OPENSSL_INCLUDE_DIR}")
message(STATUS "OpenSSL libraries: ${OPENSSL_SSL_LIB} ${OPENSSL_CRYPTO_LIB}")
