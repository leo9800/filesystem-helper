import os
from _pytest.capture import SysCapture
import grpc
import pytest
from fsh.wrapper import Syscall
from base import FSHTestBase

class TestSyscall(FSHTestBase):
	def test_read_lseek(self):
		with grpc.insecure_channel(f'127.0.0.1:{self.PORT}') as c:
			fd = Syscall(c).open(f'{self.PATH}/file', os.O_RDONLY, 0o0666)
			buf = Syscall(c).read(fd, 4)
			assert buf == b'fsh-'
			Syscall(c).lseek(fd, 9, os.SEEK_SET)
			buf = Syscall(c).read(fd, 4096)
			assert buf == b'123\n'

	def test_write_lseek(self):
		with grpc.insecure_channel(f'127.0.0.1:{self.PORT}') as c:
			fd = Syscall(c).open(f'{self.PATH}/file', os.O_WRONLY|os.O_CREAT|os.O_TRUNC, 0o0666)
			assert Syscall(c).write(fd, b'test123') == 7
			assert Syscall(c).lseek(fd, 5, os.SEEK_CUR) == 12
			assert Syscall(c).write(fd, b'test456') == 7
			Syscall(c).close(fd)

			with open(f'{self.PATH}/file', 'rb') as f:
				assert f.read() == b'test123\0\0\0\0\0test456'

	def test_invalid_open(self):
		with grpc.insecure_channel(f'127.0.0.1:{self.PORT}') as c:
			with pytest.raises(FileNotFoundError):
				Syscall(c).open(f'{self.PATH}/not-exist', os.O_RDONLY, 0o0666)

	def test_invalid_close(self):
		with grpc.insecure_channel(f'127.0.0.1:{self.PORT}') as c:
			with pytest.raises(OSError):
				Syscall(c).close(50000) # not existing fd

	def test_invalid_read(self):
		with grpc.insecure_channel(f'127.0.0.1:{self.PORT}') as c:
			with pytest.raises(OSError):
				Syscall(c).read(50000, 1) # not existing fd

	def test_invalid_write(self):
		with grpc.insecure_channel(f'127.0.0.1:{self.PORT}') as c:
			with pytest.raises(OSError):
				fd = Syscall(c).open(f'{self.PATH}/file', os.O_RDONLY, 0o0666)
				Syscall(c).write(fd, b'garbage') # read-only fd

	def test_invalid_lseek(self):
		with grpc.insecure_channel(f'127.0.0.1:{self.PORT}') as c:
			with pytest.raises(OSError):
				Syscall(c).lseek(50000, 0, os.SEEK_CUR) # not existing fd

	def test_fsync(self):
		with grpc.insecure_channel(f'127.0.0.1:{self.PORT}') as c:
			fd = Syscall(c).open(f'{self.PATH}/file', os.O_WRONLY|os.O_CREAT|os.O_TRUNC, 0o0666)
			Syscall(c).write(fd, b'test123')
			Syscall(c).fsync(fd)
			Syscall(c).close(fd)

			with open(f'{self.PATH}/file', 'rb') as f:
				assert f.read() == b'test123'

			with pytest.raises(OSError):
				Syscall(c).fsync(50000) # not existing fd

	def test_unlink(self):
		with grpc.insecure_channel(f'127.0.0.1:{self.PORT}') as c:
			assert os.path.exists(f'{self.PATH}/file') is True
			Syscall(c).unlink(f'{self.PATH}/file')
			assert os.path.exists(f'{self.PATH}/file') is False

			with pytest.raises(OSError):
				Syscall(c).unlink(f'{self.PATH}/not-exist')

	def test_truncate(self):
		with grpc.insecure_channel(f'127.0.0.1:{self.PORT}') as c:
			fd = Syscall(c).open(f'{self.PATH}/file', os.O_WRONLY|os.O_CREAT|os.O_TRUNC, 0o0666)
			Syscall(c).write(fd, b'test123')
			Syscall(c).fsync(fd)

			with open(f'{self.PATH}/file', 'rb') as f:
				assert f.read() == b'test123'

			Syscall(c).truncate(fd, 4)
			Syscall(c).fsync(fd)

			with open(f'{self.PATH}/file', 'rb') as f:
				assert f.read() == b'test'

			Syscall(c).close(fd)

			with pytest.raises(OSError):
				Syscall(c).truncate(50000, 4) # not existing fd

	def test_mkdir_rmdir(self):
		with grpc.insecure_channel(f'127.0.0.1:{self.PORT}') as c:
			assert os.path.exists(f'{self.PATH}/new-directory') is False
			Syscall(c).mkdir(f'{self.PATH}/new-directory', 0o755)
			assert os.path.exists(f'{self.PATH}/new-directory') is True

			assert os.path.exists(f'{self.PATH}/directory') is True
			Syscall(c).rmdir(f'{self.PATH}/directory')
			assert os.path.exists(f'{self.PATH}/directory') is False

			with pytest.raises(OSError):
				Syscall(c).rmdir(f'{self.PATH}/not-exist')

			with pytest.raises(OSError):
				Syscall(c).mkdir(f'{self.PATH}/file', 0o755)

	def test_listdir(self):
		with grpc.insecure_channel(f'127.0.0.1:{self.PORT}') as c:
			dirs = Syscall(c).listdir(self.PATH)
			dirs_golden = os.listdir(self.PATH)
			assert set(dirs) == set(dirs_golden)

			with pytest.raises(OSError):
				Syscall(c).listdir(f'{self.PATH}/not-exist')

	def test_utime(self):
		with grpc.insecure_channel(f'127.0.0.1:{self.PORT}') as c:
			Syscall(c).utime(f'{self.PATH}/file', 10, 20)
			stat = os.stat(f'{self.PATH}/file')
			assert stat.st_atime == 10
			assert stat.st_mtime == 20

			with pytest.raises(OSError):
				Syscall(c).utime(f'{self.PATH}/not-exist', 10, 20)

	def test_stat_path(self):
		with grpc.insecure_channel(f'127.0.0.1:{self.PORT}') as c:
			stat = Syscall(c).stat(f'{self.PATH}/file')
			stat_golden = os.stat(f'{self.PATH}/file')
			assert stat == stat_golden

			with pytest.raises(OSError):
				Syscall(c).stat(f'{self.PATH}/not-exist')

	def test_stat_fd(self):
		with grpc.insecure_channel(f'127.0.0.1:{self.PORT}') as c:
			fd = Syscall(c).open(f'{self.PATH}/file', os.O_RDONLY, 0o666)
			stat = Syscall(c).stat(fd)
			stat_golden = os.stat(f'{self.PATH}/file')
			assert stat == stat_golden

			with pytest.raises(OSError):
				Syscall(c).stat(50000) # not existing fd
