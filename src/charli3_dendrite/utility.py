"""Utility functions for handling asset information."""

import json
from datetime import datetime
from datetime import timedelta
from decimal import Decimal
from pathlib import Path
from fractions import Fraction
from typing import Tuple

import requests
from pycardano import Value

from charli3_dendrite.dataclasses.models import Assets

ASSET_PATH = Path(__file__).parent.joinpath(".assets")

ASSET_PATH.mkdir(parents=True, exist_ok=True)

# === DJED/SHEN MATHEMATICAL UTILITIES ===


class DjedRational:
    """High-precision rational number implementation for Djed stablecoin calculations.

    Uses Python's Fraction class internally to ensure exact arithmetic without
    floating-point precision errors. Critical for financial calculations where
    precision matters.
    """

    def __init__(self, numerator: int, denominator: int = 1):
        """Initialize a rational number.

        Args:
            numerator: The numerator of the rational number
            denominator: The denominator of the rational number

        Raises:
            ValueError: If denominator is zero
        """
        if denominator == 0:
            raise ValueError("Denominator cannot be zero")
        self.fraction = Fraction(numerator, denominator)

    @classmethod
    def from_tuple(cls, rational_tuple: Tuple[int, int]) -> "DjedRational":
        """Create DjedRational from (numerator, denominator) tuple.

        Args:
            rational_tuple: Tuple of (numerator, denominator)

        Returns:
            DjedRational instance
        """
        return cls(rational_tuple[0], rational_tuple[1])

    def mul(self, other: "DjedRational") -> "DjedRational":
        """Multiply this rational with another.

        Args:
            other: Another DjedRational instance

        Returns:
            New DjedRational with the product
        """
        result = self.fraction * other.fraction
        return DjedRational(result.numerator, result.denominator)

    def div(self, other: "DjedRational") -> "DjedRational":
        """Divide this rational by another.

        Args:
            other: Another DjedRational instance

        Returns:
            New DjedRational with the quotient

        Raises:
            ValueError: If dividing by zero
        """
        if other.fraction == 0:
            raise ValueError("Division by zero")
        result = self.fraction / other.fraction
        return DjedRational(result.numerator, result.denominator)

    def add(self, other: "DjedRational") -> "DjedRational":
        """Add another rational to this one.

        Args:
            other: Another DjedRational instance

        Returns:
            New DjedRational with the sum
        """
        result = self.fraction + other.fraction
        return DjedRational(result.numerator, result.denominator)

    def sub(self, other: "DjedRational") -> "DjedRational":
        """Subtract another rational from this one.

        Args:
            other: Another DjedRational instance

        Returns:
            New DjedRational with the difference
        """
        result = self.fraction - other.fraction
        return DjedRational(result.numerator, result.denominator)

    def invert(self) -> "DjedRational":
        """Return multiplicative inverse (1/x).

        Returns:
            New DjedRational with inverted value

        Raises:
            ValueError: If trying to invert zero
        """
        if self.fraction == 0:
            raise ValueError("Cannot invert zero")
        return DjedRational(self.fraction.denominator, self.fraction.numerator)

    def to_int(self, rounding: str = "ROUND_DOWN") -> int:
        """Convert to integer with specified rounding.

        Args:
            rounding: Rounding method ('ROUND_UP' or 'ROUND_DOWN')

        Returns:
            Integer representation
        """
        from decimal import Decimal, ROUND_CEILING, ROUND_FLOOR, getcontext

        # Set high precision for financial calculations
        getcontext().prec = 50

        decimal_val = Decimal(str(self.fraction))
        if rounding == "ROUND_UP":
            return int(decimal_val.quantize(Decimal("1"), rounding=ROUND_CEILING))
        else:  # ROUND_DOWN (default)
            return int(decimal_val.quantize(Decimal("1"), rounding=ROUND_FLOOR))

    def to_tuple(self) -> Tuple[int, int]:
        """Convert to (numerator, denominator) tuple for Plutus data.

        Returns:
            Tuple of (numerator, denominator)
        """
        return (self.fraction.numerator, self.fraction.denominator)

    def to_float(self) -> float:
        """Convert to float for display purposes only.

        Note: Should not be used for calculations due to precision loss.

        Returns:
            Float representation
        """
        return float(self.fraction)

    def __str__(self) -> str:
        """String representation."""
        return f"{self.fraction.numerator}/{self.fraction.denominator}"

    def __repr__(self) -> str:
        """Debug representation."""
        return f"DjedRational({self.fraction.numerator}, {self.fraction.denominator})"

    def __eq__(self, other) -> bool:
        """Equality comparison."""
        if isinstance(other, DjedRational):
            return self.fraction == other.fraction
        return False


