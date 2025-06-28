import io
import grpc
import sys
import os
from fsh.wrapper import Path, Syscall, Open

print(f'uid = {os.geteuid()}')

# wrappers for os.path.is*() functions
with grpc.insecure_channel(f'unix://{sys.argv[1]}') as c:
	os_path = Path(c)
	print(f"{os_path.isdir('/etc') = }")
	print(f"{os_path.isfile('/etc/passwd') = }")
	print(f"{os_path.islink('/etc/localtime') = }")
	print(f"{os_path.exists('/etc/not-exist') = }")

# syscalls
with grpc.insecure_channel(f'unix://{sys.argv[1]}') as c:
	syscall = Syscall(c)
	fd = syscall.open('/tmp/test123.txt', os.O_CREAT | os.O_RDWR | os.O_TRUNC, 0o0644)
	syscall.write(fd, b'Hello world from FSH!\n')
	syscall.lseek(fd, 32, os.SEEK_SET)
	syscall.write(fd, b'Another end of a file hole, created by lseek()!\n')
	syscall.close(fd)

# IO class
with grpc.insecure_channel(f'unix://{sys.argv[1]}') as c:
	with Open(c, '/tmp/test123.txt', 'rb') as f:
		print(f'{type(f) = }')
		print(f'{f.readable() = }')
		print(f'{f.writable() = }')
		print(f'{f.read() = }')
	with Open(c, '/tmp/test456.txt', 'w+b') as f:
		f.write(b'123456789')
		f.seek(2, io.SEEK_SET)
		f.write(b'abc')
