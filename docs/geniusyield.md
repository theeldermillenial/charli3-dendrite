::: charli3_dendrite.dexs.ob.geniusyield

# GeniusYield

GeniusYield is a revolutionary smart liquidity management powerhouse on Cardano that combines an advanced order book DEX with intelligent yield optimization. Unlike traditional AMM DEXs, GeniusYield operates as a sophisticated order book system that enables professional trading strategies, precise price control, and advanced market making capabilities.

## Order Book Architecture

### Core Concepts

GeniusYield implements a fully on-chain order book model that provides:

- **Direct Order Placement**: Submit limit orders directly to the blockchain
- **Partial Fill Support**: Orders can be partially filled over multiple transactions
- **Time-Based Orders**: Support for start and end time constraints
- **Fee Management**: Sophisticated maker/taker fee structures
- **Multi-Version Support**: V1 and V1.1 contract versions with different fee calculations

### Order Book Components

| Component | Description | Purpose |
|-----------|-------------|---------|
| `GeniusYieldOrderState` | Individual order representation | Manages single order lifecycle |
| `GeniusYieldOrderBook` | Complete order book state | Aggregates buy/sell orders for trading |
| `BuyOrderBook` | Buy-side order collection | Manages purchase orders |
| `SellOrderBook` | Sell-side order collection | Manages sell orders |

## Key Features

### Professional Trading Interface
- **Limit Orders**: Set precise buy/sell prices
- **Market Orders**: Execute against existing order book
- **Partial Fills**: Orders can be filled incrementally
- **Order Expiration**: Time-based order management
- **Fee Optimization**: Maker/taker fee structures reward liquidity providers

### Smart Liquidity Management
- **Dynamic Pricing**: Real-time price discovery through order matching
- **Capital Efficiency**: No permanent liquidity lock-up like AMMs
- **Professional Tools**: Advanced order types for sophisticated strategies
- **Yield Optimization**: Intelligent strategies to maximize returns

### Version Support
- **V1 Contracts**: Original implementation with specific fee rounding
- **V1.1 Contracts**: Enhanced version with improved fee calculations
- **Automatic Detection**: Framework automatically handles version differences

## Basic Usage

### Querying Order Book State

```python
from charli3_dendrite import GeniusYieldOrderState, GeniusYieldOrderBook
from charli3_dendrite.backend import get_backend
from pycardano import Assets

# Get individual orders
backend = get_backend()
selector = GeniusYieldOrderState.pool_selector()
orders = backend.get_pool_utxos(**selector.model_dump())

# Process individual orders
for order_info in orders:
    order = GeniusYieldOrderState.model_validate(order_info.model_dump())
    print(f"Order ID: {order.pool_id}")
    print(f"Available: {order.available}")
    print(f"Price: {order.price[0]}/{order.price[1]}")
    print(f"Active: {not order.inactive}")
    print(f"Contract Version: {'V1.1' if order.dex_nft.unit().startswith('642c') else 'V1'}")
```

### Complete Order Book Analysis

```python
# Get complete order book for a trading pair
trading_pair = Assets({"ada": 0, "token_policy_id": 0})  # ADA/Token pair
order_book = GeniusYieldOrderBook.get_book(
    assets=trading_pair,
    orders=None  # Will fetch all orders automatically
)

print(f"Buy Orders: {len(order_book.buy_book_full)}")
print(f"Sell Orders: {len(order_book.sell_book_full)}")

# Analyze buy side
for i, buy_order in enumerate(order_book.buy_book_full):
    print(f"Buy {i+1}: {buy_order.quantity} @ {buy_order.price}")

# Analyze sell side  
for i, sell_order in enumerate(order_book.sell_book_full):
    print(f"Sell {i+1}: {sell_order.quantity} @ {sell_order.price}")
```

### Market Data Analysis

