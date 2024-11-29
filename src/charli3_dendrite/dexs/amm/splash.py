"""Minswap DEX Module."""

from dataclasses import dataclass
from typing import Any
from typing import List
from typing import Union

from pycardano import Address
from pycardano import PlutusData
from pycardano import PlutusV1Script
from pycardano import PlutusV2Script
from pycardano.plutus import RawDatum
from pycardano import Redeemer
from pycardano import ScriptHash
from pycardano import TransactionBuilder
from pycardano import TransactionId
from pycardano import TransactionInput
from pycardano import TransactionOutput
from pycardano import UTxO

from charli3_dendrite.backend import get_backend
from charli3_dendrite.dataclasses.datums import AssetClass
from charli3_dendrite.dataclasses.datums import OrderDatum
from charli3_dendrite.dataclasses.datums import OrderType
from charli3_dendrite.dataclasses.datums import PlutusFullAddress
from charli3_dendrite.dataclasses.datums import PoolDatum
from charli3_dendrite.dataclasses.models import PoolSelector
from charli3_dendrite.dexs.core.base import AbstractPairState
from charli3_dendrite.dexs.amm.amm_types import AbstractCommonStableSwapPoolState
from charli3_dendrite.dexs.core.errors import InvalidLPError
from charli3_dendrite.dexs.core.errors import NotAPoolError
from charli3_dendrite.utility import asset_to_value
from charli3_dendrite.utility import Assets


@dataclass
class BoolFalse(PlutusData):
    CONSTR_ID = 0


@dataclass
class BoolTrue(PlutusData):
    CONSTR_ID = 1


@dataclass
class Rationale(PlutusData):
    """Rationale for Plutus data."""

    CONSTR_ID = 0
    numerator: int
    denominator: int


@dataclass
class SplashOrderDatum(OrderDatum):
    """Order Datum."""

    CONSTR_ID = 0

    tag: bytes
    beacon: bytes
    in_asset: AssetClass
    tradable_input: int
    cost_per_ex_step: int
    min_marginal_output: int
    output: AssetClass
    base_price: Rationale
    fee: int
    redeemer_address: PlutusFullAddress
    cancel_pkh: bytes
    permitted_executors: List[bytes]

    def address_source(self) -> Address:
        """This method should return the source address associated with the order."""
        return self.redeemer_address.to_address()

    def requested_amount(self) -> Assets:
        """This method should return the amount requested in the order."""
        return Assets(root={self.in_asset.assets.unit(): self.min_marginal_output})

    def order_type(self) -> OrderType:
        """This method should return the type of the order."""
        return OrderType.swap


@dataclass
class SplashSSPPoolDatum(PoolDatum):
    """Pool Datum."""

    CONSTR_ID = 0

    pool_nft: AssetClass
    an2n: int
    asset_x: AssetClass
    asset_y: AssetClass
    multiplier_x: int
    multiplier_y: int
    lp_token: AssetClass
    ampl_coeff_if_editable: Union[BoolFalse, BoolTrue]
    lp_fee_is_editable: Union[BoolFalse, BoolTrue]
    lp_fee_num: int
    protocol_fee_num: int
    dao_stable_proxy_witness: bytes
    treasury_address: bytes
    protocol_fee_x: int
    protocol_fee_y: int

    def pool_pair(self) -> Assets | None:
        """Return the asset pair associated with the pool."""
        return self.asset_x.assets + self.asset_y.assets


@dataclass
class SwapAction(PlutusData):
    CONSTR_ID = 0

    context_values_list: List[int]


@dataclass
class PDAOAction(PlutusData):
    CONSTR_ID = 1


