#!/bin/sh
export SERVER_IP="<your-ip>"
export USER="<your-user>"

export K3S_TOKEN=$(ssh $USER@$SERVER_IP "sudo -S cat /var/lib/rancher/k3s/server/node-token")

echo "K3S_TOKEN: $K3S_TOKEN"

# Then, install K3s in agent mode:
sudo curl -sfL https://get.k3s.io | K3S_URL=https://$SERVER_IP:6443 K3S_TOKEN=$K3S_TOKEN sh -