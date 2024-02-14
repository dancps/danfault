#!/usr/bin/env bash
function get_os() {
    res=""
    if [ "$(uname)" == "Darwin" ]; then
        res="macos"
    elif [ "$(expr substr $(uname -s) 1 5)" == "Linux" ]; then
        res="unix"
    # elif [ "$(expr substr $(uname -s) 1 10)" == "MINGW32_NT" ]; then
    #     # Do something under 32 bits Windows NT platform
    # elif [ "$(expr substr $(uname -s) 1 10)" == "MINGW64_NT" ]; then
    #     # Do something under 64 bits Windows NT platform
    else
        echo "Error!" 1>&2
        exit 123
    fi
    echo $res
}



# run(){
#     # Run a functions and redirects the output for the adequate one
# }