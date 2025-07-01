# VyFi

VyFi represents the next generation of intelligent AMM DEXs on Cardano, featuring a sophisticated API-driven architecture that dynamically discovers and manages liquidity pools in real-time. Unlike traditional static pool implementations, VyFi continuously adapts to market conditions through its innovative pool discovery system, providing users with the most up-to-date trading opportunities and optimal liquidity allocation.

## API-Driven Architecture Overview

VyFi's revolutionary approach combines on-chain execution with off-chain intelligence:

### Core API Features
- **Dynamic Pool Discovery**: Real-time detection and integration of new liquidity pools
- **Intelligent Pool Management**: Automated pool status monitoring and optimization
- **Live Configuration Updates**: Dynamic fee structures and pool parameters
- **Advanced Analytics**: Comprehensive pool performance and health metrics
- **Multi-Asset Support**: Sophisticated handling of complex asset pairs

### Real-Time Pool Intelligence
VyFi's API continuously monitors and updates pool information, ensuring users always have access to the latest market conditions and opportunities.

## Pool Architecture

| Pool Class | Description | Key Features |
|------------|-------------|--------------|
| `VyFiCPPState` | API-driven constant product pools | Dynamic discovery, real-time updates, intelligent fee management |

## Key Features

### Dynamic Pool Discovery
- **Automatic Pool Detection**: Continuously scans for new liquidity opportunities
- **Real-Time Pool Updates**: Live monitoring of pool status and parameters
- **Intelligent Filtering**: Smart pool selection based on user requirements
- **Market Adaptability**: Automatic adjustment to changing market conditions

### Advanced Fee Management
- **Multiple Fee Types**: Bar fees, process fees, and liquidity fees
- **Dynamic Fee Adjustment**: Fees automatically updated based on market conditions
- **Fee Optimization**: Intelligent fee routing for optimal trading costs
- **Volume-Based Discounts**: Automated fee reductions for high-volume traders

### Professional Trading Tools
- **Advanced Order Types**: Multiple swap types including Zap In/Out functionality
- **Portfolio Management**: Deposit, withdraw, and LP token management
- **Real-Time Analytics**: Live pool performance and opportunity analysis
- **API Integration**: Direct API access for algorithmic trading

## Basic Usage

### Dynamic Pool Discovery

```python
from charli3_dendrite import VyFiCPPState
from charli3_dendrite.backend import get_backend

# Get VyFi pools with dynamic discovery
backend = get_backend()

# VyFi automatically discovers available pools
selector = VyFiCPPState.pool_selector()
pools = backend.get_pool_utxos(**selector.model_dump())

# Process dynamically discovered pools
for pool_info in pools:
    pool = VyFiCPPState.model_validate(pool_info.model_dump())
    print(f"Pool ID: {pool.pool_id}")
    print(f"API-Managed Assets: {pool.unit_a} / {pool.unit_b}")
    print(f"TVL: {pool.tvl}")
    print(f"Dynamic Fees: LP={pool.lp_fee}bp, Bar={pool.bar_fee}bp")
    print(f"Pool Status: {'Live' if pool.is_live else 'Inactive'}")
```

### Intelligent Pool Selection

