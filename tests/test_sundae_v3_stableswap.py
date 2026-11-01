"""SundaeSwap V3 stableswap quotes against recorded mainnet scoops.

Each recorded swap gives a pool UTxO's reserves (net of the datum's protocol fees),
one swap order against it, and what the contract paid out and left in the pool.
"""

from __future__ import annotations

import json
import random
from pathlib import Path

import pytest
from charli3_dendrite.dataclasses.models import Assets
from charli3_dendrite.dexs.amm.sundae import SundaeSwapV3StableSwap
from charli3_dendrite.dexs.amm.sundae import SundaeV3StablePoolDatum
from charli3_dendrite.dexs.core.errors import InvalidPoolError

SWAPS = json.loads(
    (Path(__file__).parent / "data" / "sundae_v3_stableswap_swaps.json").read_text(),
)["swaps"]
_MIN_ADA = 2_000_000
_LEDGER_MAX = 2**64 - 1


def _skip_settings_read(*_args: object, **_kwargs: object) -> None:
    """Stand-in for the settings-datum read, which needs a backend."""


@pytest.fixture(autouse=True)
def _no_settings_read(monkeypatch: pytest.MonkeyPatch) -> None:
    """Pin the batcher fee normally read from the settings datum on a backend."""
    monkeypatch.setattr(
        SundaeSwapV3StableSwap,
        "get_batcher_fee",
        classmethod(_skip_settings_read),
    )
    monkeypatch.setattr(
        SundaeSwapV3StableSwap,
        "_batcher_fee",
        Assets(lovelace=1_000_000),
        raising=False,
    )


def _ids(swap: dict) -> str:
    return swap["pool_utxo"][:12] + swap["pool_utxo"][-2:]


def _values(swap: dict, assets: Assets) -> dict:
    tx_hash, tx_index = swap["pool_utxo"].split("#")
    return {
        "assets": assets,
        "datum_cbor": swap["datum_cbor"],
        "datum_hash": "",
        "tx_hash": tx_hash,
        "tx_index": int(tx_index),
        "block_time": 0,
        "block_index": 0,
        "plutus_v2": False,
    }


def _parsed_pool(
    swap: dict,
    reserves: list[int] | None = None,
) -> SundaeSwapV3StableSwap:
    """A pool built from already-parsed reserves (the pool NFT is passed in)."""
    reserve_a, reserve_b = swap["reserves"] if reserves is None else reserves
    assets = Assets(
        **{
            "lovelace": _MIN_ADA,
            swap["unit_a"]: reserve_a,
            swap["unit_b"]: reserve_b,
        },
    )
    values = _values(swap, assets)
    values["pool_nft"] = Assets(**{swap["pool_nft"]: 1})
    return SundaeSwapV3StableSwap.model_validate(values)


def _raw_pool(swap: dict) -> SundaeSwapV3StableSwap:
    """A pool built from the raw UTxO value: reserves still hold the protocol fees."""
    datum = SundaeV3StablePoolDatum.from_cbor(swap["datum_cbor"])
    reserve_a, reserve_b = swap["reserves"]
    assets = Assets(
        **{
            "lovelace": _MIN_ADA,
            swap["unit_a"]: reserve_a + datum.protocol_fees[1],
            swap["unit_b"]: reserve_b + datum.protocol_fees[2],
            swap["pool_nft"]: 1,
        },
    )
    return SundaeSwapV3StableSwap.model_validate(_values(swap, assets))


def _out_unit(swap: dict) -> str:
    return swap["unit_b"] if swap["offer_unit"] == swap["unit_a"] else swap["unit_a"]


def _takes(pool: SundaeSwapV3StableSwap, unit: str, amount: int) -> int:
    return pool.get_amount_out(Assets(**{unit: amount}))[0].quantity()


@pytest.mark.parametrize("swap", SWAPS, ids=_ids)
def test_parsed_pool_keeps_its_reserves(swap: dict) -> None:
    """Already-parsed reserves are net of protocol fees; nothing is taken again."""
    pool = _parsed_pool(swap)
    assert (pool.unit_a, pool.unit_b) == (swap["unit_a"], swap["unit_b"])
    assert [pool.reserve_a, pool.reserve_b] == swap["reserves"]
    datum = SundaeV3StablePoolDatum.from_cbor(swap["datum_cbor"])
    assert pool.volume_fee == [
        lp + protocol
        for lp, protocol in zip(
            datum.lp_fee_basis_points,
            datum.protocol_fee_basis_points,
        )
    ]