```python
# Calculate market metrics
def analyze_genius_yield_market(token_a: str, token_b: str):
    trading_pair = Assets({token_a: 0, token_b: 0})
    order_book = GeniusYieldOrderBook.get_book(trading_pair, None)
    
    if order_book.buy_book_full and order_book.sell_book_full:
        best_bid = order_book.buy_book_full[0].price
        best_ask = order_book.sell_book_full[0].price
        spread = (best_ask - best_bid) / best_bid * 100
        
        print(f"Best Bid: {best_bid}")
        print(f"Best Ask: {best_ask}")
        print(f"Spread: {spread:.2f}%")
        
        # Calculate order book depth
        buy_volume = sum(order.quantity for order in order_book.buy_book_full)
        sell_volume = sum(order.quantity for order in order_book.sell_book_full)
        
        print(f"Buy Volume: {buy_volume}")
        print(f"Sell Volume: {sell_volume}")
        
    return order_book

# Example usage
order_book = analyze_genius_yield_market("lovelace", "token_policy_id")
```

## Advanced Trading Strategies

### Market Making Strategy

```python
def genius_yield_market_making_strategy(
    token_a: str, 
    token_b: str, 
    spread_percent: float = 0.5,
    order_size: int = 1000000
):
    """Implement a basic market making strategy on GeniusYield."""
    
    # Get current order book
    trading_pair = Assets({token_a: 0, token_b: 0})
    order_book = GeniusYieldOrderBook.get_book(trading_pair, None)
    
    if not order_book.buy_book_full or not order_book.sell_book_full:
        print("Insufficient order book depth for market making")
        return
    
    # Calculate fair value (mid-market price)
    best_bid = order_book.buy_book_full[0].price
    best_ask = order_book.sell_book_full[0].price
    fair_value = (best_bid + best_ask) / 2
    
    # Calculate our bid/ask prices with spread
    our_bid = fair_value * (1 - spread_percent / 100)
    our_ask = fair_value * (1 + spread_percent / 100)
    
    print(f"Fair Value: {fair_value}")
    print(f"Our Bid: {our_bid} (size: {order_size})")
    print(f"Our Ask: {our_ask} (size: {order_size})")
    
    # Implementation would place actual orders here
    return {
        'bid_price': our_bid,
        'ask_price': our_ask,
        'bid_size': order_size,
        'ask_size': order_size
    }

# Example market making
strategy = genius_yield_market_making_strategy("lovelace", "token_policy", 0.3, 5000000)
```

### Liquidity Analysis

```python
def analyze_liquidity_depth(order_book: GeniusYieldOrderBook, price_levels: int = 5):
    """Analyze order book liquidity at different price levels."""
    
    liquidity_data = {
        'buy_levels': [],
        'sell_levels': [],
        'total_buy_liquidity': 0,
        'total_sell_liquidity': 0
    }
    
    # Analyze buy-side liquidity
    for i, order in enumerate(order_book.buy_book_full[:price_levels]):
        level_data = {
            'price': order.price,
            'quantity': order.quantity,
            'cumulative': sum(o.quantity for o in order_book.buy_book_full[:i+1])
        }
        liquidity_data['buy_levels'].append(level_data)
    
    # Analyze sell-side liquidity
    for i, order in enumerate(order_book.sell_book_full[:price_levels]):
        level_data = {
            'price': order.price,
            'quantity': order.quantity,
            'cumulative': sum(o.quantity for o in order_book.sell_book_full[:i+1])
        }
        liquidity_data['sell_levels'].append(level_data)
    
    liquidity_data['total_buy_liquidity'] = sum(o.quantity for o in order_book.buy_book_full)
    liquidity_data['total_sell_liquidity'] = sum(o.quantity for o in order_book.sell_book_full)
    
    return liquidity_data

# Usage
trading_pair = Assets({"lovelace": 0, "token_policy": 0})
ob = GeniusYieldOrderBook.get_book(trading_pair, None)
liquidity = analyze_liquidity_depth(ob)

print("Buy-side Liquidity:")
for level in liquidity['buy_levels']:
    print(f"  {level['price']}: {level['quantity']} (cum: {level['cumulative']})")

print("Sell-side Liquidity:")
for level in liquidity['sell_levels']:
    print(f"  {level['price']}: {level['quantity']} (cum: {level['cumulative']})")
```

### Order Execution Simulation

