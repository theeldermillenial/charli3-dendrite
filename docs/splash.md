# Splash

!!! info "Implementation Status"
    **Current Implementation**: Splash allows direct swaps against their pool contracts, and this is the only functionality currently implemented in the library. Users can perform bidirectional swaps directly with Splash pools.

!!! warning "Incomplete Pool Support"
    **Not all Splash pool types are implemented yet**. Specifically, **royalty pools have not been implemented** in the current version of the library. Only standard AMM pools are supported at this time.

Splash is a revolutionary bidirectional swap protocol on Cardano that fundamentally reimagines how automated market makers can operate. Unlike traditional AMMs where you need separate swap transactions for each direction, Splash enables seamless bidirectional swaps where users can exchange assets in either direction through a single, unified interface.

## Pool Types

### Constant Product Pools (CPP)
Standard automated market maker pools following the constant product formula (x * y = k) for efficient token swaps.

### Stable Swap Pools (SSP)  
Specialized pools optimized for trading between assets of similar value, offering reduced slippage for stablecoin and similar asset pairs.

### Bidirectional Pools
Unique to Splash, these pools enable advanced trading strategies with enhanced liquidity management and optimized swap execution in both directions.

## Key Features

- **Advanced Pool Architecture**: Multiple pool types for different trading scenarios
- **Bidirectional Swaps**: Innovative swap mechanisms for optimal trade execution
- **Flexible Liquidity Management**: Sophisticated tools for liquidity providers
- **Optimized Trading**: Enhanced algorithms for better price discovery and reduced slippage

## Basic Usage

```python
from charli3_dendrite import SplashCPPState, SplashSSPState, SplashCPPBidirState
from charli3_dendrite.backend import get_backend

# Get Splash CPP pools
backend = get_backend()
selector = SplashCPPState.pool_selector()
pools = backend.get_pool_utxos(**selector.model_dump())

# Process pool data
for pool_info in pools:
    pool = SplashCPPState.model_validate(pool_info.model_dump())
    print(f"Pool TVL: {pool.tvl}")
    print(f"Pool Price: {pool.price}")
```

## Advanced Features

- **Multi-Pool Architecture**: Support for CPP, SSP, and bidirectional pool configurations
- **Optimized Routing**: Advanced algorithms for finding optimal swap paths
- **Enhanced Liquidity**: Sophisticated pool management for improved capital efficiency
- **Flexible Trading**: Bidirectional capabilities enable advanced trading strategies

## Backend Limitations

!!! note "Backend Support"
    All Splash functionality is supported across DBSync, BlockFrost, and Ogmios/Kupo backends.

## See Also

- [AMM Base Classes](amm_base.md) - Understanding the AMM architecture
- [Getting Started](index.md) - Basic setup and configuration
- [Pool Types](types.md) - Detailed information about different pool implementations

::: charli3_dendrite.dexs.amm.splash 