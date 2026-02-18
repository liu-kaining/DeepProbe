# DeepProbe 开发文档

> Research anything, deeply, in one line of code.

## 目录

- [项目概述](#项目概述)
- [快速开始](#快速开始)
- [项目结构](#项目结构)
- [依赖管理](#依赖管理)
- [开发环境设置](#开发环境设置)
- [运行测试](#运行测试)
- [API 参考](#api-参考)
- [贡献指南](#贡献指南)

## 项目概述

**DeepProbe** 是一个 Python 库，用于封装 Google Gemini Deep Research API，提供简洁的 API 和自动重连功能。

### 核心特性

- **简洁 API**: 一行代码运行深度研究
- **自动重连**: 网络错误自动恢复，支持断点续传
- **结构化输出**: Pydantic 模型，类型安全
- **同步/异步**: 支持同步和异步接口
- **流式输出**: 实时输出和思考过程
- **CLI 工具**: Rich 美化的命令行界面

### 技术栈

- Python >= 3.9
- Google GenAI SDK (google-genai)
- Pydantic (数据模型)
- Rich (CLI 美化)
- Typer (CLI 框架)

## 快速开始

### 安装

```bash
pip install deep-probe
```

### 配置 API 密钥

```bash
export GEMINI_API_KEY='your-api-key'
```

或创建 `.env` 文件：

```env
GEMINI_API_KEY=your-api-key
```

获取 API 密钥: https://aistudio.google.com/apikey

### 基本使用

```python
from deep_probe import DeepProbe

probe = DeepProbe()
result = probe.research("What is quantum computing?")
print(result.report)
result.save("report.md")
```

## 项目结构

```
DeepProbe/
├── src/deep_probe/          # 核心源代码
│   ├── __init__.py         # 包入口
│   ├── core.py             # DeepProbe 核心客户端
│   ├── models.py           # Pydantic 数据模型
│   ├── exceptions.py        # 自定义异常
│   ├── cli.py              # 命令行接口
│   ├── utils.py            # 工具函数
│   └── _reconnect.py       # 自动重连管理
├── tests/                  # 测试文件
│   ├── conftest.py         # pytest 配置
│   ├── test_core.py        # 核心功能测试
│   ├── test_models.py      # 数据模型测试
│   ├── test_cli.py         # CLI 测试
│   └── test_integration.py # 集成测试（包含 API 调用）
├── examples/               # 使用示例
│   ├── basic_usage.py     # 基础用法
│   └── async_usage.py     # 异步用法
├── spec/                   # 项目规范
│   └── init_prompt.md      # 初始需求文档
├── pyproject.toml         # 项目配置
└── README.md              # 项目说明
```

## 依赖管理

### 必需依赖

在 `pyproject.toml` 中定义：

```toml
[project]
dependencies = [
    "google-genai>=0.3.0",
    "pydantic>=2.0.0",
    "rich>=13.0.0",
    "typer>=0.9.0",
    "python-dotenv>=1.0.0",
]
```

用户安装时会自动安装这些依赖。

### 开发依赖

```toml
[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-asyncio>=0.21.0",
    "pytest-cov>=4.0.0",
    "mypy>=1.0.0",
    "ruff>=0.1.0",
]
```

安装开发依赖：

```bash
pip install -e ".[dev]"
```

### 添加新依赖

1. 编辑 `pyproject.toml`
2. 添加依赖到 `dependencies` 或 `[project.optional-dependencies].dev`
3. 使用版本约束：`>=1.0.0` 或 `>=1.0.0,<2.0.0`

## 开发环境设置

### 1. 克隆仓库

```bash
git clone https://github.com/yourusername/DeepProbe.git
cd DeepProbe
```

### 2. 创建虚拟环境

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows
```

### 3. 安装依赖

```bash
# 安装项目（开发模式）
pip install -e ".[dev]"

# 或仅安装必需依赖
pip install -e .
```

### 4. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 填入你的 GEMINI_API_KEY
```

## 运行测试

### 单元测试（Mock）

```bash
# 运行所有测试
pytest

# 运行特定测试文件
pytest tests/test_core.py

# 带覆盖率
pytest --cov=src/deep_probe --cov-report=html
```

### 集成测试（实际 API 调用）

```bash
# 运行集成测试（需要 API 密钥）
python tests/test_integration.py
```

**注意**: 集成测试会进行实际的 API 调用，可能需要几分钟时间。

### 代码质量检查

```bash
# Linting
ruff check .

# 格式化
ruff format .

# 类型检查
mypy src/
```

## API 参考

### DeepProbe

主要客户端类。

```python
from deep_probe import DeepProbe

probe = DeepProbe(
    api_key="optional",      # 可选，默认从环境变量读取
    thinking_summaries=True # 是否启用思考摘要
)
```

#### 方法

- `research(topic, on_thought=None)` - 同步研究
- `research_async(topic, on_thought=None)` - 异步研究
- `research_stream(topic, on_text=None, on_thought=None)` - 流式研究
- `resume(interaction_id)` - 恢复中断的研究
- `resume_async(interaction_id)` - 异步恢复

### ResearchResult

研究结果对象。

```python
result.report          # str - Markdown 报告
result.sources         # list[Citation] - 引用来源
result.thoughts         # list[Thought] - 思考过程
result.cost_usage      # TokenUsage - Token 统计
result.interaction_id  # str - 交互 ID（用于恢复）
result.status          # ResearchStatus - 状态

result.save("file.md") # 保存报告到文件
```

### 异常

```python
from deep_probe.exceptions import (
    DeepProbeError,      # 基础异常
    ProbeAuthError,      # API 密钥错误
    ProbeNetworkError,   # 网络错误（包含 interaction_id）
    ProbeTimeoutError,   # 超时错误
    ProbeAPIError,       # API 服务器错误
    ProbeCancelledError, # 用户取消
)
```

## 贡献指南

### 开发流程

1. Fork 仓库
2. 创建功能分支: `git checkout -b feature/amazing-feature`
3. 提交更改: `git commit -m 'Add amazing feature'`
4. 推送分支: `git push origin feature/amazing-feature`
5. 创建 Pull Request

### 代码规范

- 使用 `ruff` 进行代码检查和格式化
- 使用 `mypy` 进行类型检查
- 遵循 PEP 8 代码风格
- 添加类型注解
- 编写文档字符串

### 测试要求

- 新功能必须包含测试
- 测试覆盖率应保持在 80% 以上
- 运行 `pytest` 确保所有测试通过

### 提交信息

使用清晰的提交信息：

```
feat: 添加新功能
fix: 修复 bug
docs: 更新文档
test: 添加测试
refactor: 代码重构
```

## 常见问题

### Q: 如何恢复中断的研究？

A: 使用 `interaction_id`：

```python
result = probe.resume("interaction-id-here")
```

网络错误会自动包含 `interaction_id`。

### Q: 研究需要多长时间？

A: Deep Research API 通常需要 2-10 分钟，复杂主题可能需要更长时间（最多 60 分钟）。

### Q: 如何查看研究过程？

A: 使用 `on_thought` 回调或 `--verbose` 标志：

```python
def on_thought(thought):
    print(f"💭 {thought}")

result = probe.research("topic", on_thought=on_thought)
```

### Q: 支持并发研究吗？

A: 是的，使用异步接口：

```python
results = await asyncio.gather(
    probe.research_async("topic1"),
    probe.research_async("topic2"),
)
```

## 许可证

Apache License 2.0

## 相关资源

- [项目 README](README.md)
- [Google AI Studio](https://aistudio.google.com/apikey)
- [Google Gemini API 文档](https://ai.google.dev/docs)
