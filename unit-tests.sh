#!/bin/sh

{
	cd "$(dirname "$(readlink -f "$0")")";
	rm coverage/ -rf;
	PYTHONPATH=fsh/:tests/ pytest \
		--cov-report html:coverage/ \
		--cov=fsh.wrapper \
		--cov=fsh.daemon.server \
		./tests/
}
