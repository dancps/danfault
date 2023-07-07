#!/bin/bash
DANFAULT_DIR=$(grealpath $(dirname "$0")/..) # Relative to the pwd
echo "Danfault dir: $DANFAULT_DIR"

# Install homebrew
echo Installing homebrew
if ! command -v brew &> /dev/null
then
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    (echo; echo 'eval "$(/opt/homebrew/bin/brew shellenv)"') >> /Users/dancps/.zprofile
    eval "$(/opt/homebrew/bin/brew shellenv)"
else
    echo "Homebrew is already installed"
fi

echo Installing Oh-my-zsh
if [ -d $(grealpath "~/.oh-my-zsh/") ];
then
    echo "~/.oh-my-zsh/ directory exists."
else
	echo "~/.oh-my-zsh/ directory does not exist."
    sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)"
fi

# to install grealpath
#    Commands also provided by macOS and the commands dir, dircolors, vdir have been installed with the prefix "g".
#    If you need to use these commands with their normal names, you can add a "gnubin" directory to your PATH with:
#      PATH="/opt/homebrew/opt/coreutils/libexec/gnubin:$PATH"
echo "Installing coreutils"
brew install -q coreutils 


# Calls vscode.sh
echo 'Configuring vscode'
./macos/vscode.sh

echo "Installing python"
if [ -d ~/software/python/ ];
then
    echo "~/software/python directory exists."
else
	echo "~/software/python directory does not exist."
    mkdir -p ~/software/python
fi

cd ~/software/python

curl -O https://www.python.org/ftp/python/3.8.16/Python-3.8.16.tar.xz 

tar xf Python-3.8.16.tar.xz
cd  Python-3.8.16

# Installs xcode extras
echo "Install xcode-select"
xcode-select --install

# Installs some dependencies
brew install -q pkg-config openssl@1.1 xz gdbm tcl-tk

brew install colima
brew install docker

# None of the above worked
# brew install openblas
# brew install atlas
# arch -arm64 brew install cmake
# arch -arm64 brew install patchelf
# brew install autoconf automake libtool
# brew install dbus

# # Configures python installation
  #CFLAGS="$CFLAGS -std=c11" ;\
    # --with-cxx-main=g++ \
echo "Configuring python"
make clean
export PKG_CONFIG_PATH="$(brew --prefix tcl-tk)/lib/pkgconfig"; \
  CFLAGS="-I$(brew --prefix gdbm)/include -I$(brew --prefix xz)/include"; \
  LDFLAGS="-L$(brew --prefix gdbm)/lib -L$(brew --prefix xz)/lib"
echo "PKG_CONFIG_PATH = $PKG_CONFIG_PATH" 
echo "CFLAGS = $CFLAGS" 
echo "LDFLAGS = $LDFLAGS" 
./configure --with-pydebug \
    --with-openssl="$(brew --prefix openssl@1.1)" \
    --with-tcltk-libs="$(pkg-config --libs tcl tk)" \
    --with-tcltk-includes="$(pkg-config --cflags tcl tk)"\
    --enable-optimizations --with-ensurepip=upgrade

echo "Running make"
make -s -j8
sudo make altinstall
