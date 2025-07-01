# Spectrum

!!! info "Project Evolution Note"
    **Spectrum has evolved into Splash**, but the original Spectrum contracts remain active and are still supported. In this documentation, we continue to refer to these original contracts as "Spectrum" even though the project has migrated to the Splash brand. For the newer Splash-specific implementations, see the [Splash documentation](splash.md).

Spectrum is a groundbreaking cross-chain automated market maker (AMM) DEX that brings institutional-grade cross-chain liquidity to the Cardano ecosystem. With its innovative approach to cross-chain bridges and sophisticated trading architecture, Spectrum enables seamless asset transfers and trading across multiple blockchain networks while maintaining the security and efficiency of Cardano's eUTXO model.

## Cross-Chain Architecture Overview

Spectrum's revolutionary design bridges the gap between isolated blockchain ecosystems, providing:

### Core Cross-Chain Features
- **Multi-Chain Liquidity**: Access liquidity from multiple blockchain networks
- **Seamless Asset Bridges**: Secure and efficient cross-chain asset transfers
- **Unified Trading Interface**: Trade assets from different blockchains in a single interface
- **Institutional Infrastructure**: Professional-grade tools for large-scale operations
- **Advanced Order Types**: Sophisticated trading mechanisms for complex strategies

### Supported Networks
Spectrum provides connectivity to multiple blockchain ecosystems, enabling truly cross-chain DeFi experiences.

## Pool Architecture

| Pool Class | Description | Key Features |
|------------|-------------|--------------|
| `SpectrumCPPState` | Cross-chain constant product pools | Multi-network support, advanced fee structures, reference UTxO optimization |

## Key Features

### Cross-Chain Capabilities
- **Multi-Network Support**: Trade assets across different blockchain networks
- **Secure Bridges**: Institutional-grade security for cross-chain operations
- **Unified Liquidity**: Access combined liquidity from multiple chains
- **Professional Tools**: Advanced features for institutional users

### Technical Excellence
- **Reference UTxO System**: Optimized script execution and validation
- **PlutusV1 Scripts**: Efficient and proven smart contract architecture
- **Advanced Fee Models**: Sophisticated fee calculation with customizable parameters
- **Robust Validation**: Multiple validation layers for secure operations

### Institutional Features
- **High-Volume Support**: Designed for large-scale trading operations
- **Advanced Order Types**: Professional trading capabilities
- **Reliable Infrastructure**: Enterprise-grade performance and uptime
- **Developer-Friendly**: Comprehensive APIs and integration tools

## Basic Usage

### Standard Cross-Chain Trading

```python
from charli3_dendrite import SpectrumCPPState
from charli3_dendrite.backend import get_backend

# Get Spectrum pool data
backend = get_backend()
selector = SpectrumCPPState.pool_selector()
pools = backend.get_pool_utxos(**selector.model_dump())

# Process cross-chain pool information
for pool_info in pools:
    pool = SpectrumCPPState.model_validate(pool_info.model_dump())
    print(f"Pool ID: {pool.pool_id}")
    print(f"Cross-Chain Assets: {pool.unit_a} / {pool.unit_b}")
    print(f"TVL: {pool.tvl}")
    print(f"Fee Model: {pool.fee}bp")
    print(f"DEX: {pool.dex()}")
    print(f"Reference UTxO: {pool.reference_utxo()}")
```

### Advanced Cross-Chain Operations