```python
def find_optimal_vyfi_pools(target_assets: list[str] = None):
    """Find optimal VyFi pools using API-driven discovery."""
    
    # Use VyFi's intelligent pool discovery
    if target_assets:
        selector = VyFiCPPState.pool_selector(assets=target_assets)
    else:
        selector = VyFiCPPState.pool_selector()
    
    pools = backend.get_pool_utxos(**selector.model_dump())
    
    # Analyze discovered pools
    pool_analysis = {
        'total_discovered': len(pools),
        'live_pools': 0,
        'total_tvl': 0,
        'fee_analysis': {
            'lp_fees': [],
            'bar_fees': []
        },
        'asset_coverage': set()
    }
    
    for pool_info in pools:
        try:
            pool = VyFiCPPState.model_validate(pool_info.model_dump())
            
            if hasattr(pool, 'is_live') and pool.is_live:
                pool_analysis['live_pools'] += 1
            
            pool_analysis['total_tvl'] += pool.tvl
            pool_analysis['fee_analysis']['lp_fees'].append(pool.lp_fee)
            pool_analysis['fee_analysis']['bar_fees'].append(pool.bar_fee)
            
            # Track asset coverage
            pool_analysis['asset_coverage'].add(pool.unit_a)
            pool_analysis['asset_coverage'].add(pool.unit_b)
            
        except Exception as e:
            print(f"Error processing pool: {e}")
    
    print("🤖 VyFi Pool Discovery Results:")
    print(f"   Total Pools Discovered: {pool_analysis['total_discovered']}")
    print(f"   Live Pools: {pool_analysis['live_pools']}")
    print(f"   Total TVL: {pool_analysis['total_tvl']/1000000000000:.2f}M ADA")
    print(f"   Asset Coverage: {len(pool_analysis['asset_coverage'])} unique assets")
    
    if pool_analysis['fee_analysis']['lp_fees']:
        avg_lp_fee = sum(pool_analysis['fee_analysis']['lp_fees']) / len(pool_analysis['fee_analysis']['lp_fees'])
        avg_bar_fee = sum(pool_analysis['fee_analysis']['bar_fees']) / len(pool_analysis['fee_analysis']['bar_fees'])
        print(f"   Average LP Fee: {avg_lp_fee:.2f}bp")
        print(f"   Average Bar Fee: {avg_bar_fee:.2f}bp")
    
    return pool_analysis

# Discover optimal pools
pool_discovery = find_optimal_vyfi_pools(["lovelace", "token_policy_id"])
```

### Real-Time Pool Monitoring

```python
import time
from datetime import datetime

def monitor_vyfi_pools_realtime(monitoring_duration: int = 300):
    """Monitor VyFi pools in real-time for 5 minutes (300 seconds) by default."""
    
    print("🔄 Starting VyFi Real-Time Pool Monitoring...")
    start_time = time.time()
    monitoring_data = []
    
    while time.time() - start_time < monitoring_duration:
        try:
            # Refresh pool data (VyFi pools are cached for efficiency)
            VyFiCPPState._refresh_pools()
            
            # Get current pool definitions
            current_pools = VyFiCPPState.pools()
            
            snapshot = {
                'timestamp': datetime.now().isoformat(),
                'total_pools': len(current_pools),
                'live_pools': sum(1 for pool in current_pools.values() if pool.is_live),
                'pool_refresh_time': VyFiCPPState._pools_refresh
            }
            
            monitoring_data.append(snapshot)
            
            print(f"📊 {snapshot['timestamp']}: {snapshot['live_pools']}/{snapshot['total_pools']} pools live")
            
            # Wait 30 seconds before next check
            time.sleep(30)
            
        except Exception as e:
            print(f"Monitoring error: {e}")
            break
    
    print("📈 Monitoring Complete - Summary:")
    if monitoring_data:
        print(f"   Duration: {len(monitoring_data)} snapshots over {monitoring_duration}s")
        print(f"   Pool Range: {min(s['live_pools'] for s in monitoring_data)}-{max(s['live_pools'] for s in monitoring_data)} live pools")
    
    return monitoring_data

# Example real-time monitoring (commented out for documentation)
# monitoring_results = monitor_vyfi_pools_realtime(60)  # Monitor for 1 minute
```

## Advanced Features

### Multi-Asset Trading Strategies

