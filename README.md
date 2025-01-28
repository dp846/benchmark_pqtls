# benchmark_pqtls
Repository to conduct benchmarks of post-quantum TLS handshakes using some of the signature schemes available in liboqs. Check `ALGORITHMS.md` for details on which were experimented with.

This study adapts a framework by Paquin et al:

Christian Paquin, Douglas Stebila, and Goutam Tamvada. *Benchmarking Post-Quantum Cryptography in TLS*. IACR Cryptology ePrint Archive, Report 2019/1447. [https://eprint.iacr.org/2019/1447](https://eprint.iacr.org/2019/1447).

## Useful Information

- Linux Kernel Version in use: 6.8.0-51-generic
- Experiments run on Ubuntu 22.04

## Building the Provider

From the repository root, run the `install_provider.sh` script:

```
./install_provider.sh
```

Once this is done, `third_party` will be populated with the source code from each of the dependencies of this project:
- OpenSSL
- liboqs
- oqs-provider

`provider_build` will be populated with the installed library artifacts. To run the provider, two environment variables must be set:
```
export OPENSSL_CONF=<path-to-repo>/benchmark_pqtls/provider_build/ssl/openssl.cnf
export OPENSSL_MODULES=<path-to-repo>/benchmark_pqtls/provider_build/lib
```

The provider should then be able to be used. To test this, run:
```
./provider_build/bin/openssl list -providers -verbose -provider oqsprovider  
```

## Supported Algorithms

The supported signature algorithms can be seen via:
```
./provider_build/bin/openssl list -signature-algorithms -provider oqsprovider
```

## Provider Not Found

If the provider is not being found, this is likely due to `OPENSSL_MODULES` or `OPENSSL_CONF` not being set correctly. To avoid setting this every time, the paths to the resulting provider build can be added to `~/.bashrc`.

## Running the Experiments

To run the experiments, all scripts should be executed from the repo root, requiring elevated priveleges via `sudo`.

Once the provider is successfully built (see the above steps), run:

1) `sudo ./scripts/gen_certs.sh`: to generate certificate chain files for each algorithm.

2) `sudo ./scripts/setup_namespaces.sh`: to configure the namespace for both expreiments.

3) `sudo ./scripts/run_initcwnd_experiment.sh`: to run the TCP initial congestion window experiment or...

4) `sudo ./scripts/run_mtu_experiment.sh`: to run the MTU experiment

5) `sudo ./scripts/cleanup.sh`: to tear down the namespaces and experiment artefacts

NOTE: depending on the specs of the host system, the experiments may take a long time to run, due to the large number of permutations of handshakes of a latency that is treated as a delay on the host system (~1 week of runtime for the initcwnd experiment and ~2 days for the MTU experiment).

## Troubleshooting

If any assistance is required with provider setup, there is some documentation on the OQS OpenSSL Provider repo. Otherwise, for specific help with this framework feel free to contact the repository owner: dp846@bath.ac.uk
