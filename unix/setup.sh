#!/usr/bin/env bash
DANFAULT_DIR=$(realpath $(dirname $(readlink -f setup.sh))/../)
TEMPORARY_DANFAULT=$(realpath $DANFAULT_DIR/.tmp/)
source $DANFAULT_DIR/dotfiles/.colors
source $DANFAULT_DIR/dotfiles/.alias
source $DANFAULT_DIR/dotfiles/.export
source $DANFAULT_DIR/dotfiles/.extra
source $DANFAULT_DIR/dotfiles/.source

# sudo apt update
# sudo apt upgrade -y

# sudo apt install curl -y

# TODO: install zsh
# TODO: install oh my zsh

echo -e "${Green}+==============================================================================+${Color_Off}" 
echo -e "${Green}+==         ${BGreen}danfault Setup${Color_Off}${Green}                                                   ==+${Color_Off}" 
echo -e "${Green}+==============================================================================+${Color_Off}" 
echo -e "${Green}+${Color_Off} ${BWhite}System:${Color_Off} $(uname) - $(uname -m)" 

echo -e "${Green}+ Variables:${Color_Off}" 
echo -e "${Green}+${Color_Off}  ${BWhite}DANFAULT_DIR:${Color_Off}       ${DANFAULT_DIR}" 
echo -e "${Green}+${Color_Off}  ${BWhite}TEMPORARY_DANFAULT:${Color_Off} ${TEMPORARY_DANFAULT}" 
echo -e "${Green}+==============================================================================+${Color_Off}" 



###############################################################################
### Variables and setup                                                      ###
###############################################################################
# Will set needed variables into .zshrc.

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


if [ -d "$TEMPORARY_DANFAULT" ]; then
  echo -e "${Cyan}[danfault - Setup]${Color_Off} Temporary danfault dir exists."
else
  echo -e "${Cyan}[danfault - Setup]${Color_Off} Temporary danfault dir does not exists. Creating $TEMPORARY_DANFAULT..."
  mkdir $TEMPORARY_DANFAULT
fi


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


###############################################################################
### VSCode                                                                  ###
###############################################################################
# Will copy:
#   - settings.json
#   - keybindings.json
#   - snippets/python.json

echo -e "${Cyan}[danfault - VSCode]${Color_Off} Setting-up VSCode files" 
if [ -e ~/.config/Code/User/settings.json ]
then
    echo -e "${Cyan}[danfault - VSCode]${Color_Off} Setting file already exists. Backing up into ~/.config/Code/User/settings_backup_$(date +%d%m%y%H%M%S).json"
    # cp ~/.config/Code/User/settings.json ~/.config/Code/User/settings_backup_$(date +%d%m%y%H%M%S).json
    cp $DANFAULT_DIR/vscode/config/settings.json ~/.config/Code/User/settings.json
else
    echo -e "${Cyan}[danfault - VSCode]${Color_Off} Setting file does not exists."
    cp $DANFAULT_DIR/vscode/config/settings.json ~/.config/Code/User/settings.json
fi

if [ -e ~/.config/Code/User/keybindings.json ]
then
    echo -e "${Cyan}[danfault - VSCode]${Color_Off} Keybindings file already exists. Backing up into ~/.config/Code/User/keybindings_backup_$(date +%d%m%y%H%M%S).json"
    # cp ~/.config/Code/User/keybindings.json ~/.config/Code/User/keybindings_backup_$(date +%d%m%y%H%M%S).json
    cp $DANFAULT_DIR/vscode/config/keybindings.json ~/.config/Code/User/keybindings.json
else
    echo -e "${Cyan}[danfault - VSCode]${Color_Off} Keybindings file does not exists."
    cp $DANFAULT_DIR/vscode/config/keybindings.json ~/.config/Code/User/keybindings.json
fi


if [ -e ~/.config/Code/User/snippets/python.json ]
then
    echo -e "${Cyan}[danfault - VSCode]${Color_Off} Python snippets file already exists. Backing up into ~/.config/Code/User/snippets/python_backup_$(date +%d%m%y%H%M%S).json"
    # cp ~/.config/Code/User/snippets/python.json ~/.config/Code/User/snippets/python_backup_$(date +%d%m%y%H%M%S).json
    cp $DANFAULT_DIR/vscode/snippets/python.json ~/.config/Code/User/snippets/python.json
else
    echo -e "${Cyan}[danfault - VSCode]${Color_Off} Python snippets file does not exists."
    cp $DANFAULT_DIR/vscode/snippets/python.json ~/.config/Code/User/snippets/python.json
fi


###############################################################################
### Miniforge                                                               ###
###############################################################################
# Will install conda at $HOME/conda/

echo -e "${Cyan}[danfault - conda]${Color_Off} Conda installation" 
CONDA_PREFIX_PATH=${HOME}/conda

if [ -e ${TEMPORARY_DANFAULT}/Miniforge3-$(uname)-$(uname -m).sh ]
then
    echo -e "${Cyan}[danfault - conda]${Color_Off} Conda installation file already exists at ${TEMPORARY_DANFAULT}/Miniforge3-$(uname)-$(uname -m).sh"
else
    echo -e "${Cyan}[danfault - conda]${Color_Off} Downloading conda installation file."
    cd $TEMPORARY_DANFAULT
    curl -L -O "https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-$(uname)-$(uname -m).sh"
    chmod +x Miniforge3-$(uname)-$(uname -m).sh
fi

if [ -d "${CONDA_PREFIX_PATH}" ]; then
    echo -e "${Cyan}[danfault - conda]${Color_Off} Conda folder exists."
else
    echo -e "${Cyan}[danfault - conda]${Color_Off} Installing Conda"
    ./Miniforge3-$(uname)-$(uname -m).sh -b -p "${CONDA_PREFIX_PATH}"
fi


