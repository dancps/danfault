#!/usr/bin/env bash
SETUP_FILE=$(readlink -f $0)
SETUP_DIR=$(dirname $SETUP_FILE)
DANFAULT_DIR=$(realpath $SETUP_DIR/..)
TEMPORARY_DANFAULT=$(realpath $DANFAULT_DIR/.tmp/)
source $DANFAULT_DIR/dotfiles/.colors
source $DANFAULT_DIR/dotfiles/.alias
source $DANFAULT_DIR/dotfiles/.export
source $DANFAULT_DIR/dotfiles/.extra
source $DANFAULT_DIR/dotfiles/.source

WHITESUR_THEME=false
for arg in "$@"; do
    case $arg in
        --white-sur-theme) WHITESUR_THEME=true ;;
        *) echo "Unknown option: $arg"; echo "Usage: $0 [--white-sur-theme]"; exit 1 ;;
    esac
done

sudo apt update
sudo apt upgrade -y

sudo apt install curl -y


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
### zsh                                                                ###
###############################################################################
#
# 
#  Install zsh
echo -e "${Cyan}[danfault - ZSH]${Color_Off} Installing zsh"
sudo apt install zsh
# Install oh my zsh
echo -e "${Cyan}[danfault - Oh my zsh]${Color_Off} Installing ohmyzsh"
if [ -e ~/.oh-my-zsh ]
then
    echo -e "${Cyan}[danfault - Oh my zsh]${Color_Off} Oh my ZSH is already installed"
else
    echo -e "${Cyan}[danfault - Oh my zsh]${Color_Off} Installing ohmyzsh"
    sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)" --unattended
    # Sets default sh to zsh
    chsh -s $(which zsh)
fi


###############################################################################
### Docker                                                                  ###
###############################################################################
#
# 


# Add Docker's official GPG key:
echo -e "${Cyan}[danfault - Docker]${Color_Off} Adding docker GPG keys"
sudo apt-get update
sudo apt-get install ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

# Add the repository to Apt sources:
echo -e "${Cyan}[danfault - Docker]${Color_Off} Adding Docker repo to apt sources"
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update

echo -e "${Cyan}[danfault - Docker]${Color_Off} Installing docker"
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

echo -e "${Cyan}[danfault - Docker]${Color_Off} Verifying docker"
sudo docker run hello-world


###############################################################################
### Git                                                                     ###
###############################################################################
# Will install git and copy:
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
### Ghostty                                                                 ###
###############################################################################
# Will link:
#   - config.ghostty
#   - custom.css

echo -e "${Cyan}[danfault - Ghostty]${Color_Off} Linking Ghostty config"
mkdir -p ~/.config/ghostty
ln -sf $DANFAULT_DIR/terminal-configs/ghostty/config.ghostty ~/.config/ghostty/config.ghostty
ln -sf $DANFAULT_DIR/terminal-configs/ghostty/custom.css ~/.config/ghostty/custom.css


###############################################################################
### WhiteSur theme (optional: --white-sur-theme)                            ###
###############################################################################
# macOS-like GTK, libadwaita and GNOME Shell theme. See tips/ubuntu_whitesur_ghostty.md.

if [ "$WHITESUR_THEME" = true ]; then
    WHITESUR_DIR=~/Documents/projects/repos/WhiteSur-gtk-theme

    echo -e "${Cyan}[danfault - WhiteSur]${Color_Off} Installing dependencies"
    sudo apt install -y sassc libglib2.0-dev-bin gnome-shell-extensions

    if [ -d "$WHITESUR_DIR" ]; then
        echo -e "${Cyan}[danfault - WhiteSur]${Color_Off} Updating $WHITESUR_DIR"
        git -C $WHITESUR_DIR pull
    else
        echo -e "${Cyan}[danfault - WhiteSur]${Color_Off} Cloning into $WHITESUR_DIR"
        mkdir -p $(dirname $WHITESUR_DIR)
        git clone --depth=1 https://github.com/vinceliuice/WhiteSur-gtk-theme.git $WHITESUR_DIR
    fi

    # Must not run with sudo: -l writes into ~/.config/gtk-4.0
    echo -e "${Cyan}[danfault - WhiteSur]${Color_Off} Installing theme (libadwaita, 75% top bar opacity)"
    $WHITESUR_DIR/install.sh -l --shell -p 75

    echo -e "${Cyan}[danfault - WhiteSur]${Color_Off} Applying theme"
    gsettings set org.gnome.desktop.interface gtk-theme 'WhiteSur-Dark'
    gnome-extensions enable user-theme@gnome-shell-extensions.gcampax.github.com
    gsettings set org.gnome.shell.extensions.user-theme name 'WhiteSur-Dark'
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
    curl -L "https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-$(uname)-$(uname -m).sh" -o "${TEMPORARY_DANFAULT}/Miniforge3-$(uname)-$(uname -m).sh"
    chmod +x ${TEMPORARY_DANFAULT}/Miniforge3-$(uname)-$(uname -m).sh
fi

if [ -d "${CONDA_PREFIX_PATH}" ]; then
    echo -e "${Cyan}[danfault - conda]${Color_Off} Conda folder exists."
else
    echo -e "${Cyan}[danfault - conda]${Color_Off} Installing Conda from path:"
    ${TEMPORARY_DANFAULT}/Miniforge3-$(uname)-$(uname -m).sh -b -p ${CONDA_PREFIX_PATH}
fi
