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



###### EXAMPLE FROM GPT
#  #!/bin/zsh

#  # Function to detect the OS
#  detect_os() {
#      if grep -qEi "(Microsoft|WSL)" /proc/version &> /dev/null; then
#          echo "wsl"
#      elif [[ "$OSTYPE" == "darwin"* ]]; then
#          echo "mac"
#      elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
#          echo "linux"
#      else
#          echo "unknown"
#      fi
#  }

#  # Function to perform WSL setup
#  setup_wsl() {
#      echo "Setting up for WSL..."
#      # Add your WSL-specific setup commands here
#  }

#  # Function to perform macOS setup
#  setup_mac() {
#      echo "Setting up for macOS..."
#      # Add your macOS-specific setup commands here
#  }

#  # Function to perform Linux setup
#  setup_linux() {
#      echo "Setting up for Linux..."
#      # Add your Linux-specific setup commands here
#  }

#  # Main script execution
#  os=$(detect_os)

#  case $os in
#      wsl)
#          setup_wsl
#          ;;
#      mac)
#          setup_mac
#          ;;
#      linux)
#          setup_linux
#          ;;
#      *)
#          echo "Unsupported OS detected."
#          ;;
#  esac
######
