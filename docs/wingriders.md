# WingRiders

WingRiders is a high-performance AMM DEX on Cardano designed for speed and efficiency, offering both V1 and V2 implementations with support for Constant Product Pools (CPP) and Stable Swap Pools (SSP). Known for delivering deep liquidity and lightning-fast transaction speeds, WingRiders excels at handling large volume trading with minimal slippage.

## Pool Architecture Overview

WingRiders provides a sophisticated dual-version architecture:

### V1 Implementation
- **Constant Product Pools (CPP)**: Traditional AMM pools with proven x * y = k formula
- **Stable Swap Pools (SSP)**: Specialized pools for stablecoin and similar-valued asset pairs
- **PlutusV1 Scripts**: Efficient smart contract execution

### V2 Implementation  
- **Enhanced CPP Pools**: Improved capital efficiency and dynamic fee structures
- **Advanced SSP Pools**: Configurable amplification and scaling factors
- **PlutusV2 Scripts**: Next-generation smart contract capabilities
- **Dynamic Fee System**: Adaptive fees based on pool conditions

## Supported Pool Classes

| Pool Class | Version | Type | Description |
|------------|---------|------|-------------|
| `WingRidersCPPState` | V1 | CPP | Traditional constant product pools |
| `WingRidersSSPState` | V1 | SSP | Stable swap pools for similar assets |
| `WingRidersV2CPPState` | V2 | CPP | Enhanced constant product with dynamic fees |
| `WingRidersV2SSPState` | V2 | SSP | Advanced stable pools with configurable parameters |

## Key Features

### V1 Pools
- **Fixed Fee Structure**: 0.35% for CPP, 0.06% for SSP
- **Efficient Routing**: Optimized for single and multi-hop swaps
- **Proven Architecture**: Battle-tested pool mechanics
- **ADA Optimization**: Special handling for ADA-based pools

### V2 Pools
- **Dynamic Fees**: Adaptive fee rates based on market conditions
- **Enhanced Treasuries**: Multiple treasury pools for protocol sustainability
- **Improved Capital Efficiency**: Better utilization of liquidity
- **Advanced Order Types**: Support for complex trading strategies

### Stable Swap Pools (SSP)
- **Low Slippage**: Specialized curves for similar-valued assets
- **Configurable Amplification**: Adjustable parameters for different asset pairs
- **Scaling Factors**: Custom decimal handling for precise calculations
- **Stablecoin Optimized**: Perfect for USD-pegged and similar assets

## Basic Usage

### V1 Constant Product Pools

```python
from charli3_dendrite import WingRidersCPPState
from charli3_dendrite.backend import get_backend

# Get V1 CPP pool data
backend = get_backend()
selector = WingRidersCPPState.pool_selector()
pools = backend.get_pool_utxos(**selector.model_dump())

# Process pool information
for pool_info in pools:
    pool = WingRidersCPPState.model_validate(pool_info.model_dump())
    print(f"Pool ID: {pool.pool_id}")
    print(f"Assets: {pool.unit_a} / {pool.unit_b}")
    print(f"TVL: {pool.tvl}")
    print(f"Fee: {pool.fee}bp (0.35%)")
    print(f"Price: {pool.price}")
```

### V1 Stable Swap Pools

```python
from charli3_dendrite import WingRidersSSPState

# Get V1 SSP pool data for stablecoin pairs
selector = WingRidersSSPState.pool_selector()
pools = backend.get_pool_utxos(**selector.model_dump())

for pool_info in pools:
    pool = WingRidersSSPState.model_validate(pool_info.model_dump())
    print(f"Stable Pool: {pool.pool_id}")
    print(f"Fee: {pool.fee}bp (0.06%)")
    print(f"Assets: {pool.unit_a} / {pool.unit_b}")
    
    # Low slippage calculation for stable assets
    from pycardano import Assets
    stable_input = Assets({"usdc_policy": 1000000})  # 1 USDC
    stable_output, slippage = pool.get_amount_out(stable_input)
    print(f"Slippage: {slippage:.6f}%")
```

### V2 Enhanced Pools

```python
from charli3_dendrite import WingRidersV2CPPState, WingRidersV2SSPState

# Get V2 CPP pools with dynamic fees
v2_selector = WingRidersV2CPPState.pool_selector()
v2_pools = backend.get_pool_utxos(**v2_selector.model_dump())

for pool_info in v2_pools:
    pool = WingRidersV2CPPState.model_validate(pool_info.model_dump())
    print(f"V2 Pool: {pool.pool_id}")
    print(f"Dynamic Fee: {pool.fee}bp")
    print(f"Script: {pool.default_script_class()}")

# Get V2 SSP pools with advanced configuration
v2_ssp_selector = WingRidersV2SSPState.pool_selector()
v2_ssp_pools = backend.get_pool_utxos(**v2_ssp_selector.model_dump())

for pool_info in v2_ssp_pools:
    pool = WingRidersV2SSPState.model_validate(pool_info.model_dump())
    print(f"V2 Stable Pool: {pool.pool_id}")
    print(f"Asset Multipliers: {pool.asset_mulitipliers}")
```

