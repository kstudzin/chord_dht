pods=`kubectl get pods -n chord | awk '{print $1}'`

for i in "${pods[@]}"
do
  kubectl exec -it -n chord $i -- echo hi
done