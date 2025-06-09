::: charli3_dendrite.dexs.amm.sundae

# SundaeSwap

SundaeSwap has quickly become a fan favorite among Cardano users, offering an intuitive and sweet experience for token swaps and liquidity provision. This beloved AMM DEX provides both V1 and V3 implementations, each with unique features and optimizations. SundaeSwap's vibrant community and user-centric approach make it the perfect choice for anyone looking to get the most out of Cardano's DeFi ecosystem.

## Version Architecture Overview

SundaeSwap provides two distinct versions, each designed for different use cases and performance characteristics:

### V1 Implementation
- **Traditional AMM**: Classic constant product formula (x * y = k)
- **Fixed Fee Structure**: Simple, predictable fee model
- **PlutusV1 Scripts**: Proven smart contract architecture
- **User-Friendly**: Intuitive interface perfect for beginners

### V3 Implementation
- **Enhanced Performance**: Advanced pool management and optimization
- **Dynamic Fees**: Bidirectional fee structure with ask/bid differentiation
- **PlutusV2 Scripts**: Next-generation smart contract efficiency
- **Protocol Fees**: Sophisticated fee management for sustainability
- **Advanced Features**: Enhanced liquidity management and routing

## Supported Pool Classes

| Pool Class | Version | Description | Key Features |
|------------|---------|-------------|--------------|
| `SundaeSwapCPPState` | V1 | Traditional constant product pools | Simple fee structure, proven reliability |
| `SundaeSwapV3CPPState` | V3 | Enhanced constant product pools | Dynamic fees, protocol sustainability, advanced optimization |

## Key Features

### V1 Pools
- **Simple Fee Model**: Straightforward percentage-based fees
- **Proven Reliability**: Battle-tested architecture used by thousands
- **Community Favorite**: Beloved by the Cardano community
- **Beginner Friendly**: Perfect entry point into DeFi

### V3 Pools
- **Dynamic Fee Structure**: Separate bid and ask fees for optimal market making
- **Protocol Sustainability**: Built-in protocol fees for long-term development
- **Enhanced Capital Efficiency**: Advanced algorithms for better liquidity utilization
- **Settings-Based Configuration**: Dynamic fee adjustment based on on-chain settings
- **Market Timing**: Support for market open/close timing mechanisms

## Basic Usage

### V1 Pools - Classic SundaeSwap Experience

```python
from charli3_dendrite import SundaeSwapCPPState
from charli3_dendrite.backend import get_backend

# Get V1 pool data
backend = get_backend()
selector = SundaeSwapCPPState.pool_selector()
pools = backend.get_pool_utxos(**selector.model_dump())

# Process pool information
for pool_info in pools:
    pool = SundaeSwapCPPState.model_validate(pool_info.model_dump())
    print(f"Pool ID: {pool.pool_id}")
    print(f"Assets: {pool.unit_a} / {pool.unit_b}")
    print(f"TVL: {pool.tvl}")
    print(f"Fee: {pool.fee}bp")
    print(f"DEX: {pool.dex()}")
```

### V3 Pools - Enhanced Performance

```python
from charli3_dendrite import SundaeSwapV3CPPState

# Get V3 pool data with dynamic fees
selector = SundaeSwapV3CPPState.pool_selector()
pools = backend.get_pool_utxos(**selector.model_dump())

for pool_info in pools:
    pool = SundaeSwapV3CPPState.model_validate(pool_info.model_dump())
    print(f"V3 Pool ID: {pool.pool_id}")
    print(f"Assets: {pool.unit_a} / {pool.unit_b}")
    print(f"Dynamic Fees: {pool.fee}")  # [bid_fee, ask_fee]
    print(f"Script Version: {pool.default_script_class()}")
    print(f"Batcher Fee: {pool.batcher_fee()}")
```

### Fee Structure Analysis

