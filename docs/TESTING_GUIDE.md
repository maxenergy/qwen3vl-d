# Testing Guide

AI Auto-Annotation Tool 测试完整指南

## 📖 概述

本项目采用全面的测试策略：
- ✅ **单元测试** - 独立组件测试
- ✅ **集成测试** - API 端点测试
- ✅ **覆盖率报告** - 代码覆盖率 >60%
- ✅ **CI/CD** - 自动化测试流水线
- ✅ **类型检查** - MyPy 静态类型检查
- ✅ **代码质量** - Flake8, Black, isort
- ✅ **安全检查** - Bandit, Safety

## 🏗️ 测试架构

```
tests/
├── conftest.py           # Pytest配置和fixtures
├── unit/                 # 单元测试
│   ├── __init__.py
│   └── test_config_loader.py
└── integration/          # 集成测试
    ├── __init__.py
    └── test_projects_api.py
```

## 🔧 测试环境设置

### 安装测试依赖

```bash
pip install pytest pytest-cov pytest-asyncio
```

### 配置测试环境

测试使用独立的数据库和配置：

```bash
export TESTING=true
export DATABASE_URL=sqlite:///:memory:
export REDIS_URL=redis://localhost:6379/1
export LOG_LEVEL=ERROR
```

## 🧪 运行测试

### 使用测试脚本

最简单的方式是使用提供的测试脚本：

```bash
# 运行所有测试
./scripts/run_tests.sh all

# 只运行单元测试
./scripts/run_tests.sh unit

# 只运行集成测试
./scripts/run_tests.sh integration

# 运行快速测试（不包括慢速测试）
./scripts/run_tests.sh quick

# 不生成覆盖率报告
./scripts/run_tests.sh all false
```

### 使用 Pytest 直接运行

```bash
# 运行所有测试
pytest

# 运行单元测试
pytest tests/unit/

# 运行集成测试
pytest tests/integration/

# 运行特定测试文件
pytest tests/unit/test_config_loader.py

# 运行特定测试类
pytest tests/unit/test_config_loader.py::TestDatabaseConfig

# 运行特定测试函数
pytest tests/unit/test_config_loader.py::TestDatabaseConfig::test_get_url

# 详细输出
pytest -v

# 显示print输出
pytest -s

# 失败时进入调试器
pytest --pdb

# 只运行上次失败的测试
pytest --lf

# 并行运行测试
pytest -n auto
```

### 使用测试标记

```bash
# 只运行单元测试
pytest -m unit

# 只运行集成测试
pytest -m integration

# 运行快速测试
pytest -m "not slow"

# 跳过需要 GPU 的测试
pytest -m "not requires_gpu"

# 跳过需要外部 API 的测试
pytest -m "not requires_api"
```

## 📊 测试覆盖率

### 生成覆盖率报告

```bash
# HTML 报告
pytest --cov=backend --cov=qwen3vl_d --cov-report=html

# 终端报告（显示缺失行）
pytest --cov=backend --cov=qwen3vl_d --cov-report=term-missing

# XML 报告（用于 CI）
pytest --cov=backend --cov=qwen3vl_d --cov-report=xml

# 组合多种报告
pytest --cov=backend --cov=qwen3vl_d \
       --cov-report=html \
       --cov-report=term-missing \
       --cov-report=xml
```

### 查看覆盖率

```bash
# 在浏览器中打开 HTML 报告
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

### 覆盖率要求

项目配置了最低 60% 的覆盖率要求：

```ini
# pytest.ini
addopts = --cov-fail-under=60
```

## ✍️ 编写测试

### 测试文件命名

- 单元测试: `tests/unit/test_*.py`
- 集成测试: `tests/integration/test_*.py`
- 测试类: `class Test*`
- 测试函数: `def test_*()`

### 使用 Fixtures

```python
import pytest

def test_with_client(client):
    """Use test client fixture."""
    response = client.get("/api/v1/projects")
    assert response.status_code == 200

