"""Djed/Shen Stablecoin Order Book Module.

This module provides order book functionality for Djed (collateralized stablecoin)
and Shen (liquidity token) operations, following the exact patterns established
by the GeniusYield implementation.
"""

import time
from dataclasses import dataclass
from typing import Union

from pycardano import Address
from pycardano import PlutusData
from pycardano import PlutusV1Script
from pycardano import PlutusV2Script
from pycardano import Redeemer
from pycardano import TransactionBuilder
from pycardano import TransactionId
from pycardano import TransactionInput
from pycardano import TransactionOutput
from pycardano import UTxO

from charli3_dendrite.backend import get_backend
from charli3_dendrite.dataclasses.datums import OrderDatum
from charli3_dendrite.dataclasses.datums import PlutusFullAddress
from charli3_dendrite.dataclasses.models import Assets
from charli3_dendrite.dataclasses.models import OrderType
from charli3_dendrite.dataclasses.models import PoolSelector
from charli3_dendrite.dexs.ob.ob_base import AbstractOrderBookState
from charli3_dendrite.dexs.ob.ob_base import AbstractOrderState
from charli3_dendrite.dexs.ob.ob_base import BuyOrderBook
from charli3_dendrite.dexs.ob.ob_base import OrderBookOrder
from charli3_dendrite.dexs.ob.ob_base import SellOrderBook
from charli3_dendrite.utility import DjedRational
from charli3_dendrite.utility import asset_to_value


@dataclass
class DjedRationalDatum(PlutusData):
    """Plutus-compatible rational number for on-chain data."""

    CONSTR_ID = 0
    numerator: int
    denominator: int


@dataclass
class DjedMintAction(PlutusData):
    """Djed minting action in order datum."""

    CONSTR_ID = 0
    djed_amount: int
    ada_amount: int


@dataclass
class DjedBurnAction(PlutusData):
    """Djed burning action in order datum."""

    CONSTR_ID = 1
    djed_amount: int


@dataclass
class ShenMintAction(PlutusData):
    """Shen minting action in order datum."""

    CONSTR_ID = 2
    shen_amount: int
    ada_amount: int


@dataclass
class ShenBurnAction(PlutusData):
    """Shen burning action in order datum."""

    CONSTR_ID = 3
    shen_amount: int


@dataclass
class DjedOrderDatum(OrderDatum):
    """Djed/Shen order datum structure (following existing OrderDatum pattern)."""

    CONSTR_ID = 0
    action: Union[DjedMintAction, DjedBurnAction, ShenMintAction, ShenBurnAction]
    owner_address: PlutusFullAddress
    oracle_rate: DjedRationalDatum
    creation_time: int
    order_nft: bytes

    def pool_pair(self) -> Assets | None:
        """Return the asset pair for this order (required by OrderDatum interface)."""
        if isinstance(self.action, (DjedMintAction, DjedBurnAction)):
            # Djed <-> ADA pair (placeholder policy IDs)
            return Assets(lovelace=0) + Assets(**{"djed_policy_id.djed_token_name": 0})
        else:  # Shen operations
            # Shen <-> ADA pair (placeholder policy IDs)
            return Assets(lovelace=0) + Assets(**{"shen_policy_id.shen_token_name": 0})

    def address_source(self) -> str | None:
        """Source address (required by OrderDatum interface)."""
        return self.owner_address.to_address().encode("bech32")

    def requested_amount(self) -> Assets:
        """Return the requested amount for this order (required by OrderDatum interface)."""
        if isinstance(self.action, DjedMintAction):
            return Assets(**{"djed_policy_id.djed_token_name": self.action.djed_amount})
        elif isinstance(self.action, DjedBurnAction):
            # For burn, calculate ADA amount based on oracle rate
            oracle_rate = DjedRational(
                self.oracle_rate.numerator, self.oracle_rate.denominator
            )
            ada_amount = (
                oracle_rate.invert().mul(DjedRational(self.action.djed_amount)).to_int()
            )
            return Assets(lovelace=ada_amount)
        elif isinstance(self.action, ShenMintAction):
            return Assets(**{"shen_policy_id.shen_token_name": self.action.shen_amount})
        else:  # ShenBurnAction
            # For Shen burn, calculation is more complex and requires pool state
            return Assets(lovelace=self.action.shen_amount)  # Placeholder

    def order_type(self) -> OrderType | None:
        """Order type classification (required by OrderDatum interface)."""
        if isinstance(self.action, (DjedMintAction, ShenMintAction)):
            return OrderType.deposit  # Minting = deposit operation
        else:
            return OrderType.swap  # Burning = swap operation


