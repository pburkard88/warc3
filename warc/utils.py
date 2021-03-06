"""
warc.utils
~~~~~~~~~~

This file is part of warc

:copyright: (c) 2012 Internet Archive
"""

from collections import MutableMapping, Mapping
from http.client import HTTPMessage
import email.parser
import sys
import re

SEP = re.compile("[;:=]")

class CaseInsensitiveDict(MutableMapping):
    """Almost like a dictionary, but keys are case-insensitive.

        >>> d = CaseInsensitiveDict(foo=1, Bar=2)
        >>> d['foo']
        1
        >>> d['bar']
        2
        >>> d['Foo'] = 11
        >>> d['FOO']
        11
        >>> d.keys()
        ["foo", "bar"]
    """
    def __init__(self, *args, **kwargs):
        self._d = {}
        self.update(dict(*args, **kwargs))

    def __setitem__(self, name, value):
        self._d[name.lower()] = value

    def __getitem__(self, name):
        return self._d[name.lower()]

    def __delitem__(self, name):
        del self._d[name.lower()]

    def __eq__(self, other):
        return isinstance(other, CaseInsensitiveDict) and other._d == self._d

    def __iter__(self):
        return iter(self._d)

    def __len__(self):
        return len(self._d)

class FilePart:
    """File interface over a part of file.

    Takes a file and length to read from the file and returns a file-object
    over that part of the file.
    """
    def __init__(self, fileobj, length):
        self.fileobj = fileobj
        self.length = length
        self.offset = 0
        self.buf = b''

    def read(self, size=-1):
        if size == -1:
            size = self.length

        if len(self.buf) >= size:
            content = self.buf[:size]
            self.buf = self.buf[size:]
        else:
            size = min(size, self.length - self.offset)
            content = self.buf + self.fileobj.read(size - len(self.buf))
            self.buf = b''
        self.offset += len(content)
        return content

    def _unread(self, content):
        self.buf = content + self.buf
        self.offset -= len(content)

    def readline(self, size=1024):
        chunks = []
        chunk = self.read(size)
        while chunk and b"\n" not in chunk:
            chunks.append(chunk)
            chunk = self.read(size)

        if b"\n" in chunk:
            index = chunk.index(b"\n")
            self._unread(chunk[index+1:])
            chunk = chunk[:index+1]
        chunks.append(chunk)
        return b"".join(chunks)

    def __iter__(self):
        line = self.readline()
        while line:
            yield line
            line = self.readline()

class HTTPObject(CaseInsensitiveDict):
    """Small object to help with parsing HTTP warc entries"""
    def __init__(self, request_file):
        #Parse version line
        id_str_raw = request_file.readline()
        id_str = id_str_raw.decode("iso-8859-1")
        if "HTTP" not in id_str:
            #This is not an HTTP object.
            request_file._unread(id_str_raw)
            raise ValueError("Object is not HTTP.")

        words = id_str.split()
        command = path = status = error = version = None
        #If length is not 3 it is a bad version line.
        if len(words) >= 3:
            if words[1].isdigit():
                version = words[0]
                error = words[1]
                status = " ".join(words[2:])
            else:
                command, path, version = words

        self._id = {
            "vline": id_str_raw,
            "command": command,
            "path": path,
            "status": status,
            "error": error,
            "version": version,
        }

        self._header, self.hstring = self._parse_headers(request_file)
        super().__init__(self._header)
        self.payload = request_file
        self._content = None

    @staticmethod
    def _parse_headers(fp):
        """This is a modification of the python3 http.clint.parse_headers function."""
        headers = []
        while True:
            line = fp.readline(65536)
            headers.append(line)
            if line in (b'\r\n', b'\n', b''):
                break
        hstring = b''.join(headers)
        return email.parser.Parser(_class=HTTPMessage).parsestr(hstring.decode('iso-8859-1')), hstring

    def __repr__(self):
        return(self.vline + str(self._header))

    def __getitem__(self, name):
        try:
            return super().__getitem__(name)
        except KeyError:
            value = name.lower()
            if value == "content_type":
                return self.content.type
            elif value in self.content:
                return self.content[value]
            elif value in self._id:
                return self._id[value]
            else:
                raise

    def _reset(self):
        self.payload._unread(self.hstring)
        self.payload._unread(self._id['vline'])

    def write_to(self, f):
        f.write(self._id['vline'])
        f.write(self.hstring)
        f.write(self.payload.read())
        f.write(b"\r\n\r\n")
        f.flush()

    @property
    def content(self):
        if self._content is None:
            try:
                string = self._d["content-type"]
            except KeyError:
                string = ''
            self._content = ContentType(string)
        return self._content

    @property
    def vline(self):
        return self._id["vline"].decode("iso-8859-1")

    @property
    def version(self):
        return self._id["version"]

    def write_payload_to(self, fp):
        encoding = self._header.get("Transfer-Encoding", "None")
        if encoding == "chunked":
            found = b''
            length = int(str(self.payload.readline(), "iso-8859-1").rstrip(), 16)
            while length > 0:
                found += self.payload.read(length)
                self.payload.readline()
                length = int(str(self.payload.readline(), "iso-8859-1").rstrip(), 16)
        else:
            length = int(self._header.get("Content-Length", -1))
            found = self.payload.read(length)

        fp.write(found)

class ContentType(CaseInsensitiveDict):
    def __init__(self, string):
        data = {}
        self.type = ''
        if string:
            _list = [i.strip() for i in string.lower().split(";")]
            self.type = _list[0]

            data["type"] = _list[0]
            for i in _list[1:]:
                test = [n.strip() for n in re.split(SEP, i)]
                data[test[0]] = test[1]

        super().__init__(data)

    def __repr__(self):
        return self.type

