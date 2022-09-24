
"""
Files will be read in increments of  `CHUNK_SIZE:int` bytes.

Default: 4096.
"""
CHUNK_SIZE:int = 4096

"""
File size limits. Won't limit file size if MAX_CHUNKS is None.

MAX_CHUNKS * CHUNK_SIZE = file size rounded up to the nearest 
integer where file size % chunk_size = 0.

Default: None
"""
MAX_CHUNKS:int = None

"""
Stringie will discard strings shorter than `MIN_STR_LEN:int`.

Default: 4
"""
MIN_STR_LEN:int = 4

"""
For the PartitionedBucket data type. Increase the key length to 
increase the number of partitions, but decrease the length of the 
sets or lists housing the bucket data.

Length:
- 1: 26 + 1 keys total (27)
- 2: 26 * 26 + 1 keys total (677)
- 3: 26 * 26 * 26 + 1 keys total (17,577)

Default: 1
"""
KEY_LEN:int = 1

"""
List denoting file extensions to ignore.
"""
IGNORE_EXTS:list[str] = []  
#["package", "zip", "img", "iso", "gz"]

