- [Git+Overleaf+VSCode](https://maumneto.medium.com/git-vs-code-overleaf-91ecfd586b36)
- [Using Latexmk](https://mg.readthedocs.io/latexmk.html)
- [How does Overleaf compile my project?](https://www.overleaf.com/learn/how-to/How_does_Overleaf_compile_my_project%3F)
- [Specify -output-directory when using latexmk](https://tex.stackexchange.com/questions/11710/specify-output-directory-when-using-latexmk)
- [Using ](https://tex.stackexchange.com/questions/462365/how-to-use-latex-on-vs-code)
<!-- - []()
- []()
- []()
- []()
- []()
- []() -->

# MikTeX

To instsall MikTeX:
```sh
curl -fsSL https://miktex.org/download/key | sudo tee /usr/share/keyrings/miktex-keyring.asc > /dev/null

echo "deb [signed-by=/usr/share/keyrings/miktex-keyring.asc] https://miktex.org/download/ubuntu noble universe" | sudo tee /etc/apt/sources.list.d/miktex.list


sudo apt-get update
sudo apt-get install miktex
```

To install the depencies to the latexindent:
```sh
sudo apt install libyaml-tiny-perl
sudo apt install libfile-homedir-perl
sudo apt install libfuse2 # This might crash Ubuntu

```

If ubuntu crashes, after restart ctrl+alt+F1(or F2) and:
```sh
systemctl start NetworkManager
sudo apt install ubuntu-desktop
reboot
```

In MacOS: 
```sh
brew install latexindent
```

## References
- [MikTex: Download](https://miktex.org/download)