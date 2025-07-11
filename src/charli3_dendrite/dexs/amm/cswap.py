"""CSwap DEX Module."""

from dataclasses import dataclass
from dataclasses import field
from typing import Any
from typing import ClassVar
from typing import List
from typing import Union

from pycardano import Address
from pycardano import PlutusData
from pycardano import PlutusV1Script
from pycardano import PlutusV2Script
from pycardano import PlutusV3Script
from pycardano import Redeemer

from charli3_dendrite.dataclasses.datums import OrderDatum
from charli3_dendrite.dataclasses.datums import PlutusFullAddress
from charli3_dendrite.dataclasses.datums import PoolDatum
from charli3_dendrite.dataclasses.models import Assets
from charli3_dendrite.dataclasses.models import OrderType
from charli3_dendrite.dataclasses.models import PoolSelector
from charli3_dendrite.dexs.amm.amm_types import AbstractConstantProductPoolState
from charli3_dendrite.dexs.core.errors import NotAPoolError


@dataclass
class CSwapOrderSwapType(PlutusData):
    """CSwap order type (Swap only)."""

    CONSTR_ID = 0


@dataclass
class CSwapOrderZapInType(PlutusData):
    """CSwap order type (Swap only)."""

    CONSTR_ID = 1


@dataclass
class CSwapOrderZapOutType(PlutusData):
    """CSwap order type (Swap only)."""

    CONSTR_ID = 2


@dataclass
class CSwapOrderDatum(OrderDatum):
    """CSwap order datum with ADA-only pair restriction."""

    CONSTR_ID = 0

    address: PlutusFullAddress  # Field 0: Complex address structure
    target_assets: List[List[Union[bytes, int]]]
    input_assets: List[List[Union[bytes, int]]]
    otype: Union[CSwapOrderSwapType | CSwapOrderZapInType | CSwapOrderZapOutType]
    slippage: int = 50
    platform_fee: int = 15

    @classmethod
    def create_datum(
        cls,
        address_source: Address,
        in_assets: Assets,
        out_assets: Assets,
        batcher_fee: Assets,
        deposit: Assets,
        address_target: Address | None = None,
        datum_target: PlutusData | None = None,
    ) -> "CSwapOrderDatum":
        """Create a CSwap order datum."""
        # Validate ADA-only restriction
        merged_assets = in_assets + out_assets
        if "lovelace" not in merged_assets:
            raise ValueError("CSWAP only supports ADA pairs - one token must be ADA")

        full_address = PlutusFullAddress.from_address(address_source)

        # Create target assets list (what we want to receive)
        target_assets = []
        for unit in out_assets:
            if unit == "lovelace":
                target_assets.append([b"", b"", out_assets[unit]])
            else:
                policy = bytes.fromhex(unit[:56])
                name = bytes.fromhex(unit[56:])
                target_assets.append([policy, name, out_assets[unit]])

        # Add minimum ADA requirement (2 ADA minimum)
        if "lovelace" not in out_assets:
            target_assets.append([b"", b"", 2000000])

        # Create input assets list (always zero quantity for input)
        input_assets = []
        for unit in in_assets:
            if unit == "lovelace":
                input_assets.append([b"", b"", 0])
            else:
                policy = bytes.fromhex(unit[:56])
                name = bytes.fromhex(unit[56:])
                input_assets.append([policy, name, 0])

        return cls(
            address=full_address,
            target_assets=target_assets,
            input_assets=input_assets,
            otype=CSwapOrderSwapType(),
            slippage=50,  # 0.5% default slippage
            platform_fee=15,  # 0.15% platform fee
        )

    def address_source(self) -> Address:
        """Get the source address."""
        return self.address.to_address()

    def requested_amount(self) -> Assets:
        """Get the requested amount."""
        requested = {}
        for target in self.target_assets:
            policy = target[0].hex() if target[0] else ""
            name = target[1].hex() if target[1] else ""
            unit = policy + name if policy + name else "lovelace"
            quantity = target[2]
            if unit != "lovelace" or quantity > 2000000:  # Skip minimum ADA requirement
                requested[unit] = quantity
        return Assets(requested)

    def order_type(self) -> OrderType:
        """Get the order type."""
        return OrderType.swap


