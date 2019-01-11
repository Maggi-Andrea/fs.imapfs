'''
Created on 06 dic 2018

@author: Andrea
'''
from symbol import except_clause
"""Manage filesystems on remote IMAP servers.
"""
# from __future__ import print_function
# from __future__ import unicode_literals

import calendar
import io
import re
import itertools
import socket
import threading
import typing
import email
from collections import OrderedDict
from contextlib import contextmanager

from imapclient import IMAPClient
from imaplib import IMAP4

# from ftplib import FTP

from six import PY2
from six import text_type

from . import errors
from .base import FS
from .constants import DEFAULT_CHUNK_SIZE
from .enums import ResourceType
from .enums import Seek
from .info import Info as BaseInfo
from .iotools import line_iterator
from .mode import Mode
from .path import abspath
from .path import dirname
from .path import basename
from .path import normpath
from .path import split

from imapclient.response_types import Envelope


_F = typing.TypeVar("_F", bound="IMAPFS")


__all__ = ["IMAPFS"]

RE_APPEND = re.compile(r'\[(?P<list>(.*?))\]')

class Info(BaseInfo):
    
    @property
    def flags(self):  # noqa: D402
        # type: () -> Optional[List[str]]
        """`List[str]`: the list of the flags`.

        Requires the ``"imap"`` namespace.

        Raises:
            ~fs.errors.MissingInfoNamespace: if the ``"imap"``
                namespace is not in the Info.

        """
        self._require_namespace("imap")
        return self.get("imap", "flags")
    
    @property
    def envelope(self):  # noqa: D402
        # type: () -> Optional[Envelope]
        """`Envelope`: mail envelope`.

        Requires the ``"imap"`` namespace.

        Raises:
            ~fs.errors.MissingInfoNamespace: if the ``"imap"``
                namespace is not in the Info.

        """
        self._require_namespace("imap")
        return self.get("imap", "envelope", None)

@contextmanager
def imap_errors(fs, path=None):
    # type: (IMAPFS, Optional[Text]) -> Iterator[None]
    try:
        with fs._lock:
            yield
    except socket.error:
        raise errors.RemoteConnectionError(
            msg="unable to connect to {}".format(fs.host)
        )
    except IMAP4.error as error:
        if path is not None:
            raise errors.ResourceError(
                path, msg="imap error on resource '{}' ({})".format(path, error)
            )
        else:
            raise errors.OperationFailed(msg="imap error ({})".format(error))
    except errors.FSError as e:
        raise e
    except Exception as e:
        raise errors.FSError(str(type(e)))

def imap_path(path, delimiter = '/'):
    path = path.lstrip('/') if path.startswith('/') else path
    path = path.rstrip('/') if path.endswith('/') else path
    path = path.replace('/', delimiter)
    return path

def imap_splitext(file_name):
    parts = file_name.split('.')
    if len(parts) == 1:
        return parts[0], ''
    return '.'.join(parts[:-1]), parts[-1]

def imap_join(delimiter, *paths):
    # type: (*Text) -> Text
    """Join any number of paths together.

    Arguments:
        *paths (str): Paths to join, given as positional arguments.

    Returns:
        str: The joined path.

    Example:
        >>> join('foo', 'bar', 'baz')
        'foo/bar/baz'
        >>> join('foo/bar', '../baz')
        'foo/baz'
        >>> join('foo/bar', '/baz')
        '/baz'

    """
    relpaths = []  # type: List[Text]
    for p in paths:
        if p:
            if p[0] == "/":
                del relpaths[:]
            relpaths.append(p)

    path = delimiter.join(relpaths)
    return path

def _parse_imap_error(error):
    # type: (ftplib.Error) -> Tuple[Text, Text]
    """Extract code and message from imap error."""
    error_list = [e.strip() for e in error.args[0].split(',')]
    message = None
    code = None
    if len(error_list) > 0:
        message = error_list[0]
    if len(error_list) > 1:
        code = error_list[1]
    return message, code


