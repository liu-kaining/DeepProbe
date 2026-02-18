#!/bin/bash
# DeepProbe CLI 运行脚本

# 激活虚拟环境
source venv/bin/activate

# 设置 PYTHONPATH
export PYTHONPATH="$PWD/src:$PYTHONPATH"

# 运行 CLI
python -m deep_probe.cli "$@"
