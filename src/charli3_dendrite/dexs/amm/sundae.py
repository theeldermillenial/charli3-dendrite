"""SundaeSwap DEX module."""

import time
from dataclasses import dataclass
from functools import lru_cache
from typing import Any
from typing import ClassVar
from typing import List
from typing import Union
from typing import cast

from pycardano import Address
from pycardano import Datum
from pycardano import PlutusData
from pycardano import PlutusV1Script
from pycardano import PlutusV2Script
from pycardano import PlutusV3Script
from pycardano import VerificationKeyHash

from charli3_dendrite.backend import get_backend
from charli3_dendrite.dataclasses.datums import AssetClass
from charli3_dendrite.dataclasses.datums import OrderDatum
from charli3_dendrite.dataclasses.datums import PlutusFullAddress
from charli3_dendrite.dataclasses.datums import PlutusNone
from charli3_dendrite.dataclasses.datums import PlutusPartAddress
from charli3_dendrite.dataclasses.datums import PlutusScriptAddress
from charli3_dendrite.dataclasses.datums import PoolDatum
from charli3_dendrite.dataclasses.datums import ReceiverDatum
from charli3_dendrite.dataclasses.models import Assets
from charli3_dendrite.dataclasses.models import OrderType
from charli3_dendrite.dataclasses.models import PoolSelector
from charli3_dendrite.dexs.amm.amm_types import AbstractConstantProductPoolState
from charli3_dendrite.dexs.amm.amm_types import AbstractStableSwapPoolState
from charli3_dendrite.dexs.amm.sundae_v4_stableswap_math import STABLESWAP_PRECISION
from charli3_dendrite.dexs.amm.sundae_v4_stableswap_math import stableswap_d
from charli3_dendrite.dexs.amm.sundae_v4_stableswap_math import stableswap_swap
from charli3_dendrite.dexs.amm.sundae_v4_stableswap_math import stableswap_y
from charli3_dendrite.dexs.core.errors import InvalidPoolError
from charli3_dendrite.dexs.core.errors import NoAssetsError
from charli3_dendrite.dexs.core.errors import NotAPoolError

# A swap-all SundaeSwap V3 stableswap order offers this multiple of its expected
# input, so any realistic delivery is swapped in full.
SWAP_ALL_OFFER_MULTIPLE = 2

# The largest quantity of one asset a ledger value can hold.
_LEDGER_MAX = 2**64 - 1
# Swap fees are quoted in basis points.
_FEE_BASIS = 10_000


@dataclass
class AtoB(PlutusData):
    """A to B swap direction."""

    CONSTR_ID = 0


@dataclass
class BtoA(PlutusData):
    """B to A swap direction."""

    CONSTR_ID = 1


@dataclass
class AmountOut(PlutusData):
    """Minimum amount to receive."""

    CONSTR_ID = 0
    min_receive: int


@dataclass
class SwapConfig(PlutusData):
    """Swap configuration."""

    CONSTR_ID = 0

    direction: Union[AtoB, BtoA]
    amount_in: int
    amount_out: AmountOut


@dataclass
class DepositPairQuantity(PlutusData):
    """Deposit pair quantity."""

    CONSTR_ID = 0
    amount_a: int
    amount_b: int


@dataclass
class DepositPair(PlutusData):
    """Deposit pair."""

    CONSTR_ID = 1
    assets: DepositPairQuantity


@dataclass
class DepositConfig(PlutusData):
    """Deposit configuration."""

    CONSTR_ID = 2

    deposit_pair: DepositPair


@dataclass
class WithdrawConfig(PlutusData):
    """Withdraw configuration."""

    CONSTR_ID = 1

    amount_lp: int


@dataclass
class SundaeV3PlutusNone(PlutusData):
    CONSTR_ID = 0


@dataclass
class SundaeV3ReceiverDatumHash(PlutusData):
    CONSTR_ID = 1

    datum_hash: bytes


@dataclass
class SundaeV3ReceiverInlineDatum(PlutusData):
    CONSTR_ID = 2

    datum: Datum


@dataclass
class SundaeV3ReceiverInlineDatumHash(PlutusData):
    """Inline-datum receiver identified by the 32-byte hash of the datum the batcher
    attaches inline to the forwarded output (``Constr 2 [B <hash>]``). Unlike
    ``SundaeV3ReceiverInlineDatum``, which embeds the datum itself, receivers such as
    Minswap V2 carry only the hash and verify the attached inline datum against it.
    """

    CONSTR_ID = 2

    datum_hash: bytes


@dataclass
class SundaeAddressWithDatum(PlutusData):
    """SundaeSwap address with datum."""

    CONSTR_ID = 0

    address: Union[PlutusFullAddress, PlutusScriptAddress]
    datum: Union[
        ReceiverDatum,
        PlutusNone,
    ]

    @classmethod
    def from_address(cls, address: Address) -> "SundaeAddressWithDatum":
        """Create a new address with datum."""
        return cls(address=PlutusFullAddress.from_address(address), datum=PlutusNone())


