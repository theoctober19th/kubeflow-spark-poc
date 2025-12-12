### Instructions to run Spark <> Kubeflow POC

1. Clone this repo 
```sh
git clone https://github.com/theoctober19th/kubeflow-spark-poc.git
cd kubeflow-spark-poc
```

2. Connect to Canonical VPN (IMPORTANT!) and reserve a testflinger machine with the following command. Please make sure to update the launchpad username in the file `testflinger-reservation.yaml` so that you'll be able to login later to the machine.
```sh
./reserve_machine.sh
```

3. Wait for about 10 minutes, and once you receive the IP of the machine, connect to the machine with SSH
```
ssh ubuntu@10.241.7.22
```

4. Copy the contents in `pre.sh` and run it in the machine via SSH. The script will log you out of the system itself such that the group membership changes are reflected.
```
./pre.sh
```

5.  Login into the testflinger machine with SSH again. Now run the `post.sh` script. This script will download the Kubeflow <> Spark terraform module and applies it.
```
./post.sh
```

6. Once the charms settle to `active` and `idle`, find the IP address for the Kubeflow dashboard UI with the following command:
```bash
microk8s kubectl -n kubeflow get svc istio-ingressgateway-workload -o jsonpath='{.status.loadBalancer.ingress[0].ip}'
```

7. Logout from the testflinger machine, and login with port-forwarding so that the Kubeflow UI will be accessible locally. Please make sure to update the address `10.99.99.0` to the actual address you receive from step 6, if it is different.
```bash
logout

ssh -L 8080:10.99.99.0:80 ubuntu@10.241.7.22
```

8. Now browse to the address `localhost:8080` in your local browser. When prompted for authentication, enter `admin` as username and `admin` as password. This opens the Kubeflow dashboard UI. For the first run, it will ask you to setup default Kubeflow profile (namespace). Create one with the default name `admin`. Afterwards, you'll see the Kubeflow Dashboard UI.


### Running Spark inside the Notebook

1. In the Kubeflow UI, click "Notebooks" and "+ New notebook".

2. In the setup, click "Custom Notebook" and choose custom image for notebook (under Advanced Options), and speficy the charmed-spark-jupyterlab image `ghcr.io/canonical/charmed-spark-jupyterlab:3.5-22.04_edge`. 

3. Scroll down to the bottom. In the "Advanced Options", choose the configuration "Configure PySpark for Kubeflow notebooks", and finally click on "Create". This will apply the poddefault that configures this notebook to access Spark.

4. Once the notebook pod comes up and running, connect to the notebook, and access Spark from within it. For simple sanity test, you can use the file `test_spark_notebook.ipynb` from this repo.


### Running Spark from pipeline

1. In the Kubeflow UI, click "Notebooks" and "+ New notebook".

2. In the setup, scroll down to the bottom. In the "Advanced Options", choose the configuration "Configure PySpark for Kubeflow pipelines", and finally click on "Create". 

3. Once the notebook pod comes up and running, connect to the notebook. Upload the file `test_spark_pipeline.ipynb` from this repo there, and run it to start a Kubeflow pipeline run.

4. In the terminal (inside the testflinger machine), verify that new pods containing `system-container-impl` in the name are created. To see the result of the Spark job run from the pipeline, see the pod logs of that pod.
```bash
kubectl logs -n admin spark-test-pipeline-f4zwt-system-container-impl-427000165 | grep "vowels"
```