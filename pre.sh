#! /bin/bash
sudo apt update
sudo apt upgrade -y

sudo snap install microk8s --channel 1.34-strict/stable
sudo snap alias microk8s.kubectl kubectl
sudo usermod -a -G snap_microk8s ubuntu

