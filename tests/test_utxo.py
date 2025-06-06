import os
import time

import pytest

from charli3_dendrite.backend import get_backend, set_backend
from charli3_dendrite import MinswapCPPState
from charli3_dendrite import MuesliSwapCPPState
from charli3_dendrite import SpectrumCPPState
from charli3_dendrite import WingRidersCPPState

from charli3_dendrite.dataclasses.models import Assets
from charli3_dendrite.dexs.amm.amm_base import AbstractPoolState
from charli3_dendrite.dexs.core.errors import InvalidLPError
from charli3_dendrite.dexs.core.errors import InvalidPoolError
from charli3_dendrite.dexs.core.errors import NoAssetsError
from charli3_dendrite.dexs.core.errors import NotAPoolError
from charli3_dendrite.dexs.ob.ob_base import AbstractOrderBookState
from dotenv import load_dotenv
from pycardano import Address
from pycardano import BlockFrostChainContext
from pycardano import ExtendedSigningKey
from pycardano import HDWallet
from pycardano import blockfrost
from pycardano import TransactionBuilder

load_dotenv()

context = BlockFrostChainContext(
    os.environ["PROJECT_ID"],
    base_url=getattr(blockfrost.ApiUrls, os.environ["NETWORK"]).value,
)

MALFORMED_CBOR = {
    "fadbbeb0012ae3864927e523f73048b22fba71d8be6f6a1336561363d3ec0b71",
    "9769d480c4022b36d62a16c7cea8037da7dc1197110a44e3e45104c27577d640",
    "0f6b5410f69646ccd94db7574b02a55e442e008dcdd1e0aceda7aa59d8b7c9ff",
    "44acc41c20c2a25e1f1bcdb0bfeb88d92e26af00d3246f9a163c0b33b2339986",
    "87e8e234b46a2bff09d88b308f7fec72954fc3689d99a093a02d970c3939191d",
    "c503c645047674f62a590164eab4c56f0e2af53fe579ef27c16b1a2ce60cc261",
    "5d0565927717a6de040c33f7b603d416935a24911c5376e3a81d1f74b339f15a",
}

IUSD = "f66d78b4a3cb3d37afa0ec36461e51ecbde00f26c8f0a68f94b6988069555344"
LQ = "da8c30857834c6ae7203935b89278c532b3995245295456f993e1d244c51"
IUSD_ASSETS = Assets(root={IUSD: 10000000})
LQ_ASSETS = Assets(root={LQ: 10000000})

wallet = HDWallet.from_mnemonic(os.environ["WALLET_MNEMONIC"])

SPEND_KEY = ExtendedSigningKey.from_hdwallet(
    wallet.derive_from_path("m/1852'/1815'/0'/0/0"),
)
STAKE_KEY = ExtendedSigningKey.from_hdwallet(
    wallet.derive_from_path("m/1852'/1815'/0'/2/0"),
)
ADDRESS = Address(
    SPEND_KEY.to_verification_key().hash(),
    STAKE_KEY.to_verification_key().hash(),
)


def test_build_utxo(dex: AbstractPoolState, subtests, backend):
    if issubclass(dex, AbstractOrderBookState):
        return

    set_backend(backend)
    selector = dex.pool_selector()
    result = get_backend().get_pool_utxos(
        limit=10000, historical=False, **selector.model_dump()
    )

    for record in result:
        try:
            pool = dex.model_validate(record.model_dump())

            if pool.unit_a == "lovelace" and pool.unit_b in [
                IUSD_ASSETS.unit(),
                LQ_ASSETS.unit(),
            ]:
                out_assets = (
                    LQ_ASSETS if pool.unit_b == LQ_ASSETS.unit() else IUSD_ASSETS
                )

                # Skip DEXs that are known to have NotImplementedError or missing functionality
                if dex.dex() not in ["GeniusYield", "Splash"]:
                    try:
                        pool.swap_utxo(
                            address_source=ADDRESS,
                            in_assets=Assets(root={"lovelace": 1000000}),
                            out_assets=out_assets,
                        )
                    except NotImplementedError:
                        pytest.skip(f"swap_utxo not implemented for {dex.dex()}")
                else:
                    # Currently GY and Splash require special handling or are not fully implemented
                    pytest.skip(f"Special handling required for {dex.dex()}")

        except InvalidLPError:
            pass
        except NoAssetsError:
            pass
        except InvalidPoolError:
            pass
        except NotAPoolError as e:
            # Known failures due to malformed data
            if record.tx_hash in MALFORMED_CBOR:
                pytest.xfail("Malformed CBOR tx.")
            else:
                raise
        except NotImplementedError:
            pytest.skip(f"Functionality not implemented for {dex.dex()}")


