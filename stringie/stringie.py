"""Text extraction."""

import logging
import math
import os
from typing import Sequence
import string
import time

import config
from bucket import Bucket


class Stringie:
    """Grabs meaningful strings out of a collection of files """
    def __init__(self, terms_file:str=None, output_file:str=None, 
                 ignore_case:bool=True, extract_common:bool=True, 
                 order:bool=True, dedupe:bool=True, 
                 verbose_logging:bool=True, 
                 min_len:int=config.MIN_STR_LEN,
                 max_len:int=None) -> None:

        logging.basicConfig(level=logging.DEBUG if verbose_logging else logging.INFO)

        self._search_terms:list[str] = []
        if terms_file:
            with open(terms_file, "r") as fh:
                terms:list[str] = fh.read().split("\n")
                self._search_terms = [term.strip() for term in terms]
        self._output_file:str = output_file
        self._ignore_case: bool = ignore_case
        self._extract_common: bool = extract_common
        self._verbose_logging: bool = verbose_logging
        self._charset:str = string.ascii_letters + string.digits + string.punctuation
        self._bucket:Bucket = Bucket(dedupe=dedupe, order=order)
        self._min_len:int =  min(min_len, config.MIN_STR_LEN) if min_len else config.MIN_STR_LEN
    
        self._max_len:int = max_len

    def _log(self, mesg:str, level=logging.INFO) -> None:
        """Check level and if within verbosity, print log"""
        if level < logging.INFO and not self._verbose_logging:
            return
        logging.log(level, mesg)
    
    def _log_stats(self) -> None:
        """Print bucket stats to log."""
        logging.info(f"Bucket stats: {self._bucket.size()} elements")
          
    def scan_chunk(self, chunk:bytes) -> int:
        """Scan chunk of bytes."""
        frag:str = ""
        cnt:int = 0
        add:bool = False
        for i in range(0, len(chunk)):
            c:str = chr(chunk[i])
            if c in self._charset:
                frag += str(c)
            elif len(frag.strip()) > self._min_len:
                add = True
                if len(self._search_terms) > 0:
                    add = False
                    search = frag.lower() if self._ignore_case else frag
                    for term in self._search_terms:
                        if term in search:
                            add = True
                            break
                
                if add: 
                    self._bucket.add(frag.strip())
                    cnt += 1
                    frag = ""
            else:
                frag = ""
        return cnt

    def scan_file(self, path:str, fn:str) -> int:
        """Scan a file."""
        # self._log(f"Scanning file {path}")
        cnt:int = 0
        cur_chunk:int = 1
        path = f"{path}/{fn}"
        with open(path, "rb") as fh:
            chunks:int = int(math.ceil(os.stat(path).st_size / config.CHUNK_SIZE))
            # if config.MAX_CHUNKS is not None and chunks > config.MAX_CHUNKS:  # skip if too big
            #    return 0

            chunk:bytes = fh.read(config.CHUNK_SIZE)
            while chunk:
                if cur_chunk % 1000 == 0:
                    self._log(f"{fn}: Scanning chunk {cur_chunk}/{chunks} ({round(cur_chunk * 1.0/chunks * 100, 2)}% done)")
                cnt += self.scan_chunk(chunk)
                chunk = fh.read(config.CHUNK_SIZE)
                cur_chunk += 1
            self._log(f"{fn}: Done! ({cnt} found)")
        return cnt

    def scan_tree(self, path:str) -> int:
        """Scan tree."""
        if not os.path.exists(path):
            raise FileNotFoundError(f"{path} does not exist.")

        self._log(f"Scanning tree {path}")

        # First scan the tree, then run over files. This allows some semblance of a completion percentage.
        cnt:int = 0
        total_size:int = 0
        files = []
        for root, _, fns in os.walk(path):
            for fn in fns:
                if fn.split(".").pop() in config.IGNORE_EXTS:
                    exts: str = ", ".join(config.IGNORE_EXTS)
                    logging.warn(f"ignoring files with the following extensions currently: {exts}.")
                    continue
            
                fsize = os.stat(f"{root}/{fn}").st_size
                files.append([root, fn, fsize])
                total_size += fsize

        scan_ctr:int = 1
        scan_size_ctr:int = 0
        num_files:int = len(files)
        self._log(f"Found {num_files} to scan.")
        for flist in files:

            scan_size_ctr += flist[2]

            pct_file_done:float = round(scan_ctr / num_files * 100, 2)
            pct_size_done:float = round(scan_size_ctr / total_size * 100, 2)

            cnt += self.scan_file(flist[0], flist[1]) 
            self._log(f"Scanning file {scan_ctr} of {num_files} ({pct_file_done}% files complete) / {pct_size_done}% of bytes scanned)")
            scan_ctr += 1
        self._log(f"Done! ({cnt} found)")
        return cnt
        
    def scan(self, path:str) -> None:
        """Scan tree."""
        self.scan_tree(path)
        self._print_results()

    def _print_results(self):
        """Output results to file or stdout."""
        if self._output_file:
            with open(self._output_file, "w") as fh:
                for s in self._bucket:
                    fh.write(f"{s}\n")
        else:
            for s in self._bucket:
                print(s)