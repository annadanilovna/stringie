# stringie

Scans a file tree and extracts strings (currently, just ASCII, but other character sets are on the roadmap.) Essentially the same as using the results of a `find` command piped to `strings` with some extra processing in between to extract meaningful data

Most parameters are available on command line, but see `stringie/config.py` for a few additional options.

## Usage

    $ python stringie -h
    usage: stringie [-h] [-t TERMS_FILE] [-o OUTPUT] [-l MIN] [-x MAX] [-i] [-c] [-s] [-d] [-v] path

    Extracts meaningful strings out of mixed content in a tree.

    positional arguments:
    path                  Path to extract content from.

    options:
    -h, --help            show this help message and exit
    -t TERMS_FILE, --terms_file TERMS_FILE
                            File with search terms (one per line)
    -o OUTPUT, --output OUTPUT
                            Ouptut file (if not present will print to stdout
    -l MIN, --min MIN     Minimum length of fragment. Min value between this and value in config.
    -x MAX, --max MAX     Maximum length of fragment.
    -i, --ignore_case     Ignore case
    -c, --common          Extract common set (addresses, names, phone numbers, emails, domains...
    -s, --order           Sort results
    -d, --dedupe          Dedupe results (will sort list)
    -v, --verbose         Verbose logging
                                            

## TODO
- Language support