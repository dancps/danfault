#!/usr/bin/env bash
SETUP_FILE=$(readlink -f $0)
SETUP_DIR=$(dirname $SETUP_FILE)
DANFAULT_DIR=$(realpath $SETUP_DIR/..)
TEMPORARY_DANFAULT=$(realpath $DANFAULT_DIR/.tmp/)

# Setting base environment variables
source $DANFAULT_DIR/dotfiles/.colors
BASE_ENV_PATH=$(realpath $SETUP_DIR/base_env.sh)
COMMON_UTILS_PATH=$(realpath $SETUP_DIR/utils.sh)
source $BASE_ENV_PATH
source $COMMON_UTILS_PATH



# Checks the OS and sets common OS variables.
OS=$(get_os)
echo OS=$OS

OS_ENV_VARS=$(realpath $DANFAULT_DIR/$OS/os_envs.sh)
source $OS_ENV_VARS
# case $OS in
#     "unix") $DANFAULT_DIR/$OS/os_envs.sh;;
#     "macos") echo "BBB";;
# esac

PROJECTS_DIR=$(realpath ~/$PROJECTS)
DOCUMENTS_DIR=$(realpath ~/$DOCUMENTS)


echo -e Setting project dir to: $PROJECTS_DIR
echo -e Setting documents dir to: $DOCUMENTS_DIR




# Run a script to check the OS and set common variables to each type of OS.
# Example:
#   source $

# source $DANFAULT_DIR/dotfiles/.alias
# source $DANFAULT_DIR/dotfiles/.export
# source $DANFAULT_DIR/dotfiles/.extra
# source $DANFAULT_DIR/dotfiles/.source

