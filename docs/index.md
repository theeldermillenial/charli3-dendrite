# Welcome to Charli3 Dendrite Documentation

Get ready to dive into the incredible world of decentralized exchanges (DEXs) on the Cardano blockchain! With Charli3 Dendrite, we've integrated some of the most exciting and innovative DEXs out there, each offering unique features that are transforming the way we trade and manage liquidity on Cardano.

## Getting Started

### Installation

Install Charli3 Dendrite using pip or Poetry:

```bash
# Using pip
pip install charli3_dendrite

# Using Poetry
poetry add charli3_dendrite
```

### Quick Start

Here's a simple example to get you started with fetching pool data from Minswap:

```python
from charli3_dendrite import MinswapCPPState
from charli3_dendrite.backend import set_backend
from charli3_dendrite.backend.blockfrost import BlockFrostBackend

# Configure backend (using BlockFrost for this example)
set_backend(BlockFrostBackend("your-blockfrost-project-id"))

# Get Minswap pool data
from charli3_dendrite.backend import get_backend
backend = get_backend()

selector = MinswapCPPState.pool_selector()
pools = backend.get_pool_utxos(limit=10, **selector.model_dump())

# Process the results
for pool_info in pools:
    try:
        pool = MinswapCPPState.model_validate(pool_info.model_dump())
        print(f"Pool TVL: {pool.tvl}")
        print(f"Price A->B: {pool.price[0]}, Price B->A: {pool.price[1]}")
        print(f"Assets: {pool.unit_a} / {pool.unit_b}")
        print("---")
    except Exception as e:
        print(f"Error processing pool: {e}")
```

### Backend Configuration

Charli3 Dendrite supports three backend types:

- **DBSync**: Full-featured SQL database backend (recommended for production)
- **BlockFrost**: API-based backend (good for development and testing)  
- **Ogmios/Kupo**: Node-based backend (for custom node setups)

See the [Backend Configuration](backend_base.md) guide for detailed setup instructions.

## Supported DEXs

### [Vyfi](https://vyfi.io)
  - **VyFi (VyFinance)** is nothing short of a game-changer on Cardano! This all-in-one DeFi platform delivers a powerhouse of tools, including a top-notch DEX and yield farming opportunities that cater to both newbies and seasoned pros. VyFi is your gateway to unlocking the full potential of DeFi on Cardano!

### [Minswap](https://minswap.org)
  - **Minswap** is where simplicity meets power on Cardano. As a community-driven AMM DEX, Minswap makes trading tokens and earning rewards a breeze. Whether you're new to DeFi or a veteran, Minswap's user-friendly design and robust features make it an essential stop on your Cardano journey.

### [Muesliswap](https://muesliswap.com)
  - **MuesliSwap** is not just any DEX; it's a trailblazer as the first order book-based DEX on Cardano! With MuesliSwap, you're in control, placing orders directly on the blockchain for a truly unique and hands-on trading experience. Step away from the AMM crowd and discover the distinct advantages of MuesliSwap!

### [Spectrum](https://spectrum.fi)
  - **Spectrum** (formerly ErgoDEX) is revolutionizing the cross-chain world by seamlessly connecting the Cardano and Ergo blockchains. With Spectrum, you can execute secure and efficient token swaps across networks, expanding your reach and enhancing interoperability like never before. This is the future of cross-chain trading!

### [Splash](https://splash.fi)
  - **Splash** brings innovative bidirectional swap capabilities to Cardano! This advanced AMM DEX supports multiple pool types including Constant Product Pools (CPP), Stable Swap Pools (SSP), and unique bidirectional pools that offer enhanced trading flexibility. Splash's sophisticated architecture makes it perfect for users seeking advanced DeFi strategies and optimal liquidity management.

### [Sundae](https://sundaeswap.finance)
  - **SundaeSwap** has quickly become a fan favorite among Cardano users, and it's easy to see why! This AMM DEX is as sweet as its name, offering an intuitive interface for token swaps and liquidity provision. SundaeSwap's vibrant community and user-centric approach make it the perfect choice for anyone looking to get the most out of Cardano's DeFi ecosystem.

### [Wingriders](https://wingriders.com)
  - **WingRiders** takes performance to new heights! This high-speed AMM DEX on Cardano is all about delivering deep liquidity and lightning-fast transaction speeds, making it a go-to platform for traders looking to move large volumes with efficiency and ease. Fly high with WingRiders and experience trading like never before!

### [Genius Yield](https://www.geniusyield.co/)
  - **Genius Yield** is not just a DEX; it's a smart liquidity management powerhouse on Cardano! By combining a DEX with intelligent yield optimization, Genius Yield helps you maximize your returns while enjoying a seamless and sophisticated trading experience. Get ready to be amazed by the future of DeFi with Genius Yield!

### [Axo](https://www.axo.trade/) ⚠️ DEPRECATED

!!! warning "Deprecated - Reference Only"
    **Axo has left the Cardano ecosystem** and is no longer supported. Documentation is maintained for reference only and will be removed in a future version. Consider [GeniusYield](https://www.geniusyield.co/) for order book functionality.

**Axo** was an advanced order book DEX on Cardano designed for serious traders, offering customizable strategies and high-performance order execution for both retail and institutional users.

## Special Thanks

A huge shoutout to [SteelSwap](https://steelswap.io) for their incredible collaboration and unwavering support in making Charli3 Dendrite a reality. SteelSwap has been a cornerstone in this project, and we couldn't have done it without them. Here's to the exciting future we're building together!
