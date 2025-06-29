from io import DEFAULT_BUFFER_SIZE, SEEK_CUR, SEEK_END, SEEK_SET, RawIOBase, UnsupportedOperation
from fsh import fsh_pb2, fsh_pb2_grpc
import errno
import os
import pickle
import stat
from typing import List


class Path(object):
	def __init__(self, channel) -> None:
		self.__channel = channel
		self.__stub = fsh_pb2_grpc.FSHStub(self.__channel)

	def isdir(self, path: str) -> bool:
		return self.__stub.PathIsDir(fsh_pb2.PathRequest(path=path)).ret

	def islink(self, path: str) -> bool:
		return self.__stub.PathIsLink(fsh_pb2.PathRequest(path=path)).ret

	def isfile(self, path: str) -> bool:
		return self.__stub.PathIsFile(fsh_pb2.PathRequest(path=path)).ret

	def exists(self, path: str) -> bool:
		return self.__stub.PathExists(fsh_pb2.PathRequest(path=path)).ret


class Syscall(object):
	def __init__(self, channel) -> None:
		self.__channel = channel
		self.__stub = fsh_pb2_grpc.FSHStub(self.__channel)

	def open(self, path: str, flags: int, mode: int) -> int:
		r = self.__stub.Open(fsh_pb2.OpenRequest(path=path, flags=flags, mode=mode))
		if not r.ok:
			raise pickle.loads(r.err)
		return r.ret

	def close(self, fd: int) -> None:
		r = self.__stub.Close(fsh_pb2.CloseRequest(fd=fd))
		if not r.ok:
			raise pickle.loads(r.err)

	def read(self, fd: int, n: int) -> bytes:
		r = self.__stub.Read(fsh_pb2.ReadRequest(fd=fd, n=n))
		if not r.ok:
			raise pickle.loads(r.err)
		return r.ret

	def write(self, fd: int, i: bytes) -> int:
		r = self.__stub.Write(fsh_pb2.WriteRequest(fd=fd, str=i))
		if not r.ok:
			raise pickle.loads(r.err)
		return r.ret

	def lseek(self, fd: int, pos: int, whence: int) -> int:
		r = self.__stub.Lseek(fsh_pb2.LseekRequest(fd=fd, pos=pos, whence=whence))
		if not r.ok:
			raise pickle.loads(r.err)
		return r.ret

	def fsync(self, fd: int) -> None:
		r = self.__stub.Fsync(fsh_pb2.FsyncRequest(fd=fd))
		if not r.ok:
			raise pickle.loads(r.err)

	def truncate(self, fd: int, length: int) -> None:
		r = self.__stub.Truncate(fsh_pb2.TruncateRequest(fd=fd, length=length))
		if not r.ok:
			raise pickle.loads(r.err)

	def unlink(self, path: str) -> None:
		r = self.__stub.Unlink(fsh_pb2.PathRequest(path=path))
		if not r.ok:
			raise pickle.loads(r.err)

	def mkdir(self, path: str, mode: int) -> None:
		r = self.__stub.Mkdir(fsh_pb2.MkdirRequest(path=path, mode=mode))
		if not r.ok:
			raise pickle.loads(r.err)

	def rmdir(self, path: str) -> None:
		r = self.__stub.Rmdir(fsh_pb2.PathRequest(path=path))
		if not r.ok:
			raise pickle.loads(r.err)

	def listdir(self, path: str) -> List[str]:
		r = self.__stub.Listdir(fsh_pb2.PathRequest(path=path))
		if not r.ok:
			raise pickle.loads(r.err)
		return r.ret

	def utime(self, path: str, atime: int, mtime: int, follow_symlinks: bool = False) -> None:
		r = self.__stub.Utime(fsh_pb2.UtimeRequest(
			path=path,
			atime=atime,
			mtime=mtime,
			follow_symlinks=follow_symlinks,
		))
		if not r.ok:
			raise pickle.loads(r.err)

	def stat(self, path: str|int, follow_symlinks: bool = False) -> os.stat_result:
		if isinstance(path, int):
			r = self.__stub.Stat(fsh_pb2.StatRequest(path='', fd=path, use_fd=True, follow_symlinks=follow_symlinks))
		else:
			r = self.__stub.Stat(fsh_pb2.StatRequest(path=path, fd=-1, use_fd=False, follow_symlinks=follow_symlinks))
		if not r.ok:
			raise pickle.loads(r.err)
		return pickle.loads(r.ret)