@dataclass
class PoolRedeemer(PlutusData):
    CONSTR_ID = 0

    pool_in_idx: int
    pool_out_idx: int
    action: Union[SwapAction, PDAOAction]

    def set_idx(self, tx_builder: TransactionBuilder):
        """Set the pool in and out indexes."""

        contract_hash = Address.decode(
            SplashSSPState.pool_selector().addresses[0]
        ).payment_part.payload

        # Set the input pool index
        pool_index = None
        sorted_inputs = sorted(
            tx_builder.inputs.copy(),
            key=lambda i: i.input.transaction_id.payload.hex(),
        )
        for i, utxo in enumerate(sorted_inputs):
            if utxo.output.address.payment_part.payload == contract_hash:
                pool_index = i
        assert pool_index is not None
        self.pool_in_idx = pool_index

        for i, txo in enumerate(tx_builder.outputs):
            if txo.address.payment_part.payload == contract_hash:
                pool_index = i
        assert pool_index is not None
        self.pool_out_idx = pool_index


class SplashBaseState(AbstractPairState):
    @classmethod
    def dex(cls) -> str:
        return "Splash"

    @classmethod
    def order_selector(self) -> list[str]:
        return ["addr1w9ryamhgnuz6lau86sqytte2gz5rlktv2yce05e0h3207qssa8euj"]

    @property
    def stake_address(self) -> Address | None:
        return Address.decode(self.order_selector()[0])

    @property
    def swap_forward(self) -> bool:
        return False

    @classmethod
    def order_datum_class(cls):
        return SplashOrderDatum

    @classmethod
    def default_script_class(cls) -> type[PlutusV1Script] | type[PlutusV2Script]:
        """Returns default script class of type PlutusV1Script or PlutusV2Script."""
        return PlutusV2Script


