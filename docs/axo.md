# Axo (DEPRECATED)

!!! warning "Deprecation Notice"
    **Axo has left the Cardano ecosystem** and is no longer actively supported. The Axo implementation in Charli3 Dendrite is maintained for reference purposes only and will be removed in a future version.
    
    **Current Status:**
    - Implementation exists but is commented out in package exports
    - No longer recommended for new projects
    - Existing integrations should migrate to alternative DEXs
    
    **Alternatives:** Consider using [GeniusYield](geniusyield.md) for order book functionality or other [supported AMM DEXs](index.md#supported-dexs).

---

**Axo** was an advanced order book DEX on Cardano designed for serious traders, offering customizable strategies and high-performance order execution for both retail and institutional users.

## Key Features (Historical Reference)

- **Advanced Trading Interface**: Professional-grade order book functionality
- **Customizable Strategies**: Flexible order types and trading algorithms
- **High Performance**: Optimized execution for large volume trading
- **Institutional Support**: Features designed for professional trading operations

## Order Book Architecture

Axo implemented a sophisticated on-chain order book model that enabled:

- Direct order placement and matching
- Advanced order types and market making capabilities
- Professional trading interface with complex order management
- Comprehensive price and liquidity tracking

## Technical Implementation

!!! note "Reference Only"
    This technical information is preserved for reference. Do not use in new projects.

### Basic Usage Pattern (Historical)

```python
# NOTE: This code is for reference only - Axo is deprecated
from charli3_dendrite.dexs.ob.axo import AxoOBMarketState
from charli3_dendrite.backend import get_backend

# This functionality is no longer available
backend = get_backend()
# selector = AxoOBMarketState.pool_selector()  # Not exported
# pools = backend.get_pool_utxos(**selector.model_dump())
```

::: charli3_dendrite.dexs.ob.axo 