"""Sort mixed IPv4/IPv6 addresses and ranges in proper numeric order.

Uses the stdlib ipaddress module. Addresses and networks are normalized to
a (version, start_int, prefix_len) tuple so that IPv4 always sorts before
IPv6, and within a version, hosts sort before the networks that contain them.
"""

from __future__ import annotations

import functools
import ipaddress
from typing import Iterable, List, Union

# A parsed address or network. We keep the original string so callers get
# back exactly what they put in (normalized by ipaddress, which strips
# leading zeros and collapses IPv6 notation).
SortableAddress = Union[ipaddress.IPv4Address, ipaddress.IPv6Address,
                        ipaddress.IPv4Network, ipaddress.IPv6Network]


def _range(item: SortableAddress):
    """Return (start_int, end_int, prefix_len) for an address or network.

    A bare address is treated as a /32 or /128, so its start and end are
    the address itself.
    """
    if isinstance(item, (ipaddress.IPv4Address, ipaddress.IPv6Address)):
        start = int(item)
        prefix = 32 if item.version == 4 else 128
        return start, start, prefix
    start = int(item.network_address)
    end = int(item.broadcast_address)
    return start, end, item.prefixlen


def _cmp(a: SortableAddress, b: SortableAddress) -> int:
    """Compare two addresses/networks.

    IPv4 sorts before IPv6. Within a version, if one range contains the
    other the narrower (larger prefix length) sorts first, so a host sorts
    before any network that contains it. Otherwise ordering is by numeric
    start value, then by prefix length (narrower first).
    """
    if a.version != b.version:
        return -1 if a.version < b.version else 1
    a_start, a_end, a_prefix = _range(a)
    b_start, b_end, b_prefix = _range(b)
    a_contains_b = a_start <= b_start and a_end >= b_end
    b_contains_a = b_start <= a_start and b_end >= a_end
    if a_contains_b and not b_contains_a:
        # a is wider, so b (narrower) sorts first.
        return 1
    if b_contains_a and not a_contains_b:
        return -1
    if a_start != b_start:
        return -1 if a_start < b_start else 1
    if a_prefix != b_prefix:
        return -1 if a_prefix > b_prefix else 1
    return 0


def sort_addresses(items: Iterable[Union[str, SortableAddress]]) -> List[SortableAddress]:
    """Sort a mixed list of IPv4/IPv6 addresses and CIDR ranges.

    Accepts strings or already-parsed ipaddress objects. Returns parsed
    ipaddress objects in sorted order. IPv4 sorts before IPv6; within a
    version, a host sorts before any network that contains it, otherwise
    ordering is by numeric value of the start address, then by prefix length
    (narrower first).

    Raises ValueError if any item is not a valid IP address or network.
    """
    parsed: List[SortableAddress] = []
    for raw in items:
        if isinstance(raw, (ipaddress.IPv4Address, ipaddress.IPv6Address,
                            ipaddress.IPv4Network, ipaddress.IPv6Network)):
            parsed.append(raw)
            continue
        s = str(raw).strip()
        # Try network first: ipaddress.ip_network accepts bare hosts too,
        # but with strict=True it rejects a host bits set as a network. We
        # want "192.0.2.1" to parse as an address, not a /32 network, so
        # the caller gets back an address object and our sort key reflects
        # that. Try address first, then network.
        try:
            parsed.append(ipaddress.ip_address(s))
            continue
        except ValueError:
            pass
        parsed.append(ipaddress.ip_network(s, strict=False))
    return sorted(parsed, key=functools.cmp_to_key(_cmp))