# === EXISTING UTILITY FUNCTIONS ===


def asset_info(unit: str, update: bool = False) -> dict:  # noqa: ARG001
    """Fetch and cache asset information.

    Args:
        unit (str): The unit of the asset to retrieve information for.
        update (bool): Whether to update the asset info forcefully.

    Returns:
        dict: dictionary containing asset information.
    """
    path = ASSET_PATH.joinpath(f"{unit}.json")

    if path.exists():
        with path.open() as fr:
            parsed = json.load(fr)
            if "timestamp" in parsed and (
                datetime.now() - datetime.fromtimestamp(parsed["timestamp"])
            ) < timedelta(days=1, minutes=0, seconds=0):
                return parsed

    response = requests.get(
        f"https://raw.githubusercontent.com/cardano-foundation/cardano-token-registry/master/mappings/{unit}.json",
        timeout=10,
    )

    if response.status_code != requests.codes.ok:
        msg = f"Error fetching asset info, {unit}: {response.text}"
        raise requests.HTTPError(msg)

    parsed = response.json()
    parsed["timestamp"] = datetime.now().timestamp()
    with path.open("w") as fw:
        json.dump(response.json(), fw)

    return response.json()


def asset_decimals(unit: str) -> int:
    """Asset decimals.

    All asset quantities are stored as integers. The decimals indicates a scaling factor
    for the purposes of human readability of asset denominations.

    For example, ADA has 6 decimals. This means every 10**6 units (lovelace) is 1 ADA.

    Args:
        unit: The policy id plus hex encoded name of an asset.

    Returns:
        The decimals for the asset.
    """
    if unit == "lovelace":
        return 6

    parsed = asset_info(unit)
    if "decimals" not in parsed:
        return 0

    return int(parsed["decimals"]["value"])


def asset_ticker(unit: str) -> str:
    """Ticker symbol for an asset.

    This function is designed to always return a value. If a `ticker` is available in
    the asset metadata, it is returned. Otherwise, the human readable asset name is
    returned.

    Args:
        unit: The policy id plus hex encoded name of an asset.

    Returns:
        The ticker or human readable name of an asset.
    """
    if unit == "lovelace":
        asset_ticker = "ADA"
    else:
        parsed = asset_info(unit)

        if "ticker" in parsed:
            asset_ticker = parsed["ticker"]["value"]
        else:
            asset_ticker = bytes.fromhex(unit[56:]).decode()

    return asset_ticker


def asset_name(unit: str) -> str:
    """Ticker symbol for an asset.

    This function is designed to always return a value. If a `ticker` is available in
    the asset metadata, it is returned. Otherwise, the human readable asset name is
    returned.

    Args:
        unit: The policy id plus hex encoded name of an asset.

    Returns:
        The ticker or human readable name of an asset.
    """
    if unit == "lovelace":
        asset_name = "ADA"
    else:
        parsed = asset_info(unit)

        if "name" in parsed:
            asset_name = parsed["name"]["value"]
        else:
            asset_name = bytes.fromhex(unit[56:]).decode()

    return asset_name


def asset_to_value(assets: Assets) -> Value:
    """Convert an Assets object to a pycardano.Value."""
    coin = assets["lovelace"]
    cnts = {}
    for unit, quantity in assets.items():
        if unit == "lovelace":
            continue
        policy = bytes.fromhex(unit[:56])
        asset_name = bytes.fromhex(unit[56:])
        if policy not in cnts:
            cnts[policy] = {asset_name: quantity}
        else:
            cnts[policy][asset_name] = quantity

    if len(cnts) == 0:
        return Value.from_primitive([coin])
    return Value.from_primitive([coin, cnts])


def naturalize_assets(assets: Assets) -> dict[str, Decimal]:
    """Get the number of decimals associated with an asset.

    This returns a `Decimal` with the proper precision context.

    Args:
        assets (Assets): The policy id plus hex encoded name of an asset.

    Returns:
        A dictionary where assets are keys and values are `Decimal` objects containing
            exact quantities of the asset, accounting for asset decimals.
    """
    nat_assets = {}
    for unit, quantity in assets.items():
        if unit == "lovelace":
            nat_assets["lovelace"] = Decimal(quantity) / Decimal(10**6)
        else:
            nat_assets[unit] = Decimal(quantity) / Decimal(10 ** asset_decimals(unit))

    return nat_assets
