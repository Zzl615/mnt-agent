# 开发指南

## 1. 开发环境设置

### 1.1 克隆仓库

```bash
git clone https://github.com/your-org/macro-invest-agent.git
cd macro-invest-agent
```

### 1.2 创建虚拟环境

```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
```

### 1.3 安装开发依赖

```bash
pip install -e ".[dev]"
```

**开发依赖包括：**
```
pytest>=7.0.0
pytest-cov>=4.0.0
black>=23.0.0
ruff>=0.1.0
mypy>=1.0.0
pre-commit>=3.0.0
```

### 1.4 配置pre-commit

```bash
pre-commit install
```

**.pre-commit-config.yaml:**
```yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files

  - repo: https://github.com/psf/black
    rev: 23.12.1
    hooks:
      - id: black

  - repo: https://github.com/astral-sh/ruff
    rev: v0.1.8
    hooks:
      - id: ruff
        args: [--fix]

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.8.0
    hooks:
      - id: mypy
```

## 2. 代码规范

### 2.1 Python风格指南

遵循PEP 8规范，使用black格式化。

```bash
# 格式化代码
black .

# 检查代码风格
ruff check .

# 类型检查
mypy .
```

### 2.2 命名规范

| 类型 | 规范 | 示例 |
|------|------|------|
| 模块 | snake_case | `macro_research.py` |
| 类 | PascalCase | `MacroResearchWorkflow` |
| 函数 | snake_case | `run_research()` |
| 常量 | UPPER_SNAKE_CASE | `MAX_RETRIES` |
| 变量 | snake_case | `macro_data` |

### 2.3 文档字符串

使用Google风格文档字符串：

```python
def calculate_sharpe_ratio(
    prices: pd.Series,
    risk_free_rate: float = 0.02
) -> float:
    """计算夏普比率
    
    Args:
        prices: 价格序列
        risk_free_rate: 无风险利率
        
    Returns:
        夏普比率
        
    Raises:
        ValueError: 当价格数据为空时
    """
    pass
```

## 3. 项目结构

```
macro-invest-agent/
├── mcp-servers/              # MCP服务器
│   ├── macro-data-server/
│   │   ├── server.py
│   │   └── tests/
│   └── market-data-server/
│       ├── server.py
│       └── tests/
├── agent-core/               # Agent核心
│   ├── workflows/
│   │   ├── macro_research.py
│   │   ├── strategy_builder.py
│   │   └── backtest_runner.py
│   ├── memory/
│   └── tests/
├── backtest-engine/          # 回测引擎
│   ├── strategies/
│   ├── metrics/
│   └── tests/
├── config/                   # 配置文件
├── scripts/                  # 脚本
├── docs/                     # 文档
├── tests/                    # 集成测试
└── output/                   # 输出目录
```

## 4. 扩展开发

### 4.1 添加新的MCP工具

**步骤1：** 在MCP服务器中添加工具定义

```python
# mcp-servers/macro-data-server/server.py

@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        # ... 现有工具
        Tool(
            name="get_new_indicator",
            description="获取新指标",
            inputSchema={
                "type": "object",
                "properties": {
                    "param1": {"type": "string"}
                },
                "required": ["param1"]
            }
        )
    ]
```

**步骤2：** 实现工具逻辑

```python
@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    if name == "get_new_indicator":
        result = _fetch_new_indicator(arguments["param1"])
        return [TextContent(type="text", text=result.to_json())]
```

**步骤3：** 添加测试

```python
# mcp-servers/macro-data-server/tests/test_server.py

def test_get_new_indicator():
    result = _fetch_new_indicator("test")
    assert not result.empty
```

### 4.2 添加新的策略

**步骤1：** 创建策略文件

```python
# backtest-engine/strategies/my_strategy.py
import bt
from typing import Dict

class MyStrategy(bt.Algo):
    """我的自定义策略"""
    
    def __init__(self, **kwargs):
        super().__init__()
        self.param1 = kwargs.get("param1", "default")
    
    def __call__(self, target):
        # 策略逻辑
        weights = self._calculate_weights(target)
        target.temp["weights"] = weights
        return True
    
    def _calculate_weights(self, target) -> Dict[str, float]:
        # 计算权重
        pass
```

