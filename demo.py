import grpc
import sys
import os
from fsh.wrapper import Path, Syscall

print(f'uid = {os.geteuid()}')

with grpc.insecure_channel(f'unix://{sys.argv[1]}') as c:
	f = Syscall(c)
	fd = f.open('/tmp/test123.txt', os.O_CREAT|os.O_RDWR|os.O_TRUNC, 0o0644)
	f.write(fd, b'Hello, world from FSH!\n')
	f.lseek(fd, 0, os.SEEK_SET)
	print(f'content of first 4096 bytes: \n{f.read(fd, 4096)}')
	f.close(fd)