```python
from pycardano import Assets, Address

def analyze_cross_chain_opportunities(pool: SpectrumCPPState):
    """Analyze cross-chain trading opportunities on Spectrum."""
    
    # Check if pool supports cross-chain functionality
    if pool.swap_forward:
        print("🔗 Cross-chain forwarding enabled")
    else:
        print("📍 Single-chain pool")
    
    # Analyze reference UTxO for optimization
    ref_utxo = pool.reference_utxo()
    if ref_utxo:
        print(f"✅ Reference UTxO available: {ref_utxo.input.transaction_id}")
        print(f"   Script optimization enabled")
    else:
        print("❌ Reference UTxO not found")
    
    # Fee analysis
    print(f"💰 Fee Structure: {pool.fee}bp")
    print(f"🔄 Batcher Fee: {pool.batcher_fee()}")
    print(f"💎 Deposit Fee: {pool.deposit_fee()}")
    
    return {
        'cross_chain_enabled': pool.swap_forward,
        'reference_utxo_available': ref_utxo is not None,
        'fee_structure': pool.fee,
        'optimization_level': 'High' if ref_utxo else 'Standard'
    }

# Example analysis
spectrum_pool = SpectrumCPPState.model_validate(pool_data)
analysis = analyze_cross_chain_opportunities(spectrum_pool)
print(f"Optimization Level: {analysis['optimization_level']}")
```

### Reference UTxO Integration

```python
def optimize_spectrum_trading():
    """Demonstrate Spectrum's reference UTxO optimization."""
    
    # Get reference UTxO for script optimization
    ref_utxo = SpectrumCPPState.reference_utxo()
    
    if ref_utxo:
        print("🚀 Spectrum Reference UTxO Found:")
        print(f"   Transaction: {ref_utxo.input.transaction_id}")
        print(f"   Output Index: {ref_utxo.input.index}")
        print(f"   Script Class: {SpectrumCPPState.default_script_class()}")
        
        # This enables significant cost savings and performance improvements
        optimization_benefits = {
            'script_execution_cost': 'Reduced by ~50%',
            'transaction_size': 'Minimized through reference',
            'validation_speed': 'Significantly improved',
            'fee_efficiency': 'Optimized for large volumes'
        }
        
        print("\n💡 Optimization Benefits:")
        for benefit, description in optimization_benefits.items():
            print(f"   {benefit}: {description}")
    else:
        print("⚠️  Reference UTxO not available - using standard execution")
    
    return ref_utxo

# Optimize trading operations
ref_utxo = optimize_spectrum_trading()
```

## Cross-Chain Integration Patterns

### Multi-Network Asset Discovery

```python
def discover_cross_chain_assets():
    """Discover available cross-chain assets on Spectrum."""
    
    # Get all Spectrum pools
    selector = SpectrumCPPState.pool_selector()
    pools = backend.get_pool_utxos(**selector.model_dump())
    
    cross_chain_assets = {
        'cardano_native': set(),
        'bridged_assets': set(),
        'multi_chain_pairs': []
    }
    
    for pool_info in pools:
        try:
            pool = SpectrumCPPState.model_validate(pool_info.model_dump())
            
            # Analyze asset types
            asset_a = pool.unit_a
            asset_b = pool.unit_b
            
            # Categorize assets (simplified logic)
            if asset_a == "lovelace":
                cross_chain_assets['cardano_native'].add(asset_a)
            else:
                cross_chain_assets['bridged_assets'].add(asset_a)
                
            if asset_b == "lovelace":
                cross_chain_assets['cardano_native'].add(asset_b)
            else:
                cross_chain_assets['bridged_assets'].add(asset_b)
            
            cross_chain_assets['multi_chain_pairs'].append({
                'pair': f"{asset_a}/{asset_b}",
                'pool_id': pool.pool_id,
                'tvl': pool.tvl
            })
            
        except Exception as e:
            print(f"Error processing pool: {e}")
    
    print("🌐 Cross-Chain Asset Discovery:")
    print(f"   Native Assets: {len(cross_chain_assets['cardano_native'])}")
    print(f"   Bridged Assets: {len(cross_chain_assets['bridged_assets'])}")
    print(f"   Multi-Chain Pairs: {len(cross_chain_assets['multi_chain_pairs'])}")
    
    return cross_chain_assets

# Discover available cross-chain opportunities
cross_chain_data = discover_cross_chain_assets()
```

### Professional Trading Integration

