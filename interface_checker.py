#!/usr/bin/env python3
"""
Interface Checker Tool
======================
A Python script that connects to network devices using Netmiko and checks
interface status, errors, counters, and CRC errors. Generates a comprehensive
report of all interfaces on the target device(s).

Author: NetworkThinkTank Labs
Blog: https://networkthinktank.blog
GitHub: https://github.com/NetworkThinkTank-Labs/interface-checker
"""

import json
import csv
import argparse
import sys
from datetime import datetime
from netmiko import ConnectHandler
from netmiko.exceptions import NetmikoTimeoutException, NetmikoAuthenticationException


def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Network Interface Checker - Check interface status, errors, and counters"
    )
    parser.add_argument(
        "-i", "--inventory",
        type=str,
        default="inventory.yml",
        help="Path to device inventory file (YAML format)"
    )
    parser.add_argument(
        "-H", "--host",
        type=str,
        help="Single device hostname or IP address"
    )
    parser.add_argument(
        "-u", "--username",
        type=str,
        help="SSH username"
    )
    parser.add_argument(
        "-p", "--password",
        type=str,
        help="SSH password"
    )
    parser.add_argument(
        "-d", "--device-type",
        type=str,
        default="cisco_ios",
        help="Netmiko device type (default: cisco_ios)"
    )
    parser.add_argument(
        "-o", "--output",
        type=str,
        default="output",
        help="Output directory for reports (default: output)"
    )
    parser.add_argument(
        "-f", "--format",
        type=str,
        choices=["json", "csv", "text"],
        default="text",
        help="Output format: json, csv, or text (default: text)"
    )
    parser.add_argument(
        "--errors-only",
        action="store_true",
        help="Only show interfaces with errors"
    )
    parser.add_argument(
        "--down-only",
        action="store_true",
        help="Only show interfaces that are down"
    )
    return parser.parse_args()


def connect_to_device(device_params):
    """Establish SSH connection to a network device."""
    try:
        print(f"  [*] Connecting to {device_params['host']}...")
        connection = ConnectHandler(**device_params)
        print(f"  [+] Successfully connected to {device_params['host']}")
        return connection
    except NetmikoTimeoutException:
        print(f"  [!] ERROR: Connection to {device_params['host']} timed out.")
        return None
    except NetmikoAuthenticationException:
        print(f"  [!] ERROR: Authentication failed for {device_params['host']}.")
        return None
    except Exception as e:
        print(f"  [!] ERROR: Could not connect to {device_params['host']}: {e}")
        return None


def get_interface_status(connection):
    """Retrieve interface status information using 'show ip interface brief'."""
    output = connection.send_command("show ip interface brief", use_textfsm=True)
    if isinstance(output, str):
        # TextFSM parsing failed, return raw output
        return parse_interface_brief_raw(output)
    return output


def get_interface_detail(connection, interface_name):
    """Retrieve detailed interface information including counters and errors."""
    output = connection.send_command(
        f"show interfaces {interface_name}", use_textfsm=True
    )
    if isinstance(output, str):
        return parse_interface_detail_raw(output, interface_name)
    if isinstance(output, list) and len(output) > 0:
        return output[0]
    return {}


def parse_interface_brief_raw(raw_output):
    """Parse raw 'show ip interface brief' output if TextFSM fails."""
    interfaces = []
    lines = raw_output.strip().split("\n")
    for line in lines[1:]:  # Skip header
        parts = line.split()
        if len(parts) >= 6:
            interfaces.append({
                "intf": parts[0],
                "ipaddr": parts[1],
                "status": parts[4],
                "proto": parts[5]
            })
    return interfaces


