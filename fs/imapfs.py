"""Pyfilesystem2 over IMAP using IMAPClient.
"""
import email
import io
import itertools
import re
import socket
import typing
from collections import OrderedDict
from contextlib import contextmanager
from imaplib import IMAP4
from typing import (
    Any,
    BinaryIO,
    Collection,
    Dict,
    Iterable,
    Iterator,
    List,
    Optional,
    Text,
    Tuple,
    Union,
)
from fs.base import FS
from fs.enums import ResourceType
from fs.info import Info as BaseInfo
from fs.mode import Mode
from fs.path import dirname, join, split
from fs.permissions import Permissions
from fs.subfs import SubFS
from imapclient import IMAPClient
from imapclient.response_types import Address, Envelope
from six import PY2, text_type

from fs import errors

__all__ = ["IMAPFS", "Info"]

import importlib_metadata

distribution = importlib_metadata.distribution("fs.imapfs")

__license__ = distribution.metadata.get("License")
__copyright__ = "Copyright (c) 2017-2023 Andrea Maggi"
__author__ = (
    f'{distribution.metadata.get("Author")} '
    f'<{distribution.metadata.get("Author-email")}>'
)
__version__ = distribution.metadata.get("version")

_F = typing.TypeVar("_F", bound="IMAPFS")


RE_APPEND_INFO = re.compile(r"(?<=\[)(?P<list>.*)(?=])")


class Info(BaseInfo):
    @property
    def flags(self):
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
    def envelope(self):
        # type: () -> Optional[Envelope]
        """`Envelope`: mail envelope`.

        Requires the ``"imap"`` namespace.

        Raises:
            ~fs.errors.MissingInfoNamespace: if the ``"imap"``
                namespace is not in the Info.

        """
        self._require_namespace("imap")
        return self.get("imap", "envelope")


def _dir_info(name, flags=tuple(), folder_status=None):
    # type: (Text, Tuple[bytes], Optional[Dict[bytes, bytes]]) -> Info
    raw_info = {
        "basic": {
            "name": name,
            "is_dir": True,
        },
        "details": {
            "type": int(ResourceType.directory),
        },
        "imap": {"flags": [flag.decode("ascii") for flag in flags]},
    }
    if folder_status:
        for state in folder_status:
            raw_info["imap"][state.decode("ascii").lower()] = folder_status[state]
    return Info(raw_info)


def _tuple_address(address):
    # type: (Address) -> Tuple[Optional[Text], Optional[Text], Optional[Text], Optional[Text]]
    name = address.name.decode("ascii") if address.name else None
    mailbox = address.mailbox.decode("ascii") if address.mailbox else None
    host = address.host.decode("ascii") if address.host else None
    route = address.route.decode("ascii") if address.route else None
    return name, mailbox, host, route


def _file_info(name, file):
    # type: (Text, Dict[bytes, Union[bytes, int, Envelope, Iterable[bytes]]]) -> Info
    raw_info = {
        "basic": {
            "name": name + ".eml",
            "is_dir": False,
        },
        "details": {
            "type": int(ResourceType.file),
        },
        "imap": {},
    }
    encoding = "ascii"
    if file:
        if b"RFC822.SIZE" in file:
            raw_info["details"]["size"] = file[b"RFC822.SIZE"]
        if b"FLAGS" in file:
            raw_info["imap"]["flags"] = [
                flag.decode(encoding) for flag in file[b"FLAGS"]
            ]
        if b"ENVELOPE" in file:
            ev = file[b"ENVELOPE"]
            assert isinstance(ev, Envelope)
            if ev.date:
                raw_info["details"]["accessed"] = ev.date.timestamp()
                raw_info["details"]["modified"] = ev.date.timestamp()
                raw_info["details"]["created"] = ev.date.timestamp()
            # raw_info["imap"]["envelope"] = ev
            raw_info["imap"]["subject"] = (
                ev.subject.decode(encoding) if ev.subject else None
            )
            if ev.from_:
                raw_info["imap"]["from"] = [
                    _tuple_address(address) for address in ev.from_
                ]
            if ev.sender:
                raw_info["imap"]["sender"] = [
                    _tuple_address(address) for address in ev.sender
                ]
            if ev.reply_to:
                raw_info["imap"]["reply_to"] = [
                    _tuple_address(address) for address in ev.reply_to
                ]
            if ev.to:
                raw_info["imap"]["to"] = [_tuple_address(address) for address in ev.to]
            if ev.cc:
                raw_info["imap"]["cc"] = [_tuple_address(address) for address in ev.cc]
            if ev.bcc:
                raw_info["imap"]["bcc"] = [
                    _tuple_address(address) for address in ev.bcc
                ]
            if ev.in_reply_to:
                raw_info["imap"]["in_reply_to"] = ev.in_reply_to
        if b"RFC822.HEADER" in file:
            header = email.message_from_bytes(file[b"RFC822.HEADER"])
            header_raw = {}
            for key, item in header.items():
                header_raw[key] = item
            raw_info["imap"]["header"] = header_raw

    return Info(raw_info)


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


