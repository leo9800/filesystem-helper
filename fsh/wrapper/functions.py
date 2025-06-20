import fsh_pb2
import fsh_pb2_grpc
import os
import pickle
from typing import List


class FSHFunctions(object):
	def __init__(self, channel) -> None:
		self.__channel = channel
		self.__stub = fsh_pb2_grpc.FSHStub(self.__channel)

	def PathIsdir(self, path: str) -> bool:
		return self.__stub.PathIsDir(fsh_pb2.PathRequest(path=path)).ret

	def PathIsLink(self, path: str) -> bool:
		return self.__stub.PathIsLink(fsh_pb2.PathRequest(path=path)).ret

	def PathIsFile(self, path: str) -> bool:
		return self.__stub.PathIsFile(fsh_pb2.PathRequest(path=path)).ret

	def PathExists(self, path: str) -> bool:
		return self.__stub.PathExists(fsh_pb2.PathRequest(path=path)).ret

	def Stat(self, path: str, follow_symlinks: bool = False) -> os.stat_result:
		r = self.__stub.Stat(fsh_pb2.StatRequest(path=path, follow_symlinks=follow_symlinks))
		if not r.ok:
			raise pickle.loads(r.err)
		return pickle.loads(r.ret)

	def Unlink(self, path: str) -> None:
		r = self.__stub.Unlink(fsh_pb2.PathRequest(path=path))
		if not r.ok:
			raise pickle.loads(r.err)

	def Utime(self, path: str, atime: int, mtime: int, follow_symlinks: bool = False) -> None:
		r = self.__stub.Utime(fsh_pb2.UtimeRequest(
			path=path,
			atime=atime,
			mtime=mtime,
			follow_symlinks=follow_symlinks,
		))
		if not r.ok:
			raise pickle.loads(r.err)

	def Listdir(self, path: str) -> List[str]:
		r = self.__stub.Listdir(fsh_pb2.PathRequest(path=path))
		if not r.ok:
			raise pickle.loads(r.err)
		return r.ret

	def Mkdir(self, path: str, mode: int) -> None:
		r = self.__stub.Mkdir(fsh_pb2.MkdirRequest(path=path, mode=mode))
		if not r.ok:
			raise pickle.loads(r.err)

	def Rmdir(self, path: str) -> None:
		r = self.__stub.Rmdir(fsh_pb2.PathRequest(path=path))
		if not r.ok:
			raise pickle.loads(r.err)

	def Open(self, path: str, flags: int, mode: int) -> int:
		r = self.__stub.Open(fsh_pb2.OpenRequest(path=path, flags=flags, mode=mode))
		if not r.ok:
			raise pickle.loads(r.err)
		return r.ret

	def Close(self, fd: int) -> None:
		r = self.__stub.Close(fsh_pb2.CloseRequest(fd=fd))
		if not r.ok:
			raise pickle.loads(r.err)

	def Read(self, fd: int, n: int) -> bytes:
		r = self.__stub.Read(fsh_pb2.ReadRequest(fd=fd, n=n))
		if not r.ok:
			raise pickle.loads(r.err)
		return r.ret

	def Write(self, fd: int, i: bytes) -> int:
		r = self.__stub.Write(fsh_pb2.WriteRequest(fd=fd, str=i))
		if not r.ok:
			raise pickle.loads(r.err)
		return r.ret

	def Lseek(self, fd: int, pos: int, whence: int) -> int:
		r = self.__stub.Lseek(fsh_pb2.LseekRequest(fd=fd, pos=pos, whence=whence))
		if not r.ok:
			raise pickle.loads(r.err)
		return r.ret

	def Fsync(self, fd: int) -> None:
		r = self.__stub.Fsync(fsh_pb2.FsyncRequest(fd=fd))
		if not r.ok:
			raise pickle.loads(r.err)

	def Truncate(self, fd: int, length: int) -> None:
		r = self.__stub.Truncate(fsh_pb2.TruncateRequest(fd=fd, length=length))
		if not r.ok:
			raise pickle.loads(r.err)
