import argparse
import os
import sys
import json
import tkinter as tk
import platform
from annotate.spanannotator import SpanAnnotatorFrame
from annotate.spanannotator_relations import SpanAnnotatorRelationFrame
from annotate.version import __version__
from annotate.utils import validate
from annotate.exceptions import ConfigReadError


def main():
    parser = argparse.ArgumentParser("SATYA: Span Annotator Tool, Yet Another")
    parser.add_argument("config", help="config file to run with")
    parser.add_argument("--input", help="input file to load", default=None)
    parser.add_argument(
        "--usage",
        help="span annotator(default)/ span-relationship annotator(advanced)",
        default='default',
        choices=['default', 'advanced'],
    )

    args = parser.parse_args()
    config_file = os.path.expanduser(args.config)
    if not os.path.exists(config_file):
        print(f"ERROR: no config file at {config_file}")
        sys.exit(1)
    if config_file.endswith("json"):
        config_dict = json.load(open(config_file))
    elif config_file.endswith("yml") or config_file.endswith("yaml"):
        import yaml

        config_dict = yaml.load(open(config_file))
    else:
        print(f"ERROR: unsupported format for {config_file}")
        sys.exit(1)
    print(f"Span Annotator Version {__version__}")
    print(f"OS:{platform.system()}")
    root = tk.Tk()
    try:
        validate(config_dict)
    except ConfigReadError as e:
        print(e.msg)
        sys.exit(1)
    root.geometry("1300x700+200+200")
    annotator_frame = SpanAnnotatorFrame if args.usage == 'default' else SpanAnnotatorRelationFrame
    app = annotator_frame(root, config_dict, input_file=args.input)
    app.init_ui()
    root.mainloop()


if __name__ == "__main__":
    main()