if PY2:

    def _encode(st, encoding):
        # type: (Union[Text, bytes], Text) -> str
        return st.encode(encoding) if isinstance(st, text_type) else st

    def _decode(st, encoding):
        # type: (Union[Text, bytes], Text) -> Text
        return st.decode(encoding, "replace") if isinstance(st, bytes) else st


else:

    def _encode(st, _):
        # type: (str, str) -> str
        return st

    def _decode(st, _):
        # type: (str, str) -> str
        return st


class IMAPFile(io.BytesIO):
    def __init__(self, imapfs, path, mode):
        # type: (IMAPFS, Text, Text) -> None
        self.fs = imapfs
        self.path = path
        self.mode = Mode(mode)
        self._lock = threading.Lock()

        if self.mode.reading:
            with self.fs._manage_imap() as imap:
                folder, file = split(self.path)
                imap.select_folder(imap_path(folder, self.fs._delimiter))
                file_name = imap_splitext(file)[0]
                data = [f for f in imap.fetch(file_name, ['RFC822']).values()][0][b'RFC822']
                super(IMAPFile, self).__init__(data)
        else:
            super(IMAPFile, self).__init__()
        

    def __repr__(self):
        # type: () -> str
        _repr = "<imapfile {!r} {!r} {!r}>"
        return _repr.format(self.fs.imap_url, self.path, self.mode)

    def close(self):
        # type: () -> None
        if not self.closed:
            with self._lock:
                if self.writable():
                    folder, file = split(self.path)
                    with self.fs._manage_imap() as imap:
                        value = self.getvalue()
                        if len(value) == 0:
                            value = '\r\n'
                        imap.append(imap_path(folder, self.fs._delimiter), value)
                super(IMAPFile, self).close()

    def readable(self):
        # type: () -> bool
        return self.mode.reading

    def read(self, size=-1):
        # type: (int) -> bytes
        if not self.readable():
            raise io.UnsupportedOperation('read')
        return io.BytesIO.read(self, size)
    
    def readline(self, size=-1):
        # type: (int) -> bytes
        if not self.readable():
            raise io.UnsupportedOperation('read')
        return io.BytesIO.readline(self, size)  # type: ignore
        

    def writable(self):
        # type: () -> bool
        return self.mode.writing
    
    def write(self, data):
        # type: (bytes) -> int
        if not self.writable():
            raise io.UnsupportedOperation('write')
        return io.BytesIO.write(self, data)
    
    def writelines(self, lines):
        # type: (Iterable[bytes]) -> None
        if not self.writable():
            raise io.UnsupportedOperation('write')
        return io.BytesIO.writelines(self, lines)

