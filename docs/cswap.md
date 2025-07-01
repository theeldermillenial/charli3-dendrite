# CSwap

CSwap is a community-focused automated market maker (AMM) DEX on Cardano that specializes in ADA-paired trading with innovative pool NFT management. Built with simplicity and efficiency in mind, CSwap provides accessible DeFi experiences while maintaining robust security through its beacon token system and ADA-only pair restrictions.

## Architecture Overview

CSwap's distinctive design focuses on ADA-paired liquidity and efficient pool management:

### Core Features
- **ADA-Only Pairs**: All pools must contain ADA, ensuring direct access to Cardano's native currency
- **Pool NFT System**: Beacon tokens with name "c" for secure pool identification and validation
- **Constant Product Formula**: Traditional AMM mechanics (x * y = k) with ADA optimization
- **Community Focused**: Designed for accessible DeFi participation

## Pool Architecture

| Pool Class | Description | Key Features |
|------------|-------------|--------------|
| `CSwapCPPState` | ADA-paired constant product pools | Pool NFT validation, ADA-only restrictions, maintenance fee handling |

## Key Features

### ADA-Focused Design
- **Native Currency Priority**: All pools paired with ADA for maximum accessibility
- **Direct Price Discovery**: Clear ADA-based pricing for all supported tokens
- **Simplified Trading**: Reduced complexity through ADA-only pair restrictions
- **Capital Efficiency**: Concentrated liquidity in ADA pairs

### Pool NFT System
- **Beacon Token Management**: Pool NFTs with name "c" for secure identification
- **Variable Policy IDs**: Each pool has unique policy while maintaining consistent token names

### Fee Structure
- **Batcher Fee**: 690,000 lovelace (0.69 ADA) for transaction processing

## Basic Usage

### Standard ADA Pair Trading

```python
from charli3_dendrite import CSwapCPPState
from charli3_dendrite.backend import get_backend
from charli3_dendrite.dataclasses.models import Assets

# Get CSwap pool data
backend = get_backend()
selector = CSwapCPPState.pool_selector()
pools = backend.get_pool_utxos(**selector.model_dump())

# Process ADA-paired pools
for pool_info in pools:
    pool = CSwapCPPState.model_validate(pool_info.model_dump())
    print(f"Pool ID: {pool.pool_id}")
    print(f"ADA Pair: {pool.unit_a} / {pool.unit_b}")
    print(f"TVL: {pool.tvl}")
    print(f"Fee: {pool.fee}bp")
    print(f"DEX: {pool.dex()}")
```

### ADA Swap Calculations

```python
def calculate_ada_swap(pool: CSwapCPPState, ada_amount: int):
    """Calculate swap output for ADA input on CSwap."""
    
    # Validate this is an ADA pair
    if "lovelace" not in [pool.unit_a, pool.unit_b]:
        raise ValueError("CSwap only supports ADA pairs")
    
    # Create ADA input asset
    ada_input = Assets(lovelace=ada_amount)
    
    # Calculate swap output
    output_assets, price_impact = pool.get_amount_out(ada_input)
    
    print(f"💰 CSwap ADA Swap Analysis:")
    print(f"   Input: {ada_amount / 1_000_000:.6f} ADA")
    print(f"   Output: {output_assets.quantity():,} {output_assets.unit()}")
    print(f"   Price Impact: {price_impact:.4%}")
    print(f"   Pool Fee: {pool.fee}bp")
    print(f"   ADA Reserve: {pool.reserve_a:,} lovelace")
    print(f"   Token Reserve: {pool.reserve_b:,}")
    
    return output_assets, price_impact

# Example: Swap 1 ADA for tokens
swap_result = calculate_ada_swap(cswap_pool, 1_000_000)  # 1 ADA
```

### Pool NFT Validation

```python
def validate_cswap_pool_nft(pool_data: dict):
    """Validate CSwap pool NFT according to beacon token specifications."""
    
    # Extract pool NFT using CSwap's built-in method
    try:
        pool_nft = CSwapCPPState.extract_pool_nft(pool_data)
        
        print("✅ CSwap Pool NFT Validation:")
        print(f"   NFT Unit: {pool_nft.unit()}")
        print(f"   Quantity: {pool_nft.quantity()}")
        print(f"   Token Name: {pool_nft.unit()[56:]}")  # Should be "63" (hex for "c")
        
        # Validate token name is "c"
        if pool_nft.unit()[56:] == "63":  # "c" in hex
            print("   ✅ Token name 'c' validated")
        else:
            print("   ❌ Invalid token name (should be 'c')")
        
        # Validate quantity is exactly 1
        if pool_nft.quantity() == 1:
            print("   ✅ Quantity of 1 validated")
        else:
            print("   ❌ Invalid quantity (should be 1)")
        
        return pool_nft
        
    except Exception as e:
        print(f"❌ Pool NFT validation failed: {e}")
        return None

# Validate pool NFT
pool_nft = validate_cswap_pool_nft(pool_utxo_data)
```

## Advanced Features

### ADA Pair Discovery

```python
def discover_ada_pairs():
    """Discover all available ADA pairs on CSwap."""
    
    # Get all CSwap pools
    selector = CSwapCPPState.pool_selector()
    pools = backend.get_pool_utxos(**selector.model_dump())
    
    ada_pairs = {
        'pairs': [],
        'total_tvl': 0,
        'unique_tokens': set()
    }
    
    for pool_info in pools:
        try:
            pool = CSwapCPPState.model_validate(pool_info.model_dump())
            
            # Identify the non-ADA token
            if pool.unit_a == "lovelace":
                token_unit = pool.unit_b
                ada_reserve = pool.reserve_a
                token_reserve = pool.reserve_b
            else:
                token_unit = pool.unit_a
                ada_reserve = pool.reserve_b
                token_reserve = pool.reserve_a
            
            ada_pairs['pairs'].append({
                'token': token_unit,
                'ada_reserve': ada_reserve,
                'token_reserve': token_reserve,
                'tvl': pool.tvl,
                'pool_id': pool.pool_id
            })
            
            ada_pairs['total_tvl'] += pool.tvl
            ada_pairs['unique_tokens'].add(token_unit)
            
        except Exception as e:
            print(f"Error processing pool: {e}")
    
    print("🏆 CSwap ADA Pair Discovery:")
    print(f"   Total Pairs: {len(ada_pairs['pairs'])}")
    print(f"   Unique Tokens: {len(ada_pairs['unique_tokens'])}")
    print(f"   Total TVL: {ada_pairs['total_tvl']:,} lovelace")
    print(f"   Average Pool Size: {ada_pairs['total_tvl'] // len(ada_pairs['pairs']):,} lovelace")
    
    return ada_pairs

# Discover ADA trading opportunities
ada_market = discover_ada_pairs()
```

## See Also

- [AMM Base Classes](amm_base.md) - Understanding the AMM architecture foundation
- [Minswap Documentation](minswap.md) - Comprehensive multi-pool AMM comparison
- [Splash Documentation](splash.md) - Alternative beacon token DEX implementation
- [Getting Started](index.md) - Basic setup and configuration guide
- [Pool Types Guide](types.md) - Detailed AMM mechanics and comparisons

::: charli3_dendrite.dexs.amm.cswap 