# 风险管理设计

## 1. 风险管理框架

```
┌─────────────────────────────────────────────────────────────┐
│                    风险管理体系                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │  市场风险    │  │  策略风险    │  │  操作风险           │  │
│  │  管理        │  │  管理        │  │  管理               │  │
│  └──────┬──────┘  └──────┬──────┘  └──────────┬──────────┘  │
└─────────┼────────────────┼────────────────────┼─────────────┘
          │                │                    │
┌─────────▼────────────────▼────────────────────▼─────────────┐
│                    风险控制措施                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │  仓位控制    │  │  止损机制    │  │  压力测试           │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## 2. 市场风险管理

### 2.1 风险指标

| 指标 | 说明 | 计算方法 | 预警阈值 |
|------|------|----------|----------|
| VaR | 在险价值 | 历史模拟法 | > 5% |
| 最大回撤 | 最大亏损幅度 | 峰值到谷值 | > 20% |
| 波动率 | 价格波动程度 | 标准差 | > 25% |
| Beta | 系统性风险 | 回归系数 | > 1.5 |
| 夏普比率 | 风险调整后收益 | 超额收益/波动率 | < 0.5 |

### 2.2 VaR计算

```python
# backtest-engine/metrics/risk.py
import pandas as pd
import numpy as np
from scipy import stats

def calculate_var(
    returns: pd.Series,
    confidence: float = 0.95,
    method: str = "historical"
) -> float:
    """计算VaR
    
    Args:
        returns: 收益率序列
        confidence: 置信水平
        method: 计算方法 (historical/parametric)
    
    Returns:
        VaR值
    """
    if method == "historical":
        return np.percentile(returns, (1 - confidence) * 100)
    
    elif method == "parametric":
        mean = returns.mean()
        std = returns.std()
        z_score = stats.norm.ppf(1 - confidence)
        return mean + z_score * std
    
    else:
        raise ValueError(f"Unknown method: {method}")

def calculate_conditional_var(
    returns: pd.Series,
    confidence: float = 0.95
) -> float:
    """计算条件VaR (CVaR/Expected Shortfall)"""
    var = calculate_var(returns, confidence)
    return returns[returns <= var].mean()
```

### 2.3 压力测试

```python
def stress_test(
    portfolio_weights: dict,
    scenarios: list[dict]
) -> dict:
    """压力测试
    
    Args:
        portfolio_weights: 组合权重
        scenarios: 压力场景
    
    Returns:
        压力测试结果
    """
    results = {}
    
    for scenario in scenarios:
        name = scenario["name"]
        shocks = scenario["shocks"]
        
        # 计算组合损失
        portfolio_loss = 0
        for asset, weight in portfolio_weights.items():
            if asset in shocks:
                portfolio_loss += weight * shocks[asset]
        
        results[name] = {
            "portfolio_loss": portfolio_loss,
            "shocks": shocks
        }
    
    return results

# 定义压力场景
SCENARIOS = [
    {
        "name": "2008金融危机",
        "shocks": {
            "SPY": -0.50,
            "QQQ": -0.55,
            "TLT": 0.20,
            "GLD": -0.30
        }
    },
    {
        "name": "2020疫情",
        "shocks": {
            "SPY": -0.35,
            "QQQ": -0.30,
            "TLT": 0.15,
            "GLD": -0.10
        }
    },
    {
        "name": "利率飙升",
        "shocks": {
            "SPY": -0.20,
            "QQQ": -0.25,
            "TLT": -0.30,
            "GLD": -0.15
        }
    },
    {
        "name": "滞胀",
        "shocks": {
            "SPY": -0.25,
            "QQQ": -0.30,
            "TLT": -0.10,
            "GLD": 0.20
        }
    }
]
```

## 3. 策略风险管理

### 3.1 过拟合检测

```python
def detect_overfitting(
    in_sample_metrics: dict,
    out_of_sample_metrics: dict,
    threshold: float = 0.5
) -> bool:
    """检测过拟合
    
    Args:
        in_sample_metrics: 样本内指标
        out_of_sample_metrics: 样本外指标
        threshold: 差异阈值
    
    Returns:
        是否过拟合
    """
    # 比较夏普比率
    is_sharpe_diff = abs(
        in_sample_metrics["sharpe_ratio"] - 
        out_of_sample_metrics["sharpe_ratio"]
    ) > threshold
    
    # 比较最大回撤
    is_drawdown_diff = abs(
        in_sample_metrics["max_drawdown"] - 
        out_of_sample_metrics["max_drawdown"]
    ) > threshold * 0.1
    
    return is_sharpe_diff or is_drawdown_diff