```python
def simulate_trade_execution(
    order_book: GeniusYieldOrderBook,
    trade_amount: int,
    is_buy: bool = True
) -> dict:
    """Simulate executing a large trade against the order book."""
    
    if is_buy:
        orders = order_book.sell_book_full  # Buying hits sell orders
        side = "buy"
    else:
        orders = order_book.buy_book_full   # Selling hits buy orders
        side = "sell"
    
    remaining_amount = trade_amount
    executed_orders = []
    total_cost = 0
    
    for order in orders:
        if remaining_amount <= 0:
            break
            
        fill_amount = min(remaining_amount, order.quantity)
        order_cost = fill_amount * order.price
        
        executed_orders.append({
            'price': order.price,
            'quantity': fill_amount,
            'cost': order_cost
        })
        
        remaining_amount -= fill_amount
        total_cost += order_cost
    
    average_price = total_cost / (trade_amount - remaining_amount) if trade_amount > remaining_amount else 0
    
    return {
        'side': side,
        'requested_amount': trade_amount,
        'filled_amount': trade_amount - remaining_amount,
        'unfilled_amount': remaining_amount,
        'average_price': average_price,
        'total_cost': total_cost,
        'executed_orders': executed_orders,
        'fill_rate': (trade_amount - remaining_amount) / trade_amount if trade_amount > 0 else 0
    }

# Example: Simulate buying 10,000 tokens
trading_pair = Assets({"lovelace": 0, "token_policy": 0})
ob = GeniusYieldOrderBook.get_book(trading_pair, None)
trade_result = simulate_trade_execution(ob, 10000000, is_buy=True)

print(f"Trade Simulation Results:")
print(f"Fill Rate: {trade_result['fill_rate']:.2%}")
print(f"Average Price: {trade_result['average_price']:.6f}")
print(f"Total Cost: {trade_result['total_cost']}")
```

## Smart Contract Integration

### Order Creation and Management

```python
from pycardano import Address, TransactionBuilder, PlutusData

def create_genius_yield_order(
    owner_address: Address,
    offered_asset: str,
    offered_amount: int,
    asked_asset: str,
    price_numerator: int,
    price_denominator: int,
    start_time: int = None,
    end_time: int = None
) -> PlutusData:
    """Create a GeniusYield order datum."""
    
    # This would create the actual order datum
    # Implementation details depend on specific use case
    print(f"Creating order:")
    print(f"  Offering: {offered_amount} {offered_asset}")
    print(f"  Asking: {asked_asset}")
    print(f"  Price: {price_numerator}/{price_denominator}")
    print(f"  Time Window: {start_time} to {end_time}")
    
    # Return would be actual GeniusYieldOrder datum
    return None

# Example order creation
order_datum = create_genius_yield_order(
    owner_address=Address.from_bech32("addr1..."),
    offered_asset="lovelace",
    offered_amount=1000000000,  # 1000 ADA
    asked_asset="token_policy_id",
    price_numerator=500,  # 500 tokens per ADA
    price_denominator=1,
    start_time=None,  # Active immediately
    end_time=None     # No expiration
)
```

### Fee Structure Analysis

```python
def analyze_genius_yield_fees(order_version: str = "v1.1"):
    """Analyze GeniusYield fee structures."""
    
    fee_structure = {
        'v1': {
            'base_fee': 30,  # 0.3%
            'rounding': 'ceil',  # Round up for V1
            'calculation': 'fee = ceil(amount * 30 / 10000)'
        },
        'v1.1': {
            'base_fee': 30,  # 0.3%
            'rounding': 'floor',  # Floor for V1.1
            'calculation': 'fee = amount * 30 // 10000'
        }
    }
    
    version_data = fee_structure.get(order_version, fee_structure['v1.1'])
    
    print(f"GeniusYield {order_version.upper()} Fee Structure:")
    print(f"  Base Fee: {version_data['base_fee']}bp ({version_data['base_fee']/100}%)")
    print(f"  Rounding: {version_data['rounding']}")
    print(f"  Calculation: {version_data['calculation']}")
    
    # Example calculations for different amounts
    test_amounts = [1000000, 10000000, 100000000, 1000000000]
    print(f"\nFee Examples:")
    for amount in test_amounts:
        if order_version == "v1":
            fee = -(-amount * 30 // 10000)  # Ceiling division
        else:
            fee = amount * 30 // 10000
        print(f"  {amount/1000000} ADA -> {fee} lovelace fee ({fee/amount*100:.3f}%)")
    
    return version_data

# Analyze both versions
v1_fees = analyze_genius_yield_fees("v1")
print("\n" + "="*50)
v1_1_fees = analyze_genius_yield_fees("v1.1")
```

## Professional Trading Patterns

### Arbitrage Detection

