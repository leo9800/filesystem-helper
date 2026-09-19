import array
import asyncio
import pytest
import secrets
import socket

from base import FSHTestBase
from fsh import EXCHANGE_FAIL, TOKEN_SIZE


@pytest.mark.asyncio
class TestFdSocketException(FSHTestBase):
	async def test_invalid_token_size(self):
		def test():
			d = f'{self.PREFIX}.fd.sock'
			sock = socket.socket(socket.AF_UNIX, socket.SOCK_SEQPACKET)
			sock.connect(d)
			sock.sendall(secrets.token_bytes(TOKEN_SIZE - 10))
			fds = array.array('i')
			data, _, _, _ = sock.recvmsg(1, socket.CMSG_SPACE(fds.itemsize))
			assert data == EXCHANGE_FAIL
		await asyncio.to_thread(test)

	async def test_invalid_token(self):
		def test():
			d = f'{self.PREFIX}.fd.sock'
			sock = socket.socket(socket.AF_UNIX, socket.SOCK_SEQPACKET)
			sock.connect(d)
			# this is a valid size, but we have not open any file yet ...
			sock.sendall(secrets.token_bytes(TOKEN_SIZE))
			fds = array.array('i')
			data, _, _, _ = sock.recvmsg(1, socket.CMSG_SPACE(fds.itemsize))
			assert data == EXCHANGE_FAIL
		await asyncio.to_thread(test)
