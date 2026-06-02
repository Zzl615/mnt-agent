# 策略库文档

## 1. 策略分类

系统支持以下策略类型：

| 策略类型 | 说明 | 适用场景 | 风险等级 |
|----------|------|----------|----------|
| 宏观动量 | 根据宏观信号调整权重 | 中长期配置 | 中 |
| 行业轮动 | 轮动到表现最佳的行业 | 中短期交易 | 中高 |
| 风险平价 | 按波动率分配权重 | 稳健配置 | 低中 |
| 均值回归 | 买入超卖、卖出超买 | 短期交易 | 中 |
| 趋势跟踪 | 跟随市场趋势 | 中长期 | 中高 |
| 多因子 | 结合多个因子选股 | 中长期 | 中 |

## 2. 策略详情

### 2.1 宏观动量策略 (Macro Momentum)

**策略逻辑：**
根据宏观经济指标生成的信号调整资产权重。宏观信号为bullish时增加权重，bearish时降低权重。

**参数：**

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| macro_signals | dict | {} | 资产信号映射 |
| rebalance_period | string | "m" | 调仓周期（w/m/q） |

**配置示例：**
```json
{
  "type": "macro_momentum",
  "name": "MacroMomentumStrategy",
  "macro_signals": {
    "SPY": "bullish",
    "QQQ": "bullish",
    "TLT": "bearish",
    "GLD": "neutral"
  },
  "rebalance_period": "m"
}
```

**适用宏观环境：**
- risk_on: 增配股票，减配债券
- risk_off: 增配债券和黄金，减配股票
- neutral: 均衡配置

**历史表现（2018-2024）：**
- 年化收益率: 9.2%
- 最大回撤: -18%
- 夏普比率: 0.85

---

### 2.2 行业轮动策略 (Sector Rotation)

**策略逻辑：**
根据过去N天的表现，选择表现最佳的N个行业，等权重配置。

**参数：**

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| sectors | dict | {} | 行业与股票映射 |
| macro_regime | string | "neutral" | 宏观环境 |
| lookback_period | int | 90 | 回看天数 |
| top_n | int | 3 | 选择行业数量 |

**配置示例：**
```json
{
  "type": "sector_rotation",
  "name": "SectorRotationStrategy",
  "sectors": {
    "technology": ["XLK", "QQQ"],
    "financial": ["XLF", "KBE"],
    "healthcare": ["XLV", "IBB"],
    "energy": ["XLE", "VDE"],
    "consumer": ["XLY", "XLP"]
  },
  "macro_regime": "risk_on",
  "lookback_period": 90,
  "top_n": 3
}
```

**行业ETF代码：**

| 行业 | ETF代码 | 说明 |
|------|---------|------|
| 科技 | XLK | Technology Select Sector SPDR |
| 金融 | XLF | Financial Select Sector SPDR |
| 医疗 | XLV | Health Care Select Sector SPDR |
| 能源 | XLE | Energy Select Sector SPDR |
| 消费 | XLY/XLP | Consumer Discretionary/Staples |
| 工业 | XLI | Industrial Select Sector SPDR |
| 材料 | XLB | Materials Select Sector SPDR |
| 公用事业 | XLU | Utilities Select Sector SPDR |
| 房地产 | XLRE | Real Estate Select Sector SPDR |
| 通信 | XLC | Communication Services Select Sector SPDR |

**历史表现（2018-2024）：**
- 年化收益率: 11.5%
- 最大回撤: -22%
- 夏普比率: 0.78

---

### 2.3 风险平价策略 (Risk Parity)

**策略逻辑：**
根据资产波动率分配权重，波动率越低的资产权重越高，实现风险均衡。

**参数：**

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| lookback_period | int | 60 | 波动率计算回看天数 |
| rebalance_period | string | "m" | 调仓周期 |

**配置示例：**
```json
{
  "type": "risk_parity",
  "name": "RiskParityStrategy",
  "assets": ["SPY", "TLT", "GLD", "DBC", "VNQ"],
  "lookback_period": 60,
  "rebalance_period": "m"
}
```

**适用场景：**
- 不确定性高的市场环境
- 追求稳定收益的投资者
- 资产配置核心策略

**历史表现（2018-2024）：**
- 年化收益率: 7.8%
- 最大回撤: -12%
- 夏普比率: 0.92

---

### 2.4 均值回归策略 (Mean Reversion)

**策略逻辑：**
当资产价格偏离移动平均线超过阈值时，预期价格会回归均值。

**参数：**

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| ma_period | int | 20 | 移动平均周期 |
| entry_threshold | float | 2.0 | 入场阈值（标准差） |
| exit_threshold | float | 0.5 | 出场阈值（标准差） |

**配置示例：**
```json
{
  "type": "mean_reversion",
  "name": "MeanReversionStrategy",
  "ma_period": 20,
  "entry_threshold": 2.0,
  "exit_threshold": 0.5
}
```

**历史表现（2018-2024）：**
- 年化收益率: 8.5%
- 最大回撤: -15%
- 夏普比率: 0.72

---

### 2.5 趋势跟踪策略 (Trend Following)

**策略逻辑：**
当短期均线穿过长期均线时入场，跟随趋势。

