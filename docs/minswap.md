# Minswap

Minswap is the most comprehensive and feature-rich DEX implementation in Charli3 Dendrite, offering multiple pool versions, stable swap pools, and advanced trading features. As a community-driven AMM DEX on Cardano, Minswap provides both beginner-friendly interfaces and sophisticated tools for advanced DeFi strategies.

## Pool Types Overview

Minswap supports multiple pool architectures, each optimized for different use cases:

### V1 Constant Product Pools (CPP)
Traditional automated market maker pools following the constant product formula (x * y = k).

### V2 Constant Product Pools (CPP) 
Enhanced version with improved efficiency, dynamic fees, and better capital utilization.

### Stable Swap Pools (SSP)
Specialized pools optimized for trading between assets of similar value, offering significantly reduced slippage for stablecoin pairs.

## Supported Pool Classes

| Pool Class | Description | Use Case |
|------------|-------------|----------|
| `MinswapCPPState` | V1 Constant Product Pools | General token swaps |
| `MinswapV2CPPState` | V2 Constant Product Pools | Enhanced efficiency and dynamic fees |
| `MinswapDJEDiUSDStableState` | DJED/iUSD Stable Pool | Stablecoin swaps with minimal slippage |
| `MinswapDJEDUSDCStableState` | DJED/USDC Stable Pool | DJED/USDC optimized trading |
| `MinswapDJEDUSDMStableState` | DJED/USDM Stable Pool | DJED/USDM stable pair |
| `MinswapiUSDUSDMStableState` | iUSD/USDM Stable Pool | iUSD/USDM efficient swaps |
| `MinswapUSDAUSDMStableState` | USDA/USDM Stable Pool | USDA/USDM stable trading |
| `MinswapiUSDUSDCStableState` | iUSD/USDC Stable Pool | iUSD/USDC optimized pair |

## Key Features

### V1 Pools
- **Standard AMM Logic**: Proven constant product formula
- **Fixed Fee Structure**: 0.3% trading fee
- **MIN Token Benefits**: Reduced batcher fees with MIN holdings
- **Reliable Performance**: Battle-tested pool architecture

### V2 Pools  
- **Dynamic Fees**: Configurable fee rates for each direction
- **Enhanced Efficiency**: Improved capital utilization
- **Better Routing**: Optimized for multi-hop swaps
- **PlutusV2 Scripts**: Advanced smart contract capabilities

### Stable Pools
- **Minimal Slippage**: Specialized curve for similar-valued assets
- **Amplification Factor**: Configurable amplification for different pairs
- **Stablecoin Optimized**: Perfect for USD-pegged assets
- **1% Fee Structure**: Lower fees for stable asset trades

## Basic Usage

### V1 Constant Product Pools

```python
from charli3_dendrite import MinswapCPPState
from charli3_dendrite.backend import get_backend

# Get V1 pool data
backend = get_backend()
selector = MinswapCPPState.pool_selector()
pools = backend.get_pool_utxos(**selector.model_dump())

# Process pool information
for pool_info in pools:
    pool = MinswapCPPState.model_validate(pool_info.model_dump())
    print(f"Pool ID: {pool.pool_id}")
    print(f"Assets: {pool.unit_a} / {pool.unit_b}")
    print(f"TVL: {pool.tvl}")
    print(f"Price A->B: {pool.price[0]}")
    print(f"Fee: {pool.fee}bp")
```

### V2 Enhanced Pools

```python
from charli3_dendrite import MinswapV2CPPState

# Get V2 pool data with dynamic fees
selector = MinswapV2CPPState.pool_selector()
pools = backend.get_pool_utxos(**selector.model_dump())

for pool_info in pools:
    pool = MinswapV2CPPState.model_validate(pool_info.model_dump())
    print(f"Pool ID: {pool.pool_id}")
    print(f"Dynamic Fees: {pool.fee}")  # [fee_a, fee_b]
    print(f"LP Token Policy: {pool.lp_policy()}")
```

### Stable Swap Pools

```python
from charli3_dendrite import MinswapDJEDiUSDStableState

# Get stable pool data for DJED/iUSD
selector = MinswapDJEDiUSDStableState.pool_selector()
pools = backend.get_pool_utxos(**selector.model_dump())

for pool_info in pools:
    pool = MinswapDJEDiUSDStableState.model_validate(pool_info.model_dump())
    print(f"Stable Pool: {pool.pool_id}")
    print(f"Amplification: {pool.amp}")
    print(f"Stable Fee: {pool.fee}%")
    
    # Calculate swap with minimal slippage
    from pycardano import Assets
    input_assets = Assets({"djed_policy_id": 1000000})  # 1 DJED
    output_assets, slippage = pool.get_amount_out(input_assets)
    print(f"Slippage: {slippage:.4f}%")
```

## Advanced Features

### Multi-Version Support
```python
# Query all Minswap pool types
from charli3_dendrite import (
    MinswapCPPState, MinswapV2CPPState,
    MinswapDJEDiUSDStableState, MinswapDJEDUSDCStableState
)

all_minswap_pools = [
    MinswapCPPState,           # V1 CPP
    MinswapV2CPPState,         # V2 CPP  
    MinswapDJEDiUSDStableState,  # DJED/iUSD Stable
    MinswapDJEDUSDCStableState,  # DJED/USDC Stable
    # Add other stable pools as needed
]

for pool_class in all_minswap_pools:
    selector = pool_class.pool_selector()
    pools = backend.get_pool_utxos(**selector.model_dump())
    print(f"{pool_class.__name__}: {len(pools)} pools")
```

