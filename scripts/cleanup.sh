#!/bin/bash
set -ex

### --- Remove C binary executable --- ###

rm -rf src/build

### --- Remove namespaces --- ###

ip netns del client_namespace
ip netns del server_namespace
