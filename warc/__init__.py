"""
warc
~~~~

Python library to work with WARC files.

:copyright: (c) 2012 Internet Archive
"""

from .arc import ARCFile, ARCRecord, ARCHeader
from .warc import WARCFile, WARCRecord, WARCHeader, WARCReader
from .utils import HTTPObject

def detect_format(filename):
    """Tries to figure out the type of the file. Return 'warc' for
    WARC files and 'arc' for ARC files"""

    if filename.endswith(".warc") or filename.endswith(".warc.gz"):
        return "warc"

    return "unknown"

def open(filename, mode="rb", format = None):
    """Shorthand for WARCFile(filename, mode).

    Auto detects file and opens it.

    """
    if format == "auto" or format == None:
        format = detect_format(filename)

    if format == "warc":
        return WARCFile(filename, mode)
    elif format == "arc":
        return ARCFile(filename, mode)
    else:
        raise IOError("Don't know how to open '%s' files"%format)