```

### 3.2 参数敏感性分析

```python
def parameter_sensitivity(
    strategy_class,
    param_name: str,
    param_range: list,
    data: pd.DataFrame,
    metric: str = "sharpe_ratio"
) -> pd.DataFrame:
    """参数敏感性分析
    
    Args:
        strategy_class: 策略类
        param_name: 参数名
        param_range: 参数范围
        data: 回测数据
        metric: 评估指标
    
    Returns:
        敏感性分析结果
    """
    results = []
    
    for param_value in param_range:
        strategy = strategy_class(**{param_name: param_value})
        backtest = bt.Backtest(strategy, data)
        result = bt.run(backtest)
        
        metric_value = get_metric(result, metric)
        
        results.append({
            param_name: param_value,
            metric: metric_value
        })
    
    return pd.DataFrame(results)
```

### 3.3 策略衰减监控

```python
class StrategyDecayMonitor:
    """策略衰减监控"""
    
    def __init__(self, window: int = 90):
        self.window = window
        self.performance_history = []
    
    def update(self, current_performance: float):
        """更新性能记录"""
        self.performance_history.append(current_performance)
        
        # 保持窗口大小
        if len(self.performance_history) > self.window:
            self.performance_history.pop(0)
    
    def check_decay(self, threshold: float = 0.3) -> bool:
        """检查策略衰减
        
        Args:
            threshold: 衰减阈值
        
        Returns:
            是否衰减
        """
        if len(self.performance_history) < 30:
            return False
        
        # 比较近期和远期表现
        recent = np.mean(self.performance_history[-30:])
        historical = np.mean(self.performance_history[:-30])
        
        decay_rate = (historical - recent) / abs(historical)
        
        return decay_rate > threshold
```

## 4. 操作风险管理

### 4.1 仓位控制

```python
class PositionManager:
    """仓位管理器"""
    
    def __init__(
        self,
        max_single_weight: float = 0.20,
        max_sector_weight: float = 0.40,
        max_total_weight: float = 1.0
    ):
        self.max_single_weight = max_single_weight
        self.max_sector_weight = max_sector_weight
        self.max_total_weight = max_total_weight
    
    def adjust_weights(self, weights: dict, sectors: dict) -> dict:
        """调整权重
        
        Args:
            weights: 原始权重
            sectors: 行业映射
        
        Returns:
            调整后的权重
        """
        adjusted = weights.copy()
        
        # 限制单个资产权重
        for asset in adjusted:
            if adjusted[asset] > self.max_single_weight:
                adjusted[asset] = self.max_single_weight
        
        # 限制行业权重
        sector_weights = {}
        for asset, weight in adjusted.items():
            sector = self._get_sector(asset, sectors)
            sector_weights[sector] = sector_weights.get(sector, 0) + weight
        
        for sector, weight in sector_weights.items():
            if weight > self.max_sector_weight:
                # 按比例缩减
                scale = self.max_sector_weight / weight
                for asset in adjusted:
                    if self._get_sector(asset, sectors) == sector:
                        adjusted[asset] *= scale
        
        # 归一化
        total = sum(adjusted.values())
        if total > 0:
            adjusted = {k: v/total for k, v in adjusted.items()}
        
        return adjusted
    
    def _get_sector(self, asset: str, sectors: dict) -> str:
        """获取资产所属行业"""
        for sector, assets in sectors.items():
            if asset in assets:
                return sector
        return "unknown"
```

### 4.2 止损机制

```python
class StopLossManager:
    """止损管理器"""
    
    def __init__(
        self,
        stop_loss_pct: float = 0.10,
        trailing_stop_pct: float = 0.05,
        portfolio_stop_loss: float = 0.15
    ):
        self.stop_loss_pct = stop_loss_pct
        self.trailing_stop_pct = trailing_stop_pct
        self.portfolio_stop_loss = portfolio_stop_loss
        self.high_watermarks = {}
    
    def check_stop_loss(
        self,
        positions: dict,
        current_prices: dict,
        cost_basis: dict
    ) -> dict:
        """检查止损
        
        Args:
            positions: 持仓
            current_prices: 当前价格
            cost_basis: 成本价
        
        Returns:
            需要平仓的资产
        """
        to_close = {}
        
        for asset, position in positions.items():
            if asset not in current_prices or asset not in cost_basis:
                continue
            
            current_price = current_prices[asset]
            cost = cost_basis[asset]
            
            # 固定止损
            if (cost - current_price) / cost > self.stop_loss_pct:
                to_close[asset] = position
            
            # 追踪止损
            if asset not in self.high_watermarks:
                self.high_watermarks[asset] = current_price
            else:
                self.high_watermarks[asset] = max(
                    self.high_watermarks[asset],
                    current_price
                )
                
                high = self.high_watermarks[asset]
                if (high - current_price) / high > self.trailing_stop_pct:
                    to_close[asset] = position
        
        return to_close
    
    def check_portfolio_stop_loss(
        self,
        portfolio_value: float,
        initial_value: float
    ) -> bool:
        """检查组合止损"""
        loss = (initial_value - portfolio_value) / initial_value
        return loss > self.portfolio_stop_loss
