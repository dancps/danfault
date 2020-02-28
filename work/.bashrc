# .bashrc

# Source global definitions
if [ -f /etc/bashrc ]; then
	. /etc/bashrc
fi

# The original propmt scheme was
#     [\u@\h \W]\$
PS1='${debian_chroot:+($debian_chroot)}\[\033[01;32m\]\u\[\033[00m\]:\[\033[01;34m\]\w\[\033[00m\]\$ '
# Ubuntu's original PS1 was
#     PS1='${debian_chroot:+($debian_chroot)}\[\033[01;32m\]\u@\h\[\033[00m\]:\[\033[01;34m\]\w\[\033[00m\]\$ '

# Uncomment the following line if you don't like systemctl's auto-paging feature:
# export SYSTEMD_PAGER=

# User specific aliases and functions
alias cl='clear'
alias python='python3.5'
alias pip='pip3.5'
alias ccc_004='ssh dancps@dccxl004.pok.ibm.com'
alias power9='ssh dancps@9.7.243.29'
alias xccc_001='ssh dancps@dccxc001.pok.ibm.com'
alias ibm='source /home/dancps/venvs/IBM/bin/activate'
alias psp='source /home/dancps/Documents/Study/CNN/PSPNet/venvs/PSPNet-tf/bin/activate'
alias gpn_dir='cd /home/dancps/Documents/Projetos/ws1/gpn_deeplab_psp'
alias felipe='source /home/dancps/Documents/Projetos/ws1/venvs/PSPFelipe/bin/activate'

# Exports
export PATH=$PATH:~/software/ImageJ/
export PATH=$PATH:/home/dancps/software/ffmpeg/ffmpeg-4.2.1/bin
export PATH=$PATH:/home/dancps/software/pandoc-2.9.2/bin

export MESH_OPT_DIR='/home/dancps/Documents/Projetos/ws1/libraries/mesh-optimization'