@pytest.mark.parametrize("swap", SWAPS, ids=_ids)
def test_raw_utxo_nets_protocol_fees_once(swap: dict) -> None:
    """A raw pool UTxO still holds the protocol fees; parsing takes them once."""
    pool = _raw_pool(swap)
    assert (pool.unit_a, pool.unit_b) == (swap["unit_a"], swap["unit_b"])
    assert [pool.reserve_a, pool.reserve_b] == swap["reserves"]
    assert pool.pool_id == swap["pool_nft"]


@pytest.mark.parametrize("swap", SWAPS, ids=_ids)
def test_amount_out_is_the_contract_payout(swap: dict) -> None:
    """The quote is exactly what the contract paid the order."""
    pool = _parsed_pool(swap)
    out, _ = pool.get_amount_out(Assets(**{swap["offer_unit"]: swap["offer"]}))
    assert out == Assets(**{_out_unit(swap): swap["takes"]})
    assert _raw_pool(swap).get_amount_out(
        Assets(**{swap["offer_unit"]: swap["offer"]}),
    )[0] == Assets(**{_out_unit(swap): swap["takes"]})


@pytest.mark.parametrize("swap", SWAPS, ids=_ids)
def test_amount_in_is_the_least_offer_for_the_payout(swap: dict) -> None:
    """The inverse quote is the least offer reaching the payout."""
    pool = _parsed_pool(swap)
    needed, _ = pool.get_amount_in(Assets(**{_out_unit(swap): swap["takes"]}))
    assert needed == Assets(**{swap["offer_unit"]: swap["min_offer"]})
    assert _takes(pool, swap["offer_unit"], swap["min_offer"]) >= swap["takes"]
    assert _takes(pool, swap["offer_unit"], swap["min_offer"] - 1) < swap["takes"]


@pytest.mark.parametrize("swap", SWAPS, ids=_ids)
def test_swap_result_splits_the_fee_and_moves_the_reserves(swap: dict) -> None:
    """The out-side reserve drops by the payout plus the protocol share."""
    pool = _parsed_pool(swap)
    result = pool.swap_result(Assets(**{swap["offer_unit"]: swap["offer"]}))
    assert (result.takes, result.gross, result.fee, result.protocol_share) == (
        swap["takes"],
        swap["gross"],
        swap["fee"],
        swap["protocol_share"],
    )
    reserves = list(swap["reserves"])
    i = 0 if swap["offer_unit"] == swap["unit_a"] else 1
    reserves[i] += swap["offer"]
    reserves[1 - i] -= result.takes + result.protocol_share
    assert reserves == swap["reserves_after"]
    assert _parsed_pool(swap, reserves).sum_invariant() == swap["sum_invariant_after"]


@pytest.mark.parametrize("swap", SWAPS, ids=_ids)
def test_sum_invariant_follows_the_reserves_not_the_datum(swap: dict) -> None:
    """The invariant is recomputed from the reserves, wherever they moved."""
    pool = _parsed_pool(swap)
    datum = SundaeV3StablePoolDatum.from_cbor(swap["datum_cbor"])
    assert pool.sum_invariant() == datum.sum_invariant
    # Reserves moved past the datum (the datum's invariant is now stale).
    moved = _parsed_pool(swap, swap["reserves_after"])
    assert moved.sum_invariant() == swap["sum_invariant_after"]
    # A move made directly on the reserves is seen by the next quote.
    pool.assets.root[swap["unit_a"]] = swap["reserves_after"][0]
    pool.assets.root[swap["unit_b"]] = swap["reserves_after"][1]
    assert pool.sum_invariant() == swap["sum_invariant_after"]


@pytest.mark.parametrize("swap", SWAPS[:4], ids=_ids)
def test_amount_in_matches_a_bisection(swap: dict) -> None:
    """The closed-form inverse equals a bisection over the exact quote."""
    pool = _parsed_pool(swap)
    out_unit, in_unit = _out_unit(swap), swap["offer_unit"]
    rng = random.Random(swap["pool_utxo"])
    cap = pool.max_output(out_unit) - 1
    for want in [1, 2, 3, cap] + [rng.randint(1, cap) for _ in range(20)]:
        lo, hi = 1, _LEDGER_MAX
        while lo < hi:
            mid = (lo + hi) // 2
            if _takes(pool, in_unit, mid) >= want:
                hi = mid
            else:
                lo = mid + 1
        assert pool.get_amount_in(Assets(**{out_unit: want}))[0] == Assets(
            **{in_unit: lo},
        )


