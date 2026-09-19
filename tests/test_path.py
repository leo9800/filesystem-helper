import asyncio
import grpc
import pytest

from fsh.wrapper import Path
from base import FSHTestBase


@pytest.mark.asyncio
class TestPath(FSHTestBase):
	async def test_isdir(self):
		def test():
			with grpc.insecure_channel(f'unix://{self.PREFIX}.sock') as c:
				assert Path(c).isdir(f'{self.PATH}/directory') is True
				assert Path(c).isdir(f'{self.PATH}/file') is False
				assert Path(c).isdir(f'{self.PATH}/link') is False
		await asyncio.to_thread(test)
			

	async def test_isfile(self):
		def test():
			with grpc.insecure_channel(f'unix://{self.PREFIX}.sock') as c:
				assert Path(c).isfile(f'{self.PATH}/directory') is False
				assert Path(c).isfile(f'{self.PATH}/file') is True
				assert Path(c).isfile(f'{self.PATH}/link') is True
		await asyncio.to_thread(test)

	async def test_islink(self):
		def test():
			with grpc.insecure_channel(f'unix://{self.PREFIX}.sock') as c:
				assert Path(c).islink(f'{self.PATH}/directory') is False
				assert Path(c).islink(f'{self.PATH}/file') is False
				assert Path(c).islink(f'{self.PATH}/link') is True
		await asyncio.to_thread(test)

	async def test_exists(self):
		def test():
			with grpc.insecure_channel(f'unix://{self.PREFIX}.sock') as c:
				assert Path(c).exists(f'{self.PATH}/file') is True
				assert Path(c).exists(f'{self.PATH}/not-exist') is False
		await asyncio.to_thread(test)