# === SHARED BASE CLASS FOR COMMON FUNCTIONALITY ===


class DjedShenOrderStateBase(AbstractOrderState):
    """Base class for Djed/Shen order states sharing common functionality.

    Reduces code duplication between Djed and Shen implementations by providing
    shared methods that follow the exact GeniusYield pattern.
    """

    tx_hash: str
    tx_index: int
    datum_cbor: str
    datum_hash: str
    inactive: bool = False

    _batcher_fee: Assets = Assets(lovelace=2_000_000)  # 2 ADA operator fee
    _datum_parsed: PlutusData | None = None

    @classmethod
    def dex_policy(cls) -> list[str] | None:
        """Djed/Shen order NFT policy IDs (following GeniusYield pattern)."""
        return [
            "djed_order_policy_mainnet_placeholder",  # Replace with actual policy
            "djed_order_policy_preprod_placeholder",  # Replace with actual policy
        ]

    @property
    def volume_fee(self) -> float:
        """Fee percentage for operations (following GeniusYield pattern)."""
        return 150  # 1.5% in basis points

    @property
    def reference_utxo(self) -> UTxO | None:
        """Get reference UTxO for script validation (following GeniusYield pattern)."""
        order_info = get_backend().get_pool_in_tx(
            self.tx_hash,
            assets=[self.dex_nft.unit()],
            addresses=self.pool_selector().addresses,
        )

        script = get_backend().get_script_from_address(
            Address.decode(order_info[0].address),
        )

        return UTxO(
            input=TransactionInput(
                TransactionId(bytes.fromhex(script.tx_hash)),
                index=script.tx_index,
            ),
            output=TransactionOutput(
                address=script.address,
                amount=asset_to_value(script.assets),
                script=PlutusV2Script(bytes.fromhex(script.script)),
            ),
        )

    def _get_pool_utxo(self) -> UTxO:
        """Get pool UTxO using backend (shared by both Djed and Shen)."""
        pool_utxos = get_backend().get_pool_utxos(
            addresses=["djed_pool_address_placeholder"],  # Replace with actual
            assets=["djed_pool_nft_placeholder"],  # Replace with actual
            limit=1,
            historical=False,
        )
        if not pool_utxos:
            raise RuntimeError("Pool UTxO not found")

        pool_info = pool_utxos[0]
        return UTxO(
            input=TransactionInput(
                TransactionId(bytes.fromhex(pool_info.tx_hash)),
                index=pool_info.tx_index,
            ),
            output=TransactionOutput(
                address=Address.decode(pool_info.address),
                amount=asset_to_value(pool_info.assets),
            ),
        )

    def _get_oracle_utxo(self) -> UTxO:
        """Get oracle UTxO using backend (shared by both Djed and Shen)."""
        oracle_utxos = get_backend().get_pool_utxos(
            addresses=["djed_oracle_address_placeholder"],  # Replace with actual
            assets=["djed_oracle_nft_placeholder"],  # Replace with actual
            limit=1,
            historical=False,
        )
        if not oracle_utxos:
            raise RuntimeError("Oracle UTxO not found")

        oracle_info = oracle_utxos[0]
        return UTxO(
            input=TransactionInput(
                TransactionId(bytes.fromhex(oracle_info.tx_hash)),
                index=oracle_info.tx_index,
            ),
            output=TransactionOutput(
                address=Address.decode(oracle_info.address),
                amount=asset_to_value(oracle_info.assets),
            ),
        )

    @classmethod
    def post_init(cls, values: dict[str, ...]):
        """Post initialization validation (shared logic)."""
        super().post_init(values)

        # Parse and validate order datum
        try:
            datum = cls.order_datum_class().from_cbor(values["datum_cbor"])

            # Check if order is expired (3-minute TTL)
            current_time = int(time.time())
            if current_time > datum.creation_time + 180:  # 3 minutes
                values["inactive"] = True

        except Exception as e:
            values["inactive"] = True

    @classmethod
    def order_selector(cls) -> list[str]:
        """Order contract addresses (shared)."""
        return [
            "addr1_djed_order_mainnet_placeholder",  # Replace with actual
            "addr_test1_djed_order_preprod_placeholder",  # Replace with actual
        ]

    @classmethod
    def pool_selector(cls) -> PoolSelector:
        """Pool selection for Djed/Shen orders (shared)."""
        return PoolSelector(
            addresses=[
                "addr1_djed_pool_mainnet_placeholder",  # Replace with actual
                "addr_test1_djed_pool_preprod_placeholder",  # Replace with actual
            ],
        )

    @property
    def swap_forward(self) -> bool:
        """Returns if swap forwarding is enabled."""
        return False

    @property
    def stake_address(self) -> Address | None:
        """Return the staking address."""
        return None

    @classmethod
    def order_datum_class(cls) -> type[PlutusData]:
        """Returns data class used for handling order datums."""
        return DjedOrderDatum

    @classmethod
    def default_script_class(cls) -> type[PlutusV1Script] | type[PlutusV2Script]:
        """Get default script class."""
        return PlutusV2Script

    @property
    def pool_id(self) -> str:
        """A unique identifier for the pool or ob."""
        return "Djed"