def test_max_output_is_the_first_undeliverable_amount() -> None:
    """At and past ``max_output`` no ledger offer reaches the output."""
    swap = SWAPS[0]
    pool = _parsed_pool(swap)
    out_unit, in_unit = _out_unit(swap), swap["offer_unit"]
    cap = pool.max_output(out_unit)
    assert cap == _takes(pool, in_unit, _LEDGER_MAX) + 1
    assert cap <= pool.assets.root[out_unit]
    assert pool.get_amount_in(Assets(**{out_unit: cap - 1}))[0].quantity() <= (
        _LEDGER_MAX
    )
    with pytest.raises(InvalidPoolError):
        pool.get_amount_in(Assets(**{out_unit: cap}))
    with pytest.raises(InvalidPoolError):
        pool.get_amount_in(Assets(**{out_unit: pool.assets.root[out_unit]}))
    with pytest.raises(ValueError, match="invalid for pool"):
        pool.max_output("lovelace")


def test_no_amount_quotes_nothing() -> None:
    """No offer pays nothing, and no output needs no offer."""
    swap = SWAPS[0]
    pool = _parsed_pool(swap)
    out_unit, in_unit = _out_unit(swap), swap["offer_unit"]
    assert pool.get_amount_out(Assets(**{in_unit: 0}))[0] == Assets(**{out_unit: 0})
    assert pool.get_amount_in(Assets(**{out_unit: 0}))[0] == Assets(**{in_unit: 0})
    result = pool.swap_result(Assets(**{in_unit: 0}))
    assert (result.takes, result.gross, result.fee, result.protocol_share) == (
        0,
        0,
        0,
        0,
    )


@pytest.mark.parametrize(
    "emptied",
    ["out", "in", "both"],
)
def test_an_empty_side_pays_nothing_and_delivers_nothing(emptied: str) -> None:
    """An empty side pays nothing for an offer, and no offer reaches any output."""
    swap = SWAPS[0]
    pool = _parsed_pool(swap)
    out_unit, in_unit = _out_unit(swap), swap["offer_unit"]
    if emptied in ("out", "both"):
        pool.assets.root[out_unit] = 0
    if emptied in ("in", "both"):
        pool.assets.root[in_unit] = 0
    assert pool.sum_invariant() == 0
    assert pool.get_amount_out(Assets(**{in_unit: 10}))[0] == Assets(**{out_unit: 0})
    result = pool.swap_result(Assets(**{in_unit: 10}))
    assert (result.takes, result.gross, result.fee, result.protocol_share) == (
        0,
        0,
        0,
        0,
    )
    assert pool.max_output(out_unit) == 1
    assert pool.get_amount_in(Assets(**{out_unit: 0}))[0] == Assets(**{in_unit: 0})
    with pytest.raises(InvalidPoolError):
        pool.get_amount_in(Assets(**{out_unit: 10}))
    with pytest.raises(InvalidPoolError):
        pool.get_amount_in(Assets(**{out_unit: 1}))


def test_a_negative_quantity_is_rejected() -> None:
    """A negative offer or output is not a swap."""
    swap = SWAPS[0]
    pool = _parsed_pool(swap)
    out_unit, in_unit = _out_unit(swap), swap["offer_unit"]
    with pytest.raises(ValueError, match="negative"):
        pool.get_amount_out(Assets(**{in_unit: -1}))
    with pytest.raises(ValueError, match="negative"):
        pool.swap_result(Assets(**{in_unit: -1}))
    with pytest.raises(ValueError, match="negative"):
        pool.get_amount_in(Assets(**{out_unit: -1}))


def test_foreign_or_multiple_assets_are_rejected() -> None:
    """Only a single asset of the pool's pair is accepted."""
    swap = SWAPS[0]
    pool = _parsed_pool(swap)
    with pytest.raises(ValueError, match="invalid for pool"):
        pool.get_amount_out(Assets(lovelace=10))
    with pytest.raises(ValueError, match="invalid for pool"):
        pool.get_amount_in(Assets(lovelace=10))
    with pytest.raises(ValueError, match="only have one token"):
        pool.get_amount_out(Assets(**{swap["unit_a"]: 1, swap["unit_b"]: 1}))
