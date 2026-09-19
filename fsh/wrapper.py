import array
import os
import pickle
import socket
from io import FileIO
from typing import List, Optional

from fsh import fsh_pb2, fsh_pb2_grpc, EXCHANGE_SUCCESS


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
	def __init__(self, channel, fd_uds: str) -> None:
		self.__channel = channel
		self.__fd_uds = fd_uds
		self.__stub = fsh_pb2_grpc.FSHStub(self.__channel)

	def _exchange_fd(self, token: bytes) -> Optional[int]:
		sock = socket.socket(socket.AF_UNIX, socket.SOCK_SEQPACKET)
		try:
			sock.connect(self.__fd_uds)
			sock.sendall(token)
			fds = array.array('i')
			data, ancdata, flags, addr = sock.recvmsg(1, socket.CMSG_SPACE(fds.itemsize))
			if data != EXCHANGE_SUCCESS:
				return None
			for level, typ, cmsg_data in ancdata:
				if level == socket.SOL_SOCKET and typ == socket.SCM_RIGHTS:
					fds.frombytes(cmsg_data[:len(cmsg_data) - (len(cmsg_data) % fds.itemsize)])
				# wried! the server shall never return multiple fds,
				# but we close them anyway to avoid potential issues ...
			if len(fds) != 1:
				for fd in fds: os.close(fd)
				return None
			return fds[0]
		finally:
			sock.close()

	def open(self, path: str, flags: int, mode: int) -> int:
		r = self.__stub.Open(fsh_pb2.OpenRequest(path=path, flags=flags, mode=mode))
		if not r.ok:
			raise pickle.loads(r.err)
		token = r.token
		fd = self._exchange_fd(token)
		if fd is None:  # this should not happen
			raise OSError(f'weird! unable to exchange file descriptor with token [{token.hex()}]')
		return fd

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
			return os.stat(path)
		else:
			r = self.__stub.Stat(fsh_pb2.StatRequest(path=path, follow_symlinks=follow_symlinks))
		if not r.ok:
			raise pickle.loads(r.err)
		return pickle.loads(r.ret)


def Open(channel, fd_uds: str, file: str, mode: str = 'rb') -> ByteFileIO:
	if not set(mode) <= set('xrwab+'):
		raise ValueError(f'invalid mode: {mode}')
	if sum(c in 'rwax' for c in mode) != 1 or mode.count('+') > 1:
		raise ValueError('Must have exactly one of create/read/write/append mode and at most one plus')

	flags = 0

	if 'x' in mode:
		flags = os.O_CREAT | os.O_CREAT
	elif 'r' in mode:
		flags = 0
	elif 'w' in mode:
		flags = os.O_CREAT | os.O_TRUNC
	elif 'a' in mode:
		flags = os.O_CREAT | os.O_APPEND

	if '+' in mode:
		flags |= os.O_RDWR
	elif 'r' in mode:
		flags |= os.O_RDONLY
	else:
		flags |= os.O_WRONLY

	flags |= getattr(os, 'O_BINARY', 0)
	flags |= getattr(os, 'O_NOINHERIT', 0) or getattr(os, 'O_CLOEXEC', 0)
	fd = Syscall(channel, fd_uds).open(file, flags, 0o666)
	try:
		return FileIO(fd, mode, closefd=True)
	except:
		os.close(fd)
		raise
