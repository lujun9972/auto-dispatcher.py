while true; do
    file=ibps_$(date +"%s").tar
    for i in {1..100}; do
        echo $i >> $file
        sleep 1
    done
    sleep 300
done
