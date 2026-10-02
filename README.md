# IP Address Sorter

Sort a mixed list of IPv4 and IPv6 addresses and CIDR ranges in proper numeric order using the standard library `ipaddress` module.

```python
from ip_address_sorter import sort_addresses

result = sort_addresses(["10.0.0.10", "2001:db8::1", "10.0.0.0/24", "10.0.0.2"])
for item in result:
    print(item)
# 10.0.0.2
# 10.0.0.10
# 10.0.0.0/24
# 2001:db8::1
```

## Why

The `ipaddress` module parses addresses and networks well but does not provide a sort order that mixes the two sensibly. Comparing an `IPv4Address` to an `IPv4Network` raises `TypeError`, and there is no built-in rule for whether a host should sort before or after a network that contains it. This library gives one consistent answer: IPv4 before IPv6, then by numeric start value, then by prefix length (narrower first). A bare address is treated as a /32 or /128, so it sorts adjacent to networks of the same span and before any wider network that contains it.

## Edge cases

- Networks written with host bits set (e.g. `10.0.0.1/24`) are accepted and normalized to the network address (`10.0.0.0/24`) using `strict=False`. If you need strict validation, pre-parse with `ipaddress.ip_network(s, strict=True)`.
- Input strings are stripped of surrounding whitespace.
- Already-parsed `ipaddress` objects are accepted directly and passed through.
- Invalid input raises `ValueError` from the `ipaddress` parser.

## Exports

- `sort_addresses(items)` — takes an iterable of strings or `ipaddress` objects, returns a list of parsed `ipaddress` objects sorted by `(version, start_int, prefix_len)`.
- `SortableAddress` — a `typing.Union` alias for the four return types (`IPv4Address`, `IPv6Address`, `IPv4Network`, `IPv6Network`).

## Performance

The window keeps a bounded buffer, so `push` is constant time and memory does not
grow with the length of the stream. `peak` and `trough` are linear in the window
size, which is the trade that keeps `push` cheap.

