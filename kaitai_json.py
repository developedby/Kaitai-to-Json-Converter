"""
Converts binary files parsed by kaitai structs to json.
Author: Nicolas Abril"""
import argparse
import importlib
import json
import pathlib
import shlex
import subprocess
import sys
from collections import OrderedDict

import yaml


def compile_ksy(ksy_filepath):
    command = "kaitai-struct-compiler -t python {}".format(ksy_filepath)
    subprocess.run(shlex.split(command))
    new_file = pathlib.Path(ksy_filepath).with_suffix('py')
    return str(new_file)

def bin_to_dict(bin_filepath, ksy_filepath, compiled_filepath):
    with open(ksy_filepath, 'r') as ksy_file:
        ksy_dict = yaml.load(ksy_file)

    module_name = pathlib.Path(compiled_filepath).name
    kaitai_module = importlib.import_module(module_name)
    root_struct_type = ksy_dict['meta']['id']
    root_struct_class = getattr(kaitai_module, snake_to_pascal(root_struct_type))
    root_struct = root_struct_class.from_bin(bin_filepath)

    def struct_to_dict(struct, struct_type):
        nonlocal ksy_dict, root_struct_type
        out_dict = OrderedDict()
        if struct_type == root_struct_type:
            seq = ksy_dict['seq']
        else:
            seq = ksy_dict['types'][struct_type]['seq']
        for entry in seq:
            name = entry['id']
            type_ = entry.get('type', None)
            value = getattr(struct, name)
            if type_ in ksy_dict['types']:
                out_dict[name] = struct_to_dict(value, type_)
            else:
                out_dict[name] = value
        return out_dict
    return struct_to_dict(root_struct, root_struct_type)

def snake_to_pascal(string):
    return string.replace('_', ' ').title().replace(' ', '')


def main(args):
    if args.compiled_file is None:
        compiled_file = compile_ksy(args.ksy_file)
    else:
        compiled_file = args.compiled_file

    bin_dict = bin2dict(args.bin_file, args.ksy_file, compiled_file)
    
    if args.output_file is None:
        # No output file, print json to stdout
        json.dump(bin_dict, sys.stdout, indent=args.indent)
    else: 
        with open(args.output_file, 'r') as out_file:
            json.dump(bin_dict, out_file, indent=args.indent)

if __name__ == "__main__":
    parser = argparse.ArgumentParser("kaitai_json")
    parser.add_argument('bin_file')
    parser.add_argument('ksy_file')
    parser.add_argument('-c', '--compiled_file')
    parser.add_argument('-o', '--output_file')
    parser.add_argument('--ident', default=2)
    args = parser.parse_args()
    main(args)
