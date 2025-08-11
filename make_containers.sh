#!/bin/bash


# This is meant to setup the docker containers and networks for testing
# automatically

# This will assume the Dockerfile.nat file already exists to build
# the docker image.


# We start with the subnets

# Clear all Docker items before (re)creating them


# Delete client containers
if docker ps -a --format '{{.Names}}' | grep -q '^rendezvous$'; then
	# Note, used Deepseek to help with syntax of check
	echo "rendezvous exists, stopping and deleting"
	docker stop rendezvous
	docker rm rendezvous
	echo "rendezvous successfully purged"
fi


# Delete client containers
if docker ps -a --format '{{.Names}}' | grep -q '^client1$'; then
	# Note, used Deepseek to help with syntax of check
	echo "client1 exists, stopping and deleting"
	docker stop client1
	docker rm client1
	echo "client1 successfully purged"
fi


if docker ps -a --format '{{.Names}}' | grep -q '^client2$'; then
	echo "client2 exists, stopping and deleting"
	docker stop client2
	docker rm client2
	echo "client2 successfully purged"
fi


# Delete NAT containers
if docker ps -a --format '{{.Names}}' | grep -q '^nat1$'; then
	# Note, used Deepseek to help with syntax of check
	echo "nat1 exists, stopping and deleting"
	docker stop nat1
	docker rm nat1
	echo "nat1 successfully purged"
fi


if docker ps -a --format '{{.Names}}' | grep -q '^nat2$'; then
	echo "nat2 exists, stopping and deleting"
	docker stop nat2
	docker rm nat2
	echo "nat2 successfully purged"
fi



if docker network ls | grep -q "net1"; then {
	docker network rm net1
}
fi

if docker network ls | grep -q "net2"; then {
	docker network rm net2
}
fi


if docker network ls | grep -q "pubnet"; then {
	docker network rm pubnet
}
fi


# Create networks
docker network create --subnet=192.168.10.0/24 net1
docker network create --subnet=192.168.20.0/24 net2
docker network create --subnet=10.0.0.0/24 pubnet

# Build natbox
docker build -f "./Dockerfile.nat" -t natbox . 

# Start NAT Routers
# Check if docker container exists and delete it if it does:

docker run -dit --name nat1 --cap-add=NET_ADMIN --network net1 --ip 192.168.10.100 natbox
docker run -dit --name nat2 --cap-add=NET_ADMIN --network net2 --ip 192.168.20.200 natbox

# Connect the two NAT devices to the "public internet" docker network
docker network connect --ip 10.0.0.2 pubnet nat1
docker network connect --ip 10.0.0.3 pubnet nat2

# Make a default route to forward IPs to the new device
docker exec nat1 iptables -t nat -A POSTROUTING -o eth1 -j MASQUERADE # This entered docker's CLI
docker exec nat2 iptables -t nat -A POSTROUTING -o eth1 -j MASQUERADE # This entered docker's CLI


# Setup Clients for testing
docker run -dit --name client1 --cap-add=NET_ADMIN --network net1 -v /data/Books/school/summer2025/computer_networking/project/code:/code --ip 192.168.10.101 natbox
docker run -dit --name client2 --cap-add=NET_ADMIN --network net2 -v /data/Books/school/summer2025/computer_networking/project/code:/code --ip 192.168.20.202 natbox

# Setup IP routing through the nat containers
docker exec client1 ip route replace default via 192.168.10.100
docker exec client2 ip route replace default via 192.168.20.200

# Setup the rendezvous client on pubnet
docker run -dit --name rendezvous --cap-add=NET_ADMIN --network pubnet -v /data/Books/school/summer2025/computer_networking/project/code:/code --ip 10.0.0.100 natbox


