# Agent工作流设计

## 1. 工作流概览

系统包含三个核心工作流，按顺序执行形成完整的投资研究周期：

```
┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐
│  Macro Research  │───▶│  Strategy Build  │───▶│  Backtest Run    │
│  Workflow        │    │  Workflow        │    │  Workflow        │
└──────────────────┘    └──────────────────┘    └──────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
   宏观环境评估              策略配置                回测结果
   投资信号                  资产权重                性能指标
   建议                      调仓规则                可视化
```

## 2. Macro Research Workflow

### 2.1 工作流目标

收集和分析宏观经济数据，评估当前宏观环境，生成投资信号和建议。

### 2.2 执行步骤

```
步骤1: 确定研究范围
  │
  ▼
步骤2: 收集宏观数据 (MCP工具调用)
  │
  ▼
步骤3: 数据清洗与标准化
  │
  ▼
步骤4: 趋势分析 (同比/环比/移动平均)
  │
  ▼
步骤5: 信号生成 (bullish/bearish/neutral)
  │
  ▼
步骤6: 宏观环境评估 (risk_on/risk_off/neutral)
  │
  ▼
步骤7: 生成投资建议
```

### 2.3 详细设计

#### 步骤1: 确定研究范围

```python
def determine_scope(query: str = None) -> dict:
    """根据用户查询确定研究范围"""
    default_scope = {
        "regions": ["china", "us"],
        "indicators": ["gdp", "cpi", "ppi", "m2", "lpr", "fed_rate", "treasury_yield"],
        "commodities": ["crude", "gold", "copper"],
        "timeframe": "1y"
    }
    
    if query:
        # 解析查询，调整研究范围
        scope = parse_query(query)
        return merge_scopes(default_scope, scope)
    
    return default_scope
```

#### 步骤2: 收集宏观数据

```python
async def collect_macro_data(scope: dict) -> dict:
    """通过MCP工具收集宏观数据"""
    data = {}
    
    # 中国宏观指标
    for indicator in scope["indicators"]:
        if indicator.startswith("china_"):
            data[indicator] = await mcp_call(
                "get_china_macro_indicator",
                {"indicator": indicator.replace("china_", "")}
            )
    
    # 美国宏观指标
    for indicator in scope["indicators"]:
        if indicator.startswith("us_"):
            data[indicator] = await mcp_call(
                "get_us_macro_indicator",
                {
                    "indicator": indicator.replace("us_", ""),
                    "period": scope["timeframe"]
                }
            )
    
    # 大宗商品
    for commodity in scope["commodities"]:
        data[f"commodity_{commodity}"] = await mcp_call(
            "get_global_commodity",
            {
                "commodity": commodity,
                "days": timeframe_to_days(scope["timeframe"])
            }
        )
    
    return data
```

#### 步骤4-5: 趋势分析与信号生成

```python
def analyze_trends(data: dict) -> list[MacroInsight]:
    """分析趋势并生成信号"""
    insights = []
    
    for indicator, df in data.items():
        if df.empty or "error" in df.columns:
            continue
        
        # 计算趋势
        trend = calculate_trend(df)
        
        # 生成信号
        signal = generate_signal(indicator, df, trend)
        
        # 计算置信度
        confidence = calculate_confidence(df, trend)
        
        insights.append(MacroInsight(
            indicator=indicator,
            current_value=get_latest_value(df),
            trend=trend,
            signal=signal,
            confidence=confidence,
            reasoning=generate_reasoning(indicator, df, trend, signal)
        ))
    
    return insights
```

#### 步骤6: 宏观环境评估

```python
def assess_macro_environment(insights: list[MacroInsight]) -> dict:
    """评估宏观环境"""
    bullish_count = sum(1 for i in insights if i.signal == "bullish")
    bearish_count = sum(1 for i in insights if i.signal == "bearish")
    total = len(insights)
    
    if total == 0:
        return {"regime": "unknown", "confidence": 0}
    
    bullish_ratio = bullish_count / total
    bearish_ratio = bearish_count / total
    
    if bullish_ratio > 0.6:
        regime = "risk_on"
        description = "宏观环境偏宽松，风险资产偏好上升"
    elif bearish_ratio > 0.6:
        regime = "risk_off"
        description = "宏观环境偏紧缩，避险情绪升温"
    else:
        regime = "neutral"
        description = "宏观环境中性，结构性机会为主"
    
    return {
        "regime": regime,
        "description": description,
        "bullish_count": bullish_count,
        "bearish_count": bearish_count,
        "neutral_count": total - bullish_count - bearish_count,
        "confidence": max(bullish_ratio, bearish_ratio)
    }
```