class IMAPFS(FS):
    """A FTP (File Transport Protocol) Filesystem.

    Arguments:
        host (str): A FTP host, e.g. ``'ftp.mirror.nl'``.
        user (str): A username (default is ``'anonymous'``).
        passwd (str): Password for the server, or `None` for anon.
        timeout (int): Timeout for contacting server (in seconds,
            defaults to 10).
        port (int): FTP port number (default 21).

    """

    _meta = {
        "invalid_path_chars": "\0",
        "network": True,
        "read_only": False,
        "thread_safe": True,
        "unicode_paths": True,
        "virtual": False,
    }

    def __init__(
        self,
        host,  # type: Text
        port=None,
        user="anonymous",  # type: Text
        passwd="",  # type: Text
    ):
        # type: (...) -> None
        super(IMAPFS, self).__init__()
        self.host = host
        self.port = port
        self.user = user 
        self.passwd = passwd
        self._welcome = None  # type: Optional[Text]
        self._imap = None
        self.__delimiter = None
        self.__ns_root = None
        self.imap

    def __repr__(self):
        # type: (...) -> Text
        return "IMAPFS({!r}, port={!r})".format(self.host, self.port)

    def __str__(self):
        # type: (...) -> Text
        _fmt = "<ftpfs '{host}'>" if self.port == 21 else "<ftpfs '{host}:{port}'>"
        return _fmt.format(host=self.host, port=self.port)


    def _open_imap(self):
        # type: () -> FTP
        """Open a new ftp object.
        """
        _imap = None
        with imap_errors(self):
            _imap = IMAPClient(self.host, self.port)
            _imap.login(self.user, self.passwd)
            self._welcome = _imap.welcome
        return _imap

    def _manage_imap(self):
        # type: () -> ContextManager[FTP]
        return self._get_imap()
    
    def _get_imap(self):
        # type: () -> IMAPClient
        if self._imap is not None:
            try:
                self._imap.noop()
            except IMAP4.abort:
                self._imap = None
            except ConnectionResetError:
                self._imap = None
            except socket.error:
                self._imap = None
        if self._imap is None:
            self._imap = self._open_imap()
        return self._imap
    
    @property
    def imap_url(self):
        # type: () -> Text
        """Get the FTP url this filesystem will open."""
        url = (
            "imap://{}".format(self.host)
            if self.port == 21
            else "imap://{}:{}".format(self.host, self.port)
        )
        return url

    @property
    def imap(self):
        # type: () -> FTP
        """~ftplib.FTP: the underlying FTP client.
        """
        return self._get_imap()

    def _dir_Info(self, name, flags=(), folder_status=None):
        raw_info = {
                "basic": {
                    "name": name,
                    "is_dir": True,
                },
                "details": {
                    "type": int(ResourceType.directory),
                },
                "imap": {
                        'flags' : [flag.decode('ascii') for flag in flags]
                    }
            }
        if folder_status:
            imap = raw_info['imap']
            for state in folder_status:
                imap[state.decode('ascii').lower()] = folder_status[state]
        return Info(raw_info)
    
    @staticmethod
    def _tuple_address(address):
        name = address.name.decode('ascii') if address.name else None
        mailbox = address.mailbox.decode('ascii') if address.mailbox else None
        host = address.host.decode('ascii') if address.host else None
        route = address.route.decode('ascii') if address.route else None
        return tuple([name, mailbox, host, route])
    
    @staticmethod
    def _file_Info(name, file=None):
        raw_info = {
                "basic": {
                    "name": name + '.eml',
                    "is_dir": False,
                },
                "details": {
                    "type": int(ResourceType.file),
                }
        }
        encoding = 'ascii'
        if file:
            if b'RFC822.SIZE' in file:
                raw_info['details']['size'] = file[b'RFC822.SIZE']
            if b'FLAGS' in file:
                if 'imap' not in raw_info: raw_info['imap'] = {}
                raw_info['imap']['flags'] = [flag.decode(encoding) for flag in file[b'FLAGS']]
            if b'ENVELOPE' in file:
                ev = file[b'ENVELOPE']
                if ev.date:
                    raw_info['details']['accessed'] = ev.date.timestamp()
                    raw_info['details']['modified'] = ev.date.timestamp()
                    raw_info['details']['created'] = ev.date.timestamp()
                if 'imap' not in raw_info: raw_info['imap'] = {}
                raw_info['imap']['envelope'] = ev
                raw_info['imap']['subject'] = ev.subject.decode(encoding) if ev.subject else None
                if ev.from_:
                    raw_info['imap']['from'] = [IMAPFS._tuple_address(address) for address in ev.from_]
                if ev.sender:
                    raw_info['imap']['sender'] = [IMAPFS._tuple_address(address) for address in ev.sender]
                if ev.reply_to:
                    raw_info['imap']['reply_to'] = [IMAPFS._tuple_address(address) for address in ev.reply_to]
                if ev.to:
                    raw_info['imap']['reply_to'] = [IMAPFS._tuple_address(address) for address in ev.to]
                if ev.cc:
                    raw_info['imap']['cc'] = [IMAPFS._tuple_address(address) for address in ev.cc]
                if ev.bcc:
                    raw_info['imap']['bcc'] = [IMAPFS._tuple_address(address) for address in ev.bcc]
                if ev.in_reply_to:
                    raw_info['imap']['in_reply_to'] = [IMAPFS._tuple_address(address) for address in ev.in_reply_to]
            if b'RFC822.HEADER' in file:
                header = email.message_from_bytes(file[b'RFC822.HEADER'])
                if 'imap' not in raw_info: raw_info['imap'] = {}
                header_raw = {}
                for key, item in header.items():
                    header_raw[key] = item
                raw_info['imap']['header'] = header
                
        return Info(raw_info)
    
    @property
    def _delimiter(self):
        if self.__delimiter is None:
            if self.imap.has_capability('NAMESPACE'):
                personal_namespaces = self.imap.namespace().personal
                for personal_namespace in personal_namespaces:
                    self.__delimiter = personal_namespace[1]
                    break
            else:
                for _, delimiter, _  in self.imap.list_folders():
                    if delimiter:
                        self.__delimiter = delimiter.decode('ascii')
                        break
            if self.__delimiter is None:
                self.__delimiter = ''
        return self.__delimiter
    
    @property 
    def _ns_root(self):
        if self.__ns_root is None:
            if self.imap.has_capability('NAMESPACE'):
                personal_namespaces = self.imap.namespace().personal
                for personal_namespace in personal_namespaces:
                    self.__ns_root = personal_namespace[0]
                    if self.__ns_root is not None:
                        break
            if self.__ns_root is None:
                self.__ns_root = ''
        return self.__ns_root     
    
    def _read_dir(self, path, namespaces=None):
        namespaces = namespaces or ()
        def _get_folder_list(path):
            folder_list = imap.list_folders(imap_path(path, self._delimiter))
            if len(folder_list) == 1:
                flags, delimiter, name = folder_list[0]
                if delimiter is None and b'\\Noinferiors' in flags:
                    folder_list = imap.list_folders('')
            return folder_list
        _list = []
        with imap_errors(self, path):
            imap = self.imap
            _selected = None
            try:
                if imap_path(path, self._delimiter) != '':
                    _selected = imap.select_folder(imap_path(path, self._delimiter))
            except IMAP4.error as error:
                message, _code = _parse_imap_error(error)
                raise errors.ResourceNotFound(path)
                if message == 'select failed: invalid mailbox namespace':
                    pass
                if message == 'select failed: folder does not exist':
                    raise errors.ResourceNotFound(path)
            if _selected and _selected[b'EXISTS']:
                for file_name, file in imap.fetch(imap.search(), ['FLAGS', 'ENVELOPE', 'RFC822.SIZE', 'RFC822.HEADER']).items():
                    _list.append(IMAPFS._file_Info(str(file_name), file))
            
            for flags, delimiter, name  in _get_folder_list(path):
                folder_root = None
                folder_name = None
                if delimiter:
                    foldersplit = name.rsplit(delimiter.decode('ascii'), 1)
                    if len(foldersplit) == 1:
                        folder_root, folder_name = '', foldersplit[0]
                    else:
                        folder_root, folder_name = foldersplit[0], foldersplit[1]
                if b'\\Noinferiors' in flags:
                    pass
                elif folder_root == imap_path(path, self._delimiter):
                    if delimiter:
                        delimiter = delimiter.decode('ascii')
                    else:
                        delimiter = ''
                    path_status = imap_join(self._delimiter, imap_path(path, self._delimiter), folder_name)
                    folder_status = imap.folder_status(path_status)
                    _list.append(self._dir_Info(folder_name, flags, folder_status))
        return OrderedDict({info.name: info for info in _list})


    def getinfo(self, path, namespaces=None):
        # type: (Text, Optional[Container[Text]]) -> Info
        _path = self.validatepath(path)
        if _path == "/":
            return Info(
                {
                    "basic": {"name": "", "is_dir": True},
                    "details": {"type": int(ResourceType.directory)},
                }
            )

        with imap_errors(self, path=path):
            dir_name, file_name = split(_path)
            directory = self._read_dir(dir_name, namespaces)
            if file_name not in directory:
                raise errors.ResourceNotFound(path)
            return directory[file_name]
        
    def setinfo(self, path, info):
        # type: (Text, RawInfo) -> None
        _path = self.validatepath(path)
        if not self.exists(path):
            raise errors.ResourceNotFound(path)
        if not self.isfile(path):
            raise errors.FileExpected(path)
        with imap_errors(self, path):
            if "imap" in info:
                imap_details = info["imap"]
                if "flags" in imap_details:
                    flags = imap_details['flags']
                    if not isinstance(flags, list):
                        flags = [flags, ]
                    flags = [f if isinstance(f, bytes) else f.encode('ascii') for f in flags]
                    folder, file = split(_path)
                    self.imap.select_folder(imap_path(folder, self._delimiter))
                    self.imap.set_flags(imap_splitext(file)[0], flags)

    def getmeta(self, namespace="standard"):
        # type: (Text) -> Dict[Text, object]
        _meta = {}  # type: Dict[Text, object]
        if namespace == "standard":
            _meta = self._meta.copy()
            with imap_errors(self):
                _meta["unicode_paths"] = self.imap.folder_encode
        return _meta

    def listdir(self, path):
        # type: (Text) -> List[Text]
        _path = self.validatepath(path)
        if not self.getinfo(path).is_dir:
            raise errors.DirectoryExpected(path)
        with imap_errors(self, path=path):
            dir_list = [info.name for info in self._read_dir(_path).values()]
        return dir_list
    
    def _scandir(
        self,
        path,  # type: Text
        namespaces=None   # type: Optional[Container[Text]]
    ):
        # type: (...) -> Iterator[Info]
        _path = self.validatepath(path)
        with self._lock:
            for info in self._read_dir(_path, namespaces).values():
                yield info
    
    def scandir(
        self,
        path,  # type: Text
        namespaces=None,  # type: Optional[Collection[Text]]
        page=None,  # type: Optional[Tuple[int, int]]
    ):
        # type: (...) -> Iterator[Info]
        """Get an iterator of resource info.

        Arguments:
            path (str): A path to a directory on the filesystem.
            namespaces (list, optional): A list of namespaces to include
                in the resource information, e.g. ``['basic', 'access']``.
            page (tuple, optional): May be a tuple of ``(<start>, <end>)``
                indexes to return an iterator of a subset of the resource
                info, or `None` to iterate over the entire directory.
                Paging a directory scan may be necessary for very large
                directories.

        Returns:
            ~collections.abc.Iterator: an iterator of `Info` objects.

        Raises:
            fs.errors.DirectoryExpected: If ``path`` is not a directory.
            fs.errors.ResourceNotFound: If ``path`` does not exist.

        """
        iter_info = self._scandir(path, namespaces=namespaces)
        if page is not None:
            start, end = page
            iter_info = itertools.islice(iter_info, start, end)
        return iter_info

    def makedir(
        self,  # type: _F
        path,  # type: Text
        permissions=None,  # type: Optional[Permissions]
        recreate=False,  # type: bool
    ):
        # type: (...) -> SubFS[_F]
        _path = self.validatepath(path)

        with imap_errors(self, path=path):
            if _path == "/":
                if recreate:
                    return self.opendir(path)
                else:
                    raise errors.DirectoryExists(path)
            if self.exists(path) and not  recreate:
                raise errors.DirectoryExists(path)
            if not (recreate and self.isdir(path)):
                target = imap_path(path, self._delimiter)
                folders = target.split(self._delimiter)
                check_folder = ''
                for n, folder in enumerate(folders):
                    if n == 0:
                        check_folder = folder
                    elif n < len(folders):
                        check_folder += '/' + folder
                    if n < len(folders) - 1 and not self.exists(check_folder):
                        raise errors.ResourceNotFound(path)
                try:
                    self.imap.create_folder(target)
                except IMAP4.error as error:
                    _, code = _parse_imap_error(error)
                    if code == '6':
                        raise errors.DirectoryExists(path)
                    raise errors.ResourceNotFound(path)
        return self.opendir(path)

    def openbin(self, path, mode="r", buffering=-1, **options):
        # type: (Text, Text, int, **Any) -> BinaryIO
        _mode = Mode(mode)
        _mode.validate_bin()
        _path = self.validatepath(path)
        with imap_errors(self, path):
            try:
                info = self.getinfo(_path)
            except errors.ResourceNotFound:
                if _mode.reading:
                    raise errors.ResourceNotFound(path)
                if _mode.writing and not self.isdir(dirname(_path)):
                    raise errors.ResourceNotFound(path)
            else:
                if info.is_dir:
                    raise errors.FileExpected(path)
                if info.is_file and _mode.writing:
                    raise errors.FileExists(path)
            if imap_splitext(split(_path)[1])[1] != 'eml':
                raise errors.PathError(path = path, msg="path '{path}' is invalid becouse file must have '.eml' extention")
            imap_file = IMAPFile(self, _path, mode)
        return imap_file  # type: ignore
    
    def copy(self, src_path, dst_path, overwrite=False):
        _src_path = self.validatepath(src_path)
        _dst_path = self.validatepath(dst_path)
        with imap_errors(self, src_path):
            _src_info = self.getinfo(_src_path)
            if _src_info.is_dir:
                raise errors.FileExpected(_src_path)
             
            try:
                _dst_info =  self.getinfo(_dst_path)
            except errors.ResourceNotFound:
                pass
            else:
                if _dst_info.is_file:
                    if overwrite:
                        raise errors.FileExists(dst_path)
                    else:
                        raise errors.DestinationExists(dst_path)
            _src_folder, _src_file = split(_src_path)
            self.imap.select_folder(imap_path(_src_folder, self._delimiter))
             
            _dst_folder, _dst_file = split(_dst_path)
            try:
                self.imap.copy(imap_splitext(_src_file)[0], imap_path(_dst_folder, self._delimiter))
            except IMAP4.error as error:
                raise errors.ResourceNotFound(dst_path)
                message, code = _parse_imap_error(error)
                print(message, code)
                if message == 'copy failed: [TRYCREATE] mailbox name does not exist or is not selectable':
                    if code == '0':
                        raise errors.ResourceNotFound(dst_path)
                

    def remove(self, path):
        # type: (Text) -> None
        _path = self.validatepath(path)
        with imap_errors(self, path):
            if self.isdir(path):
                raise errors.FileExpected(path=path)
            if not self.exists(path):
                raise errors.ResourceNotFound(path=path)
            dir_name, file_name = split(_path)
            self.imap.select_folder(imap_path(dir_name, self._delimiter))
            result = self.imap.delete_messages(imap_splitext(file_name)[0])
            for file_id in result.keys():
                self.imap.expunge(file_id)

    def removedir(self, path):
        # type: (Text) -> None
        _path = self.validatepath(path)
        if _path == "/":
            raise errors.RemoveRootError()
        with imap_errors(self, _path):
            if self.isfile(path):
                raise errors.DirectoryExpected(path=path)
            if not self.isempty(path):
                raise errors.DirectoryNotEmpty(path=path)
            try:
                self.imap.delete_folder(imap_path(_path, self._delimiter))
            except IMAP4.error as e:
                pass
            #TODO:

    def close(self):
        if not self.isclosed():
            try:
                self.imap.logout()
            finally:
                # type: () -> None
                super(IMAPFS, self).close()
                
    