# === DJED-SPECIFIC ORDER STATE ===


class DjedOrderState(DjedShenOrderStateBase):
    """Djed order state handling Djed mint/burn operations.

    Inherits common functionality from DjedShenOrderStateBase and implements
    Djed-specific pricing and transaction logic.
    """

    @classmethod
    def dex(cls) -> str:
        """Official dex name."""
        return "Djed"

    @property
    def price(self) -> tuple[int, int]:
        """Price for Djed operations (ADA per Djed)."""
        oracle_rate_datum = self.order_datum.oracle_rate
        oracle_rate = DjedRational(
            oracle_rate_datum.numerator, oracle_rate_datum.denominator
        )

        if isinstance(self.order_datum.action, DjedMintAction):
            # Djed mint: ADA per Djed (includes fees)
            base_rate = oracle_rate.invert()  # Convert Djed/ADA to ADA/Djed
            fee_multiplier = DjedRational(1015, 1000)  # 1.5% fee
            final_rate = base_rate.mul(fee_multiplier)
            return final_rate.to_tuple()
        else:  # DjedBurnAction
            # Djed burn: ADA per Djed (after fees)
            base_rate = oracle_rate.invert()
            fee_multiplier = DjedRational(985, 1000)  # 1.5% fee deduction
            final_rate = base_rate.mul(fee_multiplier)
            return final_rate.to_tuple()

    @property
    def available(self) -> Assets:
        """Available amount for Djed orders."""
        if isinstance(self.order_datum.action, DjedMintAction):
            return Assets(
                **{
                    "djed_policy_id.djed_token_name": self.order_datum.action.djed_amount
                }
            )
        else:  # DjedBurnAction
            # Calculate ADA to return based on current oracle rate
            ada_amount = self._calculate_ada_return(self.order_datum.action.djed_amount)
            return Assets(lovelace=ada_amount)

    def _calculate_ada_return(self, djed_amount: int) -> int:
        """Calculate ADA to return for Djed burning."""
        oracle_rate_datum = self.order_datum.oracle_rate
        oracle_rate = DjedRational(
            oracle_rate_datum.numerator, oracle_rate_datum.denominator
        )

        base_rate = oracle_rate.invert()  # ADA per Djed
        fee_multiplier = DjedRational(985, 1000)  # 1.5% fee deduction
        final_rate = base_rate.mul(fee_multiplier)

        djed_rational = DjedRational(djed_amount, 1)
        return final_rate.mul(djed_rational).to_int("ROUND_DOWN")

    def swap_utxo(
        self,
        address_source: Address,
        in_assets: Assets,
        out_assets: Assets,
        tx_builder: TransactionBuilder,
        extra_assets: Assets | None = None,
        address_target: Address | None = None,
        datum_target: PlutusData | None = None,
    ) -> tuple[TransactionOutput | None, PlutusData]:
        """Build transaction for Djed order processing."""

        # Get reference UTxOs (using shared methods)
        pool_utxo = self._get_pool_utxo()
        oracle_utxo = self._get_oracle_utxo()

        # Add order UTxO as script input (following GeniusYield pattern)
        assets = self.assets + Assets(**{self.dex_nft.unit(): 1})
        order_utxo = UTxO(
            TransactionInput(
                transaction_id=TransactionId(bytes.fromhex(self.tx_hash)),
                index=self.tx_index,
            ),
            output=TransactionOutput(
                address=Address.decode(self.address),
                amount=asset_to_value(assets),
                datum_hash=self.order_datum.hash(),
            ),
        )

        # Add script input with redeemer
        if out_assets.quantity() < self.available.quantity():
            redeemer = Redeemer(self._get_partial_redeemer(out_assets))
        else:
            redeemer = Redeemer(self._get_complete_redeemer())

        tx_builder.add_script_input(
            utxo=order_utxo,
            script=self.reference_utxo,
            redeemer=redeemer,
        )

        # Add reference inputs
        tx_builder.reference_inputs.add(pool_utxo)
        tx_builder.reference_inputs.add(oracle_utxo)

        # Process based on Djed operation type
        if isinstance(self.order_datum.action, DjedMintAction):
            return self._process_djed_mint(tx_builder, in_assets, out_assets, pool_utxo)
        else:  # DjedBurnAction
            return self._process_djed_burn(tx_builder, in_assets, out_assets, pool_utxo)

    def _process_djed_mint(
        self,
        tx_builder: TransactionBuilder,
        in_assets: Assets,
        out_assets: Assets,
        pool_utxo: UTxO,
    ) -> tuple[TransactionOutput | None, PlutusData]:
        """Process Djed minting order."""
        # Update order datum if partial fill
        order_datum = self.order_datum_class().from_cbor(self.order_datum.to_cbor())
        order_datum.action.djed_amount -= out_assets.quantity()

        # Update pool state with new Djed tokens
        updated_assets = self.assets.copy()
        updated_assets.root[in_assets.unit()] += in_assets.quantity()
        updated_assets.root[out_assets.unit()] -= out_assets.quantity()
        updated_assets += self._batcher_fee

        if out_assets.quantity() < self.available.quantity():
            # Partial fill - return updated order
            txo = TransactionOutput(
                address=Address.decode(self.address),
                amount=asset_to_value(updated_assets),
                datum_hash=order_datum.hash(),
            )
        else:
            # Complete fill - pay user and close order
            # Burn the beacon token
            tx_builder.add_minting_script(
                script=self.reference_utxo,
                redeemer=Redeemer(PlutusData()),  # Cancel redeemer placeholder
            )
            if tx_builder.mint is None:
                tx_builder.mint = asset_to_value(
                    Assets(**{self.dex_nft.unit(): -1}),
                ).multi_asset
            else:
                tx_builder.mint += asset_to_value(
                    Assets(**{self.dex_nft.unit(): -1}),
                ).multi_asset

            # Pay Djed tokens to user
            payment_assets = Assets(**{out_assets.unit(): out_assets.quantity()})
            payment_assets += Assets(lovelace=2_000_000)  # Min ADA

            txo = TransactionOutput(
                address=order_datum.owner_address.to_address(),
                amount=asset_to_value(payment_assets),
            )

        tx_builder.datums.update({order_datum.hash(): order_datum})
        return txo, order_datum

    def _process_djed_burn(
        self,
        tx_builder: TransactionBuilder,
        in_assets: Assets,
        out_assets: Assets,
        pool_utxo: UTxO,
    ) -> tuple[TransactionOutput | None, PlutusData]:
        """Process Djed burning order."""
        # Similar to mint but burning Djed for ADA
        order_datum = self.order_datum_class().from_cbor(self.order_datum.to_cbor())
        order_datum.action.djed_amount -= in_assets.quantity()

        # Update pool state
        updated_assets = self.assets.copy()
        updated_assets.root[in_assets.unit()] -= in_assets.quantity()
        updated_assets.root[out_assets.unit()] += out_assets.quantity()
        updated_assets += self._batcher_fee

        if in_assets.quantity() < self.available.quantity():
            # Partial fill
            txo = TransactionOutput(
                address=Address.decode(self.address),
                amount=asset_to_value(updated_assets),
                datum_hash=order_datum.hash(),
            )
        else:
            # Complete fill - close order and pay ADA
            # Burn the beacon token
            tx_builder.add_minting_script(
                script=self.reference_utxo,
                redeemer=Redeemer(PlutusData()),
            )
            if tx_builder.mint is None:
                tx_builder.mint = asset_to_value(
                    Assets(**{self.dex_nft.unit(): -1}),
                ).multi_asset
            else:
                tx_builder.mint += asset_to_value(
                    Assets(**{self.dex_nft.unit(): -1}),
                ).multi_asset

            # Pay ADA to user
            payment_assets = Assets(lovelace=out_assets.quantity())

            txo = TransactionOutput(
                address=order_datum.owner_address.to_address(),
                amount=asset_to_value(payment_assets),
            )

        tx_builder.datums.update({order_datum.hash(): order_datum})
        return txo, order_datum

    def _get_partial_redeemer(self, out_assets: Assets) -> PlutusData:
        """Get redeemer for partial order processing."""
        return PlutusData()  # Placeholder - implement based on actual contract

    def _get_complete_redeemer(self) -> PlutusData:
        """Get redeemer for complete order processing."""
        return PlutusData()  # Placeholder - implement based on actual contract