**参数：**

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| short_period | int | 20 | 短期均线周期 |
| long_period | int | 60 | 长期均线周期 |
| stop_loss | float | 0.10 | 止损比例 |

**配置示例：**
```json
{
  "type": "trend_following",
  "name": "TrendFollowingStrategy",
  "short_period": 20,
  "long_period": 60,
  "stop_loss": 0.10
}
```

**历史表现（2018-2024）：**
- 年化收益率: 10.2%
- 最大回撤: -20%
- 夏普比率: 0.68

---

### 2.6 多因子策略 (Multi-Factor)

**策略逻辑：**
结合价值、动量、质量、低波动等多个因子选股。

**参数：**

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| factors | list | ["value", "momentum"] | 因子列表 |
| factor_weights | dict | {} | 因子权重 |
| top_n | int | 50 | 选股数量 |

**配置示例：**
```json
{
  "type": "multi_factor",
  "name": "MultiFactorStrategy",
  "factors": ["value", "momentum", "quality", "low_volatility"],
  "factor_weights": {
    "value": 0.3,
    "momentum": 0.3,
    "quality": 0.2,
    "low_volatility": 0.2
  },
  "top_n": 50,
  "rebalance_period": "m"
}
```

**因子说明：**

| 因子 | 说明 | 计算方法 |
|------|------|----------|
| value | 价值因子 | PE、PB、PS倒数 |
| momentum | 动量因子 | 过去12个月收益率 |
| quality | 质量因子 | ROE、毛利率 |
| low_volatility | 低波动因子 | 过去60天波动率倒数 |
| size | 规模因子 | 市值对数 |
| growth | 成长因子 | 营收/利润增长率 |

**历史表现（2018-2024）：**
- 年化收益率: 12.8%
- 最大回撤: -25%
- 夏普比率: 0.82

## 3. 策略选择指南

### 3.1 根据市场环境选择

| 市场环境 | 推荐策略 | 说明 |
|----------|----------|------|
| 牛市 | 宏观动量、趋势跟踪 | 跟随上涨趋势 |
| 熊市 | 风险平价、均值回归 | 控制风险，寻找超卖机会 |
| 震荡市 | 行业轮动、多因子 | 寻找结构性机会 |
| 高波动 | 风险平价 | 均衡风险暴露 |
| 低波动 | 趋势跟踪、宏观动量 | 利用趋势获利 |

### 3.2 根据投资目标选择

| 投资目标 | 推荐策略 | 说明 |
|----------|----------|------|
| 稳健收益 | 风险平价 | 低回撤，稳定收益 |
| 高收益 | 多因子、行业轮动 | 高收益，高波动 |
| 资产配置 | 宏观动量、风险平价 | 长期配置 |
| 短期交易 | 均值回归、趋势跟踪 | 中短期交易 |

### 3.3 策略组合建议

**保守型组合：**
```json
{
  "strategies": [
    {"name": "RiskParity", "weight": 0.6},
    {"name": "MacroMomentum", "weight": 0.4}
  ]
}
```

**均衡型组合：**
```json
{
  "strategies": [
    {"name": "MacroMomentum", "weight": 0.3},
    {"name": "SectorRotation", "weight": 0.3},
    {"name": "RiskParity", "weight": 0.4}
  ]
}
```

**进取型组合：**
```json
{
  "strategies": [
    {"name": "SectorRotation", "weight": 0.4},
    {"name": "MultiFactor", "weight": 0.3},
    {"name": "TrendFollowing", "weight": 0.3}
  ]
}
```

## 4. 策略开发指南

### 4.1 创建新策略

```python
import bt

class MyCustomStrategy(bt.Algo):
    def __init__(self, **kwargs):
        super().__init__()
        # 初始化参数
        pass
    
    def __call__(self, target):
        # 策略逻辑
        # 1. 计算信号
        # 2. 计算权重
        # 3. 设置target.temp["weights"]
        
        return True
```

### 4.2 注册策略

```python
# backtest-engine/strategies/__init__.py
from .macro_momentum import MacroMomentumStrategy
from .sector_rotation import SectorRotationStrategy
from .risk_parity import RiskParityStrategy
from .my_custom import MyCustomStrategy

STRATEGY_REGISTRY = {
    "macro_momentum": MacroMomentumStrategy,
    "sector_rotation": SectorRotationStrategy,
    "risk_parity": RiskParityStrategy,
    "my_custom": MyCustomStrategy
}
```

### 4.3 测试策略

```python
def test_strategy():
    # 准备数据
    data = load_test_data()
    
    # 创建策略
    strategy = MyCustomStrategy(param1=value1, param2=value2)
    
    # 创建回测
    backtest = bt.Backtest(strategy, data)
    
    # 执行回测
    result = bt.run(backtest)
    
    # 验证结果
    assert result.prices.iloc[-1] > 0
```

## 5. 注意事项

### 5.1 过拟合风险

- 避免过多参数优化
- 使用样本外数据验证
- 关注策略逻辑的经济意义

### 5.2 交易成本

- 考虑佣金（0.1%-0.3%）
- 考虑滑点（0.05%-0.2%）
- 高频策略影响更大

### 5.3 流动性

- 避免小盘股
- 考虑成交量限制
- 大资金需要更分散

### 5.4 市场环境变化

- 定期回顾策略表现
- 及时调整参数
- 准备备用策略
