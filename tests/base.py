import asyncio
import contextlib
import os
import pytest_asyncio
import shutil

from fsh.__main__ import serve


class FSHTestBase(object):
	PREFIX = '/tmp/pytest_fsh'
	PATH = '/tmp/fsh_tests'

	@pytest_asyncio.fixture(autouse=True)
	async def setup(self):
		os.mkdir(self.PATH)
		os.mkdir(f'{self.PATH}/directory')
		with open(f'{self.PATH}/file', 'wb') as f:
			f.write(b'fsh-test-123\n')
		os.symlink(f'{self.PATH}/file', f'{self.PATH}/link')
		self.server_task = asyncio.create_task(serve(self.PREFIX))
		yield
		with contextlib.suppress(asyncio.CancelledError):
			self.server_task.cancel()
		shutil.rmtree(self.PATH)
