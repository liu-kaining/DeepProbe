# 发布指南 - Publishing Guide

## 发布到 PyPI

### 1. 准备工作

#### 1.1 更新版本号

编辑 `pyproject.toml` 中的版本号：

```toml
[project]
version = "0.1.0"  # 更新为新的版本号，如 "0.1.1"
```

遵循 [语义化版本](https://semver.org/)：
- `MAJOR.MINOR.PATCH`
- `0.1.0` → `0.1.1` (补丁更新)
- `0.1.0` → `0.2.0` (功能更新)
- `0.1.0` → `1.0.0` (重大更新)

#### 1.2 更新作者信息

已在 `pyproject.toml` 中配置：
```toml
authors = [
    { name = "liukaining", email = "" }
]
```

如需添加邮箱，修改为：
```toml
authors = [
    { name = "liukaining", email = "your-email@example.com" }
]
```

#### 1.3 检查项目信息

确保以下信息正确：
- ✅ 项目名称：`deep-probe`
- ✅ 描述：清晰准确
- ✅ README.md：完整且格式正确
- ✅ LICENSE：Apache-2.0
- ✅ 依赖：所有必需依赖已列出

### 2. 构建分发包

#### 2.1 安装构建工具

```bash
pip install build twine
```

#### 2.2 清理旧构建

```bash
rm -rf dist/ build/ *.egg-info
```

#### 2.3 构建分发包

```bash
python -m build
```

这会生成：
- `dist/deep-probe-0.1.0.tar.gz` (源码包)
- `dist/deep_probe-0.1.0-py3-none-any.whl` (wheel 包)

### 3. 检查构建结果

#### 3.1 检查包内容

```bash
python -m twine check dist/*
```

#### 3.2 测试安装（可选）

在干净环境中测试：

```bash
# 创建测试环境
python -m venv test_env
source test_env/bin/activate  # Linux/Mac
# 或 test_env\Scripts\activate  # Windows

# 安装构建的包
pip install dist/deep_probe-*.whl

# 测试导入
python -c "from deep_probe import DeepProbe; print('OK')"
```

### 4. 发布到 PyPI

#### 4.1 创建 PyPI 账户

1. 访问 https://pypi.org/account/register/
2. 注册账户
3. 验证邮箱

#### 4.2 获取 API Token（推荐）

1. 登录 PyPI
2. 访问 https://pypi.org/manage/account/
3. 滚动到 "API tokens"
4. 创建新 token（scope: 整个账户或特定项目）
5. 复制 token（只显示一次，妥善保存）

#### 4.3 配置认证

**方式 1：使用 API Token（推荐）**

创建 `~/.pypirc`：

```ini
[pypi]
username = __token__
password = pypi-你的token-here
```

**方式 2：使用用户名密码**

```ini
[pypi]
username = your-username
password = your-password
```

#### 4.4 发布到 TestPyPI（推荐先测试）

```bash
# 发布到测试环境
python -m twine upload --repository testpypi dist/*

# 测试安装
pip install --index-url https://test.pypi.org/simple/ deep-probe
```

#### 4.5 发布到正式 PyPI

```bash
# 发布到正式环境
python -m twine upload dist/*
```

### 5. 验证发布

#### 5.1 检查 PyPI 页面

访问：https://pypi.org/project/deep-probe/

#### 5.2 测试安装

```bash
# 等待几分钟让 PyPI 索引更新
pip install deep-probe

# 验证安装
python -c "from deep_probe import DeepProbe; print(DeepProbe.__module__)"
deep-probe --version
```

### 6. 发布后操作

#### 6.1 创建 Git Tag

```bash
git tag -a v0.1.0 -m "Release version 0.1.0"
git push origin v0.1.0
```

#### 6.2 创建 GitHub Release（如果使用 GitHub）

1. 访问 GitHub 仓库
2. 点击 "Releases" → "Create a new release"
3. 选择 tag：`v0.1.0`
4. 填写发布说明
5. 发布

#### 6.3 更新文档

- 更新 README.md 中的安装说明
- 更新 CHANGELOG.md（如果有）
- 更新版本号

## 发布检查清单

### 发布前检查

- [ ] 版本号已更新
- [ ] 作者信息正确
- [ ] README.md 完整且格式正确
- [ ] 所有测试通过：`pytest`
- [ ] 代码检查通过：`ruff check .`
- [ ] 类型检查通过：`mypy src/`
- [ ] LICENSE 文件存在
- [ ] `.env` 文件已添加到 `.gitignore`
- [ ] 没有敏感信息（API keys 等）

### 构建检查

- [ ] `python -m build` 成功
- [ ] `python -m twine check dist/*` 通过
- [ ] 包大小合理（< 100MB）

### 发布检查

- [ ] TestPyPI 测试安装成功
- [ ] PyPI 页面显示正确
- [ ] 可以正常安装：`pip install deep-probe`
- [ ] CLI 命令可用：`deep-probe --version`

## 常见问题

### Q: 如何更新已发布的版本？

A: 更新版本号后重新构建和发布：

```bash
# 1. 更新 pyproject.toml 中的版本号
# 2. 构建
python -m build
# 3. 发布
python -m twine upload dist/*
```

### Q: 可以删除已发布的版本吗？

A: PyPI 不允许删除已发布的版本，但可以标记为"隐藏"（yanked）：

```bash
python -m twine upload --skip-existing --repository-url https://pypi.org/legacy/ dist/*
# 然后在 PyPI 网站上标记为 yanked
```

### Q: 如何添加项目 URL？

A: 在 `pyproject.toml` 中添加：

```toml
[project.urls]
Homepage = "https://github.com/yourusername/deep-probe"
Documentation = "https://github.com/yourusername/deep-probe#readme"
Repository = "https://github.com/yourusername/deep-probe"
Issues = "https://github.com/yourusername/deep-probe/issues"
```

### Q: 需要添加 classifiers 吗？

A: 已有基本 classifiers，可以添加更多：

```toml
classifiers = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: Apache Software License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Topic :: Scientific/Engineering :: Artificial Intelligence",
    "Topic :: Software Development :: Libraries :: Python Modules",
]
```

## 自动化发布（可选）

可以使用 GitHub Actions 自动化发布流程。创建 `.github/workflows/publish.yml`：

```yaml
name: Publish to PyPI

on:
  release:
    types: [created]

jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      - name: Install build tools
        run: pip install build twine
      - name: Build package
        run: python -m build
      - name: Publish to PyPI
        env:
          TWINE_USERNAME: __token__
          TWINE_PASSWORD: ${{ secrets.PYPI_API_TOKEN }}
        run: twine upload dist/*
```

## 参考资源

- [Python Packaging User Guide](https://packaging.python.org/)
- [PyPI 文档](https://pypi.org/help/)
- [Twine 文档](https://twine.readthedocs.io/)
- [语义化版本](https://semver.org/)
