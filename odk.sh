#!/bin/sh
# Wrapper script for docker.
#
# This is used primarily for wrapping the GNU Make workflow.
# Instead of typing "make TARGET", type "./run.sh make TARGET".
# This will run the make workflow within a docker container.
#
# The assumption is that you are working in the src/ontology folder;
# we therefore map the whole repo (../..) to a docker volume.
#
# See README.md for more details.
docker run -v $PWD/:/work -w /work/ -e ROBOT_JAVA_ARGS='-Xmx20G' -e JAVA_OPTS='-Xmx16G' --rm -ti obolibrary/odkfull "$@"