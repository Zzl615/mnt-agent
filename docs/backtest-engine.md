# 回测引擎设计

## 1. 概述

回测引擎基于`bt`（backtesting）框架构建，采用树状结构设计，便于Agent理解和生成策略代码。引擎支持多种策略类型、性能评估指标和可视化输出。

## 2. 架构设计

```
┌─────────────────────────────────────────────────────────────┐
│                    Backtest Engine                           │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │  Strategy   │  │  Algorithm  │  │  Performance        │  │
│  │  Builder    │  │  Nodes      │  │  Metrics            │  │
│  └──────┬──────┘  └──────┬──────┘  └──────────┬──────────┘  │
└─────────┼────────────────┼────────────────────┼─────────────┘
          │                │                    │
┌─────────▼────────────────▼────────────────────▼─────────────┐
│                    bt Framework                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │  Strategy   │  │  Algo       │  │  Backtest           │  │
│  │  (Tree)     │  │  (Nodes)    │  │  (Execution)        │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## 3. 策略模板

### 3.1 宏观动量策略 (Macro Momentum)

根据宏观信号调整资产权重。

```python
# backtest-engine/strategies/macro_momentum.py
import bt
import pandas as pd
from typing import Dict

class MacroMomentumStrategy(bt.Algo):
    """基于宏观动量的策略"""
    
    def __init__(self, macro_signals: Dict, rebalance_period: str = "m"):
        super().__init__()
        self.macro_signals = macro_signals
        self.rebalance_period = rebalance_period
        self.last_rebalance = None
    
    def __call__(self, target):
        # 检查是否需要再平衡
        current_date = target.now
        if self.last_rebalance and not self._should_rebalance(current_date):
            return True
        
        # 根据宏观信号调整权重
        weights = self._calculate_weights(target)
        
        # 设置目标权重
        target.temp["weights"] = weights
        self.last_rebalance = current_date
        
        return True
    
    def _should_rebalance(self, current_date) -> bool:
        """判断是否需要再平衡"""
        if self.last_rebalance is None:
            return True
        
        if self.rebalance_period == "w":
            return (current_date - self.last_rebalance).days >= 7
        elif self.rebalance_period == "m":
            return (current_date - self.last_rebalance).days >= 30
        elif self.rebalance_period == "q":
            return (current_date - self.last_rebalance).days >= 90
        
        return False
    
    def _calculate_weights(self, target) -> Dict[str, float]:
        """根据宏观信号计算权重"""
        securities = target.universe.columns
        weights = {}
        
        # 基础权重：等权重
        base_weight = 1.0 / len(securities) if securities else 0.25
        
        for security in securities:
            weight = base_weight
            
            # 根据宏观信号调整
            if security in self.macro_signals:
                signal = self.macro_signals[security]
                if signal == "bullish":
                    weight *= 1.5
                elif signal == "bearish":
                    weight *= 0.5
            
            weights[security] = weight
        
        # 归一化
        total = sum(weights.values())
        if total > 0:
            weights = {k: v/total for k, v in weights.items()}
        
        return weights
```

### 3.2 行业轮动策略 (Sector Rotation)

根据宏观环境轮动到表现最佳的行业。

```python
# backtest-engine/strategies/sector_rotation.py
import bt
import pandas as pd
from typing import Dict, List

class SectorRotationStrategy(bt.Algo):
    """行业轮动策略"""
    
    def __init__(
        self,
        sectors: Dict[str, List[str]],
        macro_regime: str,
        lookback_period: int = 90,
        top_n: int = 3
    ):
        super().__init__()
        self.sectors = sectors
        self.macro_regime = macro_regime
        self.lookback_period = lookback_period
        self.top_n = top_n
        self.last_rebalance = None
    
    def __call__(self, target):
        # 检查是否需要再平衡
        if self.last_rebalance and (target.now - self.last_rebalance).days < 30:
            return True
        
        # 选择表现最佳的行业
        selected_sectors = self._select_sectors(target)
        
        # 计算权重
        weights = self._calculate_weights(selected_sectors)
        
        target.temp["weights"] = weights
        self.last_rebalance = target.now
        
        return True
    
    def _select_sectors(self, target) -> List[str]:
        """选择表现最佳的行业"""
        sector_returns = {}
        
        for sector_name, tickers in self.sectors.items():
            # 计算行业平均收益率
            returns = []
            for ticker in tickers:
                if ticker in target.prices.columns:
                    prices = target.prices[ticker]
                    if len(prices) >= self.lookback_period:
                        ret = (prices.iloc[-1] / prices.iloc[-self.lookback_period]) - 1
                        returns.append(ret)
            
            if returns:
                sector_returns[sector_name] = sum(returns) / len(returns)
        
        # 按收益率排序，选择top_n
        sorted_sectors = sorted(sector_returns.items(), key=lambda x: x[1], reverse=True)
        return [s[0] for s in sorted_sectors[:self.top_n]]
    
    def _calculate_weights(self, selected_sectors: List[str]) -> Dict[str, float]:
        """计算权重"""
        weights = {}
        
        for sector in selected_sectors:
            tickers = self.sectors[sector]
            weight_per_ticker = 1.0 / len(selected_sectors) / len(tickers)
            
            for ticker in tickers:
                weights[ticker] = weight_per_ticker
        
        return weights
