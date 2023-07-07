#!/bin/bash
echo "++++++++++++++++++++++++++++++++++++++++ VSCODE"
CODE_FOLDER=$(grealpath ~/Library/Application\ Support/Code/User/)
echo Code path: $CODE_FOLDER


DANFAULT_DIR=$(grealpath $(dirname "$0")/..) # Relative to the pwd
echo "Danfault dir: $DANFAULT_DIR"

echo "Copying files to code dir:"
echo "  Keybindings"
cp "$CODE_FOLDER/keybindings.json" "$CODE_FOLDER/keybindings_backup.json"
cp "$DANFAULT_DIR/vscode/config/keybindings_mac.json" "$CODE_FOLDER/keybindings.json"


echo "  Snippets"
cp "$DANFAULT_DIR/vscode/snippets/python.json" "$CODE_FOLDER/snippets/"

# /Users/dancps/danfault/vscode/config/keybinds_mac.json