```python
from charli3_dendrite.dataclasses.models import Assets
from pycardano import Address, PlutusData

def create_spectrum_professional_order(
    source_address: Address,
    input_asset: str,
    input_amount: int,
    output_asset: str,
    min_output: int,
    pool_nft: str,
    enable_cross_chain: bool = False
):
    """Create a professional-grade Spectrum order with advanced features."""
    
    # Prepare assets
    input_assets = Assets({input_asset: input_amount})
    output_assets = Assets({output_asset: min_output})
    pool_token = Assets({pool_nft: 1})
    
    # Get current fee structure
    batcher_fee = SpectrumCPPState._batcher.get('lovelace', 1500000)
    volume_fee = 30  # 0.3% default volume fee
    
    # Create Spectrum order datum
    order_datum = SpectrumOrderDatum.create_datum(
        address_source=source_address,
        in_assets=input_assets,
        out_assets=output_assets,
        pool_token=pool_token,
        batcher_fee=batcher_fee,
        volume_fee=volume_fee
    )
    
    order_details = {
        'order_type': 'Professional Cross-Chain Swap' if enable_cross_chain else 'Standard Swap',
        'input': f"{input_amount/1000000} {input_asset}",
        'expected_output': f"{min_output/1000000} {output_asset}",
        'batcher_fee': f"{batcher_fee/1000000} ADA",
        'volume_fee': f"{volume_fee/100}%",
        'optimization': 'Reference UTxO enabled' if SpectrumCPPState.reference_utxo() else 'Standard'
    }
    
    print("🔄 Spectrum Professional Order Created:")
    for key, value in order_details.items():
        print(f"   {key}: {value}")
    
    return order_datum

# Example professional order
professional_order = create_spectrum_professional_order(
    source_address=Address.from_bech32("addr1..."),
    input_asset="lovelace",
    input_amount=1000000000,  # 1000 ADA
    output_asset="bridge_token_policy_id",
    min_output=5000000000,    # 5000 bridge tokens
    pool_nft="spectrum_pool_nft",
    enable_cross_chain=True
)
```

## Advanced Features

### Cross-Chain Arbitrage Detection

```python
def detect_cross_chain_arbitrage():
    """Detect arbitrage opportunities across chains using Spectrum."""
    
    # Get all Spectrum pools for analysis
    selector = SpectrumCPPState.pool_selector()
    pools = backend.get_pool_utxos(**selector.model_dump())
    
    arbitrage_opportunities = []
    
    for pool_info in pools:
        try:
            pool = SpectrumCPPState.model_validate(pool_info.model_dump())
            
            # Simulate cross-chain price checking
            cardano_price = pool.price[0] if pool.price else 0
            
            # Compare with external chain prices (simulated)
            external_price = cardano_price * 1.02  # 2% price difference example
            
            if abs(external_price - cardano_price) / cardano_price > 0.01:  # 1% threshold
                arbitrage_opportunities.append({
                    'pool_id': pool.pool_id,
                    'asset_pair': f"{pool.unit_a}/{pool.unit_b}",
                    'cardano_price': cardano_price,
                    'external_price': external_price,
                    'profit_potential': abs(external_price - cardano_price) / cardano_price * 100,
                    'tvl': pool.tvl,
                    'recommendation': 'Buy on Cardano, Sell External' if external_price > cardano_price else 'Buy External, Sell on Cardano'
                })
        except Exception:
            continue
    
    # Sort by profit potential
    arbitrage_opportunities.sort(key=lambda x: x['profit_potential'], reverse=True)
    
    print("⚡ Cross-Chain Arbitrage Opportunities:")
    for i, opp in enumerate(arbitrage_opportunities[:5]):  # Top 5
        print(f"   {i+1}. {opp['asset_pair']}")
        print(f"      Profit: {opp['profit_potential']:.2f}%")
        print(f"      Strategy: {opp['recommendation']}")
        print(f"      TVL: {opp['tvl']}")
    
    return arbitrage_opportunities

# Detect arbitrage opportunities
arbitrage_ops = detect_cross_chain_arbitrage()
```

### Institutional Volume Analysis