def filename_split(file_name):
    # type: (Text) -> Tuple[Text, Text]
    parts = file_name.rsplit(".", 1)
    return (parts[0], "") if len(parts) == 1 else (parts[0], parts[1])


def _parse_imap_error(error):
    # type: (IMAP4.error) -> Tuple[Text, Text]
    """Extract code and message from imap error."""
    error_list = [e.strip() for e in error.args[0].split(",")]
    message = ""
    code = ""
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

        if self.mode.reading:
            folder, file_name = split(self.path)
            file_id = filename_split(file_name)[0]
            with imap_errors(self.fs, self.path):
                self.fs.imap.select_folder(self.fs._imap_path(folder))
                data = [f for f in self.fs.imap.fetch(file_id, ["RFC822"]).values()][0][
                    b"RFC822"
                ]
                super().__init__(data)
        else:
            super().__init__()

    def __repr__(self):
        # type: () -> str
        _repr = "IMAPFile({!r}, {!r}, {!r})"
        return _repr.format(self.fs.imap_url, self.path, self.mode)

    def close(self):
        # type: () -> None
        if not self.closed:
            if self.writable():
                value = self.getvalue()
                if len(value) == 0:
                    value = "\r\n"
                self.fs.save_message(dirname(self.path), value)
            super().close()

    def readable(self):
        # type: () -> bool
        return self.mode.reading

    def read(self, size=-1):
        # type: (int) -> bytes
        if not self.readable():
            raise io.UnsupportedOperation("read")
        return super().read(size)

    def readline(self, size=-1):
        # type: (int) -> bytes
        if not self.readable():
            raise io.UnsupportedOperation("read")
        return super().readline(size)

    def writable(self):
        # type: () -> bool
        return self.mode.writing

    def write(self, data):
        # type: (bytes) -> int
        if not self.writable():
            raise io.UnsupportedOperation("write")
        return super().write(data)

    def writelines(self, lines):
        # type: (Iterable[bytes]) -> None
        if not self.writable():
            raise io.UnsupportedOperation("write")
        return super().writelines(lines)