```python
def analyze_sundae_fees():
    """Compare SundaeSwap V1 vs V3 fee structures."""
    
    # V1 fee analysis
    v1_pool = SundaeSwapCPPState.model_validate(v1_pool_data)
    print("SundaeSwap V1 Fee Structure:")
    print(f"  Trading Fee: {v1_pool.fee}bp")
    print(f"  Batcher Fee: {v1_pool.batcher_fee()}")
    print(f"  Fee Model: Fixed percentage")
    
    # V3 fee analysis  
    v3_pool = SundaeSwapV3CPPState.model_validate(v3_pool_data)
    print("\nSundaeSwap V3 Fee Structure:")
    print(f"  Bid Fee: {v3_pool.fee[0]}bp")
    print(f"  Ask Fee: {v3_pool.fee[1]}bp")
    print(f"  Batcher Fee: {v3_pool.batcher_fee()}")
    print(f"  Fee Model: Dynamic bidirectional")
    
    # Demonstrate dynamic batcher fee retrieval
    SundaeSwapV3CPPState.get_batcher_fee()
    print(f"  Current V3 Batcher Fee: {SundaeSwapV3CPPState._batcher_fee}")

analyze_sundae_fees()
```

## Advanced Features

### Version Comparison and Migration

```python
def compare_sundae_versions():
    """Compare SundaeSwap V1 and V3 implementations."""
    
    comparison = {
        'V1': {
            'script_type': 'PlutusV1',
            'fee_structure': 'Fixed percentage',
            'batcher_fee': '2.5 ADA (fixed)',
            'target_audience': 'General users, beginners',
            'pool_policy': '0029cb7c88c7567b63d1a512c0ed626aa169688ec980730c0473b91370'
        },
        'V3': {
            'script_type': 'PlutusV2', 
            'fee_structure': 'Dynamic bid/ask fees',
            'batcher_fee': 'Dynamic (based on settings)',
            'target_audience': 'Advanced users, market makers',
            'pool_policy': 'e0302560ced2fdcbfcb2602697df970cd0d6a38f94b32703f51c312b'
        }
    }
    
    for version, features in comparison.items():
        print(f"\nSundaeSwap {version}:")
        for feature, value in features.items():
            print(f"  {feature}: {value}")
    
    return comparison

version_comparison = compare_sundae_versions()
```

### Multi-Version Pool Analysis

```python
def analyze_all_sundae_pools():
    """Analyze both V1 and V3 pools for comprehensive insights."""
    
    # Query V1 pools
    v1_selector = SundaeSwapCPPState.pool_selector()
    v1_pools = backend.get_pool_utxos(**v1_selector.model_dump())
    
    # Query V3 pools
    v3_selector = SundaeSwapV3CPPState.pool_selector()
    v3_pools = backend.get_pool_utxos(**v3_selector.model_dump())
    
    analysis_results = {
        'v1_stats': {
            'total_pools': len(v1_pools),
            'total_tvl': 0,
            'avg_fee': 0
        },
        'v3_stats': {
            'total_pools': len(v3_pools),
            'total_tvl': 0,
            'avg_bid_fee': 0,
            'avg_ask_fee': 0
        }
    }
    
    # Analyze V1 pools
    v1_fees = []
    for pool_info in v1_pools:
        pool = SundaeSwapCPPState.model_validate(pool_info.model_dump())
        analysis_results['v1_stats']['total_tvl'] += pool.tvl
        v1_fees.append(pool.fee)
    
    if v1_fees:
        analysis_results['v1_stats']['avg_fee'] = sum(v1_fees) / len(v1_fees)
    
    # Analyze V3 pools
    v3_bid_fees = []
    v3_ask_fees = []
    for pool_info in v3_pools:
        pool = SundaeSwapV3CPPState.model_validate(pool_info.model_dump())
        analysis_results['v3_stats']['total_tvl'] += pool.tvl
        if isinstance(pool.fee, list):
            v3_bid_fees.append(pool.fee[0])
            v3_ask_fees.append(pool.fee[1])
    
    if v3_bid_fees:
        analysis_results['v3_stats']['avg_bid_fee'] = sum(v3_bid_fees) / len(v3_bid_fees)
        analysis_results['v3_stats']['avg_ask_fee'] = sum(v3_ask_fees) / len(v3_ask_fees)
    
    print("SundaeSwap Ecosystem Analysis:")
    print(f"V1 Pools: {analysis_results['v1_stats']['total_pools']}")
    print(f"V1 TVL: {analysis_results['v1_stats']['total_tvl']}")
    print(f"V1 Avg Fee: {analysis_results['v1_stats']['avg_fee']:.2f}bp")
    print(f"V3 Pools: {analysis_results['v3_stats']['total_pools']}")
    print(f"V3 TVL: {analysis_results['v3_stats']['total_tvl']}")
    print(f"V3 Avg Bid Fee: {analysis_results['v3_stats']['avg_bid_fee']:.2f}bp")
    print(f"V3 Avg Ask Fee: {analysis_results['v3_stats']['avg_ask_fee']:.2f}bp")
    
    return analysis_results

# Execute comprehensive analysis
sundae_analysis = analyze_all_sundae_pools()
```

