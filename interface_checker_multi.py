#!/usr/bin/env python3
"""
Interface Checker - Multi-Device Runner
========================================
Connects to multiple network devices from a YAML inventory file and runs
the interface checker in parallel using threading.

Author: NetworkThinkTank Labs
Blog: https://networkthinktank.blog
GitHub: https://github.com/NetworkThinkTank-Labs/interface-checker
"""

import yaml
import sys
import os
import argparse
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from interface_checker import connect_to_device, check_interfaces, generate_text_report, save_report


def load_inventory(filepath):
    """Load device inventory from YAML file."""
    try:
        with open(filepath, "r") as f:
            data = yaml.safe_load(f)
        devices = data.get("devices", [])
        print(f"  [+] Loaded {len(devices)} device(s) from {filepath}")
        return devices
    except FileNotFoundError:
        print(f"  [!] ERROR: Inventory file not found: {filepath}")
        sys.exit(1)
    except yaml.YAMLError as e:
        print(f"  [!] ERROR: Invalid YAML in {filepath}: {e}")
        sys.exit(1)


def check_device(device_params, errors_only=False, down_only=False):
    """Check interfaces on a single device (thread-safe)."""
    connection = connect_to_device(device_params)
    if connection is None:
        return None

    try:
        results = check_interfaces(connection, errors_only, down_only)
        return results
    except Exception as e:
        print(f"  [!] Error on {device_params['host']}: {e}")
        return None
    finally:
        connection.disconnect()


def main():
    parser = argparse.ArgumentParser(
        description="Interface Checker - Multi-Device Runner"
    )
    parser.add_argument(
        "-i", "--inventory",
        type=str,
        default="inventory.yml",
        help="Path to YAML inventory file"
    )
    parser.add_argument(
        "-o", "--output",
        type=str,
        default="output",
        help="Output directory for reports"
    )
    parser.add_argument(
        "-t", "--threads",
        type=int,
        default=5,
        help="Number of concurrent threads (default: 5)"
    )
    parser.add_argument(
        "--errors-only",
        action="store_true",
        help="Show only interfaces with errors"
    )
    parser.add_argument(
        "--down-only",
        action="store_true",
        help="Show only interfaces that are down"
    )
    args = parser.parse_args()

    print("\n" + "=" * 60)
    print("  Network Interface Checker - Multi-Device Mode")
    print("  NetworkThinkTank Labs")
    print("=" * 60 + "\n")

    devices = load_inventory(args.inventory)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    os.makedirs(args.output, exist_ok=True)

    all_results = []

    with ThreadPoolExecutor(max_workers=args.threads) as executor:
        futures = {
            executor.submit(check_device, dev, args.errors_only, args.down_only): dev
            for dev in devices
        }

        for future in as_completed(futures):
            device = futures[future]
            try:
                result = future.result()
                if result:
                    all_results.append(result)
                    report = generate_text_report(result)
                    print(report)
                    filepath = f"{args.output}/{result['hostname']}_interfaces_{timestamp}.txt"
                    save_report(report, filepath)
            except Exception as e:
                print(f"  [!] Error processing {device['host']}: {e}")

    # Generate combined summary
    print("\n" + "=" * 60)
    print("  COMBINED SUMMARY")
    print("=" * 60)

    total_interfaces = 0
    total_errors = 0
    total_down = 0

    for result in all_results:
        hostname = result["hostname"]
        intf_count = len(result["interfaces"])
        err_count = sum(1 for i in result["interfaces"] if i["health"] == "WARNING")
        down_count = sum(1 for i in result["interfaces"] if i["health"] == "DOWN")

        total_interfaces += intf_count
        total_errors += err_count
        total_down += down_count

        print(f"  {hostname}: {intf_count} interfaces | {err_count} errors | {down_count} down")

    print(f"\n  TOTAL: {len(all_results)} devices | {total_interfaces} interfaces | {total_errors} errors | {total_down} down")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()