def test_with_db(db_session):
    """Use database session fixture."""
    # db_session is a SQLAlchemy session
    pass

def test_with_sample_data(sample_project_data):
    """Use sample data fixture."""
    assert sample_project_data["name"] == "Test Project"
```

### 可用的 Fixtures

**测试基础设施**:
- `engine` - SQLAlchemy engine (session scope)
- `db_session` - Database session (function scope)
- `client` - FastAPI test client (function scope)
- `temp_dir` - Temporary directory (function scope)

**示例数据**:
- `sample_project_data` - 示例项目数据
- `sample_generation_task_data` - 示例生成任务数据
- `sample_annotation_task_data` - 示例标注任务数据
- `sample_dataset_data` - 示例数据集数据
- `sample_training_task_data` - 示例训练任务数据
- `sample_image` - 示例图片文件

### 测试示例

#### 单元测试示例

```python
import pytest
from backend.core.config_loader import DatabaseConfig

class TestDatabaseConfig:
    """Test database configuration."""

    def test_get_url(self):
        """Test URL generation."""
        config = DatabaseConfig(
            host="localhost",
            port=5432,
            user="testuser",
            password="testpass",
            database="testdb"
        )

        expected = "postgresql://testuser:testpass@localhost:5432/testdb"
        assert config.get_url() == expected

    def test_defaults(self):
        """Test default values."""
        config = DatabaseConfig()

        assert config.host == "localhost"
        assert config.port == 5432
```

#### 集成测试示例

```python
import pytest
from fastapi.testclient import TestClient

class TestProjectsAPI:
    """Test projects API."""

    def test_create_project(self, client: TestClient):
        """Test creating a project."""
        data = {
            "name": "Test Project",
            "description": "A test project"
        }

        response = client.post("/api/v1/projects", json=data)

        assert response.status_code == 200
        result = response.json()
        assert result["name"] == "Test Project"
        assert "id" in result

    def test_get_project(self, client: TestClient):
        """Test getting a project."""
        # Create project first
        create_response = client.post("/api/v1/projects", json={
            "name": "Test Project"
        })
        project_id = create_response.json()["id"]

        # Get project
        response = client.get(f"/api/v1/projects/{project_id}")

        assert response.status_code == 200
        result = response.json()
        assert result["id"] == project_id
```

#### 异步测试示例

```python
import pytest

@pytest.mark.asyncio
async def test_async_function():
    """Test async function."""
    result = await some_async_function()
    assert result is not None
```

### 使用测试标记

```python
import pytest

@pytest.mark.unit
def test_unit():
    """Unit test."""
    pass

@pytest.mark.integration
def test_integration():
    """Integration test."""
    pass

@pytest.mark.slow
def test_slow():
    """Slow test."""
    pass

@pytest.mark.requires_gpu
def test_gpu():
    """Test requiring GPU."""
    pass

@pytest.mark.requires_api
def test_external_api():
    """Test requiring external API."""
    pass

@pytest.mark.smoke
def test_critical_feature():
    """Smoke test for critical feature."""
    pass
```

## 🚀 CI/CD 集成

### GitHub Actions

项目包含完整的 GitHub Actions 工作流：

**`.github/workflows/tests.yml`**:
- 在 Python 3.10, 3.11, 3.12 上运行测试
- PostgreSQL 和 Redis 服务
- 单元测试和集成测试
- 代码覆盖率上传到 Codecov
- Lint 检查 (black, isort, flake8)
- 安全检查 (bandit, safety)

### 触发条件

- Push to `main` or `develop` branches
- Pull requests to `main` or `develop`

### 查看测试结果

1. 在 GitHub 仓库的 **Actions** 标签查看
2. 每次提交会显示测试状态 ✅ 或 ❌
3. 点击查看详细日志和覆盖率报告

## 📋 测试清单

### 添加新功能时

- [ ] 编写单元测试
- [ ] 编写集成测试（如果涉及 API）
- [ ] 确保测试覆盖率 ≥60%
- [ ] 运行所有测试确保通过
- [ ] 检查代码格式 (`black .`)
- [ ] 检查导入顺序 (`isort .`)
- [ ] 运行 lint (`flake8 .`)

### 修复 Bug 时

- [ ] 编写复现 bug 的测试（应该失败）
- [ ] 修复 bug
- [ ] 确保测试现在通过
- [ ] 运行所有测试确保没有破坏其他功能

### 提交 PR 前

- [ ] 所有测试通过
- [ ] 覆盖率没有下降
- [ ] Lint 检查通过
- [ ] 文档已更新

## 🛠️ 调试测试

### 使用 pdb

```bash
# 失败时自动进入调试器
pytest --pdb

