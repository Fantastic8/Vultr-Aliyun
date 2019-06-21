#!/bin/bash
PING=`ping -c 5 -w 20 $1 | grep '5 received' | wc -l`
echo $PING