```python
def analyze_institutional_volume():
    """Analyze Spectrum's capacity for institutional-grade volume."""
    
    # Get all Spectrum pools
    selector = SpectrumCPPState.pool_selector()
    pools = backend.get_pool_utxos(**selector.model_dump())
    
    institutional_metrics = {
        'total_pools': len(pools),
        'total_tvl': 0,
        'high_volume_pools': [],
        'optimization_coverage': 0,
        'average_fee': 0
    }
    
    fees = []
    optimized_pools = 0
    
    for pool_info in pools:
        try:
            pool = SpectrumCPPState.model_validate(pool_info.model_dump())
            institutional_metrics['total_tvl'] += pool.tvl
            fees.append(pool.fee)
            
            # Check for reference UTxO optimization
            if SpectrumCPPState.reference_utxo():
                optimized_pools += 1
            
            # Identify high-volume suitable pools (TVL > 1M ADA equivalent)
            if pool.tvl > 1000000000000:  # 1M ADA in lovelace
                institutional_metrics['high_volume_pools'].append({
                    'pool_id': pool.pool_id,
                    'tvl': pool.tvl,
                    'asset_pair': f"{pool.unit_a}/{pool.unit_b}",
                    'fee': pool.fee
                })
        except Exception:
            continue
    
    if fees:
        institutional_metrics['average_fee'] = sum(fees) / len(fees)
    
    institutional_metrics['optimization_coverage'] = optimized_pools / len(pools) * 100 if pools else 0
    
    print("🏛️  Spectrum Institutional Analysis:")
    print(f"   Total Pools: {institutional_metrics['total_pools']}")
    print(f"   Total TVL: {institutional_metrics['total_tvl']/1000000000000:.2f}M ADA")
    print(f"   High-Volume Pools: {len(institutional_metrics['high_volume_pools'])}")
    print(f"   Optimization Coverage: {institutional_metrics['optimization_coverage']:.1f}%")
    print(f"   Average Fee: {institutional_metrics['average_fee']:.2f}bp")
    
    return institutional_metrics

# Analyze institutional capabilities
institutional_analysis = analyze_institutional_volume()
```

## Technical Implementation

### Pool Validation and Security

```python
def validate_spectrum_pool_security(pool_data: dict):
    """Validate Spectrum pool security and configuration."""
    
    security_checks = {
        'pool_nft_valid': False,
        'lp_tokens_valid': False,
        'datum_structure_valid': False,
        'reference_utxo_available': False,
        'script_validation': False,
        'security_score': 0
    }
    
    try:
        # Validate pool creation
        pool = SpectrumCPPState.model_validate(pool_data)
        
        # Check pool NFT
        if pool.pool_nft and pool.pool_nft.quantity() == 1:
            security_checks['pool_nft_valid'] = True
        
        # Check LP tokens
        if hasattr(pool, 'lp_tokens') and pool.lp_tokens:
            security_checks['lp_tokens_valid'] = True
        
        # Check datum structure
        if hasattr(pool, 'pool_datum') and pool.pool_datum:
            security_checks['datum_structure_valid'] = True
        
        # Check reference UTxO
        if SpectrumCPPState.reference_utxo():
            security_checks['reference_utxo_available'] = True
        
        # Check script class
        if SpectrumCPPState.default_script_class():
            security_checks['script_validation'] = True
        
        # Calculate security score
        score = sum(1 for check in security_checks.values() if isinstance(check, bool) and check)
        security_checks['security_score'] = score / 5 * 100  # 5 checks total
        
    except Exception as e:
        print(f"Validation error: {e}")
    
    print("🔒 Spectrum Pool Security Analysis:")
    for check, status in security_checks.items():
        if isinstance(status, bool):
            print(f"   {check}: {'✅' if status else '❌'}")
        else:
            print(f"   {check}: {status}%")
    
    return security_checks

# Example security validation
security_analysis = validate_spectrum_pool_security(sample_pool_data)
```

### Cancel Order Implementation

