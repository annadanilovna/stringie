"""Text extraction."""

import logging
import math
import os
from typing import Sequence
import string
import time

import config


class Bucket:
    """Partitioned dictionary."""
    def __init__(self, dedupe:bool=True, order:bool=True) -> None:
        self._dedupe:bool = dedupe
        self._order:bool = order
        self._data:dict = {}
        self._size:int = 0
        self._last_pruning:int = 0
        self._prune_interval: int = 10000
        self._part_keys:enumerate = None
        self._part_key_itr:str = None
        self._part_itr:int = None

    def order(self) -> bool:
        return self._order

    def dedupe(self) -> bool:
        return self._dedupe

    def size(self) -> int:
        return self._size

    def prune(self) -> None:
        """
        Speediest way is to prune periodically rather than on insertion.
        """
        st:float = time.time()
        new_size:int = 0

        logging.info("Pruning results. This may take a second...")
        for k in self._data:
            if self._dedupe:
                self._data[k] = list(set(self._data[k]))
            if self._order:
                self._data[k] = sorted(self._data[k])
            new_size += len(self._data[k])
        el:float = round(time.time() - st, 2)
        
        logging.info(f"Done in {el}s. Size was {self.size()}, now {new_size}")
        self._last_pruning = self.size()
        self._size = new_size

    def _get_part_key(self, s:str) -> str:
        """Key a string value. Returns the partition key."""
        pk:str = ""
        for i in range(0, len(s)):
            c:str = s[i].lower()
            if c in string.ascii_lowercase:
                pk += c
                if len(pk) == config.KEY_LEN:
                    break

        if len(pk) == 0:  # fallback
            pk = "_"
        return pk

    def _init_part(self, pk:str) -> None:
        """Initialize a new partition."""
        self._data[pk] = []

    def _part_add(self, pk:str, val:str) -> None:
        """Add value to partition."""
        self._data[pk].append(val)
        self._size += 1

    def _needs_pruning(self) -> bool:
        """Returns true if needs pruning."""
        return True if self.size() - self._last_pruning > self._prune_interval else False

    def add(self, val:str) -> None:
        """Add a value."""
        pk: str = self._get_part_key(val)
        if pk not in self._data:
            self._init_part(pk)
        self._part_add(pk, val)   

        if self._needs_pruning():
            self.prune()
    
    def __iter__(self) -> object:
        """Set up to iterate over the bucket."""
        self._part_keys:enumerate = enumerate(self._data.keys())
        _, self._part_key_itr = next(self._part_keys)
        self._part_itr = 0
        return self

    def __next__(self) -> str:
        """Get next value."""
    
        # if no values yet, or done
        if len(self._data[self._part_key_itr]) <= self._part_itr:
            _, self._part_key_itr = next(self._part_keys) 
            self._part_itr = 0

            # recursively call again (non-empty bucket issue)
            return self.__next__()

        v:str = self._data[self._part_key_itr][self._part_itr]
        self._part_itr += 1

        return v
        
            
class Stringie:
    """Grabs meaningful strings out of a collection of files """
    def __init__(self, terms_file:str=None, output_file:str=None, 
                 ignore_case:bool=True, extract_common:bool=True, 
                 order:bool=True, dedupe:bool=True, 
                 verbose_logging:bool=True) -> None:

        logging.basicConfig(level=logging.DEBUG if verbose_logging else logging.INFO)

        self._terms_file:str = terms_file
        self._output_file:str = output_file
        self._ignore_case: bool = ignore_case
        self._extract_common: bool = extract_common
        self._verbose_logging: bool = verbose_logging
        self._charset:str = string.ascii_letters + string.digits + string.punctuation
        self._bucket:Bucket = Bucket(dedupe=dedupe, order=order)


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
        for i in range(0, len(chunk)):
            c:str = chr(chunk[i])
            if c in self._charset:
                frag += str(c)
            elif len(frag.strip()) > config.MIN_STR_LEN:
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
            if config.MAX_CHUNKS is not None and chunks > config.MAX_CHUNKS:  # skip if too big
                return 0

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

        cnt:int = 0
        for root, _, fns in os.walk(path):
            for fn in fns:
                if fn.split(".").pop() in config.IGNORE_EXTS:
                    exts: str = ", ".join(config.IGNORE_EXTS)
                    logging.warn(f"ignoring files with the following extensions currently: {exts}.")
                    continue
                cnt += self.scan_file(root, fn)
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