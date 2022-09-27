"""Text extraction."""

import logging
import math
import os
import string
import time
from dataclasses import dataclass, field
from io import TextIOWrapper

import config


class Bucket:
    """Partitioned dictionary."""
    def __init__(self) -> None:
        self._data:set = set()

    def size(self) -> int:
        return len(self._data)

    def add(self, val:str) -> None:
        """Add a value."""
        self._data.add(val)

    def flush(self, stdout:bool=True, fn:str=None, append:bool=True) -> None:
        """
        Flush the bucket to disk or stdout.
        """
        fh:TextIOWrapper = None
        if fn is not None:
            fh = open(fn, "a" if append is True else "w")
        
        if stdout is False and fn is None:
            return

        for v in self._data:
            if stdout is True:
                print(v)
            if fh is not None:
                fh.write(f"{v}\n")


@dataclass 
class StringieScanFile:
    root:str
    fn:str
    path:str = field(init=False)
    size:int = field(init=False)
    chunks:int = field(init=False)

    def __post_init__(self):
        self.path = f"{self.root}/{self.fn}"
        self.size:int = os.stat(self.path).st_size
        self.chunks:int = int(math.ceil(self.size / config.CHUNK_SIZE))

@dataclass 
class StringieScan:
    files:list[StringieScanFile] = field(init=False)
    total_size:int = field(init=False)

    def __post_init__(self) -> None:
        self.files = []
        self.total_size = 0
    

class Stringie:
    """Grabs meaningful strings out of a collection of files """
    def __init__(self, terms_file:str=None, output_file:str=None,
                 ignore_case:bool=True, extract_common:bool=True,
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
        self._bucket:Bucket = Bucket()
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
                    search:str = frag.lower() if self._ignore_case else frag
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

    def scan_file(self, ssf:StringieScanFile) -> int:
        """Scan a file."""
        # self._log(f"Scanning file {path}")
        cnt:int = 0
        cur_chunk:int = 1
        
        with open(ssf.path, "rb") as fh:
            # if config.MAX_CHUNKS is not None and chunks > config.MAX_CHUNKS:  # skip if too big
            #    return 0
            chunk:bytes = fh.read(config.CHUNK_SIZE)
            while chunk:
                if cur_chunk % 1000 == 0:
                    a:str = f"Scanning chunk {cur_chunk}/{ssf.chunks}"
                    b:str = f"({round(cur_chunk * 1.0/ssf.chunks * 100, 2)}% done)"
                    c:str = f"({cnt} found)"
                    self._log(f"{ssf.fn}: {a} {b} {c}")
                cnt += self.scan_chunk(chunk)
                chunk = fh.read(config.CHUNK_SIZE)
                cur_chunk += 1
            self._log(f"{ssf.fn}: Done! ({cnt} found)")
            self._bucket.flush(stdout=False, fn="tmp-output.txt", append=True)
        return cnt

    def scan_tree(self, path:str) -> int:
        """Scan tree."""
        if not os.path.exists(path):
            raise FileNotFoundError(f"{path} does not exist.")

        # First scan the tree, then run over files. This allows some semblance of a completion percentage.
        cnt:int = 0
        total_size:int = 0
        files:list[StringieScanFile] = []
        scan_size_ctr:int = 0
        num_files:int = 0

        for root, _, fns in os.walk(path):
            for fn in fns:
                if fn.split(".").pop() in config.IGNORE_EXTS:
                    logging.warn(f"ignoring files with the following extensions currently: {config.IGNORE_EXTS_STR}.")
                    continue
                ssf:StringieScanFile = StringieScanFile(root=root, fn=fn)
                files.append(ssf)
                total_size += ssf.size

        num_files = len(files)
        self._log(f"Found {num_files} ({total_size} bytes) to scan.")

        for idx in range(0, num_files):
            scan_size_ctr += files[idx].size
            pct_file_done:float = round(idx / num_files * 100, 2)
            pct_size_done:float = round(scan_size_ctr / total_size * 100, 2)

            cnt += self.scan_file(files[idx])

            self._log(f"Scanning file {idx} of {num_files} ({pct_file_done}% files complete) / {pct_size_done}% of bytes scanned)")        
        return cnt

    def scan(self, path:str) -> None:
        """Scan tree."""
        self._log(f"Scanning {path}")

        # scan tree
        cnt:int = self.scan_tree(path)
        
        self._log(f"Done! ({cnt} found)")
        
        # print results
        self._bucket.flush(stdout=True, fn=self._output_file, append=False)