class ByteFileIO(RawIOBase):
	_channel = None
	_fd = -1
	_created = False
	_readable = False
	_writable = False
	_appending = False
	_seekable = None
	_closefd = True

	def __init__(self, channel, file: str, mode: str = 'rb') -> None:
		self._channel = channel
		if self._fd >= 0:
			self._stat_atopen = None
			try:
				if self._closefd:
					Syscall(self._channel).close(self._fd)
			finally:
				self._fd = -1

		if not set(mode) <= set('xrwab+'):
			raise ValueError(f'invalid mode: {mode}')
		if sum(c in 'rwax' for c in mode) != 1 or mode.count('+') > 1:
			raise ValueError('Must have exactly one of create/read/write/append mode and at most one plus')

		flags = 0

		if 'x' in mode:
			self._created = True
			self._writable = True
			flags = os.O_EXCL | os.O_CREAT
		elif 'r' in mode:
			self._readable = True
			flags = 0
		elif 'w' in mode:
			self._writable = True
			flags = os.O_CREAT | os.O_TRUNC
		elif 'a' in mode:
			self._writable = True
			self._appending = True
			flags = os.O_APPEND | os.O_CREAT

		if '+' in mode:
			self._readable = True
			self._writable = True

		if self._readable and self._writable:
			flags |= os.O_RDWR
		elif self._readable:
			flags |= os.O_RDONLY
		else:
			flags |= os.O_WRONLY

		flags |= getattr(os, 'O_BINARY', 0)
		noinherit_flag = (getattr(os, 'O_NOINHERIT', 0) or getattr(os, 'O_CLOEXEC', 0))
		flags |= noinherit_flag
		self._fd = Syscall(channel).open(file, flags, 0o666)
		self._stat_atopen = Syscall(channel).stat(self._fd)
		try:
			if stat.S_ISDIR(self._stat_atopen.st_mode):
				raise IsADirectoryError(errno.EISDIR, os.strerror(errno.EISDIR), file)
		except AttributeError:
			# Ignore the AttributeError if stat.S_ISDIR or errno.EISDIR
			# don't exist.
			pass

		self.name = file
		if self._appending:
			try:
				Syscall(channel).lseek(self._fd, 0, SEEK_END)
			except OSError as e:
				if e.errno != errno.ESPIPE:
					raise

	@property
	def _blksize(self):
		if self._stat_atopen is None:
			return DEFAULT_BUFFER_SIZE

		blksize = getattr(self._stat_atopen, "st_blksize", 0)
		if not blksize:
			return DEFAULT_BUFFER_SIZE
		return blksize

	def _checkReadable(self):
		if not self._readable:
			raise UnsupportedOperation('File not open for reading')

	def _checkWritable(self):
		if not self._writable:
			raise UnsupportedOperation('File not open for writing')

	def read(self, size=None):
		self._checkClosed()
		self._checkReadable()
		if size is None or size < 0:
			return self.readall()

		try:
			return Syscall(self._channel).read(self._fd, size)
		except BlockingIOError:
			return None

	def readall(self):
		self._checkClosed()
		self._checkReadable()
		if self._stat_atopen is None or self._stat_atopen.st_size <= 0:
			bufsize = DEFAULT_BUFFER_SIZE
		else:
			bufsize = self._stat_atopen.st_size + 1
			if self._stat_atopen.st_size > 65536:
				try:
					pos = Syscall(self._channel).lseek(self._fd, 0, SEEK_CUR)
					if self._stat_atopen.st_size >= pos:
						bufsize = self._stat_atopen.st_size - pos + 1
				except OSError:
					pass

		results = b''

		while True:
			r = self.read(bufsize)
			if not r:
				break
			results += r

		return results

	def write(self, b):
		self._checkClosed()
		self._checkWritable()
		try:
			return Syscall(self._channel).write(self._fd, b)
		except BlockingIOError:
			return None

	def seek(self, pos, whence=SEEK_SET):
		if isinstance(pos, float):
			raise TypeError('an integer is required')
		self._checkClosed()
		return Syscall(self._channel).lseek(self._fd, pos, whence)

	def tell(self):
		self._checkClosed()
		return Syscall(self._channel).lseek(self._fd, 0, SEEK_CUR)

	def truncate(self, size=None):
		self._checkClosed()
		self._checkWritable()
		if size is None:
			size = self.tell()
		Syscall(self._channel).truncate(self._fd, size)
		self._stat_atopen = None
		return size

	def close(self):
		if not self.closed:
			self._stat_atopen = None
			try:
				if self._fd >= 0:
					Syscall(self._channel).close(self._fd)
			finally:
				super().close()

	def seekable(self) -> bool:
		self._checkClosed()
		if self._seekable is None:
			try:
				self.tell()
			except OSError:
				self._seekable = False
			else:
				self._seekable = True
		return self._seekable

	def readable(self) -> bool:
		self._checkClosed()
		return self._readable

	def writable(self) -> bool:
		self._checkClosed()
		return self._writable

	def fileno(self) -> int:
		self._checkClosed()
		return self._fd

	@property
	def mode(self):
		if self._created:
			return 'x+b' if self._readable else 'xb'
		elif self._appending:
			return 'a+b' if self._readable else 'ab'
		elif self._readable:
			return 'r+b' if self._writable else 'rb'
		else:
			return 'wb'


def Open(channel, file: str, mode: str = 'rb') -> ByteFileIO:
	return ByteFileIO(channel, file, mode)