```

### 3.3 风险平价策略 (Risk Parity)

根据资产波动率分配权重，实现风险均衡。

```python
# backtest-engine/strategies/risk_parity.py
import bt
import pandas as pd
import numpy as np
from typing import Dict

class RiskParityStrategy(bt.Algo):
    """风险平价策略"""
    
    def __init__(self, lookback_period: int = 60, rebalance_period: str = "m"):
        super().__init__()
        self.lookback_period = lookback_period
        self.rebalance_period = rebalance_period
        self.last_rebalance = None
    
    def __call__(self, target):
        if self.last_rebalance and not self._should_rebalance(target.now):
            return True
        
        weights = self._calculate_risk_parity_weights(target)
        target.temp["weights"] = weights
        self.last_rebalance = target.now
        
        return True
    
    def _calculate_risk_parity_weights(self, target) -> Dict[str, float]:
        """计算风险平价权重"""
        securities = target.universe.columns
        
        # 计算波动率
        volatilities = {}
        for security in securities:
            prices = target.prices[security]
            if len(prices) >= self.lookback_period:
                returns = prices.pct_change().dropna()
                vol = returns.iloc[-self.lookback_period:].std() * np.sqrt(252)
                volatilities[security] = vol
        
        if not volatilities:
            return {s: 1.0/len(securities) for s in securities}
        
        # 风险平价：波动率越低，权重越高
        inverse_vol = {k: 1.0/v for k, v in volatilities.items()}
        total_inverse_vol = sum(inverse_vol.values())
        
        weights = {k: v/total_inverse_vol for k, v in inverse_vol.items()}
        
        return weights
```

## 4. 算法节点

### 4.1 选择节点

```python
# 选择所有资产
bt.algos.SelectAll()

# 选择特定资产
bt.algos.SelectWhere(condition)

# 排除特定资产
bt.algos.ExcludeAssets(exclude_list)
```

### 4.2 权重节点

```python
# 等权重
bt.algos.WeighEqually()

# 指定权重
bt.algos.WeighSpecified(**weights)

# 按市值权重
bt.algos.WeighByMarketCap()
```

### 4.3 执行节点

```python
# 再平衡
bt.algos.Rebalance()

# 执行交易
bt.algos.RunOnce()

# 设置佣金
bt.algos.SetCommission(commission_func)
```

### 4.4 自定义节点

```python
class StopLossAlgo(bt.Algo):
    """止损算法"""
    
    def __init__(self, threshold: float = -0.10):
        super().__init__()
        self.threshold = threshold
    
    def __call__(self, target):
        for security in target.weights.index:
            if security in target.positions:
                position_value = target.positions[security] * target.prices[security].iloc[-1]
                cost_basis = target.positions[security] * target.prices[security].iloc[-1] / (1 + self.threshold)
                
                if position_value < cost_basis:
                    target.temp["weights"][security] = 0
        
        return True
```

## 5. 性能指标

### 5.1 收益指标

```python
# backtest-engine/metrics/performance.py
import pandas as pd
import numpy as np

def calculate_total_return(prices: pd.Series) -> float:
    """计算总收益率"""
    return (prices.iloc[-1] / prices.iloc[0]) - 1

def calculate_annualized_return(prices: pd.Series) -> float:
    """计算年化收益率"""
    days = (prices.index[-1] - prices.index[0]).days
    total_return = calculate_total_return(prices)
    return (1 + total_return) ** (365 / days) - 1

def calculate_cagr(prices: pd.Series) -> float:
    """计算复合年增长率"""
    years = (prices.index[-1] - prices.index[0]).days / 365.25
    return (prices.iloc[-1] / prices.iloc[0]) ** (1 / years) - 1
```

### 5.2 风险指标

```python
def calculate_max_drawdown(prices: pd.Series) -> float:
    """计算最大回撤"""
    rolling_max = prices.cummax()
    drawdown = (prices - rolling_max) / rolling_max
    return drawdown.min()

def calculate_volatility(prices: pd.Series, annualize: bool = True) -> float:
    """计算波动率"""
    returns = prices.pct_change().dropna()
    vol = returns.std()
    if annualize:
        vol *= np.sqrt(252)
    return vol