```python
def implement_vyfi_multi_asset_strategy():
    """Implement advanced multi-asset trading strategies using VyFi's API."""
    
    # Get all available pools through API discovery
    all_pools = VyFiCPPState.pools()
    
    # Analyze asset relationships and opportunities
    asset_graph = {}
    trading_opportunities = []
    
    for pool_key, pool_def in all_pools.items():
        if not pool_def.is_live:
            continue
            
        # Extract asset information from pool definition
        a_asset = pool_def.json_.a_asset
        b_asset = pool_def.json_.b_asset
        
        # Build asset relationship graph
        a_symbol = f"{a_asset.currency_symbol}{a_asset.token_name}"
        b_symbol = f"{b_asset.currency_symbol}{b_asset.token_name}"
        
        if a_symbol not in asset_graph:
            asset_graph[a_symbol] = []
        if b_symbol not in asset_graph:
            asset_graph[b_symbol] = []
        
        asset_graph[a_symbol].append(b_symbol)
        asset_graph[b_symbol].append(a_symbol)
        
        # Identify potential arbitrage opportunities
        fees = pool_def.json_.fees_settings
        total_fee = fees.bar_fee + fees.process_fee + fees.liq_fee
        
        trading_opportunities.append({
            'pair': f"{a_symbol}/{b_symbol}",
            'pool_address': pool_def.pool_validator_utxo_address,
            'total_fee': total_fee,
            'lp_policy': pool_def.lp_policy_id_asset_id,
            'units_pair': pool_def.units_pair
        })
    
    # Sort opportunities by fee efficiency
    trading_opportunities.sort(key=lambda x: x['total_fee'])
    
    print("🎯 VyFi Multi-Asset Strategy Analysis:")
    print(f"   Total Assets Discovered: {len(asset_graph)}")
    print(f"   Trading Pairs Available: {len(trading_opportunities)}")
    print(f"   Most Efficient Pairs:")
    
    for i, opp in enumerate(trading_opportunities[:5], 1):
        print(f"      {i}. {opp['pair']} - Fee: {opp['total_fee']}bp")
    
    return {
        'asset_graph': asset_graph,
        'trading_opportunities': trading_opportunities
    }

# Implement multi-asset strategy
strategy_analysis = implement_vyfi_multi_asset_strategy()
```

### Advanced Order Types

```python
from pycardano import Address, Assets

def create_vyfi_advanced_orders():
    """Demonstrate VyFi's advanced order types and capabilities."""
    
    source_address = Address.from_bech32("addr1...")
    
    # Example: Zap In A (single asset to LP tokens)
    zap_in_order = VyFiOrderDatum(
        address=source_address.payment_part.to_primitive() + source_address.staking_part.to_primitive(),
        order=ZapInA(min_lp_receive=1000000)  # Minimum 1 LP token
    )
    
    # Example: Withdraw (LP tokens to underlying assets)
    withdraw_order = VyFiOrderDatum(
        address=source_address.payment_part.to_primitive() + source_address.staking_part.to_primitive(),
        order=Withdraw(
            min_lp_receive=WithdrawPair(
                min_amount_a=500000,  # Minimum asset A
                min_amount_b=500000   # Minimum asset B
            )
        )
    )
    
    # Example: Standard A to B swap
    swap_order = VyFiOrderDatum(
        address=source_address.payment_part.to_primitive() + source_address.staking_part.to_primitive(),
        order=AtoB(min_receive=1000000)  # Minimum receive amount
    )
    
    order_types = {
        'zap_in_a': {
            'description': 'Single asset entry to LP position',
            'use_case': 'Simplified liquidity provision',
            'order': zap_in_order
        },
        'withdraw': {
            'description': 'LP tokens to underlying assets',
            'use_case': 'Exit liquidity position',
            'order': withdraw_order
        },
        'standard_swap': {
            'description': 'Traditional A to B swap',
            'use_case': 'Regular token exchange',
            'order': swap_order
        }
    }
    
    print("📋 VyFi Advanced Order Types:")
    for order_type, details in order_types.items():
        print(f"   {order_type.replace('_', ' ').title()}:")
        print(f"      Description: {details['description']}")
        print(f"      Use Case: {details['use_case']}")
        print(f"      Order Type: {type(details['order'].order).__name__}")
    
    return order_types

# Create advanced order examples
advanced_orders = create_vyfi_advanced_orders()
```

### API Integration and Pool Definition Management

