#!/usr/bin/env python
"""Main entry point for stringie"""

import argparse
from typing import Sequence

from stringie import Stringie


if __name__ == "__main__":

    parser:argparse.ArgumentParser= argparse.ArgumentParser(description="Extracts meaningful strings out of mixed content in a tree.")

    # required base path
    parser.add_argument("path", help="Path to extract content from.")

    # optional string parameters
    parser.add_argument("-t", "--terms_file", help="File with search terms (one per line)")
    parser.add_argument("-o", "--output", help="Ouptut file (if not present will print to stdout")

    # boolean flags
    parser.add_argument("-i", "--ignore_case", help="Ignore case", action="store_true")
    parser.add_argument("-c", "--common", help="Extract common set (addresses, names, phone numbers, emails, domains...", action="store_true")
    parser.add_argument("-s", "--order", help="Sort results", action="store_true")
    parser.add_argument("-d", "--dedupe", help="Dedupe results (will sort list)", action="store_true")
    parser.add_argument("-v", "--verbose", help="Verbose logging", action="store_true")

    args:Sequence[str] = parser.parse_args()

    s:Stringie = Stringie(ignore_case=args.ignore_case,
                          terms_file=args.terms_file,
                          extract_common=args.common, 
                          output_file=args.output,
                          order=args.order, 
                          dedupe=args.dedupe, 
                          verbose_logging=args.verbose)

    s.scan(args.path)