@dataclass
class SundaeV3AddressWithDatum(PlutusData):
    CONSTR_ID = 0

    address: Union[PlutusFullAddress, PlutusScriptAddress]
    datum: Union[
        SundaeV3PlutusNone,
        SundaeV3ReceiverDatumHash,
        SundaeV3ReceiverInlineDatum,
    ]

    @classmethod
    def from_address(cls, address: Address):
        return cls(
            address=PlutusFullAddress.from_address(address),
            datum=SundaeV3PlutusNone(),
        )


@dataclass
class SundaeAddressWithDestination(PlutusData):
    """For now, destination is set to none, should be updated."""

    CONSTR_ID = 0

    address: SundaeAddressWithDatum
    destination: Union[PlutusPartAddress, PlutusNone]

    @classmethod
    def from_address(cls, address: Address) -> "SundaeAddressWithDestination":
        """Create a new address with destination."""
        null = SundaeAddressWithDatum.from_address(address)
        return cls(address=null, destination=PlutusNone())


@dataclass
class SundaeOrderDatum(OrderDatum):
    """SundaeSwap order datum."""

    ident: bytes
    address: SundaeAddressWithDestination
    fee: int
    swap: Union[DepositConfig, SwapConfig, WithdrawConfig]

    @classmethod
    def create_datum(
        cls,
        ident: bytes,
        address_source: Address,
        in_assets: Assets,
        out_assets: Assets,
        fee: int,
    ) -> "SundaeOrderDatum":
        """Create a new order datum."""
        full_address = SundaeAddressWithDestination.from_address(address_source)
        merged = in_assets + out_assets
        if in_assets.unit() == merged.unit():
            direction = AtoB()
        else:
            direction = BtoA()
        swap = SwapConfig(
            direction=direction,
            amount_in=in_assets.quantity(),
            amount_out=AmountOut(min_receive=out_assets.quantity()),
        )

        return cls(ident=ident, address=full_address, fee=fee, swap=swap)

    def address_source(self) -> Address:
        """Get the source address."""
        return self.address.address.address.to_address()

    def requested_amount(self) -> Assets:
        """Get the requested amount."""
        if isinstance(self.swap, SwapConfig):
            if isinstance(self.swap.direction, AtoB):
                return Assets({"asset_b": self.swap.amount_out.min_receive})
            else:
                return Assets({"asset_a": self.swap.amount_out.min_receive})
        else:
            return Assets({})

    def order_type(self) -> OrderType | None:
        """Get the order type."""
        order_type = None
        if isinstance(self.swap, SwapConfig):
            order_type = OrderType.swap
        elif isinstance(self.swap, DepositConfig):
            order_type = OrderType.deposit
        elif isinstance(self.swap, WithdrawConfig):
            order_type = OrderType.withdraw

        return order_type


@dataclass
class SwapV3Config(PlutusData):
    CONSTR_ID = 1
    in_value: List[Union[int, bytes]]
    out_value: List[Union[int, bytes]]


@dataclass
class DepositV3Config(PlutusData):
    CONSTR_ID = 2
    values: List[List[Union[int, bytes]]]


@dataclass
class WithdrawV3Config(PlutusData):
    CONSTR_ID = 3
    in_value: List[Union[int, bytes]]


# @dataclass
# class ZapInV3Config(PlutusData):
#     CONSTR_ID = 4
#     in_value: List[Union[int, bytes]]
#     out_value: List[Union[int, bytes]]


# @dataclass
# class ZapOutV3Config(PlutusData):
#     CONSTR_ID = 5
#     token_a: int
#     token_b: int


@dataclass
class DonateV3Config(PlutusData):
    CONSTR_ID = 4
    in_value: List[Union[int, bytes]]
    out_value: List[Union[int, bytes]]


@dataclass
class Ident(PlutusData):
    CONSTR_ID = 0
    payload: bytes


