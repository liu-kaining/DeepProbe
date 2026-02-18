### 1. 产品定位与核心价值

* **名称**: `deep-probe`
* **Slogan**: "Research anything, deeply, in one line of code."
* **设计哲学**:
* **显式优于隐式**: 默认配置即最佳配置，但允许高阶用户修改。
* **鲁棒性第一**: 网络抖动？API 超时？自动重连，绝不让用户为了 99% 的进度失败而重跑。
* **结构化输出**: 不仅仅返回一坨文本，要返回包含“思考过程”、“引用源”、“最终报告”的结构化对象。



---

### 2. 用户视角 (User Stories)

我们要实现两种极致的使用场景：

**场景 A：Python 开发者 (Library Mode)**

```python
from deep_probe import DeepProbe

# 初始化 (自动读取环境变量 GEMINI_API_KEY)
probe = DeepProbe()

# 一行代码，启动深思 (同步/异步皆可)
result = probe.research("2025年量子计算在制药领域的商业化进展")

# 拿结果
print(result.report)      # 最终 Markdown 报告
print(result.sources)     # 所有的引用链接
print(result.thoughts)    # Agent 的思考路径 (Log)

```

**场景 B：终端用户 (CLI Mode)**

```bash
# 直接在终端跑，带漂亮的进度条和实时思考日志
deep-probe "分析 DeepSeek 的技术架构创新点" --save report.md

```

---

### 3. 技术架构设计 (Architecture)

告诉 Claude Code，我们需要这样的模块划分：

```text
deep_probe/
├── __init__.py       # 暴露核心类，保持 import 路径极短
├── core.py           # 核心逻辑：DeepProbe Client，封装 API 交互
├── models.py         # 数据模型：定义 ResearchResult, ResearchEvent 等 Dataclass
├── exceptions.py     # 自定义异常：ProbeAuthError, ProbeNetworkError
├── cli.py            # 命令行入口：使用 Typer 或 Click + Rich
└── utils.py          # 工具：Markdown 处理，文件保存

```

#### 关键技术难点解决方案 (给 Claude Code 的指令)

1. **断点续连机制 (Resumable Loop)**:
* Deep Research 可能跑 10 分钟。如果网络中断，API 连接会断开。
* **方案**: 必须维护 `interaction_id`。如果 `stream` 抛出网络异常，代码必须自动捕获，并使用 `client.interactions.get(id)` 或重新建立流连接来恢复状态，而不是抛出错误给用户。


2. **双模式支持 (Sync & Async)**:
* 底层必须是 `async` 的（因为 API 是流式的）。
* 但在 `DeepProbe` 类中，要提供 `research()` (同步，内部封装 `asyncio.run`) 和 `research_async()` (异步，供 web 服务集成) 两个方法。


3. **智能超时管理**:
* Google 的 API 有时会卡在“思考”阶段。我们需要实现一个应用层的 `Keep-Alive` 检查，如果 2 分钟没有任何 `content.delta`，需要尝试刷新连接。



---

### 4. 给 Claude Code 的 Prompt (执行指令)

你可以复制下面这段话给 Claude Code，这是我作为 TD 写好的 **PRD (产品需求文档)**：

---

**Prompt Start**

我们要开发一个名为 `deep-probe` 的 Python 库。
**目标**: 封装 Google Gemini Deep Research API，提供极简的开发者体验。

**核心要求**:

1. **库结构**: 模块化设计，支持 `pip install`。
2. **依赖**: 使用 `google-genai` (最新版 SDK), `rich` (CLI 美化), `pydantic` (数据模型), `typer` (CLI 工具)。
3. **核心类 `DeepProbe**`:
* 初始化时接收 `api_key` (或读取 env)。
* 方法 `research(topic, file_path=None) -> ResearchResult`: 同步阻塞方法，返回最终结果对象。
* 方法 `research_async(...)`: 异步方法，适合集成到 FastAPI 等框架。
* **关键逻辑**: 必须实现 `stream=True` 的处理循环，并且要有 **自动重连机制**。如果流中断，利用 `interaction.id` 恢复。


4. **CLI 工具**:
* 命令 `deep-probe "TOPIC"`。
* 使用 `rich.live` 展示实时的 Agent 思考过程 (Thinking Process)。
* 支持 `--save` 参数保存 Markdown。


5. **数据模型 `ResearchResult**`:
* 属性: `markdown_content` (str), `citations` (list), `logs` (list of thoughts), `cost_usage` (token usage if available).



**代码质量要求**:

* 添加详细的 Docstrings。
* 错误处理要优雅：如果是 API Key 错误，提示用户检查 .env；如果是网络错误，自动重试 3 次后才报错。
* 输出必须是“生产级”的，不要只有简单的 print，要考虑日志分级。

请按步骤实现核心代码结构。