## Advanced Features

### Version Comparison
```python
# Compare V1 vs V2 pool features
from charli3_dendrite import WingRidersCPPState, WingRidersV2CPPState

# V1 Pool Analysis
v1_pool = WingRidersCPPState.model_validate(v1_pool_data)
print(f"V1 Fixed Fee: {v1_pool.fee}bp")
print(f"V1 DEX: {v1_pool.dex()}")

# V2 Pool Analysis
v2_pool = WingRidersV2CPPState.model_validate(v2_pool_data)
print(f"V2 Dynamic Fee: {v2_pool.fee}bp")
print(f"V2 DEX: {v2_pool.dex()}")
print(f"V2 Script Class: {v2_pool.default_script_class()}")
```

### Multi-Pool Trading Strategy
```python
# Query all WingRiders pool types for comprehensive trading
wing_riders_pools = [
    WingRidersCPPState,      # V1 CPP
    WingRidersSSPState,      # V1 SSP
    WingRidersV2CPPState,    # V2 CPP
    WingRidersV2SSPState,    # V2 SSP
]

pool_data = {}
for pool_class in wing_riders_pools:
    selector = pool_class.pool_selector()
    pools = backend.get_pool_utxos(**selector.model_dump())
    
    pool_data[pool_class.__name__] = {
        'count': len(pools),
        'pools': pools,
        'version': 'V2' if 'V2' in pool_class.__name__ else 'V1',
        'type': 'SSP' if 'SSP' in pool_class.__name__ else 'CPP'
    }
    
    print(f"{pool_class.__name__}: {len(pools)} pools")
```

### Dynamic Fee Analysis
```python
# Analyze fee structures across versions
def analyze_wing_riders_fees():
    v1_cpp_fee = WingRidersCPPState.fee  # 35bp (0.35%)
    v1_ssp_fee = WingRidersSSPState.fee  # 6bp (0.06%)
    
    print("V1 Fee Structure:")
    print(f"  CPP: {v1_cpp_fee}bp (0.35%)")
    print(f"  SSP: {v1_ssp_fee}bp (0.06%)")
    
    # V2 fees are dynamic and calculated from pool datum
    print("\nV2 Fee Structure:")
    print("  Dynamic fees based on:")
    print("  - swap_fee_in_basis")
    print("  - protocol_fee_in_basis") 
    print("  - project_fee_in_basis")
    print("  - Combined and normalized per pool")

analyze_wing_riders_fees()
```

### Batcher Fee Optimization
```python
# WingRiders dynamic batcher fee calculation
from pycardano import Assets

def calculate_wing_riders_fees(ada_amount: int):
    """Calculate WingRiders batcher fees based on ADA amount."""
    pool = WingRidersV2CPPState()  # Example pool
    
    if ada_amount <= 250_000_000:  # <= 250 ADA
        return Assets(lovelace=850_000)  # 0.85 ADA
    elif ada_amount <= 500_000_000:  # <= 500 ADA
        return Assets(lovelace=1_500_000)  # 1.5 ADA
    else:
        return Assets(lovelace=2_000_000)  # 2.0 ADA

# Example fee calculations
test_amounts = [100_000_000, 250_000_000, 500_000_000, 1_000_000_000]
for amount in test_amounts:
    fee = calculate_wing_riders_fees(amount)
    print(f"{amount/1_000_000} ADA -> {fee['lovelace']/1_000_000} ADA fee")
```

## Pool Identification

### V1 Pool Policies

**CPP Pools:**
- Pool Policy: `026a18d04a0c642759bb3d83b12e3344894e5c1c7b2aeb1a2113a570`
- DEX Policy: `026a18d04a0c642759bb3d83b12e3344894e5c1c7b2aeb1a2113a5704c`

**SSP Pools:**
- Pool Policy: `980e8c567670d34d4ec13a0c3b6de6199f260ae5dc9dc9e867bc5c93`
- DEX Policy: `980e8c567670d34d4ec13a0c3b6de6199f260ae5dc9dc9e867bc5c934c`

### V2 Pool Policies

**V2 CPP & SSP:**
- Pool Policy: `6fdc63a1d71dc2c65502b79baae7fb543185702b12c3c5fb639ed737`
- DEX Policy: `6fdc63a1d71dc2c65502b79baae7fb543185702b12c3c5fb639ed7374c`

## Migration Guide