### Fee Analysis
```python
# Compare fees across pool types
v1_pool = MinswapCPPState.model_validate(v1_pool_data)
v2_pool = MinswapV2CPPState.model_validate(v2_pool_data)
stable_pool = MinswapDJEDiUSDStableState.model_validate(stable_pool_data)

print(f"V1 Fee: {v1_pool.fee}bp (0.3%)")
print(f"V2 Fees: {v2_pool.fee}bp (dynamic)")
print(f"Stable Fee: {stable_pool.fee}% (1%)")
```

### LP Token Management
```python
# Access LP token information
v1_lp_policy = MinswapCPPState.lp_policy()
v2_lp_policy = MinswapV2CPPState.lp_policy()

print(f"V1 LP Policy: {v1_lp_policy}")
print(f"V2 LP Policy: {v2_lp_policy}")

# Get pool-specific LP tokens
pool = MinswapV2CPPState.model_validate(pool_data)
lp_token_unit = pool.lp_tokens.unit()
```

## Stable Pool Pairs

### Available Stable Pairs

| Pool Class | Asset A | Asset B | Amplification | Decimals |
|------------|---------|---------|---------------|----------|
| `MinswapDJEDiUSDStableState` | DJED | iUSD | Variable | [6, 6] |
| `MinswapDJEDUSDCStableState` | DJED | USDC | Variable | [6, 8] |
| `MinswapDJEDUSDMStableState` | DJED | USDM | Variable | [6, 6] |
| `MinswapiUSDUSDMStableState` | iUSD | USDM | Variable | [6, 6] |
| `MinswapUSDAUSDMStableState` | USDA | USDM | Variable | [6, 6] |
| `MinswapiUSDUSDCStableState` | iUSD | USDC | Variable | [6, 8] |

### Stable Pool Usage
```python
# Example: Trading on DJED/USDC stable pool
from charli3_dendrite import MinswapDJEDUSDCStableState
from pycardano import Assets

pool = MinswapDJEDUSDCStableState.model_validate(pool_data)

# Swap 100 DJED for USDC with minimal slippage
djed_input = Assets({"djed_policy": 100000000})  # 100 DJED (6 decimals)
usdc_output, slippage = pool.get_amount_out(djed_input)

print(f"Input: 100 DJED")
print(f"Output: {usdc_output} USDC")
print(f"Slippage: {slippage:.6f}%")
```

## Pool Identification

### Policy IDs and Addresses

**V1 Pools:**
- Pool Policy: `0be55d262b29f564998ff81efe21bdc0022621c12f15af08d0f2ddb1`
- LP Policy: `e4214b7cce62ac6fbba385d164df48e157eae5863521b4b67ca71d86`
- DEX Policy: `13aa2accf2e1561723aa26871e071fdf32c867cff7e7d50ad470d62f`

**V2 Pools:**
- LP/DEX Policy: `f5808c2c990d86da54bfc97d89cee6efa20cd8461616359478d96b4c`

**Stable Pools:** Each stable pool has unique policy IDs for identification.

## Backend Support

All Minswap functionality is fully supported across all backends:

| Feature | DBSync | BlockFrost | Ogmios/Kupo |
|---------|--------|------------|-------------|
| Pool Data | ✅ | ✅ | ✅ |
| V1 Pools | ✅ | ✅ | ✅ |
| V2 Pools | ✅ | ✅ | ✅ |
| Stable Pools | ✅ | ✅ | ✅ |
| Historical Data | ✅ | ❌ | ❌ |

!!! note "Backend Limitations"
    BlockFrost and Ogmios/Kupo backends don't support historical order data methods, but all pool data and current state functionality works perfectly.

## Migration Guide

### From V1 to V2
```python
# V1 pool query
v1_selector = MinswapCPPState.pool_selector()
v1_pools = backend.get_pool_utxos(**v1_selector.model_dump())

# V2 equivalent
v2_selector = MinswapV2CPPState.pool_selector()
v2_pools = backend.get_pool_utxos(**v2_selector.model_dump())

# V2 offers dynamic fees and better efficiency
for pool_info in v2_pools:
    pool = MinswapV2CPPState.model_validate(pool_info.model_dump())
    print(f"Dynamic fees: {pool.fee}")
```

## Performance Optimization

### Batch Pool Queries
```python
# Efficiently query multiple pool types
import asyncio

async def get_all_minswap_pools():
    pool_types = [
        MinswapCPPState, MinswapV2CPPState,
        MinswapDJEDiUSDStableState, MinswapDJEDUSDCStableState
    ]
    
    tasks = []
    for pool_type in pool_types:
        selector = pool_type.pool_selector()
        task = backend.get_pool_utxos(**selector.model_dump())
        tasks.append(task)
    
    results = await asyncio.gather(*tasks)
    return dict(zip(pool_types, results))
```

## See Also

- [AMM Base Classes](amm_base.md) - Understanding the AMM architecture
- [Getting Started](index.md) - Basic setup and configuration
- [Stable Swap Pools](types.md) - Detailed stable pool mechanics
- [WingRiders Documentation](wingriders.md) - Alternative V1+V2 DEX implementation

::: charli3_dendrite.dexs.amm.minswap
