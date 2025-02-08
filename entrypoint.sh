#!/bin/sh
#
# Entrypoint script for a python application in a Docker container
#

echo "Starting application..."

if [ -z "${EXPOSE_PORT}" ]; then
    EXPOSE_PORT="8091"
fi

if [ -f ".version" ]; then
    APP_VERSION=$( cat ".version" )
else
    APP_VERSION="0.0.0"
fi

export APP_VERSION

echo "Variables:"
echo "APP_VERSION='${APP_VERSION}'"

python3 server.py
