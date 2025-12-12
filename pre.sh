#! /bin/bash

# Update the package index and upgrade them
sudo apt update
sudo apt upgrade -y

# Install Microk8s
sudo snap install microk8s --channel 1.34-strict/stable
sudo snap alias microk8s.kubectl kubectl
sudo usermod -a -G snap_microk8s ubuntu

# Logout to have group changes be reflected
logout