```python
def analyze_vyfi_api_integration():
    """Analyze VyFi's API integration and pool definition system."""
    
    # Access VyFi's pool definition system
    pools = VyFiCPPState.pools()
    
    api_metrics = {
        'total_definitions': len(pools),
        'live_pools': 0,
        'fee_structures': {},
        'asset_pairs': {},
        'lp_policies': set(),
        'validator_addresses': set()
    }
    
    for pool_key, pool_def in pools.items():
        # Count live pools
        if pool_def.is_live:
            api_metrics['live_pools'] += 1
        
        # Analyze fee structures
        fees = pool_def.json_.fees_settings
        fee_key = f"Bar:{fees.bar_fee}_Process:{fees.process_fee}_Liq:{fees.liq_fee}"
        api_metrics['fee_structures'][fee_key] = api_metrics['fee_structures'].get(fee_key, 0) + 1
        
        # Track asset pairs
        pair_key = pool_def.units_pair
        api_metrics['asset_pairs'][pair_key] = api_metrics['asset_pairs'].get(pair_key, 0) + 1
        
        # Collect LP policies and validator addresses
        api_metrics['lp_policies'].add(pool_def.lp_policy_id_asset_id)
        api_metrics['validator_addresses'].add(pool_def.pool_validator_utxo_address)
    
    print("🔗 VyFi API Integration Analysis:")
    print(f"   Total Pool Definitions: {api_metrics['total_definitions']}")
    print(f"   Live Pools: {api_metrics['live_pools']}")
    print(f"   Unique Fee Structures: {len(api_metrics['fee_structures'])}")
    print(f"   Unique Asset Pairs: {len(api_metrics['asset_pairs'])}")
    print(f"   LP Policies: {len(api_metrics['lp_policies'])}")
    print(f"   Validator Addresses: {len(api_metrics['validator_addresses'])}")
    
    # Show most common fee structures
    sorted_fees = sorted(api_metrics['fee_structures'].items(), key=lambda x: x[1], reverse=True)
    print(f"\n   Most Common Fee Structures:")
    for fee_structure, count in sorted_fees[:3]:
        print(f"      {fee_structure}: {count} pools")
    
    return api_metrics

# Analyze API integration
api_analysis = analyze_vyfi_api_integration()
```

## Performance Optimization

### Pool Caching and Refresh Strategy

```python
def optimize_vyfi_performance():
    """Optimize VyFi performance through intelligent caching and refresh strategies."""
    
    # VyFi uses intelligent caching with configurable refresh intervals
    cache_info = {
        'refresh_interval': POOL_REFRESH_INTERVAL,  # 3600 seconds (1 hour)
        'current_cache_age': time.time() - VyFiCPPState._pools_refresh,
        'cache_efficiency': 'High' if VyFiCPPState._pools else 'Low'
    }
    
    optimization_strategies = {
        'automatic_refresh': {
            'description': 'Pools automatically refresh every hour',
            'benefit': 'Always up-to-date pool information',
            'implementation': 'Built into VyFi architecture'
        },
        'lazy_loading': {
            'description': 'Pools loaded on first access',
            'benefit': 'Reduced initial overhead',
            'implementation': 'Transparent to users'
        },
        'intelligent_filtering': {
            'description': 'Filter pools by assets for targeted queries',
            'benefit': 'Faster pool discovery',
            'implementation': 'Use VyFiCPPState.pool_selector(assets=["asset1", "asset2"])'
        },
        'batch_operations': {
            'description': 'Process multiple pools efficiently',
            'benefit': 'Reduced API calls and improved throughput',
            'implementation': 'Group related operations'
        }
    }
    
    print("⚡ VyFi Performance Optimization:")
    print(f"   Cache Refresh Interval: {cache_info['refresh_interval']}s")
    print(f"   Current Cache Age: {cache_info['current_cache_age']:.0f}s")
    print(f"   Cache Efficiency: {cache_info['cache_efficiency']}")
    
    print(f"\n   Optimization Strategies:")
    for strategy, details in optimization_strategies.items():
        print(f"      {strategy.replace('_', ' ').title()}:")
        print(f"         {details['description']}")
        print(f"         Benefit: {details['benefit']}")
    
    return {
        'cache_info': cache_info,
        'strategies': optimization_strategies
    }

# Optimize VyFi performance
performance_optimization = optimize_vyfi_performance()
```

### Intelligent Asset Mapping

