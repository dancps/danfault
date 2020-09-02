# VSCode 
## Python, configure everything to me please
```bash
python vscode_config.py
```

## Configs
Just copy config files to:
* `~/.config/Code/User` on Linux
* `C:\Users\username\AppData\Roaming\Code\User` on Windows 10

## Extensions

To get the list of extensions and add to the `extensions.txt` use:

```bash
code --list-extensions >> extensions.txt
```

To install you may use:

```bash
python extensions/installExtensions.py -f [file]
```

Or manually by:

```bash
code --install-extension [EXTENSION]
```

## Snippets
Just copy config files to:
* `~/.config/Code/User/snippets` on Linux
* `C:\Users\username\AppData\Roaming\Code\User\snippets` on Windows 10 (?)


## Links
* [How to export settings of Visual Studio Code?](https://stackoverflow.com/questions/35368889/how-to-export-settings-of-visual-studio-code)