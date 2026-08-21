from io import UnsupportedOperation
import os
import grpc
import pytest
from fsh.wrapper import Open
from base import FSHTestBase


class TestIOObject(FSHTestBase):
	def test_read_lseek(self):
		with grpc.insecure_channel(f'127.0.0.1:{self.PORT}') as c, Open(c, f'{self.PATH}/file', 'r') as f:
			buf = f.read(4)
			assert buf == b'fsh-'

			f.seek(9, os.SEEK_SET)
			buf = f.read(4096)
			assert buf == b'123\n'

	def test_write_lseek(self):
		with grpc.insecure_channel(f'127.0.0.1:{self.PORT}') as c, Open(c, f'{self.PATH}/file', 'w+') as f:
			assert f.writable() is True
			assert f.write(b'test123') == 7
			assert f.seek(5, os.SEEK_CUR) == 12
			assert f.write(b'test456') == 7
		with open(f'{self.PATH}/file', 'rb') as f:
			assert f.read() == b'test123\0\0\0\0\0test456'

	def test_invalid_open(self):
		with grpc.insecure_channel(f'127.0.0.1:{self.PORT}') as c:
			with pytest.raises(FileNotFoundError):
				Open(c, f'{self.PATH}/not-exist', 'r')

	def test_invalid_flag(self):
		with grpc.insecure_channel(f'127.0.0.1:{self.PORT}') as c:
			with pytest.raises(ValueError):
				Open(c, f'{self.PATH}/file', 'nonsense')

	def test_duplicated_flag(self):
		with grpc.insecure_channel(f'127.0.0.1:{self.PORT}') as c:
			with pytest.raises(ValueError):
				Open(c, f'{self.PATH}/file', 'rw+')

	def test_invalid_read_write(self):
		with grpc.insecure_channel(f'127.0.0.1:{self.PORT}') as c:
			with pytest.raises(UnsupportedOperation):
				with Open(c, f'{self.PATH}/file', 'r') as f: f.write(b'123')
			with pytest.raises(UnsupportedOperation):
				with Open(c, f'{self.PATH}/file', 'a') as f: f.read(1)

	def test_seekable(self):
		with grpc.insecure_channel(f'127.0.0.1:{self.PORT}') as c, Open(c, f'{self.PATH}/file', 'r') as f:
			assert f.seekable() is True

	def test_mode(self):
		with grpc.insecure_channel(f'127.0.0.1:{self.PORT}') as c:
			with Open(c, f'{self.PATH}/file', 'r') as f: assert f.mode == 'rb'
			with Open(c, f'{self.PATH}/file', 'w') as f: assert f.mode == 'wb'
			with Open(c, f'{self.PATH}/file', 'a') as f: assert f.mode == 'ab'
			with Open(c, f'{self.PATH}/nxf0', 'x') as f: assert f.mode == 'xb'
			with Open(c, f'{self.PATH}/file', 'r+') as f: assert f.mode == 'r+b'
			with Open(c, f'{self.PATH}/file', 'w+') as f: assert f.mode == 'r+b'
			with Open(c, f'{self.PATH}/file', 'a+') as f: assert f.mode == 'a+b'
			with Open(c, f'{self.PATH}/nxf1', 'x+') as f: assert f.mode == 'x+b'

	def test_readable(self):
		with grpc.insecure_channel(f'127.0.0.1:{self.PORT}') as c:
			with Open(c, f'{self.PATH}/file', 'a') as f: assert f.readable() is False
			with Open(c, f'{self.PATH}/file', 'a+') as f: assert f.readable() is True

	def test_truncate(self):
		with grpc.insecure_channel(f'127.0.0.1:{self.PORT}') as c:
			with Open(c, f'{self.PATH}/file', 'r+') as f:
				f.write(b'1234567890')
				f.truncate(3)
				f.flush()

			with Open(c, f'{self.PATH}/file', 'r+') as f:
				assert f.readall() == b'123'

	def test_readall_large(self):
		with open(f'{self.PATH}/largefile', 'wb') as f:
			f.write(os.urandom(134217728))
			f.flush()
		with grpc.insecure_channel(f'127.0.0.1:{self.PORT}') as c, Open(c, f'{self.PATH}/largefile', 'rb') as f:
			assert len(f.readall()) == 134217728

	def test_write_large(self):
		with grpc.insecure_channel(f'127.0.0.1:{self.PORT}') as c, Open(c, f'{self.PATH}/largefile', 'wb') as f:
			f.write(os.urandom(67108864))
			f.flush()
		with open(f'{self.PATH}/largefile', 'rb') as f:
			assert len(f.read()) == 67108864