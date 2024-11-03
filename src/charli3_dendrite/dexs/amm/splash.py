"""Minswap DEX Module."""

from audioop import mul
from dataclasses import dataclass
from hashlib import sha3_256
from typing import ClassVar
from typing import List
from typing import Union

from pycardano import Address
from pycardano import Datum
from pycardano import PlutusData
from pycardano import PlutusV1Script
from pycardano import PlutusV2Script
from pycardano import TransactionId
from pycardano import TransactionInput
from pycardano import TransactionOutput
from pycardano import UTxO
from pycardano import Value
from pycardano import VerificationKeyHash

from charli3_dendrite.dataclasses.datums import AssetClass
from charli3_dendrite.dataclasses.datums import OrderDatum
from charli3_dendrite.dataclasses.datums import PlutusFullAddress
from charli3_dendrite.dataclasses.datums import PlutusNone
from charli3_dendrite.dataclasses.datums import PoolDatum
from charli3_dendrite.dataclasses.datums import ReceiverDatum
from charli3_dendrite.dataclasses.datums import _PlutusConstrWrapper
from charli3_dendrite.dataclasses.models import OrderType
from charli3_dendrite.dataclasses.models import PoolSelector
from charli3_dendrite.dexs.amm.amm_types import AbstractCommonStableSwapPoolState
from charli3_dendrite.dexs.amm.amm_types import AbstractConstantProductPoolState
from charli3_dendrite.dexs.amm.sundae import SundaeV3PlutusNone
from charli3_dendrite.dexs.amm.sundae import SundaeV3ReceiverDatumHash
from charli3_dendrite.dexs.amm.sundae import SundaeV3ReceiverInlineDatum
from charli3_dendrite.utility import Assets


@dataclass
class BoolFalse(PlutusData):
    CONSTR_ID = 0


@dataclass
class BoolTrue(PlutusData):
    CONSTR_ID = 1


@dataclass
class SplashPoolDatum(PoolDatum):
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


class SplashSSPState(AbstractCommonStableSwapPoolState):
    """Splash StableSwap Pool State."""

    fee: int = 30
    _batcher = Assets(lovelace=2000000)
    _deposit = Assets(lovelace=2000000)
    _stake_address: ClassVar[Address] = []

    @classmethod
    def dex(cls) -> str:
        return "Splash"

    @classmethod
    def order_selector(self) -> list[str]:
        return ["addr1w9wnm7vle7al9q4aw63aw63wxz7aytnpc4h3gcjy0yufxwc3mr3e5"]

    @classmethod
    def pool_selector(cls) -> PoolSelector:
        return PoolSelector(
            addresses=["addr1w9wnm7vle7al9q4aw63aw63wxz7aytnpc4h3gcjy0yufxwc3mr3e5"],
        )

    @property
    def swap_forward(self) -> bool:
        return True

    @property
    def stake_address(self) -> Address | None:
        return None

    @classmethod
    def order_datum_class(cls) -> type[SplashOrder]:
        return SplashOrder

    @classmethod
    def script_class(cls) -> type[PlutusV2Script]:
        return PlutusV2Script

    @classmethod
    def pool_datum_class(self) -> type[SplashPoolDatum]:
        return SplashPoolDatum

    def batcher_fee(
        self,
        in_assets: Assets | None = None,
        out_assets: Assets | None = None,
        extra_assets: Assets | None = None,
    ) -> Assets:
        """Batcher fee.

        For Minswap, the batcher fee decreases linearly from 2.0 ADA to 1.5 ADA as the
        MIN in the input assets from 0 - 50,000 MIN.
        """
        MIN = "29d222ce763455e3d7a09a665ce554f00ac89d2e99a1a83d267170c64d494e"
        if extra_assets is not None and MIN in extra_assets:
            fee_reduction = min(extra_assets[MIN] // 10**5, 500000)
        else:
            fee_reduction = 0
        return self._batcher - Assets(lovelace=fee_reduction)

    @property
    def pool_id(self) -> str:
        """A unique identifier for the pool."""
        return self.pool_nft.unit()

    @classmethod
    def pool_policy(cls) -> list[str]:
        return ["0be55d262b29f564998ff81efe21bdc0022621c12f15af08d0f2ddb1"]

    @classmethod
    def lp_policy(cls) -> list[str]:
        return ["e4214b7cce62ac6fbba385d164df48e157eae5863521b4b67ca71d86"]

    @classmethod
    def dex_policy(cls) -> list[str]:
        return ["13aa2accf2e1561723aa26871e071fdf32c867cff7e7d50ad470d62f"]
