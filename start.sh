#!/bin/bash

if [ -z "$REPL_SET_NAME" ]; then
    /usr/bin/mongod --journal --dbpath /var/lib/mongodb
  else
    /usr/bin/mongod --journal --dbpath /var/lib/mongodb --replSet $REPL_SET_NAME
fi