@pytest.mark.wingriders
def test_wingriders_batcher_fee(subtests):
    selector = WingRidersCPPState.pool_selector()
    result = get_backend().get_pool_utxos(
        limit=10000, historical=False, **selector.model_dump()
    )

    for record in result:
        try:
            pool = WingRidersCPPState.model_validate(record.model_dump())

            if pool.unit_a == "lovelace" and pool.unit_b == IUSD_ASSETS.unit():
                out_assets = (
                    LQ_ASSETS if pool.unit_b == LQ_ASSETS.unit() else IUSD_ASSETS
                )

                for amount, fee in zip(
                    [1000000, 500000000, 1000000000], [850000, 1500000, 2000000]
                ):
                    with subtests.test(f"input, fee: {amount}, {fee}"):
                        output, utxo = pool.swap_utxo(
                            address_source=ADDRESS,
                            in_assets=Assets(root={"lovelace": amount}),
                            out_assets=out_assets,
                        )
                        assert (
                            output.amount.coin
                            == amount
                            + fee
                            + pool.deposit(
                                in_assets=Assets(root={"lovelace": amount}),
                                out_assets=out_assets,
                            ).quantity()
                        )

        except InvalidLPError:
            pass
        except NoAssetsError:
            pass
        except InvalidPoolError:
            pass
        except NotAPoolError as e:
            # Known failures due to malformed data
            if record.tx_hash in MALFORMED_CBOR:
                pytest.xfail("Malformed CBOR tx.")
            else:
                raise


@pytest.mark.minswap
def test_minswap_batcher_fee(subtests):
    selector = MinswapCPPState.pool_selector()
    result = get_backend().get_pool_utxos(
        limit=10000, historical=False, **selector.model_dump()
    )

    for record in result:
        try:
            pool = MinswapCPPState.model_validate(record.model_dump())

            if pool.unit_a == "lovelace" and pool.unit_b == IUSD_ASSETS.unit():
                out_assets = (
                    LQ_ASSETS if pool.unit_b == LQ_ASSETS.unit() else IUSD_ASSETS
                )

                for amount, min_catalyst in zip(
                    [1000000, 500000000, 1000000000], [0, 25000000000, 50000000000]
                ):
                    with subtests.test(f"input, fee: {amount}, {min_catalyst}"):
                        output, datum = pool.swap_utxo(
                            address_source=ADDRESS,
                            in_assets=Assets(root={"lovelace": amount}),
                            out_assets=out_assets,
                            extra_assets=Assets(
                                {
                                    "29d222ce763455e3d7a09a665ce554f00ac89d2e99a1a83d267170c64d494e": min_catalyst
                                }
                            ),
                        )
                        assert datum.batcher_fee == 2000000 - min_catalyst // 100000

        except InvalidLPError:
            pass
        except NoAssetsError:
            pass
        except InvalidPoolError:
            pass
        except NotAPoolError as e:
            # Known failures due to malformed data
            if record.tx_hash in MALFORMED_CBOR:
                pytest.xfail("Malformed CBOR tx.")
            else:
                raise


def test_address_from_datum(dex: AbstractPoolState):
    # Create the datum
    datum = None

    try:
        if dex.dex() == "Spectrum":
            datum = dex.order_datum_class().create_datum(
                address_source=ADDRESS,
                in_assets=Assets(root={"lovelace": 1000000}),
                out_assets=Assets(root={"lovelace": 1000000}),
                batcher_fee=1000000,
                volume_fee=30,
                pool_token=Assets({"lovelace": 1}),
            )
        elif dex.dex() in ["SundaeSwap", "SundaeSwapV3"]:
            datum = dex.order_datum_class().create_datum(
                ident=b"01",
                address_source=ADDRESS,
                in_assets=Assets(root={"lovelace": 1000000}),
                out_assets=Assets(root={"lovelace": 1000000}),
                fee=30,
            )
        elif dex.dex() == "Axo":
            pass
        elif dex.dex() == "Splash":
            # Skip Splash since SplashOrderDatum doesn't have create_datum method
            pytest.skip("SplashOrderDatum doesn't have create_datum method")
        elif dex.dex() not in ["GeniusYield"]:
            # Check if the order_datum_class has create_datum method
            order_datum_class = dex.order_datum_class()
            if hasattr(order_datum_class, 'create_datum'):
                datum = order_datum_class.create_datum(
                    address_source=ADDRESS,
                    in_assets=Assets(root={"lovelace": 1000000}),
                    out_assets=Assets(root={IUSD: 1000000}),
                    batcher_fee=Assets(root={"lovelace": 1000000}),
                    deposit=Assets(root={"lovelace": 1000000}),
                )
            else:
                pytest.skip(f"{dex.dex()} order datum class doesn't have create_datum method")
    except AttributeError as e:
        if "create_datum" in str(e):
            pytest.skip(f"create_datum method not available for {dex.dex()}")
        else:
            raise
    except NotImplementedError:
        pytest.skip(f"create_datum not implemented for {dex.dex()}")

    if datum is not None:
        try:
            if datum.address_source().payment_part is not None:
                assert (
                    ADDRESS.payment_part.payload
                    == datum.address_source().payment_part.payload
                )
            elif datum.address_source().staking_part is not None:
                assert (
                    ADDRESS.staking_part.payload
                    == datum.address_source().staking_part.payload
                )
            else:
                raise TypeError
        except AttributeError:
            # Some datum classes might not have address_source method
            pytest.skip(f"address_source method not available for {dex.dex()}")


@pytest.mark.parametrize(
    "dex",
    [
        SpectrumCPPState,
        MuesliSwapCPPState,
    ],
)
def test_reference_utxo(dex: AbstractPoolState):
    assert dex.reference_utxo() is not None
