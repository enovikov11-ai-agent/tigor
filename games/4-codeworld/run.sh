#!/bin/bash

mvn package
cp ./target/CodeWorld-1.0.jar ./server-data/plugins
docker-compose up