### V3 Dynamic Settings Integration

```python
def monitor_v3_settings():
    """Monitor SundaeSwap V3 dynamic settings and fee updates."""
    
    try:
        # Retrieve current V3 settings from on-chain
        SundaeSwapV3CPPState.get_batcher_fee()
        
        settings_info = {
            'current_batcher_fee': SundaeSwapV3CPPState._batcher_fee,
            'fee_components': {
                'base_fee': 'Retrieved from on-chain settings',
                'simple_fee': 'Added to base fee for total batcher fee'
            },
            'update_frequency': 'Cached for 1 hour intervals',
            'settings_address': 'addr1w9ke67k2ckdyg60v22ajqugxze79e0ax3yqgl7nway4vc5q84hpqs'
        }
        
        print("SundaeSwap V3 Dynamic Settings:")
        for key, value in settings_info.items():
            print(f"  {key}: {value}")
            
    except Exception as e:
        print(f"Settings retrieval failed: {e}")
        print("This is normal when no backend is configured")
    
    return settings_info

# Monitor current settings
v3_settings = monitor_v3_settings()
```

## Pool Optimization Strategies

### Optimal Pool Selection

```python
def find_optimal_sundae_pool(token_a: str, token_b: str, trade_amount: int):
    """Find the optimal SundaeSwap pool for a given trade."""
    
    # Check both V1 and V3 pools for the trading pair
    v1_pools = backend.get_pool_utxos(**SundaeSwapCPPState.pool_selector().model_dump())
    v3_pools = backend.get_pool_utxos(**SundaeSwapV3CPPState.pool_selector().model_dump())
    
    best_pool = None
    best_output = 0
    best_version = None
    
    # Analyze V1 pools
    for pool_info in v1_pools:
        try:
            pool = SundaeSwapCPPState.model_validate(pool_info.model_dump())
            if pool.unit_a == token_a and pool.unit_b == token_b:
                # Calculate expected output for this pool
                input_assets = Assets({token_a: trade_amount})
                output_assets, slippage = pool.get_amount_out(input_assets)
                
                if output_assets.quantity() > best_output:
                    best_output = output_assets.quantity()
                    best_pool = pool
                    best_version = "V1"
        except Exception:
            continue
    
    # Analyze V3 pools
    for pool_info in v3_pools:
        try:
            pool = SundaeSwapV3CPPState.model_validate(pool_info.model_dump())
            if pool.unit_a == token_a and pool.unit_b == token_b:
                # Calculate expected output for this pool
                input_assets = Assets({token_a: trade_amount})
                output_assets, slippage = pool.get_amount_out(input_assets)
                
                if output_assets.quantity() > best_output:
                    best_output = output_assets.quantity()
                    best_pool = pool
                    best_version = "V3"
        except Exception:
            continue
    
    return {
        'best_pool': best_pool,
        'best_version': best_version,
        'expected_output': best_output,
        'recommendation': f"Use SundaeSwap {best_version} for optimal returns"
    }

# Example usage
optimal_pool = find_optimal_sundae_pool("lovelace", "token_policy_id", 1000000000)
print(f"Recommendation: {optimal_pool['recommendation']}")
print(f"Expected Output: {optimal_pool['expected_output']}")
```

### Liquidity Provider Strategies

```python
def analyze_lp_opportunities():
    """Analyze liquidity provision opportunities across SundaeSwap versions."""
    
    strategies = {
        'conservative': {
            'recommendation': 'SundaeSwap V1',
            'reasoning': 'Proven stability, predictable fees, large community',
            'risk_level': 'Low',
            'target_pairs': ['ADA/Stablecoins', 'Major tokens']
        },
        'advanced': {
            'recommendation': 'SundaeSwap V3',
            'reasoning': 'Dynamic fees can provide better returns for active management',
            'risk_level': 'Medium',
            'target_pairs': ['Volatile pairs', 'New tokens', 'Arbitrage opportunities']
        },
        'diversified': {
            'recommendation': 'Both V1 and V3',
            'reasoning': 'Spread risk across versions, capture different market opportunities',
            'risk_level': 'Medium',
            'target_pairs': ['Balanced portfolio across versions']
        }
    }
    
    print("SundaeSwap Liquidity Provider Strategies:")
    for strategy_name, details in strategies.items():
        print(f"\n{strategy_name.title()} Strategy:")
        for key, value in details.items():
            print(f"  {key}: {value}")
    
    return strategies

lp_strategies = analyze_lp_opportunities()
```