# === SHEN-SPECIFIC ORDER STATE ===


class ShenOrderState(DjedShenOrderStateBase):
    """Shen order state handling Shen mint/burn operations.

    Inherits common functionality from DjedShenOrderStateBase and implements
    Shen-specific pricing and transaction logic. Shen pricing is more complex
    as it depends on pool reserves and collateral ratios.
    """

    @classmethod
    def dex(cls) -> str:
        """Official dex name."""
        return "Shen"

    @property
    def price(self) -> tuple[int, int]:
        """Price for Shen operations (more complex - requires pool state)."""
        return self._calculate_shen_price()

    @property
    def available(self) -> Assets:
        """Available amount for Shen orders."""
        if isinstance(self.order_datum.action, ShenMintAction):
            return Assets(
                **{
                    "shen_policy_id.shen_token_name": self.order_datum.action.shen_amount
                }
            )
        else:  # ShenBurnAction
            ada_amount = self._calculate_shen_ada_return(
                self.order_datum.action.shen_amount
            )
            return Assets(lovelace=ada_amount)

    def _calculate_shen_price(self) -> tuple[int, int]:
        """Calculate Shen price based on current pool state.

        Shen price is determined by the excess ADA reserves beyond what's needed
        to back the Djed tokens. This is more complex than Djed pricing.
        """
        try:
            # Get current pool state
            pool_utxo = self._get_pool_utxo()
            # TODO: Parse pool datum to get reserve amounts and Djed supply
            # For now, return placeholder
            return (1, 1)  # ADA per Shen - placeholder
        except Exception:
            return (1, 1)  # Fallback price

    def _calculate_shen_ada_return(self, shen_amount: int) -> int:
        """Calculate ADA to return for Shen burning.

        Based on Shen's share of excess reserves beyond Djed backing.
        """
        try:
            # Get current pool state and calculate Shen's share
            # TODO: Implement complex calculation based on pool reserves
            return shen_amount  # Placeholder - 1:1 ratio
        except Exception:
            return shen_amount  # Fallback

    def swap_utxo(
        self,
        address_source: Address,
        in_assets: Assets,
        out_assets: Assets,
        tx_builder: TransactionBuilder,
        extra_assets: Assets | None = None,
        address_target: Address | None = None,
        datum_target: PlutusData | None = None,
    ) -> tuple[TransactionOutput | None, PlutusData]:
        """Build transaction for Shen order processing."""

        # Get reference UTxOs (using shared methods)
        pool_utxo = self._get_pool_utxo()
        oracle_utxo = self._get_oracle_utxo()

        # Similar structure to Djed but with Shen-specific logic
        assets = self.assets + Assets(**{self.dex_nft.unit(): 1})
        order_utxo = UTxO(
            TransactionInput(
                transaction_id=TransactionId(bytes.fromhex(self.tx_hash)),
                index=self.tx_index,
            ),
            output=TransactionOutput(
                address=Address.decode(self.address),
                amount=asset_to_value(assets),
                datum_hash=self.order_datum.hash(),
            ),
        )

        # Add script input with redeemer
        if out_assets.quantity() < self.available.quantity():
            redeemer = Redeemer(PlutusData())  # Partial redeemer
        else:
            redeemer = Redeemer(PlutusData())  # Complete redeemer

        tx_builder.add_script_input(
            utxo=order_utxo,
            script=self.reference_utxo,
            redeemer=redeemer,
        )

        # Add reference inputs
        tx_builder.reference_inputs.add(pool_utxo)
        tx_builder.reference_inputs.add(oracle_utxo)

        # Process based on Shen operation type
        if isinstance(self.order_datum.action, ShenMintAction):
            return self._process_shen_mint(tx_builder, in_assets, out_assets, pool_utxo)
        else:  # ShenBurnAction
            return self._process_shen_burn(tx_builder, in_assets, out_assets, pool_utxo)

    def _process_shen_mint(
        self,
        tx_builder: TransactionBuilder,
        in_assets: Assets,
        out_assets: Assets,
        pool_utxo: UTxO,
    ) -> tuple[TransactionOutput | None, PlutusData]:
        """Process Shen minting order."""
        # Similar to Djed mint but for Shen tokens
        order_datum = self.order_datum_class().from_cbor(self.order_datum.to_cbor())
        order_datum.action.shen_amount -= out_assets.quantity()

        updated_assets = self.assets.copy()
        updated_assets.root[in_assets.unit()] += in_assets.quantity()
        updated_assets.root[out_assets.unit()] -= out_assets.quantity()
        updated_assets += self._batcher_fee

        if out_assets.quantity() < self.available.quantity():
            txo = TransactionOutput(
                address=Address.decode(self.address),
                amount=asset_to_value(updated_assets),
                datum_hash=order_datum.hash(),
            )
        else:
            # Complete fill logic (similar to Djed)
            tx_builder.add_minting_script(
                script=self.reference_utxo,
                redeemer=Redeemer(PlutusData()),
            )
            if tx_builder.mint is None:
                tx_builder.mint = asset_to_value(
                    Assets(**{self.dex_nft.unit(): -1}),
                ).multi_asset
            else:
                tx_builder.mint += asset_to_value(
                    Assets(**{self.dex_nft.unit(): -1}),
                ).multi_asset

            payment_assets = Assets(**{out_assets.unit(): out_assets.quantity()})
            payment_assets += Assets(lovelace=2_000_000)

            txo = TransactionOutput(
                address=order_datum.owner_address.to_address(),
                amount=asset_to_value(payment_assets),
            )

        tx_builder.datums.update({order_datum.hash(): order_datum})
        return txo, order_datum

    def _process_shen_burn(
        self,
        tx_builder: TransactionBuilder,
        in_assets: Assets,
        out_assets: Assets,
        pool_utxo: UTxO,
    ) -> tuple[TransactionOutput | None, PlutusData]:
        """Process Shen burning order."""
        # Similar to Djed burn but for Shen tokens
        order_datum = self.order_datum_class().from_cbor(self.order_datum.to_cbor())
        order_datum.action.shen_amount -= in_assets.quantity()

        updated_assets = self.assets.copy()
        updated_assets.root[in_assets.unit()] -= in_assets.quantity()
        updated_assets.root[out_assets.unit()] += out_assets.quantity()
        updated_assets += self._batcher_fee

        if in_assets.quantity() < self.available.quantity():
            txo = TransactionOutput(
                address=Address.decode(self.address),
                amount=asset_to_value(updated_assets),
                datum_hash=order_datum.hash(),
            )
        else:
            # Complete fill logic
            tx_builder.add_minting_script(
                script=self.reference_utxo,
                redeemer=Redeemer(PlutusData()),
            )
            if tx_builder.mint is None:
                tx_builder.mint = asset_to_value(
                    Assets(**{self.dex_nft.unit(): -1}),
                ).multi_asset
            else:
                tx_builder.mint += asset_to_value(
                    Assets(**{self.dex_nft.unit(): -1}),
                ).multi_asset

            payment_assets = Assets(lovelace=out_assets.quantity())

            txo = TransactionOutput(
                address=order_datum.owner_address.to_address(),
                amount=asset_to_value(payment_assets),
            )

        tx_builder.datums.update({order_datum.hash(): order_datum})
        return txo, order_datum


