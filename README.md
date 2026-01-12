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


### Running the POC in PS7 environment
Since the PS7 environment sits behind a proxy, the following additional setup is required to run the POC in the PS7 environment.

1. Before you apply the Terraform module in setup 6 in [Instructions to run Spark <> Kubeflow POC], set the model level proxy settings in the `controller` model.
```
juju switch controller
juju model-config http-proxy='http://egress.ps7.internal:3128' https-proxy='http://egress.ps7.internal:3128' snap-http-proxy='http://egress.ps7.internal:3128' snap-https-proxy='http://egress.ps7.internal:3128'
```

2. When you apply the Terraform module in step 6, use `tfvars-ps7.json` as the variable file. This file contains additional variables that set the HTTP proxy, HTTPS proxy along with the no_proxy whitelist.

3. Setting the proxy settings in the Juju model is not enough, they also need to be set in the notebook itself. To do that, the environment variables `HTTP_PROXY`, `HTTPS_PROXY` and `NO_PROXY` can be set in the notebook code. However, it is to be noted that the `spark8t` won't work if the connection to K8s master is blocked by proxy, and thus, the K8s master URL should be whitelisted via the `NO_PROXY` setting only for the `spark8t` calls. An example notebook that tests the KF pipeline with proxy is provided in the file `test_spark_pipeline_proxy.ipynb` in this repo.
```
HTTP_PROXY, HTTPS_PROXY, NO_PROXY = 'http://egress.ps7.internal:3128', 'http://egress.ps7.internal:3128', "127.0.0.1,localhost,::1,10.0.0.0/8,172.16.0.0/16,192.168.0.0/16,10.152.183.0/24,.svc,.local,.kubeflow"

def add_proxy(obj, http_proxy=HTTP_PROXY, https_proxy=HTTPS_PROXY, no_proxy=NO_PROXY):
    """Adds the proxy env vars to the PipelineTask object."""
    return (
        obj.set_env_variable(name="http_proxy", value=http_proxy)
        .set_env_variable(name="https_proxy", value=https_proxy)
        .set_env_variable(name="HTTP_PROXY", value=http_proxy)
        .set_env_variable(name="HTTPS_PROXY", value=https_proxy)
        .set_env_variable(name="no_proxy", value=no_proxy)
        .set_env_variable(name="NO_PROXY", value=no_proxy)
    )


...

def spark_component():
    ...
    
    # Whitelist REST API host URL for calls to spark8t
    with environ(NO_PROXY=rest_api_host, no_proxy=rest_api_host):
        spark_properties = registry.get(
            f"{SPARK_NAMESPACE}:{SPARK_SERVICE_ACCOUNT}"
        ).configurations.props | {
            "spark.driver.host": pod_ip,
        }

...

@pipeline(name="spark-test-pipeline")
def spark_pipeline():
    # Add proxy environment variables to the KFP component
    task = add_proxy(spark_test_component())
    kubernetes.add_pod_label(
        task,
        label_key='access-spark-pipeline',
        label_value='true',
    )

...
```