```python
def detect_arbitrage_opportunities(
    genius_yield_book: GeniusYieldOrderBook,
    external_price: float,
    min_profit_threshold: float = 0.01  # 1% minimum profit
):
    """Detect arbitrage opportunities between GeniusYield and external markets."""
    
    opportunities = []
    
    if genius_yield_book.sell_book_full:
        best_sell = genius_yield_book.sell_book_full[0]
        if external_price > best_sell.price * (1 + min_profit_threshold):
            opportunities.append({
                'type': 'buy_genius_sell_external',
                'genius_price': best_sell.price,
                'external_price': external_price,
                'profit_percent': (external_price / best_sell.price - 1) * 100,
                'max_quantity': best_sell.quantity
            })
    
    if genius_yield_book.buy_book_full:
        best_buy = genius_yield_book.buy_book_full[0]
        if external_price < best_buy.price * (1 - min_profit_threshold):
            opportunities.append({
                'type': 'buy_external_sell_genius',
                'genius_price': best_buy.price,
                'external_price': external_price,
                'profit_percent': (best_buy.price / external_price - 1) * 100,
                'max_quantity': best_buy.quantity
            })
    
    return opportunities

# Example arbitrage detection
trading_pair = Assets({"lovelace": 0, "token_policy": 0})
gy_book = GeniusYieldOrderBook.get_book(trading_pair, None)
external_market_price = 0.125  # Example external price

arbitrage_ops = detect_arbitrage_opportunities(gy_book, external_market_price, 0.005)
for op in arbitrage_ops:
    print(f"Arbitrage Opportunity: {op['type']}")
    print(f"  Profit: {op['profit_percent']:.2f}%")
    print(f"  Max Quantity: {op['max_quantity']}")
```

### Order Book Health Monitoring

```python
def monitor_order_book_health(order_book: GeniusYieldOrderBook):
    """Monitor order book health and liquidity metrics."""
    
    health_metrics = {
        'total_orders': len(order_book.buy_book_full) + len(order_book.sell_book_full),
        'buy_orders': len(order_book.buy_book_full),
        'sell_orders': len(order_book.sell_book_full),
        'spread': None,
        'mid_price': None,
        'liquidity_imbalance': None,
        'order_concentration': None
    }
    
    if order_book.buy_book_full and order_book.sell_book_full:
        best_bid = order_book.buy_book_full[0].price
        best_ask = order_book.sell_book_full[0].price
        
        health_metrics['spread'] = best_ask - best_bid
        health_metrics['mid_price'] = (best_bid + best_ask) / 2
        health_metrics['spread_percent'] = health_metrics['spread'] / health_metrics['mid_price'] * 100
        
        # Calculate liquidity imbalance
        buy_liquidity = sum(order.quantity for order in order_book.buy_book_full)
        sell_liquidity = sum(order.quantity for order in order_book.sell_book_full)
        total_liquidity = buy_liquidity + sell_liquidity
        
        if total_liquidity > 0:
            health_metrics['liquidity_imbalance'] = abs(buy_liquidity - sell_liquidity) / total_liquidity
        
        # Calculate order concentration (top 3 orders as % of total)
        if len(order_book.buy_book_full) >= 3:
            top_buy_concentration = sum(order.quantity for order in order_book.buy_book_full[:3]) / buy_liquidity
            health_metrics['buy_concentration'] = top_buy_concentration
        
        if len(order_book.sell_book_full) >= 3:
            top_sell_concentration = sum(order.quantity for order in order_book.sell_book_full[:3]) / sell_liquidity
            health_metrics['sell_concentration'] = top_sell_concentration
    
    return health_metrics

# Example health monitoring
trading_pair = Assets({"lovelace": 0, "token_policy": 0})
gy_book = GeniusYieldOrderBook.get_book(trading_pair, None)
health = monitor_order_book_health(gy_book)

print("Order Book Health Metrics:")
for metric, value in health.items():
    if isinstance(value, float):
        print(f"  {metric}: {value:.4f}")
    else:
        print(f"  {metric}: {value}")
```

## Technical Implementation Details

### Contract Version Detection

