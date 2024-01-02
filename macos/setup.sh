#!/bin/bash
DANFAULT_DIR=$(realpath $(dirname "$0")/..) # Relative to the pwd
TEMPORARY_DANFAULT=$(realpath $DANFAULT_DIR/.tmp/)
source $DANFAULT_DIR/dotfiles/.colors
source $DANFAULT_DIR/dotfiles/.alias
source $DANFAULT_DIR/dotfiles/.export
source $DANFAULT_DIR/dotfiles/.extra
source $DANFAULT_DIR/dotfiles/.source


echo -e "${Green}+==============================================================================+${Color_Off}" 
echo -e "${Green}+==         ${BGreen}danfault Setup${Color_Off}${Green}                                                   ==+${Color_Off}" 
echo -e "${Green}+==============================================================================+${Color_Off}" 
echo -e "${Green}+${Color_Off} ${BWhite}System:${Color_Off} $(uname) - $(uname -m)" 

echo -e "${Green}+ Variables:${Color_Off}" 
echo -e "${Green}+${Color_Off}  ${BWhite}DANFAULT_DIR:${Color_Off}       ${DANFAULT_DIR}" 
echo -e "${Green}+${Color_Off}  ${BWhite}TEMPORARY_DANFAULT:${Color_Off} ${TEMPORARY_DANFAULT}" 
echo -e "${Green}+==============================================================================+${Color_Off}" 


###############################################################################
### Variables and setup                                                     ###
###############################################################################
# Will set needed variables into .zshrc.


echo -e "${Cyan}[danfault - Setup]${Color_Off} Installing Oh-my-zsh"
if [ -d "~/.oh-my-zsh/" ];
then
    echo -e "${Cyan}[danfault - Setup]${Color_Off} ~/.oh-my-zsh/ directory exists."
else
	echo -e "${Cyan}[danfault - Setup]${Color_Off} ~/.oh-my-zsh/ directory does not exist."
    sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)"
    git clone https://github.com/zsh-users/zsh-autosuggestions ${ZSH_CUSTOM:-~/.oh-my-zsh/custom}/plugins/zsh-autosuggestions
fi



if grep -Fxq "export DANFAULT_DIR=${DANFAULT_DIR}" ~/.zshrc
then
    echo -e "${Cyan}[danfault - Setup]${Color_Off} Already added DANFAULT_DIR at ~/.zshrc"
else
    echo "export DANFAULT_DIR=${DANFAULT_DIR}" >> ~/.zshrc
    export DANFAULT_DIR=${DANFAULT_DIR}
fi

echo -e "${Cyan}[danfault - Setup]${Color_Off} Adding sources at ~/.zshrc" 
# dotfiles/.alias
if grep -Fxq "source $DANFAULT_DIR/dotfiles/.alias" ~/.zshrc; then echo -e "${Cyan}[danfault - Setup]${Color_Off} Already added dotfiles/.alias at ~/.zshrc"; else echo "source $DANFAULT_DIR/dotfiles/.alias" >> ~/.zshrc; fi
# dotfiles/.export
if grep -Fxq "source $DANFAULT_DIR/dotfiles/.export" ~/.zshrc; then echo -e "${Cyan}[danfault - Setup]${Color_Off} Already added dotfiles/.export at ~/.zshrc"; else echo "source $DANFAULT_DIR/dotfiles/.export" >> ~/.zshrc; fi
# dotfiles/.extra
if grep -Fxq "source $DANFAULT_DIR/dotfiles/.extra" ~/.zshrc; then echo -e "${Cyan}[danfault - Setup]${Color_Off} Already added dotfiles/.extra at ~/.zshrc"; else echo "source $DANFAULT_DIR/dotfiles/.extra" >> ~/.zshrc; fi
# dotfiles/.source
if grep -Fxq "source $DANFAULT_DIR/dotfiles/.source" ~/.zshrc; then echo -e "${Cyan}[danfault - Setup]${Color_Off} Already added dotfiles/.source at ~/.zshrc"; else echo "source $DANFAULT_DIR/dotfiles/.source" >> ~/.zshrc; fi

# Install homebrew
echo -e "${Cyan}[danfault - Setup]${Color_Off} Installing homebrew"
if ! command -v brew &> /dev/null
then
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    # (echo; echo 'eval "$(/opt/homebrew/bin/brew shellenv)"') >> /Users/dancps/.zprofile
    # eval "$(/opt/homebrew/bin/brew shellenv)"
else
    echo -e "${Cyan}[danfault - Setup]${Color_Off} Homebrew is already installed"
fi


# to install grealpath
#    Commands also provided by macOS and the commands dir, dircolors, vdir have been installed with the prefix "g".
#    If you need to use these commands with their normal names, you can add a "gnubin" directory to your PATH with:
#      PATH="/opt/homebrew/opt/coreutils/libexec/gnubin:$PATH"
# echo "Installing coreutils"
# brew install -q coreutils 


###############################################################################
### Git                                                                     ###
###############################################################################
# Will install conda and copy:
#   - .gitconfig

