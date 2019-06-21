#!/bin/bash
TCPING=`tcpping -x 5 $1 $2 | grep 'open' | wc -l`
echo $TCPING
