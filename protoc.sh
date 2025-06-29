#!/bin/sh

{
	cd "$(dirname "$(readlink -f "$0")")";
	python -m grpc_tools.protoc \
		-I proto \
		--python_out=. \
		--pyi_out=. \
		--grpc_python_out=. \
		proto/fsh/*.proto
}
