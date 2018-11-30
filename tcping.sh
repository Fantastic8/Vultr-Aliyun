#!/bin/bash
TCPING=`tcping -t 10 $1 $2 | grep 'open' | wc -l`
echo $TCPING
