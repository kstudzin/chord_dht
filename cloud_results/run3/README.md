curl --location -g --request GET 'http://18.234.177.87:30495/api/v1/query?query=avg(sum_over_time(kube_pod_status_phase{phase='\''Running'\'', namespace='\''chord'\''}[12m]) * 30)'

{
    "status": "success",
    "data": {
        "resultType": "vector",
        "result": [
            {
                "metric": {},
                "value": [
                    1639579537.335,
                    "61.698113207547195"
                ]
            }
        ]
    }
}