```python
def detect_genius_yield_version(order: GeniusYieldOrderState) -> str:
    """Detect which version of GeniusYield contracts an order uses."""
    
    dex_nft = order.dex_nft.unit()
    
    if dex_nft.startswith("22f6999d4effc0ade05f6e1a70b702c65d6b3cdf0e301e4a8267f585"):
        return "v1"
    elif dex_nft.startswith("642c1f7bf79ca48c0f97239fcb2f3b42b92f2548184ab394e1e1e503"):
        return "v1.1"
    else:
        return "unknown"

# Example version detection
selector = GeniusYieldOrderState.pool_selector()
orders = backend.get_pool_utxos(**selector.model_dump())

version_counts = {"v1": 0, "v1.1": 0, "unknown": 0}
for order_info in orders[:10]:  # Sample first 10 orders
    order = GeniusYieldOrderState.model_validate(order_info.model_dump())
    version = detect_genius_yield_version(order)
    version_counts[version] += 1
    print(f"Order {order.pool_id[:16]}... -> {version}")

print(f"\nVersion Distribution: {version_counts}")
```

### Performance Optimization

```python
import asyncio
from typing import List, Dict

async def efficient_order_book_analysis(trading_pairs: List[Assets]) -> Dict:
    """Efficiently analyze multiple trading pairs in parallel."""
    
    async def analyze_pair(pair: Assets) -> tuple[Assets, dict]:
        # Simulate async order book fetching and analysis
        order_book = GeniusYieldOrderBook.get_book(pair, None)
        
        analysis = {
            'pair': pair,
            'buy_orders': len(order_book.buy_book_full),
            'sell_orders': len(order_book.sell_book_full),
            'spread': None,
            'liquidity': 0
        }
        
        if order_book.buy_book_full and order_book.sell_book_full:
            best_bid = order_book.buy_book_full[0].price
            best_ask = order_book.sell_book_full[0].price
            analysis['spread'] = best_ask - best_bid
            analysis['liquidity'] = sum(o.quantity for o in order_book.buy_book_full + order_book.sell_book_full)
        
        return pair, analysis
    
    # Execute analysis for all pairs in parallel
    tasks = [analyze_pair(pair) for pair in trading_pairs]
    results = await asyncio.gather(*tasks)
    
    return dict(results)

# Example usage
trading_pairs = [
    Assets({"lovelace": 0, "token1": 0}),
    Assets({"lovelace": 0, "token2": 0}),
    Assets({"lovelace": 0, "token3": 0}),
]

# analysis_results = await efficient_order_book_analysis(trading_pairs)
# print("Multi-pair Analysis Complete:", len(analysis_results), "pairs")
```

## Backend Support

| Feature | DBSync | BlockFrost | Ogmios/Kupo |
|---------|--------|------------|-------------|
| Order Book Data | ✅ | ✅ | ✅ |
| Order Execution | ✅ | ✅ | ✅ |
| V1 Orders | ✅ | ✅ | ✅ |
| V1.1 Orders | ✅ | ✅ | ✅ |
| Historical Data | ✅ | ❌ | ❌ |
| Real-time Updates | ✅ | ✅ | ✅ |

!!! note "Backend Limitations"
    All order book functionality works across all backends. Historical order analysis is only available with DBSync backend.

## Advanced Configuration

### Order Book Optimization

```python
# GeniusYield recommends maximum 3 orders per transaction due to memory limits
def optimize_order_execution(order_book: GeniusYieldOrderBook, max_orders: int = 3):
    """Optimize order execution by limiting orders per transaction."""
    
    # Limit order book depth for efficient execution
    order_book.sell_book_full = order_book.sell_book_full[:max_orders]
    order_book.buy_book_full = order_book.buy_book_full[:max_orders]
    
    print(f"Optimized order book:")
    print(f"  Buy orders: {len(order_book.buy_book_full)}")
    print(f"  Sell orders: {len(order_book.sell_book_full)}")
    
    return order_book

# Usage
trading_pair = Assets({"lovelace": 0, "token_policy": 0})
ob = GeniusYieldOrderBook.get_book(trading_pair, None)
optimized_ob = optimize_order_execution(ob, max_orders=3)
```

## See Also

- [Order Book Base Classes](order_book_base.md) - Understanding order book architecture
- [AMM vs Order Book](types.md) - Comparing different DEX models
- [Getting Started](index.md) - Basic setup and configuration
- [Professional Trading](axo.md) - Alternative order book implementation (deprecated)

::: charli3_dendrite.dexs.ob.geniusyield
