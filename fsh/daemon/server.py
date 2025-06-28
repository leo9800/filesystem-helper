import fsh_pb2
import fsh_pb2_grpc
import os
import pickle


class FSH(fsh_pb2_grpc.FSHServicer):
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
			if request.use_fd:
				stat = os.stat(request.fd)
			else:
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
			return fsh_pb2.OpenResponse(ok=False, err=pickle.dumps(e), ret=-1)
		else:
			return fsh_pb2.OpenResponse(ok=True, err=b'', ret=fd)

	def Close(self, request: fsh_pb2.CloseRequest, context) -> fsh_pb2.NoneResponse:
		try:
			os.close(request.fd)
		except Exception as e:
			return fsh_pb2.NoneResponse(ok=False, err=pickle.dumps(e))
		else:
			return fsh_pb2.NoneResponse(ok=True, err=b'')

	def Read(self, request: fsh_pb2.ReadRequest, context) -> fsh_pb2.ReadResponse:
		try:
			c = os.read(request.fd, request.n)
		except Exception as e:
			return fsh_pb2.ReadResponse(ok=False, err=pickle.dumps(e), ret=b'')
		else:
			return fsh_pb2.ReadResponse(ok=True, err=b'', ret=c)

	def Write(self, request: fsh_pb2.WriteRequest, context) -> fsh_pb2.WriteResponse:
		try:
			n = os.write(request.fd, request.str)
		except Exception as e:
			return fsh_pb2.WriteResponse(ok=False, err=pickle.dumps(e), ret=-1)
		else:
			return fsh_pb2.WriteResponse(ok=True, err=b'', ret=n)

	def Lseek(self, request: fsh_pb2.LseekRequest, context) -> fsh_pb2.LseekResponse:
		try:
			n = os.lseek(request.fd, request.pos, request.whence)
		except Exception as e:
			return fsh_pb2.LseekResponse(ok=False, err=pickle.dumps(e), ret=-1)
		else:
			return fsh_pb2.LseekResponse(ok=True, err=b'', ret=n)

	def Fsync(self, request: fsh_pb2.FsyncRequest, context) -> fsh_pb2.NoneResponse:
		try:
			os.fsync(request.fd)
		except Exception as e:
			return fsh_pb2.NoneResponse(ok=False, err=pickle.dumps(e))
		else:
			return fsh_pb2.NoneResponse(ok=True, err=b'')

	def Truncate(self, request: fsh_pb2.TruncateRequest, context) -> fsh_pb2.NoneResponse:
		try:
			os.truncate(request.fd, request.length)
		except Exception as e:
			return fsh_pb2.NoneResponse(ok=False, err=pickle.dumps(e))
		else:
			return fsh_pb2.NoneResponse(ok=True, err=b'')
