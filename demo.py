import grpc
import sys
import os
from fsh.wrapper.functions import FSHFunctions

print(f'uid = {os.geteuid()}')

with grpc.insecure_channel(f'unix://{sys.argv[1]}') as c:
	f = FSHFunctions(c)
	fd = f.Open('/tmp/test123.txt', os.O_CREAT|os.O_RDWR|os.O_TRUNC, 0o0644)
	f.Write(fd, b'Hello, world from FSH!\n')
	f.Lseek(fd, 0, os.SEEK_SET)
	print(f'content of first 4096 bytes: \n{f.Read(fd, 4096)}')
	f.Close(fd)