```

### 4.3 异常检测

```python
class AnomalyDetector:
    """异常检测"""
    
    def __init__(self, window: int = 60):
        self.window = window
        self.return_history = []
    
    def update(self, daily_return: float):
        """更新收益率历史"""
        self.return_history.append(daily_return)
        if len(self.return_history) > self.window:
            self.return_history.pop(0)
    
    def detect_anomaly(self, threshold: float = 3.0) -> bool:
        """检测异常
        
        Args:
            threshold: 异常阈值（标准差）
        
        Returns:
            是否异常
        """
        if len(self.return_history) < 20:
            return False
        
        mean = np.mean(self.return_history)
        std = np.std(self.return_history)
        
        if std == 0:
            return False
        
        latest = self.return_history[-1]
        z_score = abs(latest - mean) / std
        
        return z_score > threshold
```

## 5. 风险报告

### 5.1 风险报告生成

```python
def generate_risk_report(
    portfolio_weights: dict,
    returns: pd.Series,
    benchmark_returns: pd.Series = None
) -> dict:
    """生成风险报告
    
    Args:
        portfolio_weights: 组合权重
        returns: 收益率序列
        benchmark_returns: 基准收益率
    
    Returns:
        风险报告
    """
    report = {
        "risk_metrics": {
            "var_95": calculate_var(returns, 0.95),
            "var_99": calculate_var(returns, 0.99),
            "cvar_95": calculate_conditional_var(returns, 0.95),
            "max_drawdown": calculate_max_drawdown_from_returns(returns),
            "volatility": returns.std() * np.sqrt(252),
            "sharpe_ratio": calculate_sharpe_ratio_from_returns(returns),
            "sortino_ratio": calculate_sortino_ratio_from_returns(returns)
        },
        "concentration": {
            "max_single_weight": max(portfolio_weights.values()),
            "top3_weight": sum(sorted(portfolio_weights.values(), reverse=True)[:3]),
            "herfindahl_index": sum(w**2 for w in portfolio_weights.values())
        }
    }
    
    if benchmark_returns is not None:
        report["relative_risk"] = {
            "beta": calculate_beta(returns, benchmark_returns),
            "tracking_error": calculate_tracking_error(returns, benchmark_returns),
            "information_ratio": calculate_information_ratio(returns, benchmark_returns)
        }
    
    # 压力测试
    report["stress_test"] = stress_test(portfolio_weights, SCENARIOS)
    
    return report
```

### 5.2 风险预警

```python
class RiskAlertSystem:
    """风险预警系统"""
    
    def __init__(self, thresholds: dict):
        self.thresholds = thresholds
        self.alerts = []
    
    def check_risks(self, risk_report: dict) -> list[dict]:
        """检查风险
        
        Args:
            risk_report: 风险报告
        
        Returns:
            预警列表
        """
        alerts = []
        
        # 检查VaR
        if risk_report["risk_metrics"]["var_95"] < -self.thresholds["var"]:
            alerts.append({
                "type": "VAR_EXCEEDED",
                "level": "HIGH",
                "message": f"VaR超过阈值: {risk_report['risk_metrics']['var_95']:.2%}"
            })
        
        # 检查最大回撤
        if risk_report["risk_metrics"]["max_drawdown"] < -self.thresholds["max_drawdown"]:
            alerts.append({
                "type": "DRAWDOWN_EXCEEDED",
                "level": "HIGH",
                "message": f"最大回撤超过阈值: {risk_report['risk_metrics']['max_drawdown']:.2%}"
            })
        
        # 检查集中度
        if risk_report["concentration"]["max_single_weight"] > self.thresholds["max_single_weight"]:
            alerts.append({
                "type": "CONCENTRATION_RISK",
                "level": "MEDIUM",
                "message": f"单资产权重过高: {risk_report['concentration']['max_single_weight']:.2%}"
            })
        
        self.alerts.extend(alerts)
        return alerts
    
    def get_active_alerts(self) -> list[dict]:
        """获取当前预警"""
        return self.alerts[-10:]  # 返回最近10条
