#!/bin/bash
# PyPI 发布脚本
# 使用方法：
#   1. 设置环境变量：export PYPI_TOKEN="pypi-你的token"
#   2. 运行：./publish.sh

set -e

echo "🚀 开始发布 deep-probe 到 PyPI..."

# 检查 token
if [ -z "$PYPI_TOKEN" ]; then
    echo "❌ 错误: 请设置 PYPI_TOKEN 环境变量"
    echo "   例如: export PYPI_TOKEN='pypi-你的token'"
    exit 1
fi

# 设置认证
export TWINE_USERNAME="__token__"
export TWINE_PASSWORD="$PYPI_TOKEN"

# 检查构建文件
if [ ! -d "dist" ] || [ -z "$(ls -A dist/*.whl dist/*.tar.gz 2>/dev/null)" ]; then
    echo "📦 构建分发包..."
    python -m build
fi

# 检查包
echo "✅ 检查构建结果..."
python -m twine check dist/*

# 发布到 PyPI
echo "📤 上传到 PyPI..."
# Get the latest version from pyproject.toml to upload only new version
LATEST_VERSION=$(grep -E "^version = " pyproject.toml | sed 's/version = "\(.*\)"/\1/')
if [ -n "$LATEST_VERSION" ]; then
    echo "📦 Uploading version $LATEST_VERSION only..."
    python -m twine upload --skip-existing dist/deep_probe-${LATEST_VERSION}*
else
    echo "⚠️  Could not detect version, uploading all files with --skip-existing..."
    python -m twine upload --skip-existing dist/*
fi

echo "✅ 发布完成！"
echo "📝 访问: https://pypi.org/project/deep-probe/"
echo ""
echo "💡 测试安装: pip install deep-probe"