#### 步骤7: 生成投资建议

```python
def generate_recommendations(environment: dict, insights: list) -> list[dict]:
    """生成投资建议"""
    recommendations = []
    regime = environment["regime"]
    
    # 资产配置建议
    asset_allocation = get_asset_allocation(regime)
    recommendations.extend(asset_allocation)
    
    # 行业/板块建议
    sector_picks = get_sector_picks(insights, regime)
    recommendations.extend(sector_picks)
    
    # 风险提示
    risk_warnings = get_risk_warnings(insights)
    recommendations.extend(risk_warnings)
    
    return recommendations

def get_asset_allocation(regime: str) -> list[dict]:
    """根据宏观环境获取资产配置建议"""
    allocations = {
        "risk_on": [
            {"asset": "equity", "action": "overweight", "weight": 0.6, "rationale": "风险偏好上升"},
            {"asset": "bonds", "action": "underweight", "weight": 0.2, "rationale": "利率上行压力"},
            {"asset": "commodities", "action": "neutral", "weight": 0.15, "rationale": "经济扩张支撑"},
            {"asset": "cash", "action": "underweight", "weight": 0.05, "rationale": "降低现金持有"}
        ],
        "risk_off": [
            {"asset": "equity", "action": "underweight", "weight": 0.3, "rationale": "风险偏好下降"},
            {"asset": "bonds", "action": "overweight", "weight": 0.4, "rationale": "避险需求上升"},
            {"asset": "gold", "action": "overweight", "weight": 0.15, "rationale": "避险资产"},
            {"asset": "cash", "action": "overweight", "weight": 0.15, "rationale": "保持流动性"}
        ],
        "neutral": [
            {"asset": "equity", "action": "neutral", "weight": 0.45, "rationale": "结构性机会"},
            {"asset": "bonds", "action": "neutral", "weight": 0.3, "rationale": "均衡配置"},
            {"asset": "commodities", "action": "neutral", "weight": 0.1, "rationale": "精选品种"},
            {"asset": "cash", "action": "neutral", "weight": 0.15, "rationale": "保持灵活性"}
        ]
    }
    return allocations.get(regime, allocations["neutral"])
```

### 2.4 输出格式

```json
{
  "timestamp": "2024-01-01T00:00:00Z",
  "macro_environment": {
    "regime": "risk_on",
    "description": "宏观环境偏宽松，风险资产偏好上升",
    "confidence": 0.75
  },
  "insights": [
    {
      "indicator": "China CPI",
      "current_value": 0.7,
      "trend": "down",
      "signal": "bullish",
      "confidence": 0.8,
      "reasoning": "CPI下降，通缩风险，政策宽松预期"
    }
  ],
  "recommendations": [
    {
      "asset": "equity",
      "action": "overweight",
      "weight": 0.6,
      "rationale": "风险偏好上升"
    }
  ]
}
```

## 3. Strategy Builder Workflow

### 3.1 工作流目标

根据宏观研究结果，构建具体的投资组合策略，包括资产选择、权重分配、调仓规则。

### 3.2 执行步骤

```
步骤1: 解析宏观研究结果
  │
  ▼
步骤2: 选择目标资产
  │
  ▼
步骤3: 计算初始权重
  │
  ▼
步骤4: 应用宏观信号调整
  │
  ▼
步骤5: 确定调仓规则
  │
  ▼
步骤6: 生成策略配置
```

### 3.3 详细设计

#### 步骤2: 选择目标资产

```python
def select_assets(recommendations: list[dict], universe: list[str] = None) -> list[str]:
    """根据建议选择目标资产"""
    if universe is None:
        universe = get_default_universe()
    
    selected = []
    for rec in recommendations:
        if rec["action"] in ["overweight", "neutral"]:
            assets = map_asset_to_tickers(rec["asset"], universe)
            selected.extend(assets)
    
    return list(set(selected))

def map_asset_to_tickers(asset_class: str, universe: list[str]) -> list[str]:
    """将资产类别映射到具体标的"""
    mapping = {
        "equity": ["SPY", "QQQ", "IWM"],
        "bonds": ["TLT", "IEF", "SHY"],
        "commodities": ["GLD", "USO", "DBA"],
        "gold": ["GLD"],
        "cash": ["BIL"]
    }
    return mapping.get(asset_class, [])
```