### From V1 to V2
```python
# V1 to V2 Migration Example
from charli3_dendrite import WingRidersCPPState, WingRidersV2CPPState

# V1 Pool Query
v1_selector = WingRidersCPPState.pool_selector()
v1_pools = backend.get_pool_utxos(**v1_selector.model_dump())

# V2 Equivalent
v2_selector = WingRidersV2CPPState.pool_selector()
v2_pools = backend.get_pool_utxos(**v2_selector.model_dump())

print("Migration Benefits:")
print("✅ Dynamic fees instead of fixed rates")
print("✅ PlutusV2 script efficiency")
print("✅ Enhanced treasury management")
print("✅ Better capital utilization")
```

### SSP Configuration Migration
```python
# V1 SSP to V2 SSP Migration
from charli3_dendrite import WingRidersSSPState, WingRidersV2SSPState

v1_ssp = WingRidersSSPState.model_validate(v1_ssp_data)
v2_ssp = WingRidersV2SSPState.model_validate(v2_ssp_data)

print("SSP Enhancements:")
print(f"V1 Fixed Multipliers: [1, 1]")
print(f"V2 Dynamic Multipliers: {v2_ssp.asset_mulitipliers}")
print("✅ Configurable scaling factors")
print("✅ Precise decimal handling")
```

## Performance Optimization

### Batch Pool Queries
```python
import asyncio
from typing import Dict, List

async def get_all_wing_riders_pools() -> Dict[str, List]:
    """Efficiently query all WingRiders pool types."""
    pool_classes = [
        WingRidersCPPState,
        WingRidersSSPState,
        WingRidersV2CPPState,
        WingRidersV2SSPState,
    ]
    
    # Create async tasks for parallel execution
    tasks = []
    for pool_class in pool_classes:
        selector = pool_class.pool_selector()
        task = backend.get_pool_utxos(**selector.model_dump())
        tasks.append((pool_class.__name__, task))
    
    # Execute all queries in parallel
    results = {}
    for name, task in tasks:
        pools = await task
        results[name] = pools
    
    return results

# Usage
all_pools = await get_all_wing_riders_pools()
for pool_type, pools in all_pools.items():
    print(f"{pool_type}: {len(pools)} pools")
```

### Optimal Pool Selection
```python
def find_best_wing_riders_pool(token_a: str, token_b: str, amount: int):
    """Find the best WingRiders pool for a specific trade."""
    
    # Check V2 pools first for better efficiency
    v2_cpp_pools = backend.get_pool_utxos(**WingRidersV2CPPState.pool_selector().model_dump())
    v2_ssp_pools = backend.get_pool_utxos(**WingRidersV2SSPState.pool_selector().model_dump())
    
    best_pool = None
    best_output = 0
    
    # Analyze V2 pools (preferred)
    for pool_data in v2_cpp_pools + v2_ssp_pools:
        # ... pool analysis logic
        pass
    
    # Fallback to V1 if needed
    if not best_pool:
        v1_pools = backend.get_pool_utxos(**WingRidersCPPState.pool_selector().model_dump())
        # ... V1 analysis
    
    return best_pool
```

## Backend Support

| Feature | DBSync | BlockFrost | Ogmios/Kupo |
|---------|--------|------------|-------------|
| V1 CPP Pools | ✅ | ✅ | ✅ |
| V1 SSP Pools | ✅ | ✅ | ✅ |
| V2 CPP Pools | ✅ | ✅ | ✅ |
| V2 SSP Pools | ✅ | ✅ | ✅ |
| Dynamic Fees | ✅ | ✅ | ✅ |
| Historical Data | ✅ | ❌ | ❌ |

!!! note "Backend Limitations"
    All current pool data and trading functionality works across all backends. Historical order data is only available with DBSync backend.

## Troubleshooting

### Common Issues

**Pool Not Found:**
```python
try:
    pool = WingRidersV2CPPState.model_validate(pool_data)
except NotAPoolError:
    print("Invalid DEX NFT or pool configuration")
    # Check if using correct pool class for the data
```

**Fee Calculation Errors:**
```python
# Ensure correct fee calculation for V2 pools
pool_datum = pool.pool_datum
calculated_fee = (
    pool_datum.swap_fee_in_basis +
    pool_datum.protocol_fee_in_basis +
    pool_datum.project_fee_in_basis
) * 10000 / pool_datum.fee_basis
```

## See Also

- [AMM Base Classes](amm_base.md) - Understanding the AMM architecture
- [Minswap Documentation](minswap.md) - Alternative V1+V2 implementation
- [Stable Swap Mechanics](types.md) - Detailed stable pool information
- [Getting Started](index.md) - Basic setup and configuration

::: charli3_dendrite.dexs.amm.wingriders
