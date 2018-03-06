#!/bin/bash
PING=`ping -c 5 -w 20 $1 | grep '0 received' | wc -l`
echo $PING
