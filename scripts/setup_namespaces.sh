#!/bin/bash
set -ex

# NOTE: Framework and setup is similar to that found here: https://github.com/xvzcf/pq-tls-benchmark 

### --- Variables --- ###

SERVER_NS=server_namespace
SERVER_VETH_LL_ADDR=00:00:00:00:00:02
SERVER_VETH=server_veth

CLIENT_NS=client_namespace
CLIENT_VETH_LL_ADDR=00:00:00:00:00:01
CLIENT_VETH=client_veth

### --- Namespace setup --- ###

# Create 
ip netns add ${SERVER_NS}
ip netns add ${CLIENT_NS}

# Add veth
ip link add \
   name ${SERVER_VETH} \
   address ${SERVER_VETH_LL_ADDR} \
   netns ${SERVER_NS} type veth \
   peer name ${CLIENT_VETH} \
   address ${CLIENT_VETH_LL_ADDR} \
   netns ${CLIENT_NS}

# Setup
ip netns exec ${SERVER_NS} \
   ip link set dev ${SERVER_VETH} up
ip netns exec ${SERVER_NS} \
   ip link set dev lo up
ip netns exec ${SERVER_NS} \
   ip addr add 10.0.0.1/24 dev ${SERVER_VETH}

ip netns exec ${CLIENT_NS} \
   ip addr add 10.0.0.2/24 dev ${CLIENT_VETH}
ip netns exec ${CLIENT_NS} \
   ip link set dev lo up
ip netns exec ${CLIENT_NS} \
   ip link set dev ${CLIENT_VETH} up
ip netns exec ${CLIENT_NS} \
   ip link set dev lo up

ip netns exec ${SERVER_NS} \
   ip neigh add 10.0.0.2 \
      lladdr ${CLIENT_VETH_LL_ADDR} \
      dev ${SERVER_VETH}
ip netns exec ${CLIENT_NS} \
   ip neigh add 10.0.0.1 \
      lladdr ${SERVER_VETH_LL_ADDR} \
      dev ${CLIENT_VETH}

# Turning off optimisations
ip netns exec ${CLIENT_NS} \
   ethtool -K ${CLIENT_VETH} gso off gro off tso off

ip netns exec ${SERVER_NS} \
   ethtool -K ${SERVER_VETH} gso off gro off tso off

# Enabling netem
ip netns exec ${CLIENT_NS} \
   tc qdisc add \
      dev ${CLIENT_VETH} \
      root netem
ip netns exec ${SERVER_NS} \
   tc qdisc add \
      dev ${SERVER_VETH} \
      root netem
