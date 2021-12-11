import kubernetes

kubernetes.config.load_kube_config()

v1 = kubernetes.client.CoreV1Api()
pods = v1.list_pod_for_all_namespaces(label_selector='app=chord')
for i in pods.items:
    print("%s\t%s\t%s" % (i.status.pod_ip, i.metadata.namespace, i.metadata.name))

deleted = v1.delete_namespaced_pod('spark-driver-deploy-58bbbfcb-9spnr', 'default')
print(f'{deleted}')