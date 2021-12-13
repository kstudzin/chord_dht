pods=`kubectl get pods -n chord --no-headers | awk '{print $1}'`

pods=(${pods//\n/ })
for i in "${pods[@]}"
do
  kubectl exec -it -n chord $i -- echo hi
done