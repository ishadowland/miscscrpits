import ipaddress
import random

def generate_ips(ip_ranges, num_ips):
    """
    生成指定数量的唯一随机 IP 地址，来自用户指定的多个不连续的 IP 地址段。

    Args:
        ip_ranges (list): IP 地址段列表，例如：["192.168.1.0/24", "10.0.0.0/24", "172.16.0.0/28"]
        num_ips (int): 要生成的 IP 地址数量（范围 10-5000）。

    Returns:
        str: 逗号分隔的 IP 地址字符串。
    """

    if not 10 <= num_ips <= 5000:
        raise ValueError("IP 地址数量必须在 10 到 5000 之间。")

    all_ips = []
    for ip_range in ip_ranges:
        try:
            network = ipaddress.ip_network(ip_range)
            # Exclude network and broadcast addresses
            ips = [str(ip) for ip in network.hosts()]
            all_ips.extend(ips)
        except ValueError as e:
            print(f"警告: 无效的 IP 地址段 '{ip_range}': {e}")
            continue  # Skip invalid IP ranges

    if not all_ips:
        return ""  # No valid IPs to generate

    if num_ips > len(all_ips):
        print(f"警告: 请求的 IP 地址数量 ({num_ips}) 大于可用地址总数 ({len(all_ips)})。生成所有可用的唯一 IP 地址。")
        num_ips = len(all_ips)

    unique_ips = set()
    while len(unique_ips) < num_ips:
        unique_ips.add(random.choice(all_ips))

    return ",".join(unique_ips)


if __name__ == '__main__':
    ip_ranges = ["192.168.1.0/24", "10.0.0.0/24", "172.16.0.0/28"]  # 示例 IP 地址段
    num_ips = 300  # 示例 IP 地址数量

    try:
        generated_ips = generate_ips(ip_ranges, num_ips)
        print(generated_ips)
    except ValueError as e:
        print(f"错误: {e}")

    # 示例 2： 测试指定数量大于可用数量
    ip_ranges_small = ["192.168.1.0/30"] # 仅包含 192.168.1.1 和 192.168.1.2
    num_ips_large = 10
    try:
        generated_ips_large = generate_ips(ip_ranges_small, num_ips_large)
        print(generated_ips_large)
    except ValueError as e:
        print(f"错误: {e}")
