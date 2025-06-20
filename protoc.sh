#!/bin/sh

python -m grpc_tools.protoc \
-I. \
--python_out=fsh/ --pyi_out=fsh/ --grpc_python_out=fsh/ \
fsh.proto