@dataclass
class SundaeV3OrderDatum(OrderDatum):
    CONSTR_ID = 0

    ident: Ident
    owner: PlutusPartAddress
    max_protocol_fee: int
    destination: SundaeV3AddressWithDatum
    swap: Union[
        DepositV3Config,
        WithdrawV3Config,
        # ZapInV3Config,
        # ZapOutV3Config,
        DonateV3Config,
        SwapV3Config,
    ]
    extension: Union[Datum, bytes]

    @classmethod
    def create_datum(
        cls,
        ident: bytes,
        address_source: Address,
        in_assets: Assets,
        out_assets: Assets,
        fee: int,
        address_target: Address | None = None,
        datum_target: PlutusData | None = None,
    ):
        # Swap forwarding: when a target address is supplied the filled output
        # is sent there with an optional inline receiver datum (so it can fund
        # the next order in a cross-protocol chain) instead of returning to the
        # source wallet. No target -> source, no inline datum.
        if address_target is None:
            full_address = SundaeV3AddressWithDatum.from_address(address_source)
        else:
            receiver_datum = (
                SundaeV3ReceiverInlineDatum(datum=datum_target)
                if datum_target is not None
                else SundaeV3PlutusNone()
            )
            full_address = SundaeV3AddressWithDatum(
                address=PlutusFullAddress.from_address(address_target),
                datum=receiver_datum,
            )
        merged = in_assets + out_assets
        if in_assets.unit() == merged.unit():
            direction = AtoB()
        else:
            direction = BtoA()
        swap = SwapConfig(
            direction=direction,
            amount_in=in_assets.quantity(),
            amount_out=AmountOut(min_receive=out_assets.quantity()),
        )

        if in_assets.unit() == "lovelace":
            in_policy = in_name = ""
        else:
            in_policy = in_assets.unit()[:56]
            in_name = in_assets.unit()[56:]

        if out_assets.unit() == "lovelace":
            out_policy = out_name = ""
        else:
            out_policy = out_assets.unit()[:56]
            out_name = out_assets.unit()[56:]

        in_value = [
            bytes.fromhex(in_policy),
            bytes.fromhex(in_name),
            in_assets.quantity(),
        ]
        out_value = [
            bytes.fromhex(out_policy),
            bytes.fromhex(out_name),
            out_assets.quantity(),
        ]

        return cls(
            ident=Ident(payload=ident),
            owner=PlutusPartAddress(address=address_source.staking_part.payload),
            max_protocol_fee=fee,
            destination=full_address,
            swap=SwapV3Config(in_value=in_value, out_value=out_value),
            extension=PlutusData().to_cbor(),
        )

    def address_source(self) -> Address:
        return Address(staking_part=VerificationKeyHash(self.owner.address))

    def requested_amount(self) -> Assets:
        if isinstance(self.swap, SwapV3Config):
            asset = (self.swap.out_value[0] + self.swap.out_value[1]).hex()
            if asset == "":
                asset = "lovelace"
            return Assets({asset: self.swap.out_value[2]})
        else:
            return Assets({})

    def order_type(self) -> OrderType:
        order_type = None
        if isinstance(self.swap, SwapV3Config):
            order_type = OrderType.swap
        elif isinstance(self.swap, DepositV3Config):
            order_type = OrderType.deposit
        elif isinstance(self.swap, WithdrawV3Config):
            order_type = OrderType.withdraw

        return order_type


@dataclass
class LPFee(PlutusData):
    """Liquidity pool fee."""

    CONSTR_ID = 0
    numerator: int
    denominator: int


@dataclass
class LiquidityPoolAssets(PlutusData):
    """Liquidity pool assets."""

    CONSTR_ID = 0
    asset_a: AssetClass
    asset_b: AssetClass


@dataclass
class SundaePoolDatum(PoolDatum):
    """SundaeSwap pool datum."""

    assets: LiquidityPoolAssets
    ident: bytes
    last_swap: int
    fee: LPFee

    def pool_pair(self) -> Assets | None:
        return self.assets.asset_a.assets + self.assets.asset_b.assets


@dataclass
class SundaeV3PoolDatum(PlutusData):
    CONSTR_ID = 0
    ident: bytes
    assets: List[List[bytes]]
    circulation_lp: int
    bid_fees_per_10_thousand: int
    ask_fees_per_10_thousand: int
    fee_manager: Union[PlutusNone, Any]
    market_open: int  # time in milliseconds
    protocol_fees: int

    def pool_pair(self) -> Assets | None:
        assets = {}
        for asset in self.assets:
            assets[asset[0].hex() + asset[1].hex()] = 0
        if "" in assets:
            assets.pop("")
            assets["lovelace"] = 0
        return Assets(**assets)


@dataclass
class SundaeV3StablePoolDatum(PlutusData):
    CONSTR_ID = 0
    ident: bytes
    assets: List[List[bytes]]
    circulation_lp: int
    lp_fee_basis_points: list[int]
    protocol_fee_basis_points: list[int]
    fee_manager: Union[PlutusNone, Any]
    market_open: int  # time in milliseconds
    protocol_fees: list[int]  # [scooper fees, asset A lp_fee, asset B lp_fee]
    amp: int
    sum_invariant: int
    linear_amplification_manager: Union[PlutusNone, Any]

    def pool_pair(self) -> Assets | None:
        assets = {}
        for asset in self.assets:
            assets[asset[0].hex() + asset[1].hex()] = 0
        if "" in assets:
            assets.pop("")
            assets["lovelace"] = 0
        return Assets(**assets)


@dataclass
class SundaeV3Settings(PlutusData):
    CONSTR_ID = 0
    settings_admin: Datum  # NativeScript
    metadata_admin: PlutusFullAddress
    treasury_admin: Datum  # NativeScript
    treasury_address: PlutusFullAddress
    treasury_allowance: List[int]
    authorized_scoopers: Union[PlutusNone, Any]  # List[PlutusPartAddress]]
    authorized_staking_keys: List[Any]
    base_fee: int
    simple_fee: int
    strategy_fee: int
    pool_creation_fee: int
    extensions: Union[Datum, bytes]


