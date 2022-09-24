import logging
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
        
