import kfp 
from kfp.dsl import component, pipeline
# from kfp import kubernetes



@component(
    base_image="ghcr.io/canonical/charmed-spark:3.5-22.04_edge",
    packages_to_install=["pyspark==3.4.2"] # TODO: remove this after py4j in PYTHONPATH fixed in image
)
def spark_test_component() -> None:
    import logging
    import os
    import pyspark
    import socket
    from lightkube import Client
    from operator import add
    from spark8t.services import K8sServiceAccountRegistry
    from spark8t.services import LightKube as LightKubeInterface
    
    def count_vowels(text: str) -> int:
      count = 0
      for char in text:
        if char.lower() in "aeiou":
          count += 1
      return count

    lines = """Canonical's Charmed Data Platform solution for Apache Spark runs Spark jobs on your Kubernetes cluster.
    You can get started right away with MicroK8s - the mightiest tiny Kubernetes distro around! 
    The spark-client snap simplifies the setup process to run Spark jobs against your Kubernetes cluster. 
    Spark on Kubernetes is a complex environment with many moving parts.
    Sometimes, small mistakes can take a lot of time to debug and figure out.
    """

    app_name = "CountVowels"
    SPARK_SERVICE_ACCOUNT = os.environ["SPARK_SERVICE_ACCOUNT"]
    SPARK_NAMESPACE = os.environ["SPARK_NAMESPACE"]

    # with SparkSession(app_name=app_name, namespace=SPARK_NAMESPACE, username=SPARK_SERVICE_ACCOUNT) as spark:
    #     n = spark.sparkContext.parallelize(lines.splitlines(), 2).map(count_vowels).reduce(add)
    #     logging.warning(f"The number of vowels in the string is {n}")


    pod_ip = socket.gethostbyname(socket.gethostname())
    k8s_master = Client().config.cluster.server
    interface = LightKubeInterface(None, None)
    registry = K8sServiceAccountRegistry(interface)
    
    spark_properties = registry.get(
        f"{SPARK_NAMESPACE}:{SPARK_SERVICE_ACCOUNT}"
    ).configurations.props | {
        "spark.driver.host": pod_ip,
        "spark.kubernetes.container.image": "ghcr.io/canonical/charmed-spark:3.5-22.04_edge" # TODO: remove once integration hub is able to set this
    }

    builder = pyspark.sql.SparkSession\
                    .builder\
                    .appName(app_name)\
                    .master(f"k8s://{k8s_master}")
    for conf, val in spark_properties.items():
        builder = builder.config(conf, val)
    session = builder.getOrCreate()

    n = session.sparkContext.parallelize(lines.splitlines(), 2).map(count_vowels).reduce(add)
    logging.warning(f"The number of vowels in the string is {n}")



@pipeline(name="spark-test-pipeline")
def spark_pipeline():
    task = spark_test_component()
    # kubernetes.add_pod_label(
    #     task,
    #     label_key='canonical-pyspark',
    #     label_value='true',
    # )
    # kubernetes.add_pod_annotation(
    #     task,
    #     annotation_key='traffic.sidecar.istio.io/excludeInboundPorts',
    #     annotation_value='37371,6060',
    # )
    # kubernetes.add_pod_annotation(
    #     task,
    #     annotation_key='traffic.sidecar.istio.io/excludeOutboundPorts',
    #     annotation_value='37371,6060',
    # )



client=kfp.Client()
kfp.compiler.Compiler().compile(
    spark_pipeline,
    package_path="spark_test_pipeline.yaml"
)
run = client.create_run_from_pipeline_func(
    spark_pipeline,
    arguments={},
    enable_caching=False
)