# === SHARED ORDER BOOK BASE CLASS ===


class DjedShenOrderBookBase(AbstractOrderBookState):
    """Base class for Djed/Shen order books sharing common functionality."""

    fee: int = 150  # 1.5% fee in basis points
    _deposit: Assets = Assets(lovelace=2_000_000)

    @classmethod
    def order_selector(cls) -> list[str]:
        """Order selection information."""
        return DjedShenOrderStateBase.order_selector()

    @classmethod
    def pool_selector(cls) -> PoolSelector:
        """Pool selection information."""
        return DjedShenOrderStateBase.pool_selector()

    @property
    def swap_forward(self) -> bool:
        """Returns if swap forwarding is enabled."""
        return True

    @classmethod
    def default_script_class(cls):
        """Get default script class."""
        return DjedShenOrderStateBase.default_script_class()

    @classmethod
    def order_datum_class(cls):
        """Returns data class used for handling order datums."""
        return DjedShenOrderStateBase.order_datum_class()

    @property
    def stake_address(self) -> Address | None:
        """Return the staking address."""
        return None


# === DJED ORDER BOOK ===


class DjedOrderBook(DjedShenOrderBookBase):
    """Djed order book for Djed mint/burn operations."""

    @classmethod
    def get_book(
        cls,
        assets: Assets,
        orders: list[DjedOrderState] | None = None,
    ) -> "DjedOrderBook":
        """Create Djed order book."""
        if orders is None:
            selector = DjedOrderState.pool_selector()

            result = get_backend().get_pool_utxos(
                limit=1000,
                historical=False,
                **selector.model_dump(),
            )

            # Filter for Djed orders only
            orders = [
                DjedOrderState.model_validate(r.model_dump())
                for r in result
                if cls._is_djed_order(r)
            ]

        # Sort into buy (mint) and sell (burn) orders
        buy_orders = []  # Djed mint orders
        sell_orders = []  # Djed burn orders

        for order in orders:
            if order.inactive:
                continue

            price = order.price[0] / order.price[1]
            o = OrderBookOrder(
                price=price,
                quantity=int(order.available.quantity()),
                state=order,
            )

            if isinstance(order.order_datum.action, DjedMintAction):
                buy_orders.append(o)  # Mint = Buy
            else:  # DjedBurnAction
                sell_orders.append(o)  # Burn = Sell

        ob = DjedOrderBook(
            assets=assets,
            plutus_v2=True,
            block_time=int(time.time()),
            block_index=0,
            sell_book_full=SellOrderBook(sell_orders),
            buy_book_full=BuyOrderBook(buy_orders),
        )

        # Limit orders per transaction (following GeniusYield pattern)
        ob.sell_book_full = ob.sell_book_full[:3]
        ob.buy_book_full = ob.buy_book_full[:3]

        return ob

    @classmethod
    def dex(cls) -> str:
        """Official dex name."""
        return "Djed"

    @property
    def pool_id(self) -> str:
        """A unique identifier for the pool or ob."""
        return "Djed"

    @classmethod
    def _is_djed_order(cls, order_data) -> bool:
        """Check if order is a Djed order (not Shen)."""
        try:
            # Parse datum to check action type
            datum = DjedOrderDatum.from_cbor(order_data.datum_cbor)
            return isinstance(datum.action, (DjedMintAction, DjedBurnAction))
        except Exception:
            return False


