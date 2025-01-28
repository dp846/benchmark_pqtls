# Algorithms Experimented With

Below lists a summary of all algorithms that were experimented with in this project's benchmarks.

| liboqs Algorithm Name | Status                                          | Signature Size <br>(bytes) | Public Key Size (bytes) |
| --------------------- | :---------------------------------------------- | -------------------------- | ----------------------- |
| mldsa44               | Standardised                                    | 2420                       | 1,312                   |
| mldsa65               | Standardised                                    | 3309                       | 1,952                   |
| mldsa87               | Standardised                                    | 4627                       | 2,592                   |
| sphincssha2128fsimple | Standardised*                                   | 17088                      | 32                      |
| falcon512             | Selected for standardisation** (in process)     | 752                        | 897                     |
| falcon1024            | Selected for standardisation** (in process)     | 1462                       | 1,793                   |
| mayo1                 | Round 2 of additional <br>signature competition | 321                        | 1168                    |
| mayo3                 | Round 2 of additional <br>signature competition | 577                        | 2656                    |
| mayo5                 | Round 2 of additional <br>signature competition | 838                        | 5008                    |
| CROSSrsdp128balanced  | Round 2 of additional <br>signature competition | 12912                      | 77                      |

\*Standardised as SLH-DSA, though this change is not yet present in liboqs.

\*\*To be standardised in future as FN-DSA.