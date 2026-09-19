import asyncio
import contextlib
import grpc
import os
import socket
import sys

from fsh.server import FSH, fd_socket_listen
from fsh import fsh_pb2_grpc


async def serve(prefix: str):
	uds_grpc = f'{prefix}.sock'
	uds_fd = f'{prefix}.fd.sock'
	assert not os.path.exists(uds_grpc)
	assert not os.path.exists(uds_fd)

	fsh = FSH()
	fd_sock = socket.socket(socket.AF_UNIX, socket.SOCK_SEQPACKET)
	fd_sock.setblocking(False)
	fd_sock.bind(uds_fd)
	fd_sock.listen()
	os.chmod(uds_fd, 0o0700)

	grpc_server = grpc.aio.server()
	fsh_pb2_grpc.add_FSHServicer_to_server(fsh, grpc_server)
	grpc_server.add_insecure_port(f'unix://{uds_grpc}')
	await grpc_server.start()
	os.chmod(uds_grpc, 0o0700)

	fd_listen = asyncio.create_task(fd_socket_listen(fd_sock, fsh))

	try:
		with contextlib.suppress(asyncio.CancelledError):
			await grpc_server.wait_for_termination()
	except KeyboardInterrupt:
		sys.exit(0)
	finally:
		with contextlib.suppress(asyncio.CancelledError):
			await grpc_server.stop(None)
		fd_listen.cancel()
		with contextlib.suppress(asyncio.CancelledError):
			await fd_listen
		fd_sock.close()
		with contextlib.suppress(FileNotFoundError):
			os.unlink(uds_grpc)
		with contextlib.suppress(FileNotFoundError):
			os.unlink(uds_fd)

if __name__ == '__main__':
	asyncio.run(serve(prefix=f'/tmp/fsh_{os.geteuid()}_{os.getpid()}'))
