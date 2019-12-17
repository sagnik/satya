import argparse
import os
import sys
import json
import tkinter as tk
import platform
from annotate.spanannotator import SpanAnnotatorFrame
from annotate.version import __version__
from annotate.consts import SHORTCUT_LABELS_KEY, RESERVED_SHORT_CUT_CHARS


def main():
    parser = argparse.ArgumentParser('SATYA: Span Annotator Tool, Yet Another')
    parser.add_argument('config', help='config file to run with')
    args = parser.parse_args()
    config_file = os.path.expanduser(args.config)
    if not os.path.exists(config_file):
        print(f'ERROR: no config file at {config_file}')
        sys.exit(1)
    if config_file.endswith('json'):
        config_dict = json.load(open(config_file))
    elif config_file.endswith('yml') or config_file.endswith('yaml'):
        import yaml
        config_dict = yaml.load(open(config_file))
    else:
        print(f'ERROR: unsupported format for {config_file}')
        sys.exit(1)
    print(f'Span Annotator Version {__version__}')
    print(f'OS:{platform.system()}')
    root = tk.Tk()
    root.geometry("1300x700+200+200")
    shortcut_labels = config_dict.get(SHORTCUT_LABELS_KEY, {})
    for shortcut_label in shortcut_labels:
        if shortcut_label in RESERVED_SHORT_CUT_CHARS:
            print(f'char [{shortcut_label}] can not be used as a short cut key')
            sys.exit(1)
    app = SpanAnnotatorFrame(root, config_dict)
    root.mainloop()


if __name__ == '__main__':
    main()
