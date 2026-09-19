import asyncio
import grpc
import os
import pytest
from io import UnsupportedOperation

from fsh.wrapper import Open
from base import FSHTestBase


@pytest.mark.asyncio
class TestIOObject(FSHTestBase):
	async def test_read_lseek(self):
		def test():
			d = f'{self.PREFIX}.fd.sock'
			with grpc.insecure_channel(f'unix://{self.PREFIX}.sock') as c, Open(c, d, f'{self.PATH}/file', 'r') as f:
				buf = f.read(4)
				assert buf == b'fsh-'

				f.seek(9, os.SEEK_SET)
				buf = f.read(4096)
				assert buf == b'123\n'
		await asyncio.to_thread(test)

	async def test_write_lseek(self):
		def test():
			d = f'{self.PREFIX}.fd.sock'
			with grpc.insecure_channel(f'unix://{self.PREFIX}.sock') as c, Open(c, d, f'{self.PATH}/file', 'w+') as f:
				assert f.writable() is True
				assert f.write(b'test123') == 7
				assert f.seek(5, os.SEEK_CUR) == 12
				assert f.write(b'test456') == 7
			with open(f'{self.PATH}/file', 'rb') as f:
				assert f.read() == b'test123\0\0\0\0\0test456'
		await asyncio.to_thread(test)

	async def test_invalid_open(self):
		def test():
			d = f'{self.PREFIX}.fd.sock'
			with grpc.insecure_channel(f'unix://{self.PREFIX}.sock') as c:
				with pytest.raises(FileNotFoundError):
					Open(c, d, f'{self.PATH}/not-exist', 'r')
		await asyncio.to_thread(test)

	async def test_invalid_flag(self):
		def test():
			d = f'{self.PREFIX}.fd.sock'
			with grpc.insecure_channel(f'unix://{self.PREFIX}.sock') as c:
				with pytest.raises(ValueError):
					Open(c, d, f'{self.PATH}/file', 'nonsense')
		await asyncio.to_thread(test)

	async def test_duplicated_flag(self):
		def test():
			d = f'{self.PREFIX}.fd.sock'
			with grpc.insecure_channel(f'unix://{self.PREFIX}.sock') as c:
				with pytest.raises(ValueError):
					Open(c, d, f'{self.PATH}/file', 'rw+')
		await asyncio.to_thread(test)

	async def test_invalid_read_write(self):
		def test():
			d = f'{self.PREFIX}.fd.sock'
			with grpc.insecure_channel(f'unix://{self.PREFIX}.sock') as c:
				with pytest.raises(UnsupportedOperation):
					with Open(c, d, f'{self.PATH}/file', 'r') as f: f.write(b'123')
				with pytest.raises(UnsupportedOperation):
					with Open(c, d, f'{self.PATH}/file', 'a') as f: f.read(1)
		await asyncio.to_thread(test)

	async def test_seekable(self):
		def test():
			d = f'{self.PREFIX}.fd.sock'
			with grpc.insecure_channel(f'unix://{self.PREFIX}.sock') as c, Open(c, d, f'{self.PATH}/file', 'r') as f:
				assert f.seekable() is True
		await asyncio.to_thread(test)

	async def test_mode(self):
		def test():
			d = f'{self.PREFIX}.fd.sock'
			with grpc.insecure_channel(f'unix://{self.PREFIX}.sock') as c:
				with Open(c, d, f'{self.PATH}/file', 'r') as f: assert set(f.mode) == set('rb')
				with Open(c, d, f'{self.PATH}/file', 'w') as f: assert set(f.mode) == set('wb')
				with Open(c, d, f'{self.PATH}/file', 'a') as f: assert set(f.mode) == set('ab')
				with Open(c, d, f'{self.PATH}/nxf0', 'x') as f: assert set(f.mode) == set('xb')
				with Open(c, d, f'{self.PATH}/file', 'r+') as f: assert set(f.mode) == set('r+b')
				with Open(c, d, f'{self.PATH}/file', 'w+') as f: assert set(f.mode) == set('r+b')
				with Open(c, d, f'{self.PATH}/file', 'a+') as f: assert set(f.mode) == set('a+b')
				with Open(c, d, f'{self.PATH}/nxf1', 'x+') as f: assert set(f.mode) == set('x+b')
		await asyncio.to_thread(test)

	async def test_readable(self):
		def test():
			d = f'{self.PREFIX}.fd.sock'
			with grpc.insecure_channel(f'unix://{self.PREFIX}.sock') as c:
				with Open(c, d, f'{self.PATH}/file', 'a') as f: assert f.readable() is False
				with Open(c, d, f'{self.PATH}/file', 'a+') as f: assert f.readable() is True
		await asyncio.to_thread(test)

	async def test_truncate(self):
		def test():
			d = f'{self.PREFIX}.fd.sock'
			with grpc.insecure_channel(f'unix://{self.PREFIX}.sock') as c:
				with Open(c, d, f'{self.PATH}/file', 'r+') as f:
					f.write(b'1234567890')
					f.truncate(3)
					f.flush()

				with Open(c, d, f'{self.PATH}/file', 'r+') as f:
					assert f.readall() == b'123'
		await asyncio.to_thread(test)

	async def test_large_read(self):
		def test():
			d = f'{self.PREFIX}.fd.sock'
			with open(f'{self.PATH}/largefile', 'wb') as f:
				f.write(os.urandom(1073741824))  # 1gb
				f.flush()
			with grpc.insecure_channel(f'unix://{self.PREFIX}.sock') as c, Open(c, d, f'{self.PATH}/largefile', 'rb') as f:
				assert len(f.readall()) == 1073741824
		await asyncio.to_thread(test)

	async def test_large_write(self):
		def test():
			d = f'{self.PREFIX}.fd.sock'
			with grpc.insecure_channel(f'unix://{self.PREFIX}.sock') as c, Open(c, d, f'{self.PATH}/largefile', 'wb') as f:
				f.write(os.urandom(1073741824))  # 1gb
				f.flush()
			with open(f'{self.PATH}/largefile', 'rb') as f:
				assert len(f.read()) == 1073741824
		await asyncio.to_thread(test)
