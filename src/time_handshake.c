#define _POSIX_C_SOURCE 199309L
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <sys/time.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <unistd.h>

#include <openssl/provider.h>
#include <openssl/ssl.h>
#include <openssl/err.h>
#include <openssl/crypto.h>

#define SERVER_IP "10.0.0.1"
#define SERVER_PORT 4433


// Get current time in secs
static double get_time(void) {
    struct timeval tv;
    gettimeofday(&tv, NULL);
    return (double)tv.tv_sec + (double)tv.tv_usec / 1000000;
}

int main(int argc, char *argv[]) {
    if (argc < 3) {
        fprintf(stderr, "Usage: %s <sig_alg> <measurements>\n", argv[0]);
        return 1;
    }
    
    const char *sig_alg = argv[1];
    int measurements = atoi(argv[2]);
    if (measurements <= 0)
        measurements = 1;

    // Dynamically build CA file path based on the sig algorithm.
    char ca_file[256];
    snprintf(ca_file, sizeof(ca_file), "provider_build/nginx/conf/certs/%s_RootCA.crt", sig_alg);

    // Initialisations
    SSL_library_init();
    SSL_load_error_strings();
    OpenSSL_add_ssl_algorithms();

    OSSL_LIB_CTX *libctx = OSSL_LIB_CTX_new();
    if (!libctx) {
        fprintf(stderr, "Failed to create OpenSSL libctx\n");
        return 1;
    }

    // Load providers: default and oqsprovider
    OSSL_PROVIDER *defaultprov = OSSL_PROVIDER_load(libctx, "default");
    if (!defaultprov) {
        fprintf(stderr, "Failed to load default provider\n");
        ERR_print_errors_fp(stderr);
        OSSL_LIB_CTX_free(libctx);
        return 1;
    }
    OSSL_PROVIDER *oqsprov = OSSL_PROVIDER_load(libctx, "oqsprovider");
    if (!oqsprov) {
        fprintf(stderr, "Failed to load OQS provider\n");
        ERR_print_errors_fp(stderr);
        OSSL_PROVIDER_unload(defaultprov);
        OSSL_LIB_CTX_free(libctx);
        return 1;
    }

    // Create SSL context for TLS client operations
    SSL_CTX *ctx = SSL_CTX_new_ex(libctx, NULL, TLS_client_method());
    if (!ctx) {
        fprintf(stderr, "Failed to create SSL_CTX\n");
        ERR_print_errors_fp(stderr);
        goto cleanup;
    }
    // Load CA certificate to verify server certificate
    if (!SSL_CTX_load_verify_locations(ctx, ca_file, NULL)) {
        fprintf(stderr, "Failed to load CA file: %s\n", ca_file);
        ERR_print_errors_fp(stderr);
        goto cleanup;
    }

    // Loop for the specified number of handshake measurements
    for (int i = 0; i < measurements; i++) {
        // Create a new TCP socket
        int sock = socket(AF_INET, SOCK_STREAM, 0);
        if (sock < 0) {
            perror("socket");
            goto cleanup;
        }

        // Set up server address
        struct sockaddr_in addr;
        memset(&addr, 0, sizeof(addr));
        addr.sin_family = AF_INET;
        addr.sin_port = htons(SERVER_PORT);
        addr.sin_addr.s_addr = inet_addr(SERVER_IP);

        // Connect to server
        if (connect(sock, (struct sockaddr*)&addr, sizeof(addr)) != 0) {
            perror("connect");
            close(sock);
            goto cleanup;
        }

        // Create new SSL obj
        SSL *ssl = SSL_new(ctx);
        if (!ssl) {
            fprintf(stderr, "Failed to create SSL object\n");
            ERR_print_errors_fp(stderr);
            close(sock);
            goto cleanup;
        }
        SSL_set_fd(ssl, sock);

        // Measure the time taken for SSL_connect (the  TLS handshake)
        double start = get_time();
        int ret = SSL_connect(ssl);
        double end = get_time();

        if (ret != 1) {
            fprintf(stderr, "Handshake failed on measurement %d\n", i);
            ERR_print_errors_fp(stderr);
            SSL_free(ssl);
            close(sock);
            goto cleanup;
        }

        // Output the handshake time in ms
        // If this is not the first measurement, prepend a comma first to build up a string of 
        // lots of measuremnets
        double handshake_time_ms = (end - start) * 1000.0;
        if (i > 0)
            printf(",");
        printf("%.6f", handshake_time_ms);

        // Cleanup
        SSL_shutdown(ssl);
        SSL_free(ssl);
        close(sock);
    }
    printf("\n");

cleanup:
    if (ctx)
        SSL_CTX_free(ctx);
    OSSL_PROVIDER_unload(oqsprov);
    OSSL_PROVIDER_unload(defaultprov);
    OSSL_LIB_CTX_free(libctx);
    EVP_cleanup();
    return 0;
}