```python
def implement_vyfi_asset_mapping():
    """Implement intelligent asset mapping for VyFi pools."""
    
    # VyFi's asset encoding system
    def encode_asset_example(policy_id: str, asset_name: str) -> str:
        """Example of VyFi's asset encoding."""
        if len(policy_id) != POLICY_ID_LENGTH:
            raise ValueError(f"Invalid policy ID length: {len(policy_id)}")
        return policy_id + asset_name
    
    def decode_asset_example(encoded_asset: str) -> tuple[str, str]:
        """Example of VyFi's asset decoding."""
        if len(encoded_asset) < POLICY_ID_LENGTH:
            raise ValueError("Invalid encoded asset length")
        policy_id = encoded_asset[:POLICY_ID_LENGTH]
        asset_name = encoded_asset[POLICY_ID_LENGTH:]
        return policy_id, asset_name
    
    # Demonstrate asset mapping with pool data
    pools = VyFiCPPState.pools()
    asset_mapping = {}
    
    for pool_key, pool_def in pools.items():
        # Extract asset information
        a_asset = pool_def.json_.a_asset
        b_asset = pool_def.json_.b_asset
        
        # Create asset mappings
        a_encoded = encode_asset_example(a_asset.currency_symbol, a_asset.token_name)
        b_encoded = encode_asset_example(b_asset.currency_symbol, b_asset.token_name)
        
        asset_mapping[pool_key] = {
            'asset_a': {
                'encoded': a_encoded,
                'currency_symbol': a_asset.currency_symbol,
                'token_name': a_asset.token_name
            },
            'asset_b': {
                'encoded': b_encoded,
                'currency_symbol': b_asset.currency_symbol,
                'token_name': b_asset.token_name
            }
        }
    
    print("🗺️  VyFi Asset Mapping System:")
    print(f"   Total Asset Mappings: {len(asset_mapping)}")
    print(f"   Policy ID Length: {POLICY_ID_LENGTH} characters")
    print(f"   Address Hash Length: {ADDRESS_HASH_LENGTH} bytes")
    
    # Show example mappings
    sample_mappings = list(asset_mapping.items())[:3]
    for pool_key, mapping in sample_mappings:
        print(f"\n   Pool {pool_key}:")
        print(f"      Asset A: {mapping['asset_a']['currency_symbol']}/{mapping['asset_a']['token_name']}")
        print(f"      Asset B: {mapping['asset_b']['currency_symbol']}/{mapping['asset_b']['token_name']}")
    
    return asset_mapping

# Implement asset mapping
asset_mapping = implement_vyfi_asset_mapping()
```

## Technical Implementation

### Order Validation and Processing

```python
def validate_vyfi_orders(order_data: dict):
    """Validate VyFi order structure and processing requirements."""
    
    validation_results = {
        'address_valid': False,
        'order_type_valid': False,
        'amount_parameters_valid': False,
        'address_structure_valid': False,
        'validation_score': 0
    }
    
    try:
        # Validate order structure
        order = VyFiOrderDatum.model_validate(order_data)
        
        # Check address structure (28 bytes payment + optional 28 bytes staking)
        if len(order.address) in [ADDRESS_HASH_LENGTH, ADDRESS_HASH_LENGTH * 2]:
            validation_results['address_valid'] = True
            validation_results['address_structure_valid'] = True
        
        # Validate order type
        valid_order_types = [AtoB, BtoA, Deposit, Withdraw, ZapInA, ZapInB, LPFlushA]
        if type(order.order) in valid_order_types:
            validation_results['order_type_valid'] = True
        
        # Check amount parameters
        if hasattr(order.order, 'min_receive') or hasattr(order.order, 'min_lp_receive'):
            validation_results['amount_parameters_valid'] = True
        
        # Calculate validation score
        score = sum(1 for key, value in validation_results.items() 
                   if key != 'validation_score' and value)
        validation_results['validation_score'] = score / 4 * 100  # 4 checks total
        
    except Exception as e:
        print(f"Validation error: {e}")
    
    print("✅ VyFi Order Validation:")
    for check, status in validation_results.items():
        if check != 'validation_score':
            print(f"   {check.replace('_', ' ').title()}: {'✅' if status else '❌'}")
        else:
            print(f"   Validation Score: {status:.1f}%")
    
    return validation_results

# Example order validation
sample_order = {
    'address': b'x' * ADDRESS_HASH_LENGTH * 2,  # Full address (payment + staking)
    'order': AtoB(min_receive=1000000)
}
validation_results = validate_vyfi_orders(sample_order)
```

### Pool Definition Structure Analysis