def calculate_value_at_risk(returns: pd.Series, confidence: float = 0.95) -> float:
    """计算VaR"""
    return np.percentile(returns, (1 - confidence) * 100)
```

### 5.3 风险调整后收益

```python
def calculate_sharpe_ratio(prices: pd.Series, risk_free_rate: float = 0.02) -> float:
    """计算夏普比率"""
    returns = prices.pct_change().dropna()
    excess_returns = returns - risk_free_rate / 252
    
    if returns.std() == 0:
        return 0
    
    return (excess_returns.mean() / returns.std()) * np.sqrt(252)

def calculate_sortino_ratio(prices: pd.Series, risk_free_rate: float = 0.02) -> float:
    """计算索提诺比率"""
    returns = prices.pct_change().dropna()
    excess_returns = returns - risk_free_rate / 252
    
    downside_returns = returns[returns < 0]
    downside_std = downside_returns.std() * np.sqrt(252)
    
    if downside_std == 0:
        return 0
    
    return (excess_returns.mean() * 252) / downside_std

def calculate_calmar_ratio(prices: pd.Series) -> float:
    """计算卡尔玛比率"""
    annualized_return = calculate_annualized_return(prices)
    max_drawdown = abs(calculate_max_drawdown(prices))
    
    if max_drawdown == 0:
        return 0
    
    return annualized_return / max_drawdown
```

### 5.4 基准对比

```python
def calculate_alpha(portfolio_returns: pd.Series, benchmark_returns: pd.Series) -> float:
    """计算Alpha"""
    beta = calculate_beta(portfolio_returns, benchmark_returns)
    portfolio_annual = portfolio_returns.mean() * 252
    benchmark_annual = benchmark_returns.mean() * 252
    
    return portfolio_annual - beta * benchmark_annual

def calculate_beta(portfolio_returns: pd.Series, benchmark_returns: pd.Series) -> float:
    """计算Beta"""
    covariance = portfolio_returns.cov(benchmark_returns)
    benchmark_variance = benchmark_returns.var()
    
    if benchmark_variance == 0:
        return 0
    
    return covariance / benchmark_variance

def calculate_information_ratio(
    portfolio_returns: pd.Series,
    benchmark_returns: pd.Series
) -> float:
    """计算信息比率"""
    active_returns = portfolio_returns - benchmark_returns
    
    if active_returns.std() == 0:
        return 0
    
    return (active_returns.mean() / active_returns.std()) * np.sqrt(252)
```

## 6. 可视化

### 6.1 收益曲线

```python
# backtest-engine/visualizer.py
import matplotlib.pyplot as plt
import seaborn as sns

def plot_equity_curve(result, benchmark=None, save_path=None):
    """绘制收益曲线"""
    fig, ax = plt.subplots(figsize=(12, 6))
    
    result.prices.plot(ax=ax, label="Portfolio", linewidth=2)
    
    if benchmark is not None:
        benchmark.plot(ax=ax, label="Benchmark", linewidth=2, linestyle="--")
    
    ax.set_title("Portfolio Equity Curve", fontsize=14)
    ax.set_xlabel("Date")
    ax.set_ylabel("Value")
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
    
    plt.show()
```

### 6.2 回撤图

```python
def plot_drawdown(result, save_path=None):
    """绘制回撤图"""
    fig, ax = plt.subplots(figsize=(12, 6))
    
    drawdown = result.prices / result.prices.cummax() - 1
    drawdown.plot(ax=ax, color="red", linewidth=2)
    
    ax.fill_between(drawdown.index, drawdown, 0, alpha=0.3, color="red")
    
    ax.set_title("Portfolio Drawdown", fontsize=14)
    ax.set_xlabel("Date")
    ax.set_ylabel("Drawdown")
    ax.grid(True, alpha=0.3)
    
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
    
    plt.show()
```

### 6.3 月度收益热力图

```python
def plot_monthly_returns_heatmap(result, save_path=None):
    """绘制月度收益热力图"""
    monthly_returns = result.prices.resample("M").last().pct_change().dropna()
    
    # 重塑数据
    years = monthly_returns.index.year
    months = monthly_returns.index.month
    returns_df = pd.DataFrame({
        "Year": years,
        "Month": months,
        "Return": monthly_returns.values
    })
    returns_pivot = returns_df.pivot(index="Year", columns="Month", values="Return")
    
    # 绘制热力图
    fig, ax = plt.subplots(figsize=(12, 8))
    sns.heatmap(returns_pivot, annot=True, fmt=".2%", cmap="RdYlGn", ax=ax, center=0)
    
    ax.set_title("Monthly Returns Heatmap", fontsize=14)
    ax.set_xlabel("Month")
    ax.set_ylabel("Year")
    
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
    
    plt.show()