## Technical Implementation Details

### Pool Identification and Validation

```python
def validate_sundae_pool(pool_data: dict, expected_version: str = None):
    """Validate and identify SundaeSwap pool version."""
    
    validation_results = {
        'is_valid': False,
        'version': None,
        'pool_policy': None,
        'validation_errors': []
    }
    
    try:
        # Try V1 validation
        if expected_version != "V3":
            try:
                pool = SundaeSwapCPPState.model_validate(pool_data)
                validation_results['is_valid'] = True
                validation_results['version'] = 'V1'
                validation_results['pool_policy'] = SundaeSwapCPPState.pool_policy()
                return validation_results
            except Exception as e:
                validation_results['validation_errors'].append(f"V1 validation failed: {e}")
        
        # Try V3 validation
        if expected_version != "V1":
            try:
                pool = SundaeSwapV3CPPState.model_validate(pool_data)
                validation_results['is_valid'] = True
                validation_results['version'] = 'V3'
                validation_results['pool_policy'] = SundaeSwapV3CPPState.pool_policy()
                return validation_results
            except Exception as e:
                validation_results['validation_errors'].append(f"V3 validation failed: {e}")
        
    except Exception as e:
        validation_results['validation_errors'].append(f"General validation error: {e}")
    
    return validation_results

# Example validation
pool_validation = validate_sundae_pool(sample_pool_data)
print(f"Pool Version: {pool_validation['version']}")
print(f"Is Valid: {pool_validation['is_valid']}")
```

### Fee Calculation Comparison

```python
def compare_fee_calculations(trade_amount: int):
    """Compare fee calculations between V1 and V3."""
    
    fee_comparison = {
        'trade_amount': trade_amount,
        'v1_calculations': {},
        'v3_calculations': {}
    }
    
    # V1 fee calculation (fixed percentage)
    v1_pool = SundaeSwapCPPState()
    v1_batcher_fee = v1_pool.batcher_fee()
    v1_trading_fee = trade_amount * v1_pool.fee / 10000 if hasattr(v1_pool, 'fee') else 0
    
    fee_comparison['v1_calculations'] = {
        'batcher_fee': v1_batcher_fee.get('lovelace', 0),
        'trading_fee': v1_trading_fee,
        'total_fee_ada': v1_batcher_fee.get('lovelace', 0) / 1000000,
        'fee_model': 'Fixed percentage'
    }
    
    # V3 fee calculation (dynamic)
    v3_pool = SundaeSwapV3CPPState()
    try:
        v3_batcher_fee = v3_pool.batcher_fee()
        v3_bid_fee = trade_amount * 30 / 10000  # Example bid fee
        v3_ask_fee = trade_amount * 30 / 10000  # Example ask fee
        
        fee_comparison['v3_calculations'] = {
            'batcher_fee': v3_batcher_fee.get('lovelace', 0),
            'bid_fee': v3_bid_fee,
            'ask_fee': v3_ask_fee,
            'total_fee_ada': v3_batcher_fee.get('lovelace', 0) / 1000000,
            'fee_model': 'Dynamic bid/ask'
        }
    except:
        fee_comparison['v3_calculations'] = {
            'error': 'V3 settings not available'
        }
    
    print("SundaeSwap Fee Comparison:")
    print(f"Trade Amount: {trade_amount/1000000} ADA")
    print(f"V1 Total Fee: {fee_comparison['v1_calculations']['total_fee_ada']:.2f} ADA")
    if 'error' not in fee_comparison['v3_calculations']:
        print(f"V3 Total Fee: {fee_comparison['v3_calculations']['total_fee_ada']:.2f} ADA")
    
    return fee_comparison

# Example fee comparison
fee_analysis = compare_fee_calculations(100000000)  # 100 ADA trade
```

## Integration Patterns

### Smart Contract Integration