```python
def analyze_vyfi_pool_structure():
    """Analyze VyFi's comprehensive pool definition structure."""
    
    # Get a sample pool definition for analysis
    pools = VyFiCPPState.pools()
    if not pools:
        print("No pools available for analysis")
        return
    
    sample_pool = next(iter(pools.values()))
    
    structure_analysis = {
        'basic_info': {
            'units_pair': sample_pool.units_pair,
            'pair': sample_pool.pair,
            'is_live': sample_pool.is_live
        },
        'addresses': {
            'pool_validator': sample_pool.pool_validator_utxo_address,
            'order_validator': sample_pool.order_validator_utxo_address
        },
        'tokens': {
            'lp_policy': sample_pool.lp_policy_id_asset_id,
            'a_asset': f"{sample_pool.json_.a_asset.currency_symbol}/{sample_pool.json_.a_asset.token_name}",
            'b_asset': f"{sample_pool.json_.b_asset.currency_symbol}/{sample_pool.json_.b_asset.token_name}",
            'main_nft': f"{sample_pool.json_.main_nft.currency_symbol}/{sample_pool.json_.main_nft.token_name}"
        },
        'fees': {
            'bar_fee': sample_pool.json_.fees_settings.bar_fee,
            'process_fee': sample_pool.json_.fees_settings.process_fee,
            'liq_fee': sample_pool.json_.fees_settings.liq_fee
        }
    }
    
    print("🏗️  VyFi Pool Definition Structure:")
    for category, data in structure_analysis.items():
        print(f"\n   {category.replace('_', ' ').title()}:")
        for key, value in data.items():
            print(f"      {key}: {value}")
    
    return structure_analysis

# Analyze pool structure
pool_structure = analyze_vyfi_pool_structure()
```

## Backend Support

| Feature | DBSync | BlockFrost | Ogmios/Kupo |
|---------|--------|------------|-------------|
| Pool Discovery | ✅ | ✅ | ✅ |
| API Integration | ✅ | ✅ | ✅ |
| Real-time Updates | ✅ | ✅ | ✅ |
| Order Processing | ✅ | ✅ | ✅ |
| Historical Data | ✅ | ❌ | ❌ |
| Pool Analytics | ✅ | ✅ | ✅ |

!!! note "Backend Limitations"
    All VyFi API-driven functionality works across all backends. Historical pool analytics are only available with DBSync backend.

## API Integration Best Practices

### Efficient Pool Management

```python
def implement_vyfi_best_practices():
    """Implement best practices for VyFi API integration."""
    
    best_practices = {
        'pool_discovery': {
            'practice': 'Use targeted asset filtering',
            'implementation': 'VyFiCPPState.pool_selector(assets=["specific", "assets"])',
            'benefit': 'Faster discovery, reduced overhead'
        },
        'cache_management': {
            'practice': 'Respect cache refresh intervals',
            'implementation': 'Allow automatic refresh every 3600 seconds',
            'benefit': 'Optimal balance of freshness and performance'
        },
        'error_handling': {
            'practice': 'Handle API unavailability gracefully',
            'implementation': 'Catch exceptions during pool refresh',
            'benefit': 'Robust application behavior'
        },
        'batch_processing': {
            'practice': 'Process multiple pools efficiently',
            'implementation': 'Group operations on similar pools',
            'benefit': 'Improved throughput and reduced latency'
        }
    }
    
    print("📋 VyFi Integration Best Practices:")
    for practice_area, details in best_practices.items():
        print(f"\n   {practice_area.replace('_', ' ').title()}:")
        print(f"      Practice: {details['practice']}")
        print(f"      Implementation: {details['implementation']}")
        print(f"      Benefit: {details['benefit']}")
    
    return best_practices

# Get best practices guide
best_practices = implement_vyfi_best_practices()
```

## See Also

- [AMM Base Classes](amm_base.md) - Understanding the AMM architecture
- [API-Driven DEXs](types.md) - API integration patterns for DEX implementations
- [Getting Started](index.md) - Basic setup and configuration
- [Dynamic Trading](spectrum.md) - Cross-chain and dynamic pool strategies

::: charli3_dendrite.dexs.amm.vyfi
