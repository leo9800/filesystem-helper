import asyncio
import os
import grpc
import pytest

from fsh.wrapper import Syscall
from base import FSHTestBase


@pytest.mark.asyncio
class TestSyscall(FSHTestBase):
	async def test_read_lseek(self):
		def test():
			d = f'{self.PREFIX}.fd.sock'
			with grpc.insecure_channel(f'unix://{self.PREFIX}.sock') as c:
				fd = Syscall(c, d).open(f'{self.PATH}/file', os.O_RDONLY, 0o0666)
				buf = os.read(fd, 4)
				assert buf == b'fsh-'
				os.lseek(fd, 9, os.SEEK_SET)
				buf = os.read(fd, 4096)
				assert buf == b'123\n'
		await asyncio.to_thread(test)

	async def test_write_lseek(self):
		def test():
			d = f'{self.PREFIX}.fd.sock'
			with grpc.insecure_channel(f'unix://{self.PREFIX}.sock') as c:
				fd = Syscall(c, d).open(f'{self.PATH}/file', os.O_WRONLY|os.O_CREAT|os.O_TRUNC, 0o0666)
				assert os.write(fd, b'test123') == 7
				assert os.lseek(fd, 5, os.SEEK_CUR) == 12
				assert os.write(fd, b'test456') == 7
				os.close(fd)

				with open(f'{self.PATH}/file', 'rb') as f:
					assert f.read() == b'test123\0\0\0\0\0test456'
		await asyncio.to_thread(test)

	async def test_invalid_open(self):
		def test():
			d = f'{self.PREFIX}.fd.sock'
			with grpc.insecure_channel(f'unix://{self.PREFIX}.sock') as c:
				with pytest.raises(FileNotFoundError):
					Syscall(c, d).open(f'{self.PATH}/not-exist', os.O_RDONLY, 0o0666)
		await asyncio.to_thread(test)

	async def test_unlink(self):
		def test():
			d = f'{self.PREFIX}.fd.sock'
			with grpc.insecure_channel(f'unix://{self.PREFIX}.sock') as c:
				assert os.path.exists(f'{self.PATH}/file') is True
				Syscall(c, d).unlink(f'{self.PATH}/file')
				assert os.path.exists(f'{self.PATH}/file') is False

				with pytest.raises(OSError):
					Syscall(c, d).unlink(f'{self.PATH}/not-exist')
		await asyncio.to_thread(test)

	async def test_mkdir_rmdir(self):
		def test():
			d = f'{self.PREFIX}.fd.sock'
			with grpc.insecure_channel(f'unix://{self.PREFIX}.sock') as c:
				assert os.path.exists(f'{self.PATH}/new-directory') is False
				Syscall(c, d).mkdir(f'{self.PATH}/new-directory', 0o755)
				assert os.path.exists(f'{self.PATH}/new-directory') is True

				assert os.path.exists(f'{self.PATH}/directory') is True
				Syscall(c, d).rmdir(f'{self.PATH}/directory')
				assert os.path.exists(f'{self.PATH}/directory') is False

				with pytest.raises(OSError):
					Syscall(c, d).rmdir(f'{self.PATH}/not-exist')

				with pytest.raises(OSError):
					Syscall(c, d).mkdir(f'{self.PATH}/file', 0o755)
		await asyncio.to_thread(test)

	async def test_listdir(self):
		def test():
			d = f'{self.PREFIX}.fd.sock'
			with grpc.insecure_channel(f'unix://{self.PREFIX}.sock') as c:
				dirs = Syscall(c, d).listdir(self.PATH)
				dirs_golden = os.listdir(self.PATH)
				assert set(dirs) == set(dirs_golden)

				with pytest.raises(OSError):
					Syscall(c, d).listdir(f'{self.PATH}/not-exist')
		await asyncio.to_thread(test)

	async def test_utime(self):
		def test():
			d = f'{self.PREFIX}.fd.sock'
			with grpc.insecure_channel(f'unix://{self.PREFIX}.sock') as c:
				Syscall(c, d).utime(f'{self.PATH}/file', 10, 20)
				stat = os.stat(f'{self.PATH}/file')
				assert stat.st_atime == 10
				assert stat.st_mtime == 20

				with pytest.raises(OSError):
					Syscall(c, d).utime(f'{self.PATH}/not-exist', 10, 20)
		await asyncio.to_thread(test)

	async def test_stat_path(self):
		def test():
			d = f'{self.PREFIX}.fd.sock'
			with grpc.insecure_channel(f'unix://{self.PREFIX}.sock') as c:
				stat = Syscall(c, d).stat(f'{self.PATH}/file')
				stat_golden = os.stat(f'{self.PATH}/file')
				assert stat == stat_golden

				with pytest.raises(OSError):
					Syscall(c, d).stat(f'{self.PATH}/not-exist')
		await asyncio.to_thread(test)

	async def test_stat_fd(self):
		def test():
			d = f'{self.PREFIX}.fd.sock'
			with grpc.insecure_channel(f'unix://{self.PREFIX}.sock') as c:
				fd = Syscall(c, d).open(f'{self.PATH}/file', os.O_RDONLY, 0o0644)
				stat = Syscall(c, d).stat(fd)
				stat_golden = os.stat(f'{self.PATH}/file')
				assert stat == stat_golden

				with pytest.raises(OSError):
					Syscall(c, d).stat(4869)
		await asyncio.to_thread(test)
