import array
import asyncio
import os
import pickle
import secrets
import socket
import threading
from typing import Dict, Optional

from fsh import fsh_pb2, fsh_pb2_grpc, EXCHANGE_FAIL, EXCHANGE_SUCCESS, TOKEN_SIZE


class FSH(fsh_pb2_grpc.FSHServicer):
	def __init__(self) -> None:
		self._fd_map: Dict[bytes, int] = {}
		self._fd_lock = threading.Lock()

	def PathIsDir(self, request: fsh_pb2.PathRequest, context) -> fsh_pb2.BoolResponse:
		return fsh_pb2.BoolResponse(ok=True, err=b'', ret=os.path.isdir(request.path))

	def PathIsLink(self, request: fsh_pb2.PathRequest, context) -> fsh_pb2.BoolResponse:
		return fsh_pb2.BoolResponse(ok=True, err=b'', ret=os.path.islink(request.path))

	def PathIsFile(self, request: fsh_pb2.PathRequest, context) -> fsh_pb2.BoolResponse:
		return fsh_pb2.BoolResponse(ok=True, err=b'', ret=os.path.isfile(request.path))

	def PathExists(self, request: fsh_pb2.PathRequest, context) -> fsh_pb2.BoolResponse:
		return fsh_pb2.BoolResponse(ok=True, err=b'', ret=os.path.exists(request.path))

	def Stat(self, request: fsh_pb2.StatRequest, context) -> fsh_pb2.StatResponse:
		try:
			stat = os.stat(request.path, follow_symlinks=request.follow_symlinks)
		except Exception as e:
			return fsh_pb2.StatResponse(ok=False, err=pickle.dumps(e), ret=b'')
		else:
			return fsh_pb2.StatResponse(ok=True, err=b'', ret=pickle.dumps(stat))

	def Unlink(self, request: fsh_pb2.PathRequest, context) -> fsh_pb2.NoneResponse:
		try:
			os.unlink(request.path)
		except Exception as e:
			return fsh_pb2.NoneResponse(ok=False, err=pickle.dumps(e))
		else:
			return fsh_pb2.NoneResponse(ok=True, err=b'')

	def Utime(self, request: fsh_pb2.UtimeRequest, context) -> fsh_pb2.NoneResponse:
		try:
			os.utime(
				request.path,
				times=(request.atime, request.mtime),
				follow_symlinks=request.follow_symlinks
			)
		except Exception as e:
			return fsh_pb2.NoneResponse(ok=False, err=pickle.dumps(e))
		else:
			return fsh_pb2.NoneResponse(ok=True, err=b'')

	def Listdir(self, request: fsh_pb2.PathRequest, context) -> fsh_pb2.ListdirResponse:
		try:
			l = os.listdir(request.path)
		except Exception as e:
			return fsh_pb2.ListdirResponse(ok=False, err=pickle.dumps(e), ret=[])
		else:
			return fsh_pb2.ListdirResponse(ok=True, err=b'', ret=l)

	def Mkdir(self, request: fsh_pb2.MkdirRequest, context) -> fsh_pb2.NoneResponse:
		try:
			os.mkdir(request.path, mode=request.mode)
		except Exception as e:
			return fsh_pb2.NoneResponse(ok=False, err=pickle.dumps(e))
		else:
			return fsh_pb2.NoneResponse(ok=True, err=b'')

	def Rmdir(self, request: fsh_pb2.PathRequest, context) -> fsh_pb2.NoneResponse:
		try:
			os.rmdir(request.path)
		except Exception as e:
			return fsh_pb2.NoneResponse(ok=False, err=pickle.dumps(e))
		else:
			return fsh_pb2.NoneResponse(ok=True, err=b'')

	def Open(self, request: fsh_pb2.OpenRequest, context) -> fsh_pb2.OpenResponse:
		try:
			fd = os.open(request.path, flags=request.flags, mode=request.mode)
		except Exception as e:
			return fsh_pb2.OpenResponse(ok=False, err=pickle.dumps(e), token=b'')
		try:
			token = secrets.token_bytes(TOKEN_SIZE)
			with self._fd_lock:
				while token in self._fd_map: token = secrets.token_bytes(TOKEN_SIZE)
			self._fd_map[token] = fd
		except Exception as e:
			os.close(fd)
			raise  # this should not fail, if so, raise to upper level
		return fsh_pb2.OpenResponse(ok=True, err=b'', token=token)

	def exchange_fd(self, token: bytes) -> Optional[int]:
		with self._fd_lock:
			return self._fd_map.pop(token, None)


async def fd_socket_listen(s: socket.socket, fsh: FSH):
	loop = asyncio.get_running_loop()
	while True:
		cs, _ = await loop.sock_accept(s)
		asyncio.create_task(fd_socket_accept(cs, fsh))


async def fd_socket_accept(cs: socket.socket, fsh: FSH):
	loop = asyncio.get_running_loop()
	fd = None
	try:
		token = cs.recv(TOKEN_SIZE)
		if len(token) != TOKEN_SIZE:
			await loop.sock_sendall(cs, EXCHANGE_FAIL)
			return
		fd = fsh.exchange_fd(token)
		if fd is None:
			await loop.sock_sendall(cs, EXCHANGE_FAIL)
			return
		cs.sendmsg(
			[EXCHANGE_SUCCESS],
			[(socket.SOL_SOCKET, socket.SCM_RIGHTS, array.array('i', [fd]))],
		)
	except Exception:
		raise
	finally:
		if fd is not None:
			os.close(fd)
		cs.close()