@dataclass
class CSwapPoolDatum(PoolDatum):
    """CSwap pool datum with LP token tracking."""

    CONSTR_ID = 0

    total_lp_tokens: int  # Field 0: total lp tokens issued
    pool_fee: int  # Field 1: pool fee per 10K (85 = 0.85%)
    quote_policy: bytes  # Field 2: quote policy id - ADA (empty)
    quote_name: bytes  # Field 3: quote asset name - ADA (empty)
    base_policy: bytes  # Field 4: base policy id - token policy
    base_name: bytes  # Field 5: base asset name - token name
    lp_token_policy: bytes  # Field 6: lp token policy id
    lp_token_name: bytes  # Field 7: lp token asset name

    def pool_pair(self) -> Assets | None:
        """Return the pool pair assets."""
        quote_unit = "lovelace"
        base_unit = (self.base_policy + self.base_name).hex()
        if not base_unit:
            base_unit = "lovelace"

        return Assets(**{quote_unit: 0, base_unit: 0})


class CSwapCPPState(AbstractConstantProductPoolState):
    """CSwap CPP state with beacon token validation."""

    fee: int = 85  # Pool fee per 10K (0.85%)
    _batcher = Assets(lovelace=690000)  # 0.69 ADA batcher fee
    _deposit = Assets(lovelace=2000000)  # 2 ADA deposit
    _stake_address: ClassVar[Address] = Address.decode(
        "addr1z8d9k3aw6w24eyfjacy809h68dv2rwnpw0arrfau98jk6nhv88awp8sgxk65d6kry0mar3rd0dlkfljz7dv64eu39vfs38yd9p"
    )

    @classmethod
    def dex(cls) -> str:
        """Get the DEX name."""
        return "CSWAP"

    @classmethod
    def order_selector(cls) -> list[str]:
        """Get the order selector."""
        return [cls._stake_address.encode()]

    @classmethod
    def pool_selector(cls) -> PoolSelector:
        """Get the pool selector."""
        return PoolSelector(
            addresses=[
                "addr1z8ke0c9p89rjfwmuh98jpt8ky74uy5mffjft3zlcld9h7ml3lmln3mwk0y3zsh3gs3dzqlwa9rjzrxawkwm4udw9axhs6fuu6e"
            ]
        )

    @property
    def swap_forward(self) -> bool:
        """Check if swap forwarding is enabled."""
        return False

    @property
    def stake_address(self) -> Address:
        """Get the stake address."""
        return self._stake_address

    @classmethod
    def order_datum_class(cls) -> type[CSwapOrderDatum]:
        """Get the order datum class."""
        return CSwapOrderDatum

    @classmethod
    def pool_datum_class(cls) -> type[CSwapPoolDatum]:
        """Get the pool datum class."""
        return CSwapPoolDatum

    @property
    def pool_id(self) -> str:
        """A unique identifier for the pool."""
        return f"cswap-{self.unit_a}-{self.unit_b}"

    @classmethod
    def extract_pool_nft(cls, values: dict[str, Any]) -> Assets | None:
        """Extract the CSwap pool NFT from the UTXO.

        CSwap uses a pool NFT system similar to Splash and Spectrum. The pool NFT:
        - Has name "c" (single character, hex: 63)
        - Has quantity of exactly 1
        - Policy ID varies between pools

        Args:
            values: The pool UTXO inputs.

        Returns:
            Assets: The pool NFT or None if not found.
        """
        assets = values["assets"]

        # If the pool NFT is already extracted, validate it
        if "pool_nft" in values:
            pool_nft = Assets(**dict(values["pool_nft"].items()))
            if pool_nft.quantity() != 1:
                raise NotAPoolError("CSWAP pool NFT must have quantity of exactly 1")

            # Check if token name is "c" (hex: 63)
            unit = pool_nft.unit()
            if len(unit) < 56 or unit[56:] != "63":  # "c" in hex
                raise NotAPoolError("CSWAP pool NFT must have name 'c'")

            return pool_nft

        # Search for pool NFT with name "c"
        pool_nft = None
        for asset_unit in assets:
            # Skip lovelace
            if asset_unit == "lovelace":
                continue

            # Check if token name is "c" (hex: 63)
            if len(asset_unit) >= 56 and asset_unit[56:] == "63":
                quantity = assets[asset_unit]
                if quantity == 1:
                    pool_nft = Assets(root={asset_unit: assets.root.pop(asset_unit)})
                    break

        if pool_nft is None:
            raise NotAPoolError(
                "CSWAP pool must contain exactly one pool NFT with name 'c'"
            )

        values["pool_nft"] = pool_nft
        return pool_nft

    def get_amount_out(
        self,
        asset: Assets,
        precise: bool = True,
    ) -> tuple[Assets, float]:
        """Get the output asset amount given an input asset amount.

        Validates ADA-only restriction before processing.
        """
        # Validate ADA-only restriction
        if "lovelace" not in [self.unit_a, self.unit_b]:
            raise ValueError("CSWAP only supports ADA pairs - one token must be ADA")

        if asset.unit() not in [self.unit_a, self.unit_b]:
            raise ValueError(f"Asset {asset.unit()} not valid for this pool")

        if len(asset) != 1:
            raise ValueError("Only one asset can be provided for swap calculation")

        # Ensure one of the pair assets is ADA
        merged_test = Assets(**{asset.unit(): 1, "lovelace": 1})
        if not any(unit in [self.unit_a, self.unit_b] for unit in merged_test):
            raise ValueError("CSWAP only supports ADA pairs")

        return super().get_amount_out(asset, precise)

    def get_amount_in(
        self,
        asset: Assets,
        precise: bool = True,
    ) -> tuple[Assets, float]:
        """Get the input asset amount given a desired output asset amount.

        Validates ADA-only restriction before processing.
        """
        # Validate ADA-only restriction
        if "lovelace" not in [self.unit_a, self.unit_b]:
            raise ValueError("CSWAP only supports ADA pairs - one token must be ADA")

        if asset.unit() not in [self.unit_a, self.unit_b]:
            raise ValueError(f"Asset {asset.unit()} not valid for this pool")

        if len(asset) != 1:
            raise ValueError("Only one asset can be provided for swap calculation")

        # Ensure one of the pair assets is ADA
        merged_test = Assets(**{asset.unit(): 1, "lovelace": 1})
        if not any(unit in [self.unit_a, self.unit_b] for unit in merged_test):
            raise ValueError("CSwap only supports ADA pairs")

        return super().get_amount_in(asset, precise)

    @classmethod
    def skip_init(cls, values: dict[str, Any]) -> bool:
        """Skip initialization if pool NFT is already present.

        Args:
            values: The pool UTXO inputs.

        Returns:
            bool: True if initialization should be skipped, False otherwise.
        """
        if "pool_nft" in values:
            # Pool NFT already extracted, just validate assets format
            if not isinstance(values["assets"], Assets):
                values["assets"] = Assets.model_validate(values["assets"])

            return True
        else:
            return False

    @classmethod
    def post_init(cls, values: dict[str, Any]) -> dict[str, Any]:
        """Post initialization for CSwap pools."""
        super().post_init(values)

        assets = values["assets"]

        # Validate this is an ADA pair
        asset_units = list(assets.root.keys())
        if "lovelace" not in asset_units:
            raise NotAPoolError("CSWAP pools must contain ADA (lovelace)")

        # Subtract 2 ADA pool maintenance from lovelace reserves
        # CSwap pools require 2 ADA minimum to maintain the pool
        if len(assets) == 2:
            assets.root["lovelace"] -= 2000000  # 2 ADA maintenance

        # Parse datum if available, add in 15 basis points for platform fee
        if "datum_cbor" in values:
            try:
                datum = CSwapPoolDatum.from_cbor(values["datum_cbor"])
                values["fee"] = datum.pool_fee + 15
            except Exception:
                # If datum parsing fails, use default fee
                values["fee"] = 85 + 15

        return values

    @classmethod
    def default_script_class(
        cls,
    ) -> type[PlutusV1Script] | type[PlutusV2Script] | type[PlutusV3Script]:
        """Get default script class as Plutus V3."""
        return PlutusV3Script

    @classmethod
    def cancel_redeemer(cls) -> PlutusData:
        """Returns the redeemer data for canceling transaction."""
        return Redeemer(CSwapOrderSwapType())