#### 步骤3-4: 权重计算与调整

```python
def calculate_weights(
    assets: list[str],
    recommendations: list[dict],
    environment: dict
) -> dict[str, float]:
    """计算资产权重"""
    # 基础权重：等权重
    base_weight = 1.0 / len(assets)
    weights = {asset: base_weight for asset in assets}
    
    # 根据宏观信号调整
    for rec in recommendations:
        asset_tickers = map_asset_to_tickers(rec["asset"], assets)
        adjustment = get_adjustment_factor(rec["action"])
        
        for ticker in asset_tickers:
            if ticker in weights:
                weights[ticker] *= adjustment
    
    # 归一化
    total = sum(weights.values())
    if total > 0:
        weights = {k: v/total for k, v in weights.items()}
    
    return weights

def get_adjustment_factor(action: str) -> float:
    """获取调整因子"""
    factors = {
        "overweight": 1.5,
        "neutral": 1.0,
        "underweight": 0.5
    }
    return factors.get(action, 1.0)
```

#### 步骤5: 确定调仓规则

```python
def determine_rebalance_rule(environment: dict) -> dict:
    """确定调仓规则"""
    regime = environment["regime"]
    
    rules = {
        "risk_on": {
            "frequency": "monthly",
            "threshold": 0.05,  # 权重偏离5%触发调仓
            "method": "calendar"
        },
        "risk_off": {
            "frequency": "weekly",
            "threshold": 0.03,
            "method": "threshold"
        },
        "neutral": {
            "frequency": "monthly",
            "threshold": 0.05,
            "method": "calendar"
        }
    }
    
    return rules.get(regime, rules["neutral"])
```

### 3.4 输出格式

```json
{
  "name": "MacroMomentumStrategy",
  "assets": ["SPY", "QQQ", "TLT", "GLD"],
  "weights": {
    "SPY": 0.35,
    "QQQ": 0.25,
    "TLT": 0.20,
    "GLD": 0.20
  },
  "rebalance": {
    "frequency": "monthly",
    "threshold": 0.05,
    "method": "calendar"
  },
  "constraints": {
    "max_single_weight": 0.40,
    "min_single_weight": 0.05,
    "max_turnover": 0.30
  }
}
```

## 4. Backtest Runner Workflow

### 4.1 工作流目标

使用历史数据验证策略表现，生成性能指标和可视化报告。

### 4.2 执行步骤

```
步骤1: 加载策略配置
  │
  ▼
步骤2: 获取历史数据
  │
  ▼
步骤3: 构建回测引擎
  │
  ▼
步骤4: 执行回测
  │
  ▼
步骤5: 计算性能指标
  │
  ▼
步骤6: 生成可视化
  │
  ▼
步骤7: 输出回测报告
```

### 4.3 详细设计

#### 步骤2: 获取历史数据

```python
async def fetch_backtest_data(
    assets: list[str],
    start_date: str,
    end_date: str,
    benchmark: str = "SPY"
) -> pd.DataFrame:
    """获取回测历史数据"""
    tickers = assets + [benchmark]
    
    # 通过MCP获取数据
    data = await mcp_call(
        "get_stock_history",
        {
            "tickers": tickers,
            "start_date": start_date,
            "end_date": end_date
        }
    )
    
    # 数据清洗
    data = clean_market_data(data)
    
    return data
```

#### 步骤3-4: 构建并执行回测

```python
def run_backtest(
    strategy: dict,
    data: pd.DataFrame,
    initial_capital: float = 1000000
) -> bt.backtest_result:
    """执行回测"""
    # 创建策略
    bt_strategy = create_bt_strategy(strategy)
    
    # 创建回测
    backtest = bt.Backtest(
        bt_strategy,
        data,
        initial_capital=initial_capital
    )
    
    # 执行回测
    result = bt.run(backtest)
    
    return result

def create_bt_strategy(strategy_config: dict) -> bt.Strategy:
    """创建bt回测策略"""
    algos = [
        bt.algos.SelectAll(),
        MacroMomentumStrategy(
            macro_signals=strategy_config.get("macro_signals", {}),
            rebalance_period=strategy_config["rebalance"]["frequency"]
        ),
        bt.algos.WeighSpecified(**strategy_config["weights"]),
        bt.algos.Rebalance()
    ]
    
    return bt.Strategy(
        strategy_config["name"],
        algos
    )
```

