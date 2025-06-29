import os
import shutil
import grpc
from fsh import fsh_pb2_grpc
from fsh.daemon.server import FSH
from concurrent import futures


class FSHTestBase(object):
	PORT = 50001
	PATH = '/tmp/fsh_tests'

	def setup_method(self, test_method):
		self.server = grpc.server(futures.ThreadPoolExecutor(max_workers=4))
		fsh_pb2_grpc.add_FSHServicer_to_server(FSH(), self.server)
		self.server.add_insecure_port(f'127.0.0.1:{self.PORT}')
		self.server.start()

		os.mkdir(self.PATH)
		os.mkdir(f'{self.PATH}/directory')
		with open(f'{self.PATH}/file', 'wb') as f:
			f.write(b'fsh-test-123\n')
		os.symlink(f'{self.PATH}/file', f'{self.PATH}/link')

	def teardown_method(self, test_method):
		self.server.stop(None)
		shutil.rmtree(self.PATH)
