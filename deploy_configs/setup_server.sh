#!/bin/bash
# ==============================================================================
# PIMS Server Initialization Script
# Runs on Ubuntu 22.04 LTS / 24.04 LTS
# Target timezone: Asia/Karachi (PKT)
# ==============================================================================

set -e

# Ensure script is run as root
if [ "$EUID" -ne 0 ]; then
  echo "Please run as root or using sudo"
  exit 1
fi

echo "=== Updating System Package Index ==="
apt-get update -y
apt-get upgrade -y

echo "=== Installing Dependencies ==="
apt-get install -y \
    ca-certificates \
    curl \
    gnupg \
    lsb-release \
    ufw \
    git \
    zip \
    unzip \
    tar

echo "=== Configuring Timezone to Asia/Karachi ==="
timedatectl set-timezone Asia/Karachi
echo "Timezone set to:"
timedatectl

echo "=== Installing Docker & Docker Compose Plugin ==="
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg --yes
chmod a+r /etc/apt/keyrings/docker.gpg

echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  tee /etc/apt/sources.list.d/docker.list > /dev/null

apt-get update -y
apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

echo "=== Configuring Docker Auto-Start ==="
systemctl enable --now docker

# Add non-root user (default user who will manage deployment, change 'ubuntu' or 'sj' if different)
TARGET_USER=$(logname || echo ${SUDO_USER:-$USER})
if [ -n "$TARGET_USER" ] && [ "$TARGET_USER" != "root" ]; then
    echo "Adding user '$TARGET_USER' to the docker group..."
    usermod -aG docker "$TARGET_USER"
    echo "User '$TARGET_USER' added. Log out and back in to apply group privileges."
fi

echo "=== Configuring UFW Firewall rules ==="
ufw default deny incoming
ufw default allow outgoing
ufw allow 22/tcp comment 'SSH'
ufw allow 80/tcp comment 'HTTP'
ufw allow 443/tcp comment 'HTTPS'
ufw allow 4756/tcp comment 'PIMS Direct Port'
echo "y" | ufw enable
ufw status verbose

echo "=============================================================================="
echo " Server Setup Completed successfully!"
echo " Docker version: $(docker --version)"
echo " Docker Compose version: $(docker compose version)"
echo " System Time: $(date)"
echo "=============================================================================="