```python
from pycardano import Address, Assets, PlutusData

def create_sundae_swap_order(
    version: str,
    source_address: Address,
    input_asset: str,
    input_amount: int,
    output_asset: str,
    min_output: int,
    pool_identifier: str
):
    """Create a SundaeSwap order for either V1 or V3."""
    
    input_assets = Assets({input_asset: input_amount})
    output_assets = Assets({output_asset: min_output})
    
    if version.upper() == "V1":
        # V1 order creation
        ident = bytes.fromhex(pool_identifier[60:])  # Last 32 chars for V1
        order_datum = SundaeOrderDatum.create_datum(
            ident=ident,
            address_source=source_address,
            in_assets=input_assets,
            out_assets=output_assets,
            fee=2500000  # V1 fixed batcher fee
        )
        print(f"Created SundaeSwap V1 order")
        
    elif version.upper() == "V3":
        # V3 order creation  
        ident = bytes.fromhex(pool_identifier[64:])  # Last 28 chars for V3
        
        # Get current V3 settings for dynamic fee
        SundaeSwapV3CPPState.get_batcher_fee()
        current_fee = SundaeSwapV3CPPState._batcher_fee.get('lovelace', 1280000)
        
        order_datum = SundaeV3OrderDatum.create_datum(
            ident=ident,
            address_source=source_address,
            in_assets=input_assets,
            out_assets=output_assets,
            fee=current_fee
        )
        print(f"Created SundaeSwap V3 order with dynamic fee: {current_fee}")
    
    else:
        raise ValueError(f"Unsupported version: {version}")
    
    return order_datum

# Example order creation
swap_order = create_sundae_swap_order(
    version="V3",
    source_address=Address.from_bech32("addr1..."),
    input_asset="lovelace",
    input_amount=100000000,
    output_asset="token_policy_id",
    min_output=1000000,
    pool_identifier="pool_nft_unit_here"
)
```

## Backend Support

| Feature | DBSync | BlockFrost | Ogmios/Kupo |
|---------|--------|------------|-------------|
| V1 Pool Data | ✅ | ✅ | ✅ |
| V3 Pool Data | ✅ | ✅ | ✅ |
| Dynamic V3 Settings | ✅ | ✅ | ✅ |
| Order Placement | ✅ | ✅ | ✅ |
| Historical Data | ✅ | ❌ | ❌ |
| Real-time Fees | ✅ | ✅ | ✅ |

!!! note "Backend Limitations"
    All current SundaeSwap functionality works across all backends. V3 dynamic settings retrieval works on all backends, but historical analysis requires DBSync.

## Community and Ecosystem

### SundaeSwap's Sweet Spot in Cardano DeFi

SundaeSwap has established itself as the community favorite through:

- **User-Friendly Design**: Intuitive interface that welcomes DeFi newcomers
- **Community Focus**: Strong emphasis on user feedback and community governance
- **Sweet Branding**: Memorable and approachable brand that makes DeFi fun
- **Reliable Performance**: Consistent operation and user satisfaction
- **Innovation Balance**: Thoughtful evolution from V1 to V3 maintaining simplicity

### Integration with Other Protocols

```python
def sundae_ecosystem_analysis():
    """Analyze SundaeSwap's role in the broader Cardano ecosystem."""
    
    ecosystem_position = {
        'primary_role': 'Community AMM',
        'target_users': ['DeFi beginners', 'Community members', 'Casual traders'],
        'strengths': [
            'User experience',
            'Community trust',
            'Brand recognition',
            'Reliable operation'
        ],
        'integration_opportunities': [
            'Yield farming protocols',
            'Portfolio management tools',
            'Cross-DEX aggregators',
            'Educational platforms'
        ]
    }
    
    print("SundaeSwap Ecosystem Analysis:")
    for key, value in ecosystem_position.items():
        print(f"{key}: {value}")
    
    return ecosystem_position

ecosystem_analysis = sundae_ecosystem_analysis()
```

## See Also

- [AMM Base Classes](amm_base.md) - Understanding the AMM architecture
- [Splash Documentation](splash.md) - Comparison with bidirectional swap capabilities
- [Getting Started](index.md) - Basic setup and configuration
- [Community DEXs Guide](types.md) - Comparing community-focused DEX implementations

::: charli3_dendrite.dexs.amm.sundae
