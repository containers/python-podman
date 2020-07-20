#!/bin/bash


function help {
# Display helping message
cat <<EOF
usage: $0 [<args>]

Compare python-podman implemention of the libpod varlink interface

Arguments:
    -b, --branch   The libpod branch or commit ID to compare with (default: master)
    -d, --debug    Turn on the debug mode
examples:
    $0 --branch=master
EOF
}

function clean {
    if [ -f ${LOCAL_INTERFACE_FILE} ]; then
        rm ${LOCAL_INTERFACE_FILE}
    fi
}

function download {
    echo "Downloading the libpod's defined interface"
    url=${LIBPOD_RAW_URL}/${BRANCH}/${INTERFACE}
    echo ${url}
    curl ${url} -o ${LOCAL_INTERFACE_FILE}
}

function extract {
    cat ${LOCAL_INTERFACE_FILE} | \
        grep "method" | \
        grep -v "^#" | \
        awk '{print $2}' | \
        awk -F "(" '{print $1}'
}

function compare {
    for method in $(extract)
    do
        grep -ri podman -e "${method}" &>/dev/null;
        if [ $? != 0 ]; then
            echo -e "Method ${method} seems not yet implemented"
        fi
    done
}

BRANCH="master"
IGNORE_ERRORS=false
# Parse command line user inputs
for i in "$@"
do
    case $i in
        # The host to use
        -b=*|--branch=*)
        BRANCH="${i#*=}"
        shift 1
        ;;
        # Ignore error
        -i|--ignore)
        IGNORE_ERRORS=true
        shift 1
        ;;
        # Turn on the debug mode
        -d|--debug)
        set -x
        shift 1
        ;;
        # Display the helping message
        -h|--help)
        help
        exit 0
        ;;
    esac
done

EXIT_CODE=0
LIBPOD_REPO=containers/libpod
INTERFACE=cmd/podman/varlink/io.podman.varlink
LOCAL_INTERFACE_FILE=/tmp/$(basename ${INTERFACE})
LIBPOD_RAW_URL=https://raw.githubusercontent.com/${LIBPOD_REPO}

clean
download
result=$(compare)
echo -e "${result}"
if [ ! -z "${result}" ]; then
    echo "$(echo -e "${result}" | wc -l) error(s) found"
    if [ ${IGNORE_ERRORS} = true ]; then
        echo "You asked to ignore errors so This script will return status 0"
    else
        EXIT_CODE=1
    fi
else
    echo "libpod and python-podman seems properly synchronized"
fi
clean

echo "Comparison finished...bye!"
exit ${EXIT_CODE}
