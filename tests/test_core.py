import ipaddress
import unittest

from ip_address_sorter import sort_addresses


class TestSortAddresses(unittest.TestCase):

    def test_empty_list(self):
        self.assertEqual(sort_addresses([]), [])

    def test_single_ipv4(self):
        result = sort_addresses(["10.0.0.1"])
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], ipaddress.IPv4Address("10.0.0.1"))

    def test_ipv4_numeric_order(self):
        result = sort_addresses(["10.0.0.10", "10.0.0.2", "10.0.0.1"])
        addrs = [int(r) for r in result]
        self.assertEqual(addrs, sorted(addrs))

    def test_ipv6_numeric_order(self):
        result = sort_addresses(["2001:db8::a", "2001:db8::1", "2001:db8::9"])
        addrs = [int(r) for r in result]
        self.assertEqual(addrs, sorted(addrs))

    def test_ipv4_before_ipv6(self):
        result = sort_addresses(["2001:db8::1", "10.0.0.1"])
        self.assertEqual(result[0], ipaddress.IPv4Address("10.0.0.1"))
        self.assertEqual(result[1], ipaddress.IPv6Address("2001:db8::1"))

    def test_network_sorts_by_start(self):
        result = sort_addresses(["10.0.1.0/24", "10.0.0.0/24", "10.0.2.0/24"])
        starts = [int(r.network_address) for r in result]
        self.assertEqual(starts, sorted(starts))

    def test_host_before_containing_network(self):
        # 10.0.0.0 (the host) should sort before 10.0.0.0/24 (the network)
        # because a /32 has a smaller prefix value than /24 in our key.
        result = sort_addresses(["10.0.0.0/24", "10.0.0.0"])
        self.assertEqual(result[0], ipaddress.IPv4Address("10.0.0.0"))
        self.assertEqual(result[1], ipaddress.IPv4Network("10.0.0.0/24"))

    def test_narrower_network_before_wider_same_start(self):
        result = sort_addresses(["10.0.0.0/8", "10.0.0.0/24", "10.0.0.0/16"])
        self.assertEqual(result[0].prefixlen, 24)
        self.assertEqual(result[1].prefixlen, 16)
        self.assertEqual(result[2].prefixlen, 8)

    def test_mixed_addresses_and_networks(self):
        result = sort_addresses([
            "192.168.1.0/24",
            "10.0.0.1",
            "2001:db8::/32",
            "10.0.0.0/24",
            "192.168.0.5",
        ])
        # IPv4 addresses and networks first, ordered numerically, then IPv6.
        self.assertEqual(result[0], ipaddress.IPv4Address("10.0.0.1"))
        self.assertEqual(result[1], ipaddress.IPv4Network("10.0.0.0/24"))
        self.assertEqual(result[2], ipaddress.IPv4Address("192.168.0.5"))
        self.assertEqual(result[3], ipaddress.IPv4Network("192.168.1.0/24"))
        self.assertEqual(result[4], ipaddress.IPv6Network("2001:db8::/32"))

    def test_accepts_pre_parsed_objects(self):
        addr = ipaddress.IPv4Address("10.0.0.1")
        net = ipaddress.IPv4Network("10.0.0.0/24")
        result = sort_addresses([net, addr])
        self.assertEqual(result[0], addr)
        self.assertEqual(result[1], net)

    def test_ipv6_normalization(self):
        # Compressed and expanded forms should parse to equal objects.
        result = sort_addresses(["2001:0db8:0000:0000:0000:0000:0000:0001",
                                  "2001:db8::1"])
        self.assertEqual(result[0], result[1])

    def test_invalid_input_raises(self):
        with self.assertRaises(ValueError):
            sort_addresses(["not-an-ip"])

    def test_network_with_host_bits_set(self):
        # strict=False in our parser allows this; it should be normalized.
        result = sort_addresses(["10.0.0.1/24"])
        self.assertEqual(result[0], ipaddress.IPv4Network("10.0.0.0/24"))

    def test_whitespace_stripped(self):
        result = sort_addresses(["  10.0.0.1  "])
        self.assertEqual(result[0], ipaddress.IPv4Address("10.0.0.1"))


if __name__ == "__main__":
    unittest.main()
