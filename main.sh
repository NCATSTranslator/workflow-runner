#!/usr/bin/env bash

PORT=3084

# https://stackoverflow.com/a/14203146
POSITIONAL=()
while [[ $# -gt 0 ]]
do
key="$1"

case $key in
    -p|--port)
    PORT="$2"
    shift # past argument
    shift # past value
    ;;
    *)    # unknown option
    POSITIONAL+=("$1") # save it in an array for later
    shift # past argument
    ;;
esac
done

uvicorn app.server:APP --host 0.0.0.0 --port $PORT --workers 4
