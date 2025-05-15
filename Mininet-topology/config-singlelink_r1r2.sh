#!/bin/bash -x

set -e

# For now, devices are all at the same IP address and port
#mn=localhost:8080; t1=$mn; t2=$mn
echo "* t1 is at $t1"
echo "* t2 is at $t2"
# URL for REST server
url="localhost:8080"; t1=$url; t2=$url; r1=$url; r2=$url
curl="curl -s"


echo "* Attempting to configure simplelink_alt_r1.py network"

$curl "$t1/connect?node=t1&ethPort=1&wdmPort=2&channel=2"
$curl "$t2/connect?node=t2&ethPort=1&wdmPort=2&channel=2"
#$curl "$t1/turn_on?node=t1"
#$curl "$t2/turn_on?node=t2"

echo "* Monitoring signals at endpoints"
$curl "$t1/monitor?monitor=t1-monitor"
$curl "$t2/monitor?monitor=t2-monitor"

echo "* Resetting ROADM"
$curl "$r1/reset?node=r1"
$curl "$r2/reset?node=r2"

echo "* Configuring ROADM to forward ch1 from t1 to t2"
$curl "$r1/connect?node=r1&port1=1&port2=2&channels=2"
$curl "$r2/connect?node=r2&port1=1&port2=2&channels=2"


echo "* Turning on terminals/transceivers"
$curl "$t1/turn_on?node=t1"
$curl "$t2/turn_on?node=t2"

echo "* Monitoring signals at endpoints"
for tname in t1 t2; do
    url=${!tname}
    echo "* $tname"
    $curl "$url/monitor?monitor=$tname-monitor"
done


echo "* Done."