```

### 6.4 综合报告

```python
def generate_backtest_report(result, benchmark=None, output_dir="output/"):
    """生成回测报告"""
    from pathlib import Path
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # 绘制图表
    plot_equity_curve(result, benchmark, f"{output_dir}/equity_curve.png")
    plot_drawdown(result, f"{output_dir}/drawdown.png")
    plot_monthly_returns_heatmap(result, f"{output_dir}/monthly_returns.png")
    
    # 计算指标
    metrics = {
        "total_return": calculate_total_return(result.prices),
        "annualized_return": calculate_annualized_return(result.prices),
        "max_drawdown": calculate_max_drawdown(result.prices),
        "sharpe_ratio": calculate_sharpe_ratio(result.prices),
        "sortino_ratio": calculate_sortino_ratio(result.prices),
        "calmar_ratio": calculate_calmar_ratio(result.prices),
        "volatility": calculate_volatility(result.prices)
    }
    
    # 保存指标
    import json
    with open(f"{output_dir}/metrics.json", "w") as f:
        json.dump(metrics, f, indent=2, default=str)
    
    return metrics
```

## 7. 回测执行

### 7.1 创建回测

```python
def create_backtest(
    strategy_config: dict,
    data: pd.DataFrame,
    initial_capital: float = 1000000,
    commission: float = 0.001
) -> bt.Backtest:
    """创建回测"""
    # 创建策略
    strategy = build_strategy(strategy_config)
    
    # 创建回测
    backtest = bt.Backtest(
        strategy,
        data,
        initial_capital=initial_capital,
        commissions=commission
    )
    
    return backtest

def build_strategy(config: dict) -> bt.Strategy:
    """构建策略"""
    algos = []
    
    # 选择资产
    algos.append(bt.algos.SelectAll())
    
    # 添加策略算法
    strategy_type = config.get("type", "macro_momentum")
    
    if strategy_type == "macro_momentum":
        algos.append(MacroMomentumStrategy(
            macro_signals=config.get("macro_signals", {}),
            rebalance_period=config.get("rebalance_period", "m")
        ))
    elif strategy_type == "sector_rotation":
        algos.append(SectorRotationStrategy(
            sectors=config.get("sectors", {}),
            macro_regime=config.get("macro_regime", "neutral"),
            lookback_period=config.get("lookback_period", 90),
            top_n=config.get("top_n", 3)
        ))
    elif strategy_type == "risk_parity":
        algos.append(RiskParityStrategy(
            lookback_period=config.get("lookback_period", 60),
            rebalance_period=config.get("rebalance_period", "m")
        ))
    
    # 设置权重
    if "weights" in config:
        algos.append(bt.algos.WeighSpecified(**config["weights"]))
    else:
        algos.append(bt.algos.WeighEqually())
    
    # 再平衡
    algos.append(bt.algos.Rebalance())
    
    return bt.Strategy(config.get("name", "Strategy"), algos)
```

### 7.2 执行回测

```python
def run_backtest(backtest: bt.Backtest) -> bt.backtest_result:
    """执行回测"""
    result = bt.run(backtest)
    return result

def run_multiple_backtests(backtests: list) -> dict:
    """执行多个回测"""
    results = {}
    for bt in backtests:
        result = bt.run()
        results[bt.name] = result
    return results
```

## 8. 参数优化

### 8.1 网格搜索

```python
from itertools import product

def grid_search_optimize(
    strategy_class,
    param_grid: dict,
    data: pd.DataFrame,
    metric: str = "sharpe_ratio"
) -> dict:
    """网格搜索优化参数"""
    best_result = None
    best_metric = -float("inf")
    best_params = None
    
    # 生成参数组合
    param_names = list(param_grid.keys())
    param_values = list(param_grid.values())
    
    for params in product(*param_values):
        param_dict = dict(zip(param_names, params))
        
        # 创建策略
        strategy = strategy_class(**param_dict)
        backtest = bt.Backtest(strategy, data)
        
        # 执行回测
        result = bt.run(backtest)
        
        # 评估指标
        metric_value = get_metric(result, metric)
        
        if metric_value > best_metric:
            best_metric = metric_value
            best_params = param_dict
            best_result = result
    
    return {
        "best_params": best_params,
        "best_metric": best_metric,
        "best_result": best_result
    }
```

## 9. 注意事项

### 9.1 过拟合风险

- 使用样本外数据验证
- 限制参数数量
- 使用交叉验证

### 9.2 幸存者偏差

- 包含退市股票
- 使用历史成分股

### 9.3 交易成本

- 考虑佣金和滑点
- 考虑冲击成本

### 9.4 流动性约束

- 限制单只股票最大权重
- 考虑成交量限制
