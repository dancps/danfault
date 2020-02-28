# VSCode 
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
python installExtensions.py -f [file]
```

Or manually by:

```bash
code --install-extension [EXTENSION]
```

## Links
* [How to export settings of Visual Studio Code?](https://stackoverflow.com/questions/35368889/how-to-export-settings-of-visual-studio-code)