class SundaeSwapCPPState(AbstractConstantProductPoolState):
    """SundaeSwap constant product pool state."""

    fee: int = 0
    _batcher = Assets(lovelace=2500000)
    _deposit = Assets(lovelace=2000000)
    _stake_address: ClassVar[Address] = Address.from_primitive(
        "addr1wxaptpmxcxawvr3pzlhgnpmzz3ql43n2tc8mn3av5kx0yzs09tqh8",
    )

    @classmethod
    def dex(cls) -> str:
        """Get the DEX name."""
        return "SundaeSwap"

    @classmethod
    def order_selector(self) -> list[str]:
        """Get the order selector."""
        return [self._stake_address.encode()]

    @classmethod
    def pool_selector(cls) -> PoolSelector:
        return PoolSelector(
            addresses=["addr1w9qzpelu9hn45pefc0xr4ac4kdxeswq7pndul2vuj59u8tqaxdznu"],
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
    def order_datum_class(self) -> type[SundaeOrderDatum]:
        """Get the order datum class."""
        return SundaeOrderDatum

    @classmethod
    def pool_datum_class(cls) -> type[SundaePoolDatum]:
        """Get the pool datum class."""
        return SundaePoolDatum

    @property
    def pool_id(self) -> str:
        """A unique identifier for the pool."""
        return self.pool_nft.unit()

    @classmethod
    def skip_init(cls, values) -> bool:
        """Skip the initialization process."""
        if "pool_nft" in values and "dex_nft" in values and "fee" in values:
            try:
                super().extract_pool_nft(values)
            except InvalidPoolError:
                raise NotAPoolError("No pool NFT found.")
            if len(values["assets"]) == 3:
                # Send the ADA token to the end
                if isinstance(values["assets"], Assets):
                    values["assets"].root["lovelace"] = values["assets"].root.pop(
                        "lovelace",
                    )
                else:
                    values["assets"]["lovelace"] = values["assets"].pop("lovelace")
            values["assets"] = Assets.model_validate(values["assets"])
            return True
        else:
            return False

    @classmethod
    def extract_pool_nft(cls, values) -> Assets:
        """Extract the pool NFT."""
        try:
            super().extract_pool_nft(values)
        except InvalidPoolError:
            if len(values["assets"]) == 0:
                raise NoAssetsError
            else:
                raise NotAPoolError("No pool NFT found.")

    @classmethod
    def pool_policy(cls) -> list[str]:
        """Get the pool policy."""
        return ["0029cb7c88c7567b63d1a512c0ed626aa169688ec980730c0473b91370"]

    @classmethod
    def post_init(cls, values):
        """Post initialization."""
        super().post_init(values)

        assets = values["assets"]
        datum = SundaePoolDatum.from_cbor(values["datum_cbor"])

        if len(assets) == 2:
            assets.root[assets.unit(0)] -= 2000000
        elif len(assets) == 1:
            msg = "Reserves contains only 1 token."
            raise InvalidPoolError(msg)

        numerator = datum.fee.numerator
        denominator = datum.fee.denominator
        values["fee"] = int(numerator * 10000 / denominator)

    def swap_datum(
        self,
        address_source: Address,
        in_assets: Assets,
        out_assets: Assets,
        extra_assets: Assets | None = None,
        address_target: Address | None = None,
        datum_target: PlutusData | None = None,
        minimum_receive: Assets | None = None,
        swap_all: bool = False,
    ) -> PlutusData:
        """Create a swap datum."""
        swap_all_kwargs = self._swap_all_kwargs(SundaeOrderDatum, swap_all)

        if self.swap_forward and address_target is not None:
            print(f"{self.__class__.__name__} does not support swap forwarding.")

        ident = bytes.fromhex(self.pool_nft.unit()[60:])

        return SundaeOrderDatum.create_datum(
            ident=ident,
            address_source=address_source,
            in_assets=in_assets,
            out_assets=out_assets if minimum_receive is None else minimum_receive,
            fee=self.batcher_fee(in_assets=in_assets, out_assets=out_assets).quantity(),
            **swap_all_kwargs,
        )


class SundaeSwapV3CPPState(AbstractConstantProductPoolState):
    fee: int | list[int] = [30, 30]
    _batcher = Assets(lovelace=1280000)
    _deposit = Assets(lovelace=2000000)
    _stake_address: ClassVar[Address] = Address.from_primitive(
        "addr1z8ax5k9mutg07p2ngscu3chsauktmstq92z9de938j8nqa7zcka2k2tsgmuedt4xl2j5awftvqzmmv3vs2yduzqxfcmsyun6n3",
    )

    def batcher_fee(
        self,
        in_assets: Assets | None = None,
        out_assets: Assets | None = None,
        extra_assets: Assets | None = None,
    ) -> Assets:
        return self.__class__._batcher_fee
        # return Assets(lovelace=1280000)

    @classmethod
    def dex(cls) -> str:
        return "SundaeSwapV3"

    @classmethod
    def default_script_class(self) -> type[PlutusV1Script] | type[PlutusV2Script]:
        return PlutusV2Script

    @classmethod
    def order_selector(self) -> list[str]:
        return [self._stake_address.encode()]

    @classmethod
    def pool_selector(cls) -> PoolSelector:
        return PoolSelector(
            addresses=["addr1w8srqftqemf0mjlukfszd97ljuxdp44r372txfcr75wrz2cp9h6f8"],
        )

    @classmethod
    def pool_policy(cls) -> list[str]:
        return ["e0302560ced2fdcbfcb2602697df970cd0d6a38f94b32703f51c312b"]

    @property
    def swap_forward(self) -> bool:
        return True

    @property
    def stake_address(self) -> Address:
        return self._stake_address

    @classmethod
    def order_datum_class(self) -> type[SundaeV3OrderDatum]:
        return SundaeV3OrderDatum

    @classmethod
    def pool_datum_class(self) -> type[SundaeV3PoolDatum]:
        return SundaeV3PoolDatum

    @property
    def pool_id(self) -> str:
        """A unique identifier for the pool."""
        return self.pool_nft.unit()

    @classmethod
    @lru_cache
    def get_batcher_fee(cls, last_check: int = time.time() // 3600):
        try:
            settings = get_backend().get_datum_from_address(
                address=Address.decode(
                    "addr1w9ke67k2ckdyg60v22ajqugxze79e0ax3yqgl7nway4vc5q84hpqs",
                ),
                asset="6d9d7acac59a4469ec52bb207106167c5cbfa689008ffa6ee92acc5073657474696e6773",
            )
        except ValueError:
            print(
                "No settings found for SundaeSwapV3, likely because no backend is set.",
            )
            return

        datum = SundaeV3Settings.from_cbor(settings.datum_cbor)
        cls._batcher_fee = Assets(lovelace=datum.simple_fee + datum.base_fee)

    @classmethod
    def skip_init(cls, values) -> bool:
        if "pool_nft" in values:
            try:
                super().extract_pool_nft(values)
            except InvalidPoolError:
                raise NotAPoolError("No pool NFT found.")
            if len(values["assets"]) == 3:
                # Send the ADA token to the end
                if isinstance(values["assets"], Assets):
                    values["assets"].root["lovelace"] = values["assets"].root.pop(
                        "lovelace",
                    )
                else:
                    values["assets"]["lovelace"] = values["assets"].pop("lovelace")

            datum = SundaeV3PoolDatum.from_cbor(values["datum_cbor"])
            values["fee"] = datum.bid_fees_per_10_thousand
            values["assets"] = Assets.model_validate(values["assets"])

            cls.get_batcher_fee()
            return True
        else:
            return False

    @classmethod
    def extract_pool_nft(cls, values) -> Assets:
        try:
            super().extract_pool_nft(values)
        except InvalidPoolError:
            if len(values["assets"]) == 0:
                raise NoAssetsError
            else:
                raise NotAPoolError("No pool NFT found.")

    @classmethod
    def post_init(cls, values):
        super().post_init(values)

        assets = values["assets"]
        datum = SundaeV3PoolDatum.from_cbor(values["datum_cbor"])

        if len(assets) == 2:
            assets.root[assets.unit(0)] -= datum.protocol_fees

        values["fee"] = [datum.bid_fees_per_10_thousand, datum.ask_fees_per_10_thousand]

        cls.get_batcher_fee()

    def swap_datum(
        self,
        address_source: Address,
        in_assets: Assets,
        out_assets: Assets,
        extra_assets: Assets | None = None,
        address_target: Address | None = None,
        datum_target: PlutusData | None = None,
        minimum_receive: Assets | None = None,
        swap_all: bool = False,
    ) -> PlutusData:
        """Create a swap datum.

        Raises:
            ValueError: If ``swap_all`` is set. The constant-product pool swaps
                exactly the order's offer, so the order cannot swap an amount
                unknown when the datum is built.
        """
        if swap_all:
            raise self._swap_all_error(
                "the constant-product pool swaps exactly the order's offer",
            )

        ident = bytes.fromhex(self.pool_nft.unit()[64:])

        datum = SundaeV3OrderDatum.create_datum(
            ident=ident,
            address_source=address_source,
            in_assets=in_assets,
            out_assets=out_assets if minimum_receive is None else minimum_receive,
            fee=self.batcher_fee(in_assets=in_assets, out_assets=out_assets).quantity(),
            address_target=address_target,
            datum_target=datum_target,
        )

        return datum


@dataclass(frozen=True)
class SundaeV3StableSwapResult:
    """One swap against a SundaeSwap V3 stableswap pool, as the contract settles it.

    ``gross`` is the out-side amount the curve releases, ``fee`` the swap fee taken
    from it (rounded up), ``takes`` what the trader receives (``gross - fee``) and
    ``protocol_share`` the part of ``fee`` the pool books as protocol fees. The
    out-side reserve drops by ``takes + protocol_share``; the rest of the fee stays
    with liquidity providers.
    """

    takes: int
    gross: int
    fee: int
    protocol_share: int


class SundaeSwapV3StableSwap(AbstractStableSwapPoolState):
    """SundaeSwap V3 stableswap pool.

    The pool prices two reserves on the curve ``4A(x + y) + D = 4AD + D^3 / (4xy)``
    over reserves scaled by :data:`STABLESWAP_PRECISION`, with the contract's exact
    integer rounding: the swap fee is taken from the output, rounded up. Reserves
    are the pool UTxO's holdings net of the asset-side protocol fees its datum has
    accrued (``protocol_fees[1]`` and ``protocol_fees[2]``). The scooper ADA
    accrual (``protocol_fees[0]``) is not netted, so on an ADA-paired pool the
    lovelace reserve still holds it.
    """

    _batcher = Assets(lovelace=500000)
    _deposit = Assets(lovelace=2000000)
    _stake_address: ClassVar[Address] = Address.from_primitive(
        "addr1w94tv2296rvdv2ywysankephl7wqnx3cuzyz3r66dd79azc4swz8d",
    )

    _amp: int | None = None
    _protocol_bps: tuple[int, int] | None = None
    _d_memo: tuple[tuple[int, int, int], int] | None = None

    def batcher_fee(
        self,
        in_assets: Assets | None = None,
        out_assets: Assets | None = None,
        extra_assets: Assets | None = None,
    ) -> Assets:
        """Batcher fee."""
        return self.__class__._batcher_fee

    @classmethod
    def dex(cls) -> str:
        return "SundaeSwapV3"

    @classmethod
    def default_script_class(
        self,
    ) -> type[PlutusV1Script] | type[PlutusV2Script] | type[PlutusV3Script]:
        return PlutusV3Script

    @classmethod
    def order_selector(self) -> list[str]:
        return [self._stake_address.encode()]

    @classmethod
    def pool_selector(cls) -> PoolSelector:
        return PoolSelector(
            addresses=["addr1w9x70xsvzuvqqv9l7npksfwtd6vu4gq8h33j77y4vx3x64s20wr4w"],
        )

    @classmethod
    def pool_policy(cls) -> list[str]:
        return [
            "4de79a0c17180030bff4c36825cb6e99caa007bc632f789561a26d56",
        ]

    @property
    def swap_forward(self) -> bool:
        return True

    @property
    def stake_address(self) -> Address:
        return self._stake_address

    @classmethod
    def order_datum_class(self) -> type[SundaeV3OrderDatum]:
        return SundaeV3OrderDatum

    @classmethod
    def pool_datum_class(self) -> type[SundaeV3PoolDatum]:
        return SundaeV3StablePoolDatum

    @property
    def pool_id(self) -> str:
        """A unique identifier for the pool."""
        return self.pool_nft.unit()

    @classmethod
    @lru_cache
    def get_batcher_fee(cls, last_check: int = time.time() // 3600):
        try:
            settings = get_backend().get_datum_from_address(
                address=Address.decode(
                    "addr1w9ke67k2ckdyg60v22ajqugxze79e0ax3yqgl7nway4vc5q84hpqs",
                ),
                asset="6d9d7acac59a4469ec52bb207106167c5cbfa689008ffa6ee92acc5073657474696e6773",
            )
        except ValueError:
            print(
                "No settings found for SundaeSwapV3, likely because no backend is set.",
            )
            return

        datum = SundaeV3Settings.from_cbor(settings.datum_cbor)
        cls._batcher_fee = Assets(lovelace=datum.simple_fee + datum.base_fee)

    @classmethod
    def skip_init(cls, values) -> bool:
        if "pool_nft" in values:
            try:
                super().extract_pool_nft(values)
            except InvalidPoolError:
                raise NotAPoolError("No pool NFT found.")
            if len(values["assets"]) == 3:
                # Send the ADA token to the end
                if isinstance(values["assets"], Assets):
                    values["assets"].root["lovelace"] = values["assets"].root.pop(
                        "lovelace",
                    )
                else:
                    values["assets"]["lovelace"] = values["assets"].pop("lovelace")

            # Already-parsed reserves are net of protocol fees: never subtract them.
            values["assets"] = Assets.model_validate(values["assets"])
            super().post_init(values)
            datum = SundaeV3StablePoolDatum.from_cbor(values["datum_cbor"])
            values["fee"] = cls._datum_fees(datum)

            cls.get_batcher_fee()
            return True
        else:
            return False

    @classmethod
    def extract_pool_nft(cls, values) -> Assets:
        try:
            super().extract_pool_nft(values)
        except InvalidPoolError:
            if len(values["assets"]) == 0:
                raise NoAssetsError
            else:
                raise NotAPoolError("No pool NFT found.")

    @staticmethod
    def _datum_fees(datum: SundaeV3StablePoolDatum) -> list[int]:
        """The swap fee per offered side: liquidity plus protocol basis points."""
        return [
            lp + protocol
            for lp, protocol in zip(
                datum.lp_fee_basis_points,
                datum.protocol_fee_basis_points,
            )
        ]

    @classmethod
    def post_init(cls, values):
        """Parse a raw pool UTxO, netting the asset-side protocol fees it holds."""
        super().post_init(values)

        assets = values["assets"]
        datum = SundaeV3StablePoolDatum.from_cbor(values["datum_cbor"])

        assets.root[assets.unit(0)] -= datum.protocol_fees[1]
        assets.root[assets.unit(1)] -= datum.protocol_fees[2]

        values["fee"] = cls._datum_fees(datum)

        cls.get_batcher_fee()

    @property
    def amp(self) -> int:
        if self._amp is None:
            self._amp = self.pool_datum.amp

        return self._amp

    @property
    def protocol_fee_basis_points(self) -> tuple[int, int]:
        """The protocol's basis points of the swap fee, per offered side."""
        if self._protocol_bps is None:
            datum = cast(SundaeV3StablePoolDatum, self.pool_datum)
            bps = datum.protocol_fee_basis_points
            self._protocol_bps = (bps[0], bps[1])
        return self._protocol_bps

    def sum_invariant(self) -> int:
        """The invariant ``D`` of the current reserves.

        Computed from the reserves, never read from the datum, so reserves moved
        past the datum still quote exactly. Zero when a side is empty. Memoised on
        the reserves, so a move made directly on ``assets`` never serves a stale
        value.
        """
        key = (self.assets.quantity(0), self.assets.quantity(1), self.amp)
        if self._d_memo is not None and self._d_memo[0] == key:
            return self._d_memo[1]
        d = stableswap_d(
            self.amp,
            key[0] * STABLESWAP_PRECISION,
            key[1] * STABLESWAP_PRECISION,
        )
        self._d_memo = (key, d)
        return d

    def _swap_side(self, unit: str) -> int:
        """The reserve index of ``unit``.

        Raises:
            ValueError: ``unit`` is not one of the pool's two reserves.
        """
        if unit == self.unit_a:
            return 0
        if unit == self.unit_b:
            return 1
        msg = f"Asset {unit} is invalid for pool {self.unit_a}-{self.unit_b}"
        raise ValueError(msg)

    def _single(self, asset: Assets) -> tuple[str, int, int]:
        """The unit, reserve index and quantity of a one-asset ``asset``.

        Raises:
            ValueError: ``asset`` is not exactly one of the pool's reserves, or
                its quantity is negative.
        """
        if len(asset) != 1:
            msg = "Asset should only have one token."
            raise ValueError(msg)
        unit = asset.unit()
        side = self._swap_side(unit)
        quantity = asset.quantity()
        if quantity < 0:
            msg = f"Quantity of {unit} is negative."
            raise ValueError(msg)
        return unit, side, quantity

    def _side_fee(self, side: int) -> int:
        """The swap fee, in basis points, of a trade offering reserve ``side``."""
        fee = self.volume_fee
        if fee is None:
            return 0
        if isinstance(fee, (int, float)):
            return int(fee)
        return int(fee[side])

    def _swap(self, side: int, amount: int) -> SundaeV3StableSwapResult:
        """The settled swap offering ``amount`` of reserve ``side``.

        All zero for no offer, or when a side is empty.
        """
        reserve_in = self.assets.quantity(side)
        reserve_out = self.assets.quantity(1 - side)
        if amount <= 0 or reserve_in <= 0 or reserve_out <= 0:
            return SundaeV3StableSwapResult(takes=0, gross=0, fee=0, protocol_share=0)
        fee = self._side_fee(side)
        quote = stableswap_swap(
            self.amp,
            self.sum_invariant(),
            reserve_in,
            1,
            reserve_out,
            1,
            amount,
            (fee, _FEE_BASIS),
        )
        protocol = self.protocol_fee_basis_points[side]
        protocol_share = quote.fee * protocol // fee if fee > 0 else 0
        return SundaeV3StableSwapResult(
            takes=quote.takes,
            gross=quote.gross,
            fee=quote.fee,
            protocol_share=protocol_share,
        )

    def swap_result(self, asset: Assets) -> SundaeV3StableSwapResult:
        """The settled swap offering the one-asset ``asset``.

        All zero for no offer, or when a side is empty.

        Raises:
            ValueError: ``asset`` is not exactly one of the pool's reserves, or
                its quantity is negative.
        """
        _, side, amount = self._single(asset)
        return self._swap(side, amount)

    def get_amount_out(
        self,
        asset: Assets,
        precise: bool = True,
    ) -> tuple[Assets, float]:
        """The exact output for the one-asset offer ``asset``.

        The output is the contract's payout, an integer whatever ``precise`` is:
        zero for no offer, or when a side is empty. The second value is always 0.

        Raises:
            ValueError: ``asset`` is not exactly one of the pool's reserves, or
                its quantity is negative.
        """
        _, side, amount = self._single(asset)
        out_unit = self.unit_b if side == 0 else self.unit_a
        return Assets(**{out_unit: self._swap(side, amount).takes}), 0

    def max_output(self, out_unit: str) -> int:
        """The smallest undeliverable output of ``out_unit``.

        One past what the largest ledger offer of the other reserve buys: the
        output never decreases as the offer grows. One when a side is empty, as
        no offer then delivers anything.

        Raises:
            ValueError: ``out_unit`` is not one of the pool's reserves.
        """
        side = 1 - self._swap_side(out_unit)
        return self._swap(side, _LEDGER_MAX).takes + 1

    def get_amount_in(
        self,
        asset: Assets,
        precise: bool = True,
    ) -> tuple[Assets, float]:
        """The least offer whose exact output reaches the one-asset ``asset``.

        Zero for no output. The input is an integer whatever ``precise`` is. The
        second value is always 0.

        Raises:
            ValueError: ``asset`` is not exactly one of the pool's reserves, or
                its quantity is negative.
            InvalidPoolError: no ledger quantity of the other reserve reaches the
                output (it is at or past :meth:`max_output`), which holds for any
                positive output when a side is empty.
        """
        _, out_side, want = self._single(asset)
        side = 1 - out_side
        in_unit = self.unit_a if side == 0 else self.unit_b
        if want == 0:
            return Assets(**{in_unit: 0}), 0
        reserve_in = self.assets.quantity(side)
        reserve_out = self.assets.quantity(out_side)
        offer = None
        if reserve_in > 0 and reserve_out > 0:
            offer = self._least_offer(side, want)
        if offer is None:
            msg = (
                f"{type(self).__name__}: no amount of {in_unit} reaches {want} "
                f"of {asset.unit()}."
            )
            raise InvalidPoolError(msg)
        return Assets(**{in_unit: offer}), 0

    def _least_offer(self, side: int, want: int) -> int | None:
        """The least offer of reserve ``side`` whose takes reach ``want``.

        ``None`` when no ledger quantity does. The output is released by the curve
        as ``gross`` and the fee taken from it, so the least ``gross`` netting
        ``want`` is found first. The post-swap out-side reserve must then be at most
        ``Y = (reserve_out - gross) * P``; the curve is symmetric in its two
        reserves, so the least in-side reserve on or above it at ``Y`` is
        ``stableswap_y(D, Y)``, and the offer is what lifts the in-side reserve
        there. A final step against the exact quote pins the minimum.
        """
        fee = self._side_fee(side)
        if fee >= _FEE_BASIS:
            return None
        reserve_in = self.assets.quantity(side)
        reserve_out = self.assets.quantity(1 - side)

        def net(gross: int) -> int:
            return gross - (gross * fee + _FEE_BASIS - 1) // _FEE_BASIS

        gross = -(-want * _FEE_BASIS // (_FEE_BASIS - fee))
        while net(gross) < want:
            gross += 1
        while gross > 1 and net(gross - 1) >= want:
            gross -= 1
        if gross >= reserve_out:
            return None

        x_min = stableswap_y(
            self.amp,
            self.sum_invariant(),
            (reserve_out - gross) * STABLESWAP_PRECISION,
        )
        offer = max(-(-x_min // STABLESWAP_PRECISION) - reserve_in, 1)
        if offer > _LEDGER_MAX:
            return None
        while self._swap(side, offer).takes < want:
            offer += 1
            if offer > _LEDGER_MAX:
                return None
        while offer > 1 and self._swap(side, offer - 1).takes >= want:
            offer -= 1
        return offer

    def swap_datum(
        self,
        address_source: Address,
        in_assets: Assets,
        out_assets: Assets,
        extra_assets: Assets | None = None,
        address_target: Address | None = None,
        datum_target: PlutusData | None = None,
        minimum_receive: Assets | None = None,
        swap_all: bool = False,
    ) -> PlutusData:
        """Create a swap datum.

        The stableswap pool swaps the smaller of the order's offer and the input it
        holds. With ``swap_all`` the offer is ``SWAP_ALL_OFFER_MULTIPLE`` times
        ``in_assets``, so the order swaps whatever amount of the input token it
        holds when executed. The order value is still built from ``in_assets``.

        Raises:
            ValueError: If ``swap_all`` is set with an ADA input. An ADA offer
                shares the order value with the protocol fee and deposit, so
                swapping all of it would leave no ADA on the output.
        """
        if swap_all and in_assets.unit() == "lovelace":
            raise self._swap_all_error(
                "an ADA input cannot swap whatever arrives because the deposit "
                "and fee share the input value",
            )

        ident = bytes.fromhex(self.pool_nft.unit()[64:])

        offer = in_assets
        if swap_all:
            offer = Assets(
                root={in_assets.unit(): SWAP_ALL_OFFER_MULTIPLE * in_assets.quantity()},
            )

        datum = SundaeV3OrderDatum.create_datum(
            ident=ident,
            address_source=address_source,
            in_assets=offer,
            out_assets=out_assets if minimum_receive is None else minimum_receive,
            fee=self.batcher_fee(in_assets=in_assets, out_assets=out_assets).quantity(),
            address_target=address_target,
            datum_target=datum_target,
        )

        return datum
