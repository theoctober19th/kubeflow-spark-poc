#! /bin/bash

# setup microk8s
mkdir -p ~/.kube
microk8s status --wait-ready
microk8s config > ~/.kube/config
sudo microk8s enable rbac 
sudo microk8s enable minio 
sudo microk8s enable metallb:10.99.99.0-10.99.99.100
sudo microk8s enable hostpath-storage
sudo microk8s enable dns

# setup juju
sudo snap install juju
juju clouds
juju bootstrap --agent-version 3.6.9  microk8s
juju add-model hello

# prepare system for kubeflow-spark
sudo sysctl fs.inotify.max_user_instances=1280
sudo sysctl fs.inotify.max_user_watches=655360
sudo snap install spark-client --channel 3.4/stable
sudo snap install jhack
sudo snap connect jhack:dot-local-share-juju snapd

# deploy kubeflow-spark setup
git clone https://github.com/canonical/charmed-kubeflow-solutions.git
cd charmed-kubeflow-solutions
git checkout poc/kubeflow-spark
cd modules/kubeflow-spark
sudo snap install terraform --classic
terraform init
terraform apply -var-file examples/tfvars.json -auto-approve

# configure kubeflow-spark-setup
juju switch kubeflow
juju config dex-auth static-username=admin
juju config dex-auth static-password=admin

# output kubeflow UI address
microk8s kubectl -n kubeflow get svc istio-ingressgateway-workload -o jsonpath='{.status.loadBalancer.ingress[0].ip}'