```

## 6. 风险限额

### 6.1 限额设置

| 风险类型 | 限额 | 说明 |
|----------|------|------|
| 单日最大亏损 | 2% | 组合价值的2% |
| 月度最大亏损 | 5% | 组合价值的5% |
| 最大回撤 | 15% | 从峰值的最大跌幅 |
| 单资产最大权重 | 20% | 单个资产不超过20% |
| 单行业最大权重 | 40% | 单个行业不超过40% |
| VaR (95%) | 3% | 日VaR不超过3% |

### 6.2 限额监控

```python
class LimitMonitor:
    """限额监控"""
    
    def __init__(self, limits: dict):
        self.limits = limits
        self.daily_pnl = []
        self.monthly_pnl = []
        self.peak_value = 0
    
    def update(self, portfolio_value: float, daily_return: float):
        """更新监控数据"""
        self.daily_pnl.append(daily_return)
        self.monthly_pnl.append(daily_return)
        
        # 更新峰值
        self.peak_value = max(self.peak_value, portfolio_value)
        
        # 清理历史数据
        if len(self.daily_pnl) > 1:
            self.daily_pnl.pop(0)
        if len(self.monthly_pnl) > 22:
            self.monthly_pnl.pop(0)
    
    def check_limits(self, portfolio_value: float) -> list[dict]:
        """检查限额"""
        breaches = []
        
        # 检查日亏损
        daily_loss = sum(self.daily_pnl)
        if daily_loss < -self.limits["daily_loss"]:
            breaches.append({
                "type": "DAILY_LOSS",
                "value": daily_loss,
                "limit": -self.limits["daily_loss"]
            })
        
        # 检查月亏损
        monthly_loss = sum(self.monthly_pnl)
        if monthly_loss < -self.limits["monthly_loss"]:
            breaches.append({
                "type": "MONTHLY_LOSS",
                "value": monthly_loss,
                "limit": -self.limits["monthly_loss"]
            })
        
        # 检查回撤
        drawdown = (portfolio_value - self.peak_value) / self.peak_value
        if drawdown < -self.limits["max_drawdown"]:
            breaches.append({
                "type": "DRAWDOWN",
                "value": drawdown,
                "limit": -self.limits["max_drawdown"]
            })
        
        return breaches
```

## 7. 应急预案

### 7.1 触发条件

| 事件 | 触发条件 | 应急措施 |
|------|----------|----------|
| 市场崩盘 | 单日跌幅>5% | 减仓50%，转入防御 |
| 流动性危机 | 成交量萎缩50% | 暂停交易，评估风险 |
| 系统故障 | 数据中断>1小时 | 切换备用系统 |
| 策略失效 | 连续3月跑输基准 | 暂停策略，重新评估 |

### 7.2 应急流程

```python
class EmergencyProtocol:
    """应急预案"""
    
    def __init__(self):
        self.is_emergency = False
    
    def trigger_emergency(self, event_type: str, reason: str):
        """触发应急预案"""
        self.is_emergency = True
        
        # 记录事件
        logger.critical(f"Emergency triggered: {event_type} - {reason}")
        
        # 执行应急措施
        if event_type == "MARKET_CRASH":
            self._handle_market_crash()
        elif event_type == "LIQUIDITY_CRISIS":
            self._handle_liquidity_crisis()
        elif event_type == "SYSTEM_FAILURE":
            self._handle_system_failure()
        elif event_type == "STRATEGY_FAILURE":
            self._handle_strategy_failure()
    
    def _handle_market_crash(self):
        """处理市场崩盘"""
        # 1. 减仓
        # 2. 转入防御性资产
        # 3. 通知相关人员
        pass
    
    def _handle_liquidity_crisis(self):
        """处理流动性危机"""
        # 1. 暂停交易
        # 2. 评估持仓流动性
        # 3. 制定退出计划
        pass
    
    def _handle_system_failure(self):
        """处理系统故障"""
        # 1. 切换备用系统
        # 2. 检查数据完整性
        # 3. 恢复交易
        pass
    
    def _handle_strategy_failure(self):
        """处理策略失效"""
        # 1. 暂停策略
        # 2. 分析失效原因
        # 3. 重新优化或替换
        pass
    
    def resolve_emergency(self):
        """解除应急状态"""
        self.is_emergency = False
        logger.info("Emergency resolved")
```

## 8. 合规要求

### 8.1 数据合规

- 使用合法公开数据源
- 遵守数据使用协议
- 不存储敏感个人信息

### 8.2 交易合规

- 遵守市场交易规则
- 不进行市场操纵
- 不进行内幕交易

### 8.3 报告合规

- 保留所有交易记录
- 定期生成风险报告
- 接受审计检查

## 9. 持续改进

### 9.1 风险模型更新

- 每季度回顾风险模型
- 根据市场变化调整参数
- 引入新的风险因子

### 9.2 压力测试更新

- 定期更新压力场景
- 加入新的历史危机场景
- 考虑极端但可能的场景

### 9.3 监控指标优化

- 监控预警准确率
- 减少误报和漏报
- 优化阈值设置