# === SHEN ORDER BOOK ===


class ShenOrderBook(DjedShenOrderBookBase):
    """Shen order book for Shen mint/burn operations."""

    @classmethod
    def get_book(
        cls,
        assets: Assets,
        orders: list[ShenOrderState] | None = None,
    ) -> "ShenOrderBook":
        """Create Shen order book."""
        if orders is None:
            selector = ShenOrderState.pool_selector()

            result = get_backend().get_pool_utxos(
                limit=1000,
                historical=False,
                **selector.model_dump(),
            )

            # Filter for Shen orders only
            orders = [
                ShenOrderState.model_validate(r.model_dump())
                for r in result
                if cls._is_shen_order(r)
            ]

        # Sort into buy (mint) and sell (burn) orders
        buy_orders = []  # Shen mint orders
        sell_orders = []  # Shen burn orders

        for order in orders:
            if order.inactive:
                continue

            price = order.price[0] / order.price[1]
            o = OrderBookOrder(
                price=price,
                quantity=int(order.available.quantity()),
                state=order,
            )

            if isinstance(order.order_datum.action, ShenMintAction):
                buy_orders.append(o)  # Mint = Buy
            else:  # ShenBurnAction
                sell_orders.append(o)  # Burn = Sell

        ob = ShenOrderBook(
            assets=assets,
            plutus_v2=True,
            block_time=int(time.time()),
            block_index=0,
            sell_book_full=SellOrderBook(sell_orders),
            buy_book_full=BuyOrderBook(buy_orders),
        )

        # Limit orders per transaction (following GeniusYield pattern)
        ob.sell_book_full = ob.sell_book_full[:3]
        ob.buy_book_full = ob.buy_book_full[:3]

        return ob

    @classmethod
    def dex(cls) -> str:
        """Official dex name."""
        return "Shen"

    @property
    def pool_id(self) -> str:
        """A unique identifier for the pool or ob."""
        return "Shen"

    @classmethod
    def _is_shen_order(cls, order_data) -> bool:
        """Check if order is a Shen order (not Djed)."""
        try:
            # Parse datum to check action type
            datum = DjedOrderDatum.from_cbor(order_data.datum_cbor)
            return isinstance(datum.action, (ShenMintAction, ShenBurnAction))
        except Exception:
            return False
