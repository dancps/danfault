import os
from pdf2image import convert_from_path
import argparse
import traceback
import pytesseract as tess
from datetime import datetime as dt
try:
    from termcolor import colored
except ImportError:
    def colored(inp,*s):
        return inp
try:
    from tqdm import tqdm
except ImportError:
    def tqdm(inp,*s):
        return inp

def calls(type_call):
    if(type_call=='error'): return '['+colored('x','red')+']'
    elif(type_call=='warning'): return '['+colored('!','yellow')+']'
    elif(type_call=='message'): return '['+colored('~','cyan')+']'

def generate_indexed_name(name,index,output=None,format=".png",debug=False):
    if not(format.startswith(".")): format = "."+format
    if format.replace(".","").lower() in ["png","jpg","jpeg","txt"]:
        format = format.lower()
    else:
        raise ValueError(f"Wrong format \"{format}\".")
    name_dir = os.path.dirname(name)
    
    # Defines the new name
    name_base = os.path.splitext(os.path.basename(name))[0]
    new_base = name_base+f"_{index}"+format
    
    # Defines the output dir
    output_path = os.path.join(name_dir,name_base) if output==None else os.path.join(output)
    output_path = os.path.realpath(output_path)
    if(not(os.path.isdir(output_path))):
        if(debug): print(f'{output_path} doesn\'t exist. Creating it...')
        os.makedirs(output_path)
    # Joins the output dir and the new name
    new = os.path.join(output_path, new_base)
    
    return new

def main():
    parser = argparse.ArgumentParser()

    parser.add_argument('-i', '--input', required=True, type=str, help='input')
    parser.add_argument('-o', '--output', type=str, help='output')
    parser.add_argument('-v', '--verbose', help='increase output verbosity', action='store_true')
    parser.add_argument('-d', '--debug', help='increase output verbosity', action='store_true')
    parser.add_argument('-t', '--text', help='tries to convert the image to text format', action='store_true')
    parser.add_argument('-l', '--language', type=str, default="eng", help='sets the language to the text convertion')
    # TODO: Add pages options
    #       Must suport single pages and intervals:
    #           -p 1 2 3 5:23 
    #       Must process weird page selections:
    #           -p -1 -> last page
   
    args = parser.parse_args()
   
    # Tests if the input file exists
    if(not(os.path.isfile(args.input))):
        input_file = None
        raise ValueError(f"O arquivo {args.input} não existe.")
    else:
        input_file = args.input

    # Convert the pdf to image
    images = convert_from_path(input_file)
    
    for i in tqdm(range(len(images))):
        new_img_name = generate_indexed_name(input_file,index=i,output=args.output,debug=args.debug)
        image = images[i]
        if(args.debug): print(new_img_name)
        image.save(new_img_name, 'PNG')
        
        if(args.text):
            new_text_name = generate_indexed_name(input_file,index=i,output=args.output,format=".txt",debug=args.debug)
            output_text = tess.image_to_string(image, lang=args.language)
            with open(new_text_name,'w') as fl:
                fl.write(output_text)

if(__name__=='__main__'):
    init=dt.now()
    try:
        main()
    except Exception as e:    
        print(e)
        print("Traceback do erro:")
        traceback.print_tb(e.__traceback__)
    end=dt.now()
    print(calls('message'),'Elapsed time: {}'.format(end-init))