**步骤2：** 注册策略

```python
# backtest-engine/strategies/__init__.py
from .my_strategy import MyStrategy

STRATEGY_REGISTRY["my_strategy"] = MyStrategy
```

**步骤3：** 添加测试

```python
# backtest-engine/tests/test_my_strategy.py

def test_my_strategy():
    strategy = MyStrategy(param1="value")
    # 测试逻辑
```

### 4.3 添加新的工作流

**步骤1：** 创建工作流文件

```python
# agent-core/workflows/my_workflow.py
from typing import Dict

class MyWorkflow:
    """我的自定义工作流"""
    
    def __init__(self, mcp_client):
        self.mcp_client = mcp_client
    
    async def run(self, **kwargs) -> Dict:
        # 工作流逻辑
        pass
```

**步骤2：** 在Agent中集成

```python
# agent-core/agent.py
from .workflows.my_workflow import MyWorkflow

class MacroInvestAgent:
    def __init__(self):
        self.my_workflow = MyWorkflow(self.mcp_client)
    
    async def run_custom_workflow(self):
        return await self.my_workflow.run()
```

## 5. 测试指南

### 5.1 单元测试

```python
# tests/unit/test_macro_research.py
import pytest
from agent_core.workflows.macro_research import MacroResearchWorkflow

@pytest.fixture
def mock_mcp_client():
    return MockMCPClient()

def test_macro_research(mock_mcp_client):
    workflow = MacroResearchWorkflow(mock_mcp_client)
    result = workflow.run_research()
    
    assert "macro_environment" in result
    assert "insights" in result
```

### 5.2 集成测试

```python
# tests/integration/test_full_cycle.py
import pytest
from scripts.run_agent import MacroInvestAgent

@pytest.mark.asyncio
async def test_full_cycle():
    agent = MacroInvestAgent()
    report = await agent.run_full_cycle()
    
    assert report is not None
    assert "MACRO ENVIRONMENT" in report
```

### 5.3 运行测试

```bash
# 运行所有测试
pytest

# 运行特定测试
pytest tests/unit/test_macro_research.py

# 生成覆盖率报告
pytest --cov=. --cov-report=html
```

## 6. 调试技巧

### 6.1 日志调试

```python
import logging

logger = logging.getLogger(__name__)

def my_function():
    logger.debug("Debug message")
    logger.info("Info message")
    logger.warning("Warning message")
    logger.error("Error message")
```

### 6.2 使用调试器

```bash
# 使用pdb
python -m pdb scripts/run_agent.py

# 使用ipdb
pip install ipdb
python -m ipdb scripts/run_agent.py
```

### 6.3 性能分析

```bash
# 使用cProfile
python -m cProfile -o profile.stats scripts/run_agent.py

# 使用snakeviz查看
pip install snakeviz
snakeviz profile.stats
```

## 7. 贡献指南

### 7.1 提交Pull Request

1. Fork仓库
2. 创建特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建Pull Request

### 7.2 提交信息规范

```
<type>(<scope>): <subject>

<body>

<footer>
```

**type类型：**
- `feat`: 新功能
- `fix`: 修复bug
- `docs`: 文档更新
- `style`: 代码格式
- `refactor`: 重构
- `test`: 测试
- `chore`: 构建/工具

**示例：**
```
feat(strategy): add risk parity strategy

Add risk parity strategy that allocates weights based on volatility.

Closes #123
```

## 8. 常见问题

### 8.1 数据获取失败

**问题：** MCP工具调用返回空数据

**解决方案：**
1. 检查网络连接
2. 检查数据源API是否可用
3. 查看日志获取详细错误信息

### 8.2 回测结果异常

**问题：** 回测收益率异常高或低

**解决方案：**
1. 检查数据完整性
2. 检查策略逻辑
3. 检查交易成本设置
4. 检查是否有未来函数

### 8.3 内存溢出

**问题：** 处理大量数据时内存不足

**解决方案：**
1. 分批处理数据
2. 使用生成器
3. 增加内存限制
4. 使用更高效的数据结构
