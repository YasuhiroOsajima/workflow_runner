#!/bin/bash

# Use like this:
#
#  $ git clone https://github.com/YasuhiroOsajima/workflow_runner.git
#  $ cd workflow_runner
#  $ python3 -m vevn venv
#  $ source venv/bin/activate
#  $ pip install -r requirements.txt
#  $ bash install.sh


PYTHON_PATH=`which python`
RUNNER_PATH=`pwd`/cmd/workflow_runner.py
LOCAL_BIN="${HOME}/.local/bin"

LOCAL_BIN_WC=`echo ${PATH} | grep ${LOCAL_BIN} | wc -l`
if [ ${LOCAL_BIN_WC} = 1 ]; then
    BIN_PATH=${LOCAL_BIN}
else
    BIN_PATH='/usr/local/bin/'
fi

RUNNER_FILE="${BIN_PATH}/workflow_runner"


# create runner file
cat <<__EOT__ > ${RUNNER_FILE}
#!/bin/bash

${PYTHON_PATH} ${RUNNER_PATH} \$@
__EOT__

chmod 755 ${RUNNER_FILE}
