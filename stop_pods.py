import random
import sys
import time
from datetime import datetime


import kubernetes

timestring = sys.argv[1]
seconds = pt = datetime.strptime(timestring, '%M:%S,%f')
print(f'Stopping a pod after an average of {seconds} seconds')

kubernetes.config.load_kube_config()

v1 = kubernetes.client.CoreV1Api()
pods = v1.list_pod_for_all_namespaces(label_selector='app=chord').items

while True:
    pod_idx = random.randrange(len(pods))
    pod = pods[pod_idx]
    deleted = v1.delete_namespaced_pod(pod.metadata.name, 'chord')
    print(f'Deleted pod {pod.metadata.name}')

    sleep_time = random.gauss(seconds, 3)
    time.sleep(sleep_time)