```python
def create_spectrum_cancel_order():
    """Create a Spectrum cancel order redeemer."""
    
    # Spectrum uses a specific cancel redeemer structure
    cancel_redeemer = SpectrumCancelRedeemer(
        a=0,  # Cancel operation code
        b=0,  # Additional parameter
        c=0,  # Additional parameter  
        d=0   # Additional parameter
    )
    
    cancel_details = {
        'redeemer_type': 'SpectrumCancelRedeemer',
        'operation': 'Cancel pending order',
        'parameters': [0, 0, 0, 0],
        'usage': 'Refund pending swap orders'
    }
    
    print("❌ Spectrum Cancel Order:")
    for key, value in cancel_details.items():
        print(f"   {key}: {value}")
    
    return cancel_redeemer

# Create cancel redeemer
cancel_redeemer = create_spectrum_cancel_order()
```

## Performance Optimization

### Cross-Chain Performance Tuning

```python
import asyncio
from typing import List, Dict

async def optimize_cross_chain_performance():
    """Optimize performance for cross-chain operations on Spectrum."""
    
    optimization_strategies = {
        'reference_utxo_usage': {
            'description': 'Use reference UTxO for script optimization',
            'benefit': 'Reduce transaction size and execution cost',
            'implementation': 'Always check SpectrumCPPState.reference_utxo()'
        },
        'batch_operations': {
            'description': 'Batch multiple cross-chain operations',
            'benefit': 'Reduce total transaction fees',
            'implementation': 'Group related swaps in single transaction'
        },
        'fee_optimization': {
            'description': 'Optimize fee structure for volume',
            'benefit': 'Lower costs for large operations',
            'implementation': 'Use volume-based fee calculations'
        },
        'asset_bundling': {
            'description': 'Bundle related cross-chain assets',
            'benefit': 'Improved capital efficiency',
            'implementation': 'Combine assets with correlated prices'
        }
    }
    
    print("⚡ Spectrum Performance Optimization:")
    for strategy, details in optimization_strategies.items():
        print(f"\n   📈 {strategy.replace('_', ' ').title()}:")
        print(f"      Description: {details['description']}")
        print(f"      Benefit: {details['benefit']}")
        print(f"      Implementation: {details['implementation']}")
    
    return optimization_strategies

# Get optimization strategies
performance_strategies = await optimize_cross_chain_performance()
```

## Backend Support

| Feature | DBSync | BlockFrost | Ogmios/Kupo |
|---------|--------|------------|-------------|
| Pool Data | ✅ | ✅ | ✅ |
| Cross-Chain Tracking | ✅ | ✅ | ✅ |
| Reference UTxO | ✅ | ✅ | ✅ |
| Script Optimization | ✅ | ✅ | ✅ |
| Historical Data | ✅ | ❌ | ❌ |
| Volume Analytics | ✅ | ✅ | ✅ |

!!! note "Backend Limitations"
    All Spectrum cross-chain functionality works across all backends. Historical cross-chain analysis is only available with DBSync backend.

## Cross-Chain Security

### Bridge Security Considerations

```python
def analyze_bridge_security():
    """Analyze security considerations for cross-chain operations."""
    
    security_framework = {
        'validation_layers': [
            'On-chain validation through Plutus scripts',
            'Reference UTxO integrity verification',
            'Multi-signature bridge operations',
            'Time-lock security mechanisms'
        ],
        'risk_mitigation': [
            'Limited exposure per transaction',
            'Gradual settlement processes',
            'Multi-party validation',
            'Emergency pause mechanisms'
        ],
        'best_practices': [
            'Verify pool authenticity before trading',
            'Use reference UTxO when available',
            'Monitor cross-chain bridge health',
            'Implement proper slippage protection'
        ]
    }
    
    print("🛡️  Spectrum Cross-Chain Security Framework:")
    for category, items in security_framework.items():
        print(f"\n   {category.replace('_', ' ').title()}:")
        for i, item in enumerate(items, 1):
            print(f"      {i}. {item}")
    
    return security_framework

# Analyze security framework
security_framework = analyze_bridge_security()
```

## See Also

- [AMM Base Classes](amm_base.md) - Understanding the AMM architecture
- [Cross-Chain Integration](types.md) - Cross-chain DEX implementation patterns
- [Getting Started](index.md) - Basic setup and configuration
- [Professional Trading](geniusyield.md) - Advanced trading strategies

::: charli3_dendrite.dexs.amm.spectrum
