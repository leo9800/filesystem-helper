import grpc
from fsh.wrapper import Path
from base import FSHTestBase

class TestPath(FSHTestBase):
	def test_isdir(self):
		with grpc.insecure_channel(f'127.0.0.1:{self.PORT}') as c:
			assert Path(c).isdir(f'{self.PATH}/directory') is True
			assert Path(c).isdir(f'{self.PATH}/file') is False
			assert Path(c).isdir(f'{self.PATH}/link') is False

	def test_isfile(self):
		with grpc.insecure_channel(f'127.0.0.1:{self.PORT}') as c:
			assert Path(c).isfile(f'{self.PATH}/directory') is False
			assert Path(c).isfile(f'{self.PATH}/file') is True
			assert Path(c).isfile(f'{self.PATH}/link') is True

	def test_islink(self):
		with grpc.insecure_channel(f'127.0.0.1:{self.PORT}') as c:
			assert Path(c).islink(f'{self.PATH}/directory') is False
			assert Path(c).islink(f'{self.PATH}/file') is False
			assert Path(c).islink(f'{self.PATH}/link') is True

	def test_exists(self):
		with grpc.insecure_channel(f'127.0.0.1:{self.PORT}') as c:
			assert Path(c).exists(f'{self.PATH}/file') is True
			assert Path(c).exists(f'{self.PATH}/not-exist') is False
