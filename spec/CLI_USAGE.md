# CLI 使用指南

## 快速开始

### 方式 1: 使用 Python 模块（推荐，无需安装）

```bash
# 激活虚拟环境
source venv/bin/activate

# 设置 PYTHONPATH
export PYTHONPATH=$PWD/src:$PYTHONPATH

# 运行 CLI
python -m deep_probe.cli research "What is quantum computing?"
```

### 方式 2: 安装项目后使用（需要安装）

```bash
# 激活虚拟环境
source venv/bin/activate

# 安装项目（需要网络连接）
pip install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org hatchling
pip install -e .

# 使用 CLI 命令
deep-probe research "What is quantum computing?"
```

## CLI 命令示例

### 基本使用

```bash
# 基本研究
python -m deep_probe.cli research "What is quantum computing?"

# 保存到文件
python -m deep_probe.cli research "AI trends 2024" --save report.md

# 显示思考过程
python -m deep_probe.cli research "Climate change effects" --verbose

# 流式输出
python -m deep_probe.cli research "Research topic" --stream

# 安静模式（仅输出报告）
python -m deep_probe.cli research "Test topic" --quiet
```

### 恢复之前的研究

```bash
# 恢复研究（使用 interaction_id）
python -m deep_probe.cli research --resume "interaction-id-here"
```

### 查看帮助

```bash
# 查看版本
python -m deep_probe.cli --version

# 查看帮助
python -m deep_probe.cli --help

# 查看配置说明
python -m deep_probe.cli config
```

## 环境变量

确保设置了 API 密钥：

```bash
# 方式 1: 环境变量
export GEMINI_API_KEY='your-api-key'

# 方式 2: .env 文件（推荐）
# 项目根目录下的 .env 文件会自动加载
echo "GEMINI_API_KEY=your-api-key" > .env
```

## 完整示例

```bash
# 1. 激活虚拟环境
source venv/bin/activate

# 2. 设置 PYTHONPATH
export PYTHONPATH=$PWD/src:$PYTHONPATH

# 3. 运行研究（带保存）
python -m deep_probe.cli research \
  "What are the main applications of quantum computing?" \
  --save quantum_report.md \
  --verbose

# 4. 查看结果
cat quantum_report.md
```

## 故障排除

### 问题: ModuleNotFoundError

**解决方案**: 设置 PYTHONPATH
```bash
export PYTHONPATH=$PWD/src:$PYTHONPATH
```

### 问题: API 密钥错误

**解决方案**: 检查 .env 文件或环境变量
```bash
# 检查环境变量
echo $GEMINI_API_KEY

# 检查 .env 文件
cat .env
```

### 问题: 网络连接问题

**解决方案**: 使用 --trusted-host 选项安装依赖
```bash
pip install --trusted-host pypi.org \
  --trusted-host pypi.python.org \
  --trusted-host files.pythonhosted.org \
  hatchling
```

## 快捷脚本（可选）

创建一个 `deep-probe` 脚本：

```bash
#!/bin/bash
# 保存为 deep-probe（在项目根目录）

source venv/bin/activate
export PYTHONPATH=$PWD/src:$PYTHONPATH
python -m deep_probe.cli "$@"
```

然后：
```bash
chmod +x deep-probe
./deep-probe research "What is quantum computing?"
```
