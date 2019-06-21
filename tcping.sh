#!/bin/bash
TCPING=`tcpping -t 10 $1 $2 | grep 'open' | wc -l`
echo $TCPING
