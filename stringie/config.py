
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
MIN_STR_LEN:int = 3

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

The first line is media types which are largely useless, unless looking for data 
in EXIF, ID3, etc. OR steganography is involved.

The second line is generally included just because the files are large.
"""
IGNORE_EXTS:list[str] = ["mov", "mp4", "wav", "gif", "jpg", "png", "bmp",  # these typically don't have anything 
                         "package", "zip", "img", "iso", "gz"]  # these are typically really big and really slow