#### 步骤5: 计算性能指标

```python
def calculate_metrics(result: bt.backtest_result) -> dict:
    """计算性能指标"""
    prices = result.prices
    
    metrics = {
        "total_return": calculate_total_return(prices),
        "annualized_return": calculate_annualized_return(prices),
        "max_drawdown": calculate_max_drawdown(prices),
        "sharpe_ratio": calculate_sharpe_ratio(prices),
        "sortino_ratio": calculate_sortino_ratio(prices),
        "calmar_ratio": calculate_calmar_ratio(prices),
        "volatility": calculate_volatility(prices),
        "win_rate": calculate_win_rate(prices),
        "avg_win_loss_ratio": calculate_avg_win_loss_ratio(prices)
    }
    
    return metrics
```

### 4.4 输出格式

```json
{
  "period": {
    "start": "2018-01-01",
    "end": "2024-12-31",
    "days": 2557
  },
  "performance": {
    "total_return": 0.85,
    "annualized_return": 0.092,
    "max_drawdown": -0.18,
    "sharpe_ratio": 0.85,
    "sortino_ratio": 1.12,
    "volatility": 0.12
  },
  "benchmark_comparison": {
    "benchmark_return": 0.72,
    "alpha": 0.13,
    "beta": 0.85,
    "information_ratio": 0.45
  },
  "plots": {
    "equity_curve": "output/equity_curve.png",
    "drawdown": "output/drawdown.png",
    "monthly_returns": "output/monthly_returns.png"
  }
}
```

## 5. 自我修正机制

### 5.1 错误检测

```python
class SelfCorrection:
    def __init__(self, max_retries: int = 3):
        self.max_retries = max_retries
        self.retry_count = 0
    
    async def execute_with_correction(self, workflow_func, *args, **kwargs):
        """执行工作流并自动修正错误"""
        while self.retry_count < self.max_retries:
            try:
                result = await workflow_func(*args, **kwargs)
                
                # 验证结果
                if self.validate_result(result):
                    return result
                else:
                    raise ValueError("Result validation failed")
                    
            except Exception as e:
                self.retry_count += 1
                error_context = self.build_error_context(e)
                
                # 生成修正方案
                correction = await generate_correction(error_context)
                
                # 应用修正
                kwargs.update(correction)
        
        raise RuntimeError("Max retries exceeded")
```

### 5.2 验证规则

```python
def validate_result(result: dict) -> bool:
    """验证工作流结果"""
    # 检查必要字段
    required_fields = ["macro_environment", "insights", "recommendations"]
    for field in required_fields:
        if field not in result:
            return False
    
    # 检查数据有效性
    if len(result["insights"]) == 0:
        return False
    
    # 检查权重和为1
    if "strategy" in result:
        weights = result["strategy"].get("weights", {})
        if abs(sum(weights.values()) - 1.0) > 0.01:
            return False
    
    return True
```

## 6. 上下文管理

### 6.1 记忆存储

```python
class AgentMemory:
    def __init__(self, storage_path: str = "memory/"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
    
    def save_research(self, research: dict):
        """保存研究结果"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = self.storage_path / f"research_{timestamp}.json"
        
        with open(filename, "w") as f:
            json.dump(research, f, indent=2, default=str)
    
    def get_history(self, limit: int = 10) -> list[dict]:
        """获取历史研究"""
        files = sorted(self.storage_path.glob("research_*.json"), reverse=True)
        
        history = []
        for f in files[:limit]:
            with open(f) as fp:
                history.append(json.load(fp))
        
        return history
```

### 6.2 上下文构建

```python
def build_context(
    query: str,
    history: list[dict] = None,
    macro_results: dict = None
) -> str:
    """构建Agent上下文"""
    context = f"用户查询: {query}\n\n"
    
    if history:
        context += "历史研究:\n"
        for h in history[:3]:
            context += f"- {h['timestamp']}: {h['macro_environment']['regime']}\n"
        context += "\n"
    
    if macro_results:
        context += f"当前宏观环境: {macro_results['macro_environment']['regime']}\n"
        context += f"置信度: {macro_results['macro_environment']['confidence']:.0%}\n"
    
    return context
```
