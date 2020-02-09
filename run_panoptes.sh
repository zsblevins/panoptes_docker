#!/bin/bash

# Take mount dir as arg, otherwise use $PWD
if [[ $1 == "" ]]; then
  mount=$PWD
else
  mount=$1
fi

if [[ $(uname) == "Darwin" ]]; then
  mount_options=":delegated"
else
  mount_options=""
fi

docker run -d \
    --sysctl net.core.somaxconn=511 \
    --name="panoptes_docker" \
    --shm-size=2G \
    -v ${mount}/plugins/polling:/home/panoptes_v/lib/python3.6/site-packages/yahoo_panoptes/plugins/polling/${mount_options} \
    -v ${mount}/conf/localhost.json:/home/panoptes/conf/localhost.json${mount_options} \
    -p 127.0.0.1:8080:3000/tcp \
    panoptes_docker