# 开始时就进入调试器
pytest --trace
```

### 查看详细输出

```bash
# 显示 print 输出
pytest -s

# 详细模式
pytest -v

# 最详细模式
pytest -vv
```

### 只运行失败的测试

```bash
# 只运行上次失败的测试
pytest --lf

# 先运行失败的测试，然后运行其他测试
pytest --ff
```

## 📈 代码质量工具

### Black (代码格式化)

```bash
# 检查格式
black --check backend/ qwen3vl_d/ tests/

# 自动格式化
black backend/ qwen3vl_d/ tests/
```

### isort (导入排序)

```bash
# 检查导入
isort --check-only backend/ qwen3vl_d/ tests/

# 自动排序
isort backend/ qwen3vl_d/ tests/
```

### Flake8 (Lint)

```bash
# 运行 lint
flake8 backend/ qwen3vl_d/ tests/ --max-line-length=127

# 只检查严重错误
flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
```

### Bandit (安全检查)

```bash
# 检查安全问题
bandit -r backend/ qwen3vl_d/

# 高严重性问题
bandit -r backend/ qwen3vl_d/ -ll
```

### Safety (依赖安全)

```bash
# 检查依赖漏洞
safety check
```

## 🆘 故障排查

### 测试失败但代码正确

**可能原因**:
- 测试隔离问题（数据库状态）
- 环境变量未设置
- 依赖版本不匹配

**解决方案**:
```bash
# 清理并重新运行
pytest --cache-clear

# 使用新的数据库会话
pytest -v --force-sugar
```

### 覆盖率不准确

**解决方案**:
```bash
# 清除旧的覆盖率数据
coverage erase

# 重新运行测试
pytest --cov=backend --cov=qwen3vl_d --cov-report=html
```

### Import 错误

**解决方案**:
```bash
# 确保项目根目录在 PYTHONPATH
export PYTHONPATH=$PWD:$PYTHONPATH

# 或使用开发模式安装
pip install -e .
```

## 📚 最佳实践

### 1. 测试命名

- 清晰描述测试的功能
- 使用 `test_` 前缀
- 包含预期行为

```python
# ✓ Good
def test_create_project_returns_201_with_valid_data():
    pass

# ✗ Bad
def test_project():
    pass
```

### 2. 一个测试一个断言

```python
# ✓ Good
def test_project_name():
    assert project.name == "Test"

def test_project_description():
    assert project.description == "Desc"

# ✗ Bad
def test_project():
    assert project.name == "Test"
    assert project.description == "Desc"
    assert project.status == "active"
```

### 3. 使用 Fixtures

```python
# ✓ Good
def test_with_fixture(sample_project_data):
    # Use fixture data
    pass

# ✗ Bad
def test_without_fixture():
    data = {"name": "Test", ...}  # Duplicate data
    pass
```

### 4. 测试隔离

- 每个测试独立
- 不依赖测试顺序
- 清理测试数据

### 5. 快速测试

- 单元测试应该非常快（< 1秒）
- 使用 mock 避免外部依赖
- 标记慢速测试

## 📖 参考资源

- [Pytest Documentation](https://docs.pytest.org/)
- [Coverage.py](https://coverage.readthedocs.io/)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [GitHub Actions](https://docs.github.com/en/actions)
