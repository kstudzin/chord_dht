pods=`kubectl get pods -n chord --no-headers | awk '{print $1}'`

pods=(${pods//\n/ })
for i in "${pods[@]}"
do
  kubectl exec -it -n chord $i -- tc qdisc add dev eth0 root netem delay 100ms 20ms distribution normal
done