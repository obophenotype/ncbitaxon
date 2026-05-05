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
# To inspect memory/time consumption of each make target, run with:
#   ODK_DEBUG=yes ./odk.sh make <target>
#
# See README.md for more details.
ODK_TAG=v1.6
ODK_DEBUG=${ODK_DEBUG:-no}

TIMECMD=
if [ x$ODK_DEBUG = xyes ]; then
    # The format string uses non-breaking spaces (U+00A0) instead of
    # normal spaces, to prevent the shell from tokenizing it.
    TIMECMD="/usr/bin/time -f ### DEBUG STATS ###\nElapsed time: %E\nPeak memory: %M kb"
fi

docker run -v $PWD/:/work -w /work/ -e ROBOT_JAVA_ARGS='-Xmx20G' -e JAVA_OPTS='-Xmx16G' -e ODK_DEBUG=$ODK_DEBUG --rm -ti obolibrary/odkfull:$ODK_TAG $TIMECMD "$@"