echo -e "${Cyan}[danfault - git]${Color_Off} Setting-up VSCode files" 
if git --version
then
    echo -e "${Cyan}[danfault - git]${Color_Off} Git installed" 
else
    echo -e "${Cyan}[danfault - git]${Color_Off} Git not installed" 
    sudo apt install git
fi
if [ -e ~/.gitconfig ]
then
    echo -e "${Cyan}[danfault - git]${Color_Off} .gitconfig file already exists. Backing up into ~/.gitconfig_backup_$(date +%d%m%y%H%M%S)"
    cp ~/.gitconfig ~/.gitconfig_backup_$(date +%d%m%y%H%M%S)
    cp $DANFAULT_DIR/git/.gitconfig ~/.gitconfig
else
    echo -e "${Cyan}[danfault - git]${Color_Off} .gitconfig file does not exists."
    cp $DANFAULT_DIR/git/.gitconfig ~/.gitconfig
fi

# Calls vscode.sh
echo -e "${Cyan}[danfault - vscode]${Color_Off} Configuring vscode"
# ./macos/vscode.sh

echo -e "${Cyan}[danfault - python]${Color_Off} Installing python"
if [ -d ~/software/python/ ];
then
    echo -e "${Cyan}[danfault - python]${Color_Off} ~/software/python directory exists."
else
	echo -e "${Cyan}[danfault - python]${Color_Off} ~/software/python directory does not exist."
    mkdir -p ~/software/python
    cd ~/software/python

fi


# Installs xcode extras
# echo "Install xcode-select"
# xcode-select --install

# Installs some dependencies
echo -e "${Cyan}[danfault - python]${Color_Off} Installing some dependencies"
brew install -q pkg-config openssl@1.1 xz gdbm tcl-tk

# Installs colima and docker
# brew install colima
# brew install docker

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
if python3.8 --version >/dev/null
then
    echo -e "${Cyan}[danfault - python]${Color_Off} Python installed" 
else
    echo -e "${Cyan}[danfault - python]${Color_Off} Python not installed" 

    echo -e "${Cyan}[danfault - python]${Color_Off} Configuring python"
    make clean
    export PKG_CONFIG_PATH="$(brew --prefix tcl-tk)/lib/pkgconfig"; \
      CFLAGS="-I$(brew --prefix gdbm)/include -I$(brew --prefix xz)/include"; \
      LDFLAGS="-L$(brew --prefix gdbm)/lib -L$(brew --prefix xz)/lib"
    echo -e "${Cyan}[danfault - python]${Color_Off}    PKG_CONFIG_PATH = $PKG_CONFIG_PATH" 
    echo -e "${Cyan}[danfault - python]${Color_Off}    CFLAGS = $CFLAGS" 
    echo -e "${Cyan}[danfault - python]${Color_Off}    LDFLAGS = $LDFLAGS" 

    echo -e "${Cyan}[danfault - python]${Color_Off} Downloading python"
    curl -O https://www.python.org/ftp/python/3.8.16/Python-3.8.16.tar.xz 
    tar xf Python-3.8.16.tar.xz
    cd  Python-3.8.16

    echo -e "${Cyan}[danfault - python]${Color_Off} Running ./configure"
    ./configure --with-pydebug \
        --with-openssl="$(brew --prefix openssl@1.1)" \
        --with-tcltk-libs="$(pkg-config --libs tcl tk)" \
        --with-tcltk-includes="$(pkg-config --cflags tcl tk)"\
        --enable-optimizations --with-ensurepip=upgrade

    echo -e "${Cyan}[danfault - python]${Color_Off} Running make"
    make -s -j8
    sudo make altinstall
fi


###############################################################################
### Miniforge                                                               ###
###############################################################################
# Will install conda at $HOME/conda/

# echo -e "${Cyan}[danfault - conda]${Color_Off} Conda installation" 
# CONDA_PREFIX_PATH=${HOME}/conda

# if [ -e ${TEMPORARY_DANFAULT}/Miniforge3-$(uname)-$(uname -m).sh ]
# then
#     echo -e "${Cyan}[danfault - conda]${Color_Off} Conda installation file already exists at ${TEMPORARY_DANFAULT}/Miniforge3-$(uname)-$(uname -m).sh"
# else
#     echo -e "${Cyan}[danfault - conda]${Color_Off} Downloading conda installation file."
#     cd $TEMPORARY_DANFAULT
#     curl -L -O "https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-$(uname)-$(uname -m).sh"
#     chmod +x Miniforge3-$(uname)-$(uname -m).sh
# fi

# if [ -d "${CONDA_PREFIX_PATH}" ]; then
#     echo -e "${Cyan}[danfault - conda]${Color_Off} Conda folder exists."
# else
#     echo -e "${Cyan}[danfault - conda]${Color_Off} Installing Conda"
#     ./Miniforge3-$(uname)-$(uname -m).sh -b -p "${CONDA_PREFIX_PATH}"
# fi
