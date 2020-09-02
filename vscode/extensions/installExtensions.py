import os
import argparse

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-f","--file",default="./extensions.txt")
    args = parser.parse_args()

    cwd = os.getcwd()
    file_path=args.file
    print("-> Installing from file {}".format(os.path.join(cwd,file_path)))

    ext_file = open(os.path.join(cwd,file_path))#open file
    for extension in ext_file:
        if(extension.startswith("#")): continue
        command = 'code --install-extension {}'.format(extension.strip())
        print("+ Installing {}".format(extension.strip()))
        os.system(command)

if(__name__=="__main__"):
    main()