class SplashSSPState(SplashBaseState, AbstractCommonStableSwapPoolState):
    """Splash StableSwap Pool State."""

    fee: int = 30
    _batcher = Assets(lovelace=0)
    _deposit = Assets(lovelace=2000000)

    @classmethod
    def pool_selector(cls) -> PoolSelector:
        return PoolSelector(
            addresses=["addr1w9wnm7vle7al9q4aw63aw63wxz7aytnpc4h3gcjy0yufxwc3mr3e5"],
        )

    def _get_ann(self) -> int:
        """The modified amp value.

        This is the derived amp value (ann) from the original stableswap paper. This is
        implemented here as the default, but a common variant of this does not use the
        exponent. The alternative version is provided in the
        AbstractCommonStableSwapPoolState class. WingRiders uses this version.
        """
        return self.pool_datum.an2n // 4

    @classmethod
    def script_class(cls) -> type[PlutusV2Script]:
        return PlutusV2Script

    @classmethod
    def pool_datum_class(self) -> type[SplashSSPPoolDatum]:
        return SplashSSPPoolDatum

    @property
    def pool_id(self) -> str:
        """A unique identifier for the pool."""
        return self.pool_nft.unit()

    @classmethod
    def extract_pool_nft(cls, values: dict[str, Any]) -> Assets | None:
        """Extract the pool nft from the UTXO.

        Some DEXs put a pool nft into the pool UTXO.

        This function checks to see if the pool nft is in the UTXO if the DEX policy is
        defined.

        If the pool nft is in the values, this value is skipped because it is assumed
        that this utxo has already been parsed.

        Args:
            values: The pool UTXO inputs.

        Returns:
            Assets: None or the pool nft.
        """
        assets = values["assets"]
        datum: SplashSSPPoolDatum = SplashSSPPoolDatum.from_cbor(values["datum_cbor"])
        pool_assets = [
            datum.lp_token.assets.unit(),
            datum.asset_x.assets.unit(),
            datum.asset_y.assets.unit(),
        ]

        # If the pool nft is in the values, it's been parsed already
        if "pool_nft" in values:
            pool_nft = Assets(
                **dict(values["pool_nft"].items()),
            )
            if pool_nft.quantity() != 1 or not pool_nft.unit().lower().endswith(
                bytes(b"nft").hex()
            ):
                raise NotAPoolError("A pool must have one pool NFT token.")

        # Check for the pool nft
        else:
            pool_nft = None
            for asset in assets:
                name = bytes.fromhex(asset[56:])
                if not name.lower().endswith(b"nft") or asset in pool_assets:
                    continue
                elif assets[asset] == 1:
                    pool_nft = Assets(**{asset: assets.root.pop(asset)})
                    break
            if pool_nft is None:
                raise NotAPoolError(f"A pool must have one pool NFT token: {name}.")

            values["pool_nft"] = pool_nft

        return pool_nft

    @classmethod
    def extract_lp_tokens(cls, values: dict[str, Any]) -> Assets:
        """Extract the lp tokens from the UTXO.

        Args:
            values: The pool UTXO inputs.

        Returns:
            Assets: None or the pool nft.
        """
        assets = values["assets"]
        datum: SplashSSPPoolDatum = SplashSSPPoolDatum.from_cbor(values["datum_cbor"])
        lp_token = datum.lp_token.assets.unit()

        # If no pool policy id defined, return nothing
        if "lp_tokens" in values:
            lp_tokens = values["lp_tokens"]

        # Check for the pool nft
        else:
            if lp_token not in assets:
                raise InvalidLPError("A pool must have pool lp tokens.")

            else:
                lp_tokens = Assets(**{lp_token: assets.root.pop(lp_token)})

            values["lp_tokens"] = lp_tokens

        return lp_tokens

    @classmethod
    def post_init(cls, values):
        super().post_init(values)

        datum: SplashSSPPoolDatum = SplashSSPPoolDatum.from_cbor(values["datum_cbor"])

        values["fee"] = (datum.lp_fee_num + datum.protocol_fee_num) / 10

        assets = values["assets"]
        assets.root[assets.unit(0)] -= datum.protocol_fee_x
        assets.root[assets.unit(1)] -= datum.protocol_fee_y

        cls.asset_mulitipliers = [
            datum.multiplier_x,
            datum.multiplier_y,
        ]

    def get_amount_out(
        self, asset: Assets, precise: bool = False, fee_on_input: bool = False
    ) -> tuple[Assets, float]:
        return super().get_amount_out(asset=asset, precise=precise, fee_on_input=False)

    def get_amount_in(
        self, asset: Assets, precise: bool = False, fee_on_input: bool = False
    ) -> tuple[Assets, float]:
        return super().get_amount_in(asset=asset, precise=precise, fee_on_input=False)

    def swap_utxo(
        self,
        address_source: Address,
        in_assets: Assets,
        out_assets: Assets,
        tx_builder: TransactionBuilder | None = None,
        extra_assets: Assets | None = None,
        address_target: Address | None = None,
        datum_target: PlutusData | None = None,
    ) -> tuple[TransactionOutput | None, PlutusData]:
        assert self.tx_hash is not None
        assert self.pool_nft is not None
        assert self.lp_tokens is not None
        assert tx_builder is not None

        order_info = get_backend().get_pool_in_tx(
            self.tx_hash,
            assets=[self.pool_nft.unit()],
            addresses=self.pool_selector().addresses,
        )

        # Get the output assets
        out_assets, _ = self.get_amount_out(asset=in_assets)

        # Create the output redeemer
        redeemer = Redeemer(
            PoolRedeemer(
                pool_in_idx=0,
                pool_out_idx=0,
                action=SwapAction(context_values_list=[int(self._get_d())]),
            )
        )

        # Create the pool input UTxO
        assets = self.assets + self.pool_nft + self.lp_tokens
        input_utxo = UTxO(
            TransactionInput(
                transaction_id=TransactionId(bytes.fromhex(self.tx_hash)),
                index=self.tx_index,
            ),
            output=TransactionOutput(
                address=order_info[0].address,
                amount=asset_to_value(assets),
                datum=self.pool_datum,
            ),
        )

        # Create the pool output UTxO
        # TODO: add protocol and fees
        assets.root[in_assets.unit()] += in_assets.quantity()
        assets.root[out_assets.unit()] -= out_assets.quantity()
        txo = TransactionOutput(
            address=order_info[0].address,
            amount=asset_to_value(assets),
            datum=self.pool_datum,
        )

        # Add the script input
        pool_hash = Address.decode(order_info[0].address).payment_part.payload
        script = (
            get_backend()
            .get_script_from_address(
                Address(payment_part=ScriptHash(payload=pool_hash)),
            )
            .to_utxo()
        )
        tx_builder.add_script_input(utxo=input_utxo, script=script, redeemer=redeemer)

        return txo, self.pool_datum
