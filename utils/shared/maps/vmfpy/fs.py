from typing import Union, IO, Optional, List, NamedTuple, Mapping, Iterable, Iterator, Set, Dict, Tuple, cast
from pathlib import PurePosixPath
import os
from io import TextIOBase, BufferedIOBase, TextIOWrapper
import vpk

# workaround for https://github.com/python/typeshed/issues/1229
AnyTextIO = Union[TextIOBase, IO[str]]
AnyBinaryIO = Union[BufferedIOBase, IO[bytes]]


class VPKFileIOWrapper(BufferedIOBase):
    """An IO wrapper for a file inside a VPK archive."""
    def __init__(self, vpkf: vpk.VPKFile):
        self._vpkf = vpkf

    def save(self, path: str) -> None:
        self._vpkf.save(path)

    def verify(self) -> bool:
        return self._vpkf.verify()

    # BufferedIOBase implementation
    def close(self) -> None:
        super().close()
        self._vpkf.close()

    def read(self, size: Optional[int] = -1) -> bytes:
        if size is None:
            size = -1
        return self._vpkf.read(size)

    def read1(self, size: Optional[int] = -1) -> bytes:
        return self.read(size)

    def readable(self) -> bool:
        return True

    def readline(self, size: Optional[int] = -1) -> bytes:
        if size != -1:
            raise NotImplementedError()
        return self._vpkf.readline()

    def readlines(self, hint: Optional[int] = -1) -> List[bytes]:
        if hint != -1:
            raise NotImplementedError()
        return self._vpkf.readlines()

    def seek(self, offset: int, whence: int = 0) -> int:
        self._vpkf.seek(offset, whence)
        return self._vpkf.tell()

    def seekable(self) -> bool:
        return True

    def tell(self) -> int:
        return self._vpkf.tell()


def vmf_path(path: str) -> PurePosixPath:
    return PurePosixPath(path.replace("\\", "/").lstrip("/").lower())


class DirContents(NamedTuple):
    dirs: Set[str]
    files: Set[str]


class FileInfo(NamedTuple):
    path: str
    vpk_data: Optional[Tuple[vpk.VPK, Tuple[bytes, int, int, int, int, int]]]


class VMFFileSystem(Mapping[PurePosixPath, AnyBinaryIO]):
    """File system for opening game files."""
    def __init__(self, dirs: Iterable[str] = None, paks: Iterable[str] = None, index_files: bool = False) -> None:
        self._dirs: Set[str] = set() if dirs is None else set(dirs)
        self._paks: Set[str] = set() if paks is None else set(paks)
        self._index: Dict[PurePosixPath, FileInfo] = dict()
        self.tree: Dict[PurePosixPath, DirContents] = dict()
        if index_files:
            self.index_all()

    def add_dir(self, path: str) -> None:
        self._dirs.add(path)

    def remove_dir(self, path: str) -> None:
        self._dirs.remove(path)

    def add_pak(self, path: str) -> None:
        self._paks.add(path)

    def remove_pak(self, path: str) -> None:
        self._paks.remove(path)

    def iter_dir(self, directory: str) -> Iterator[Tuple[PurePosixPath, FileInfo]]:
        root: str
        files: List[str]
        for root, _, files in os.walk(directory):
            root_path = vmf_path(root)
            for file_name in files:
                path = root_path.relative_to(vmf_path(directory)) / file_name.lower()
                yield (path, FileInfo(os.path.join(root, file_name), None))

    def iter_dirs(self) -> Iterator[Tuple[PurePosixPath, FileInfo]]:
        for directory in self._dirs:
            yield from self.iter_dir(directory)

    def iter_pak(self, pak_file: str) -> Iterator[Tuple[PurePosixPath, FileInfo]]:
        pak = vpk.open(pak_file)
        for pak_path, metadata in pak.read_index_iter():
            path = vmf_path(pak_path)
            yield (path, FileInfo(pak_path, (pak, metadata)))

    def iter_paks(self) -> Iterator[Tuple[PurePosixPath, FileInfo]]:
        for pak_file in self._paks:
            yield from self.iter_pak(pak_file)

    def iter_all(self) -> Iterator[Tuple[PurePosixPath, FileInfo]]:
        yield from self.iter_dirs()
        yield from self.iter_paks()

    def _do_index(self, index_iter: Iterator[Tuple[PurePosixPath, FileInfo]]) -> None:
        for path, info in index_iter:
            self._index[path] = info
            directory = path.parent
            if directory not in self.tree:
                self.tree[directory] = DirContents(set(), set())
            self.tree[directory].files.add(path.name)
            last_parent = directory
            for parent in directory.parents:
                if parent not in self.tree:
                    self.tree[parent] = DirContents(set(), set())
                self.tree[parent].dirs.add(last_parent.name)
                last_parent = parent

    def index_dir(self, directory: str) -> None:
        self._do_index(self.iter_dir(directory))

    def index_dirs(self) -> None:
        self._do_index(self.iter_dirs())

    def index_pak(self, pak_file: str) -> None:
        self._do_index(self.iter_pak(pak_file))

    def index_paks(self) -> None:
        self._do_index(self.iter_paks())

    def index_all(self) -> None:
        self._do_index(self.iter_all())

    def clear_index(self) -> None:
        self._index.clear()
        self.tree.clear()

    def _do_open(self, info: FileInfo) -> AnyBinaryIO:
        if info.vpk_data is None:
            return open(info.path, 'rb')
        else:
            return VPKFileIOWrapper(info.vpk_data[0].get_vpkfile_instance(info.path, info.vpk_data[1]))

    def open_file(self, path: Union[str, PurePosixPath]) -> AnyBinaryIO:
        if isinstance(path, str):
            path = vmf_path(path)
        if path not in self._index:
            raise FileNotFoundError(path)
        return self._do_open(self._index[path])

    def open_file_utf8(self, path: Union[str, PurePosixPath]) -> TextIOWrapper:
        return TextIOWrapper(cast(IO[bytes], self.open_file(path)), encoding='utf-8')

    def __getitem__(self, key: Union[str, PurePosixPath]) -> AnyBinaryIO:
        if isinstance(key, str):
            key = vmf_path(key)
        return self._do_open(self._index[key])

    def __len__(self) -> int:
        return len(self._index)

    def __iter__(self) -> Iterator[PurePosixPath]:
        return iter(self._index)

    def __contains__(self, item: object) -> bool:
        return item in self._index
