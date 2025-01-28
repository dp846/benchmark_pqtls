# Simple Commands to Run a PQ Client / Server Connection

```
./provider_build/bin/openssl req -x509 -new -newkey dilithium3 -keyout dilithium3_CA.key -out dilithium3_CA.crt -nodes -subj "/CN=test CA" -days 365 -config provider_build/ssl/openssl.cnf

openssl genpkey -algorithm dilithium3 -out dilithium3_srv.key -config provider_build/ssl/openssl.cnf

./provider_build/bin/openssl req -new -newkey dilithium3 -keyout certs/dilithium3_srv.key -out certs/dilithium3_srv.csr -nodes -subj "/CN=test server" -config provider_build/ssl/openssl.cnf

./provider_build/bin/openssl x509 -req -in certs/dilithium3_srv.csr -out certs/dilithium3_srv.crt -CA certs/dilithium3_CA.crt -CAkey certs/dilithium3_CA.key -CAcreateserial -days 365



./provider_build/bin/openssl s_server -cert certs/dilithium3_srv.crt -key certs/dilithium3_srv.key -www -tls1_3 -groups kyber768:frodo640shake
```

In a new terminal, set up the OpenSSL module and config environment variables (see the setup_provider.sh script) and run:
```
export OPENSSL_CONF=provider_build/ssl/openssl.cnf
export OPENSSL_MODULES=provider_build/lib
./provider_build/bin/openssl s_client -groups frodo640shake -CAfile certs/dilithium3_CA.crt
```