def parse_interface_detail_raw(raw_output, interface_name):
    """Parse raw 'show interfaces' output for error counters."""
    result = {
        "interface": interface_name,
        "input_errors": "0",
        "output_errors": "0",
        "crc": "0",
        "collisions": "0",
        "input_packets": "0",
        "output_packets": "0",
        "in_rate_bps": "0",
        "out_rate_bps": "0"
    }
    for line in raw_output.split("\n"):
        line = line.strip()
        if "input errors" in line:
            parts = line.split(",")
            for part in parts:
                if "input errors" in part:
                    result["input_errors"] = part.strip().split()[0]
                if "CRC" in part:
                    result["crc"] = part.strip().split()[0]
        if "output errors" in line:
            parts = line.split(",")
            for part in parts:
                if "output errors" in part:
                    result["output_errors"] = part.strip().split()[0]
                if "collisions" in part:
                    result["collisions"] = part.strip().split()[0]
        if "packets input" in line:
            result["input_packets"] = line.strip().split()[0]
        if "packets output" in line:
            result["output_packets"] = line.strip().split()[0]
        if "input rate" in line and "bps" in line:
            parts = line.split()
            for idx, p in enumerate(parts):
                if p == "bps":
                    result["in_rate_bps"] = parts[idx - 1]
                    break
        if "output rate" in line and "bps" in line:
            parts = line.split()
            for idx, p in enumerate(parts):
                if p == "bps":
                    result["out_rate_bps"] = parts[idx - 1]
                    break
    return result


def check_interfaces(connection, errors_only=False, down_only=False):
    """Check all interfaces on a device and return structured data."""
    hostname = connection.find_prompt().replace("#", "").replace(">", "").strip()
    print(f"  [*] Checking interfaces on {hostname}...")

    # Get interface brief status
    interfaces_brief = get_interface_status(connection)

    results = []
    for intf in interfaces_brief:
        intf_name = intf.get("intf", intf.get("interface", "Unknown"))
        status = intf.get("status", "unknown")
        protocol = intf.get("proto", intf.get("protocol", "unknown"))
        ip_addr = intf.get("ipaddr", intf.get("ip_address", "unassigned"))

        # Get detailed counters for each interface
        detail = get_interface_detail(connection, intf_name)

        interface_data = {
            "interface": intf_name,
            "ip_address": ip_addr,
            "status": status,
            "protocol": protocol,
            "input_errors": detail.get("input_errors", "0"),
            "output_errors": detail.get("output_errors", "0"),
            "crc_errors": detail.get("crc", "0"),
            "collisions": detail.get("collisions", "0"),
            "input_packets": detail.get("input_packets", "0"),
            "output_packets": detail.get("output_packets", "0"),
            "in_rate_bps": detail.get("in_rate_bps", "0"),
            "out_rate_bps": detail.get("out_rate_bps", "0"),
        }

        # Determine health status
        has_errors = (
            int(interface_data["input_errors"]) > 0 or
            int(interface_data["output_errors"]) > 0 or
            int(interface_data["crc_errors"]) > 0
        )
        is_down = status.lower() != "up"

        if has_errors:
            interface_data["health"] = "WARNING"
        elif is_down:
            interface_data["health"] = "DOWN"
        else:
            interface_data["health"] = "HEALTHY"

        # Apply filters
        if errors_only and not has_errors:
            continue
        if down_only and not is_down:
            continue

        results.append(interface_data)

    print(f"  [+] Found {len(results)} interfaces on {hostname}")
    return {"hostname": hostname, "interfaces": results, "timestamp": datetime.now().isoformat()}


def generate_text_report(device_results):
    """Generate a human-readable text report."""
    report = []
    report.append("=" * 100)
    report.append(f"  INTERFACE CHECKER REPORT")
    report.append(f"  Device: {device_results['hostname']}")
    report.append(f"  Timestamp: {device_results['timestamp']}")
    report.append("=" * 100)
    report.append("")

    # Summary
    total = len(device_results["interfaces"])
    healthy = sum(1 for i in device_results["interfaces"] if i["health"] == "HEALTHY")
    warnings = sum(1 for i in device_results["interfaces"] if i["health"] == "WARNING")
    down = sum(1 for i in device_results["interfaces"] if i["health"] == "DOWN")

    report.append(f"  SUMMARY: {total} interfaces | {healthy} Healthy | {warnings} Warnings | {down} Down")
    report.append("-" * 100)
    report.append("")

    # Header
    header = f"{'Interface':<25} {'IP Address':<18} {'Status':<10} {'Protocol':<10} {'In Errors':<12} {'Out Errors':<12} {'CRC':<10} {'Health':<10}"
    report.append(header)
    report.append("-" * 100)

    for intf in device_results["interfaces"]:
        line = (
            f"{intf['interface']:<25} "
            f"{intf['ip_address']:<18} "
            f"{intf['status']:<10} "
            f"{intf['protocol']:<10} "
            f"{intf['input_errors']:<12} "
            f"{intf['output_errors']:<12} "
            f"{intf['crc_errors']:<10} "
            f"{intf['health']:<10}"
        )
        report.append(line)

    report.append("")
    report.append("=" * 100)

    # Detailed section for interfaces with errors
    error_interfaces = [i for i in device_results["interfaces"] if i["health"] == "WARNING"]
    if error_interfaces:
        report.append("")
        report.append("  INTERFACES WITH ERRORS (Detailed)")
        report.append("-" * 100)
        for intf in error_interfaces:
            report.append(f"  Interface: {intf['interface']}")
            report.append(f"    Input Errors:  {intf['input_errors']}")
            report.append(f"    Output Errors: {intf['output_errors']}")
            report.append(f"    CRC Errors:    {intf['crc_errors']}")
            report.append(f"    Collisions:    {intf['collisions']}")
            report.append(f"    Input Rate:    {intf['in_rate_bps']} bps")
            report.append(f"    Output Rate:   {intf['out_rate_bps']} bps")
            report.append("")

    return "\n".join(report)