class IMAPFS(FS):
    """A IMAPFS Filesystem.

    Arguments:
        host (str): A IMAP host, e.g. ``'imap.mirror.nl'``.
        port (int): IMAP port number (default 993).
        user (str): A username (default is ``'anonymous'``).
        passwd (str): Password for the server, or `None` for anon.
    """

    _delimiter: Text
    _ns_root: Text

    _meta = {
        "invalid_path_chars": "\0",
        "network": True,
        "read_only": False,
        "thread_safe": True,
        "unicode_paths": True,
        "virtual": False,
        "supports_rename": False,
    }

    def __init__(
        self,
        host,  # type: Text
        port=None,  # type: Optional[int]
        user="anonymous",  # type: Text
        passwd="",  # type: Text
    ):
        # type: (...) -> None
        super().__init__()
        self.host = host
        self.port = port
        self.user = user
        self.passwd = passwd
        self._welcome = None  # type: Optional[Text]
        self._imap = None
        self._ns_root = None  # type: Optional[Text]
        self._get_imap()

    def __repr__(self):
        # type: () -> Text
        return f"IMAPFS({self.host!r}, port={self.port!r})"

    def __str__(self):
        # type: () -> Text
        return (
            f"<imapfs '{self.host}'>"
            if self.port == 993
            else f"<imapfs '{self.host}:{self.por}'>"
        )

    @property
    def imap(self):
        # type: () -> IMAPClient
        """~imapclient.IMAPClient: the underlying IMAP client."""
        return self._get_imap()

    def _get_imap(self):
        # type: () -> IMAPClient
        if self._imap is not None:
            try:
                self._imap.noop()
            except (IMAP4.abort, ConnectionResetError, socket.error):
                self._imap_shutdown()
                self._imap = None
        if self._imap is None:
            self._imap = self._open_imap()
        return self._imap

    def _open_imap(self):
        # type: () -> IMAPClient
        """Open a new ftp object."""
        with imap_errors(self):
            imap_client = IMAPClient(self.host, self.port)
            imap_client.login(self.user, self.passwd)
            self._welcome = imap_client.welcome
            if imap_client.has_capability("NAMESPACE"):
                personal_namespaces = imap_client.namespace().personal
                for personal_namespace in personal_namespaces:
                    self._ns_root = personal_namespace[0]
                    self._delimiter = personal_namespace[1]
                    break
            else:
                for _, delimiter, _ in imap_client.list_folders():
                    if delimiter:
                        self._ns_root = ""
                        self._delimiter = delimiter.decode("ascii")
                        break
                else:
                    self._ns_root = ""
                    self._delimiter = ""
        return imap_client

    def _imap_path(self, fs_path):
        # type: (Text) -> Text
        fs_path = fs_path.lstrip("/") if fs_path.startswith("/") else fs_path
        fs_path = fs_path.rstrip("/") if fs_path.endswith("/") else fs_path
        fs_path = fs_path.replace("/", self._delimiter)
        return fs_path

    def _imap_shutdown(self):
        if self._imap is not None:
            try:
                self._imap.shutdown()
            except Exception as e:
                print(f"imap shutdown error: {e}")

    @property
    def imap_url(self):
        # type: () -> Text
        """Get the FTP url this filesystem will open."""
        return (
            f"imap://{self.host}"
            if self.port == 21
            else f"imap://{self.host}:{self.port}"
        )

    def getmeta(self, namespace="standard"):
        # type: (Text) -> Dict[Text, object]
        _meta = {}  # type: Dict[Text, object]
        if namespace == "standard":
            _meta = self._meta.copy()
            with imap_errors(self):
                _meta["unicode_paths"] = self.imap.folder_encode
        return _meta

    def _get_folder_list(self, fs_path):
        # type: (Text) -> Iterable[Tuple[bytes, Text, Text]]
        imap = self.imap
        folder_list = imap.list_folders(self._imap_path(fs_path))
        if len(folder_list) == 1:
            flags, delimiter, _ = folder_list[0]
            if delimiter is None and b"\\Noinferiors" in flags:
                folder_list = imap.list_folders("")
        return folder_list

    def listdir(self, path):
        # type: (Text) -> List[Text]
        fs_dir_path = self.validatepath(path)
        if not self.getinfo(path).is_dir:
            raise errors.DirectoryExpected(path)
        dir_list = []
        with imap_errors(self, path):
            imap = self.imap
            try:
                if fs_dir_path != "/":
                    selected = imap.select_folder(self._imap_path(fs_dir_path))
                else:
                    selected = None
            except IMAP4.error:
                raise errors.ResourceNotFound(fs_dir_path)
            else:
                if selected and selected[b"EXISTS"]:
                    for element_id in imap.search():
                        dir_list.append(f"{element_id}.eml")
            for flags, delimiter, name in self._get_folder_list(fs_dir_path):
                if b"\\Noinferiors" in flags:
                    pass
                else:
                    delimiter = delimiter.decode("ascii") if delimiter else None
                    parent_folder = None
                    sub_folder = None
                    if delimiter:
                        folder_split = name.rsplit(delimiter, 1)
                        if len(folder_split) == 1:
                            parent_folder, sub_folder = "", folder_split[0]
                        else:
                            parent_folder, sub_folder = folder_split[0], folder_split[1]
                    if parent_folder == self._imap_path(fs_dir_path):
                        dir_list.append(sub_folder)
        return dir_list

    def getinfo(self, path, namespaces=None):
        # type: (Text, Optional[Collection[Text]]) -> Info
        fs_path = self.validatepath(path)
        if fs_path == "/":
            return Info(
                {
                    "basic": {"name": "", "is_dir": True},
                    "details": {"type": int(ResourceType.directory)},
                }
            )

        with imap_errors(self, path):
            imap = self.imap
            if fs_path.endswith(".eml"):
                # looking for a file
                fs_dir_path, fs_element = split(fs_path)
                imap_dir_path = self._imap_path(fs_dir_path)
                try:
                    selected = imap.select_folder(imap_dir_path)
                    if not selected[b"EXISTS"]:
                        raise errors.ResourceNotFound(path)
                    else:
                        file_id = int(filename_split(fs_element)[0])
                        fetch_dict = imap.fetch(
                            [file_id],
                            ["FLAGS", "ENVELOPE", "RFC822.SIZE", "RFC822.HEADER"],
                        )
                        if file_id in fetch_dict:
                            return _file_info(str(file_id), fetch_dict[file_id])
                        else:
                            raise errors.ResourceNotFound(path)
                except IMAP4.error:
                    raise errors.ResourceNotFound(path)
            else:
                # looking for a folder
                if imap.folder_exists(self._imap_path(fs_path)):
                    folder_status = imap.folder_status(self._imap_path(fs_path))
                    fs_folder_path = split(fs_path)[0]
                    folders = imap.list_folders(self._imap_path(fs_folder_path))
                    while (
                        len(folders) == 0
                        or len(folders) == 1
                        and b"\\Noinferiors" in folders[0][0]
                    ):
                        fs_folder_path = split(fs_folder_path)[0]
                        folders = imap.list_folders(self._imap_path(fs_folder_path))
                    for flags, _delimiter, name in folders:
                        if name == self._imap_path(fs_path):
                            return _dir_info(
                                name=split(fs_path)[1],
                                flags=flags,
                                folder_status=folder_status,
                            )
                else:
                    raise errors.ResourceNotFound(path)

    def setinfo(self, path, info):
        # type: (Text, Dict[Text, Dict[Text, Union[Text, List[Text]]]]) -> None
        _fs_path = self.validatepath(path)
        if not self.exists(path):
            raise errors.ResourceNotFound(path)
        if not self.isfile(path):
            raise errors.FileExpected(path)
        with imap_errors(self, path):
            if "imap" in info:
                imap_details = info["imap"]
                if "flags" in imap_details:
                    if isinstance(imap_details["flags"], Text):
                        flags = [
                            imap_details["flags"],
                        ]
                    else:
                        flags = imap_details["flags"]
                    folder, file_name = split(_fs_path)
                    self.imap.select_folder(self._imap_path(folder))
                    self.imap.set_flags(
                        filename_split(file_name)[0],
                        [
                            f if isinstance(f, bytes) else f.encode("ascii")
                            for f in flags
                        ],
                    )

    def _scandir(
        self,
        path,  # type: Text
        namespaces=None,  # type: Optional[Collection[Text]]
    ):
        # type: (...) -> Iterator[Info]
        fs_dir_path = self.validatepath(path)
        with imap_errors(self, fs_dir_path):
            try:
                if fs_dir_path != "/":
                    selected = self.imap.select_folder(self._imap_path(fs_dir_path))
                else:
                    selected = None
            except IMAP4.error:
                raise errors.ResourceNotFound(fs_dir_path)
            else:
                if selected and selected[b"EXISTS"]:
                    for file_name, file in self.imap.fetch(
                        self.imap.search(),
                        ["FLAGS", "ENVELOPE", "RFC822.SIZE", "RFC822.HEADER"],
                    ).items():
                        yield _file_info(str(file_name), file)

            for flags, delimiter, name in self._get_folder_list(fs_dir_path):
                if b"\\Noinferiors" in flags:
                    pass
                else:
                    delimiter = delimiter.decode("ascii") if delimiter else None
                    parent_folder = None
                    sub_folder = None
                    if delimiter:
                        folder_split = name.rsplit(delimiter, 1)
                        if len(folder_split) == 1:
                            parent_folder, sub_folder = "", folder_split[0]
                        else:
                            parent_folder, sub_folder = folder_split[0], folder_split[1]
                    if parent_folder == self._imap_path(fs_dir_path):
                        folder_status = self.imap.folder_status(
                            self._imap_path(join(fs_dir_path, sub_folder))
                        )
                        yield _dir_info(
                            name=sub_folder, flags=flags, folder_status=folder_status
                        )

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
        self,
        path,  # type: Text
        permissions=None,  # type: Optional[Permissions]
        recreate=False,  # type: bool
    ):
        # type: (...) -> SubFS[FS]
        _fs_path = self.validatepath(path)

        with imap_errors(self, path):
            if _fs_path == "/":
                if recreate:
                    return self.opendir(path)
                else:
                    raise errors.DirectoryExists(path)
            if self.exists(path) and not recreate:
                raise errors.DirectoryExists(path)
            if not (recreate and self.isdir(path)):
                folders = _fs_path.split("/")
                check_folder = ""
                for n, folder in enumerate(folders):
                    if n == 0:
                        check_folder = folder
                    elif n < len(folders):
                        check_folder += "/" + folder
                    if n < len(folders) - 1 and not self.exists(check_folder):
                        raise errors.ResourceNotFound(path)
                try:
                    self.imap.create_folder(self._imap_path(_fs_path))
                except IMAP4.error as error:
                    _, code = _parse_imap_error(error)
                    if code == "6":
                        raise errors.DirectoryExists(path)
                    raise errors.ResourceNotFound(path)
        return self.opendir(path)

    def save_message(self, path, msg):
        # type: (Text, bytes) -> Tuple[Text, Text]
        _fs_path = self.validatepath(path)
        with imap_errors(self, path):
            result = self.imap.append(self._imap_path(path), msg)
            append_info = (
                RE_APPEND_INFO.search(result.decode("ascii")).group("list").split(" ")
            )
            return append_info[1], append_info[2]

    def openbin(self, path, mode="r", buffering=-1, **options):
        # type: (Text, Text, int, **Any) -> BinaryIO
        mode_object = Mode(mode)
        mode_object.validate_bin()
        fs_path = self.validatepath(path)
        fs_folder, fs_file_name = split(fs_path)
        with imap_errors(self, path):
            try:
                info = self.getinfo(fs_path)
            except errors.ResourceNotFound:
                if mode_object.reading:
                    raise errors.ResourceNotFound(path)
                if mode_object.writing and not self.isdir(dirname(fs_path)):
                    raise errors.ResourceNotFound(path)
            else:
                if info.is_dir:
                    raise errors.FileExpected(path)
                if info.is_file and mode_object.writing:
                    raise errors.FileExists(path)
            if filename_split(fs_file_name)[1] != "eml":
                raise errors.PathError(
                    path=path,
                    msg="path '{path}' is invalid because file must have '.eml' extension.",
                )
            imap_file = IMAPFile(self, fs_path, mode)
        return imap_file  # type: ignore

    def copy(
        self,
        src_path,  # type: Text
        dst_path,  # type: Text
        overwrite=False,  # type: bool
        preserve_time=False,  # type: bool
    ):
        # type: (...) -> None
        _src_path = self.validatepath(src_path)
        _dst_path = self.validatepath(dst_path)
        with imap_errors(self, src_path):
            _src_info = self.getinfo(src_path)
            if _src_info.is_dir:
                raise errors.FileExpected(src_path)
            try:
                _dst_info = self.getinfo(dst_path)
            except errors.ResourceNotFound:
                pass
            else:
                if _dst_info.is_file:
                    if not overwrite:
                        raise errors.DestinationExists(dst_path)
                    else:
                        raise errors.FileExists(dst_path)
            _src_folder, _src_file = split(_src_path)
            self.imap.select_folder(self._imap_path(_src_folder))
            _dst_folder, _dst_file = split(_dst_path)
            try:
                self.imap.copy(
                    filename_split(_src_file)[0], self._imap_path(_dst_folder)
                )
            except IMAP4.error:
                raise errors.ResourceNotFound(dst_path)

    def remove(self, path):
        # type: (Text) -> None
        _fs_path = self.validatepath(path)
        with imap_errors(self, path):
            if self.isdir(path):
                raise errors.FileExpected(path=path)
            if not self.exists(path):
                raise errors.ResourceNotFound(path=path)
            folder, file_name = split(_fs_path)
            self.imap.select_folder(self._imap_path(folder))
            result = self.imap.delete_messages(filename_split(file_name)[0])
            for file_id in result.keys():
                self.imap.expunge(file_id)

    def removedir(self, path):
        # type: (Text) -> None
        _fs_path = self.validatepath(path)
        if _fs_path == "/":
            raise errors.RemoveRootError()
        with imap_errors(self, path):
            if self.isfile(path):
                raise errors.DirectoryExpected(path=path)
            if not self.isempty(path):
                raise errors.DirectoryNotEmpty(path=path)
            try:
                self.imap.delete_folder(self._imap_path(_fs_path))
            except IMAP4.error:
                pass

    def close(self):
        # type: () -> None
        if not self.isclosed():
            try:
                self.imap.logout()
            except Exception:
                self._imap_shutdown()
            finally:
                super(IMAPFS, self).close()
