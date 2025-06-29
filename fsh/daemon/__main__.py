from concurrent import futures
from fsh.daemon.server import FSH
from fsh import fsh_pb2_grpc
import os
import grpc

SERVER_THREADS = 8

def serve():
	uds = f'/tmp/fsh_{os.geteuid()}_{os.getpid()}.sock'
	assert not os.path.exists(uds)  # this can barely exist ...
	try:
		server = grpc.server(futures.ThreadPoolExecutor(max_workers=SERVER_THREADS))
		fsh_pb2_grpc.add_FSHServicer_to_server(FSH(), server)
		server.add_insecure_port(f'unix://{uds}')
		server.start()
		os.chmod(uds, 0o0700)
		server.wait_for_termination()
	except Exception as e:
		raise e
	finally:
		os.unlink(uds)

if __name__ == '__main__':
	serve()