def generate_csv_report(device_results):
    """Generate a CSV report."""
    import io
    output = io.StringIO()
    fieldnames = [
        "interface", "ip_address", "status", "protocol",
        "input_errors", "output_errors", "crc_errors", "collisions",
        "input_packets", "output_packets", "in_rate_bps", "out_rate_bps", "health"
    ]
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    for intf in device_results["interfaces"]:
        writer.writerow(intf)
    return output.getvalue()


def generate_json_report(device_results):
    """Generate a JSON report."""
    return json.dumps(device_results, indent=2)


def save_report(content, filepath):
    """Save report content to a file."""
    import os
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w") as f:
        f.write(content)
    print(f"  [+] Report saved to {filepath}")


def load_inventory(inventory_path):
    """Load device inventory from a YAML file."""
    try:
        import yaml
        with open(inventory_path, "r") as f:
            inventory = yaml.safe_load(f)
        return inventory.get("devices", [])
    except FileNotFoundError:
        print(f"  [!] Inventory file not found: {inventory_path}")
        return []
    except Exception as e:
        print(f"  [!] Error loading inventory: {e}")
        return []


def main():
    """Main function to run the interface checker."""
    args = parse_arguments()

    print("\n" + "=" * 60)
    print("  Network Interface Checker Tool")
    print("  NetworkThinkTank Labs")
    print("=" * 60 + "\n")

    devices = []

    if args.host:
        # Single device mode
        if not args.username:
            args.username = input("  Enter SSH username: ")
        if not args.password:
            import getpass
            args.password = getpass.getpass("  Enter SSH password: ")

        devices.append({
            "device_type": args.device_type,
            "host": args.host,
            "username": args.username,
            "password": args.password,
        })
    else:
        # Inventory mode
        inventory = load_inventory(args.inventory)
        if not inventory:
            print("  [!] No devices found. Use --host or provide an inventory file.")
            sys.exit(1)
        devices = inventory

    all_results = []

    for device_params in devices:
        connection = connect_to_device(device_params)
        if connection is None:
            continue

        try:
            results = check_interfaces(
                connection,
                errors_only=args.errors_only,
                down_only=args.down_only
            )
            all_results.append(results)

            # Generate and save report
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            hostname = results["hostname"]

            if args.format == "text":
                report = generate_text_report(results)
                filepath = f"{args.output}/{hostname}_interfaces_{timestamp}.txt"
                print(report)
            elif args.format == "csv":
                report = generate_csv_report(results)
                filepath = f"{args.output}/{hostname}_interfaces_{timestamp}.csv"
            elif args.format == "json":
                report = generate_json_report(results)
                filepath = f"{args.output}/{hostname}_interfaces_{timestamp}.json"

            save_report(report, filepath)

        except Exception as e:
            print(f"  [!] Error checking interfaces on {device_params['host']}: {e}")
        finally:
            connection.disconnect()
            print(f"  [*] Disconnected from {device_params['host']}\n")

    # Summary
    print("\n" + "=" * 60)
    print(f"  Scan Complete: {len(all_results)} device(s) checked")
    print("=" * 60)


if __name__ == "__main__":
    main()
