# Network Interface Checker Tool

> NetworkThinkTank Labs — Hands-on networking labs for engineers, by engineers. Blog: [networkthinktank.blog](https://networkthinktank.blog)

## Overview

The **Network Interface Checker** is a Python-based automation tool that connects to network devices via SSH (using Netmiko) and generates comprehensive reports on interface status, error counters, CRC errors, and overall interface health. It supports single-device and multi-device modes, multiple output formats (text, CSV, JSON), and filtering options to quickly identify problematic interfaces.

This tool is designed for **network engineers** who need to:
- Quickly audit interface health across multiple devices
- Identify interfaces with rising error counters or CRC errors
- Generate structured reports for documentation or NOC dashboards
- Automate routine interface checks as part of network monitoring

## Blog Article

📖 Read the full blog post with step-by-step walkthrough:  
**[Automating Interface Health Checks with Python and Netmiko](https://networkthinktank.blog)**

## Features

- ✅ **SSH-based connectivity** using Netmiko (supports Cisco IOS, NX-OS, Arista EOS, Juniper JunOS, and more)
- ✅ **Interface status checking** — up/down, admin down, protocol status
- ✅ **Error counter analysis** — input errors, output errors, CRC errors, collisions
- ✅ **Health classification** — HEALTHY, WARNING, or DOWN for each interface
- ✅ **Multiple output formats** — human-readable text, CSV, and JSON
- ✅ **Filtering options** — show only interfaces with errors (`--errors-only`) or down interfaces (`--down-only`)
- ✅ **Multi-device support** — scan multiple devices from a YAML inventory file
- ✅ **Concurrent execution** — multi-threaded scanning for faster results
- ✅ **Detailed error reports** — deep-dive into interfaces with problems

## Repository Structure

```
interface-checker/
├── interface_checker.py          # Main script — single device interface checker
├── interface_checker_multi.py    # Multi-device runner with threading
├── inventory.yml                 # Sample device inventory (YAML)
├── requirements.txt              # Python dependencies
├── README.md                     # This file
└── sample-output/
    ├── sample_output.txt         # Sample text report
    ├── sample_output.json        # Sample JSON report
    └── sample_output.csv         # Sample CSV report
```

## Prerequisites

| Requirement | Details |
|-------------|---------|
| **Python** | Version 3.8 or higher |
| **pip** | Python package manager |
| **Network Devices** | SSH-enabled (Cisco IOS, NX-OS, Arista EOS, Juniper, etc.) |
| **Network Access** | SSH connectivity to target devices (port 22) |
| **Credentials** | Valid SSH username/password for target devices |

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/NetworkThinkTank-Labs/interface-checker.git
cd interface-checker
```

### 2. Create a Virtual Environment (Recommended)

```bash
python3 -m venv venv
source venv/bin/activate        # Linux/macOS
# venv\Scripts\activate          # Windows
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

## Usage

### Single Device Mode

Check interfaces on a single device by specifying the host directly:

```bash
# Basic usage — interactive prompts for username/password
python interface_checker.py -H 192.168.1.1

# Specify credentials on the command line
python interface_checker.py -H 192.168.1.1 -u admin -p admin123

# Specify device type (default: cisco_ios)
python interface_checker.py -H 192.168.1.1 -u admin -p admin123 -d cisco_nxos

# Output in JSON format
python interface_checker.py -H 192.168.1.1 -u admin -p admin123 -f json

# Output in CSV format
python interface_checker.py -H 192.168.1.1 -u admin -p admin123 -f csv

# Show only interfaces with errors
python interface_checker.py -H 192.168.1.1 -u admin -p admin123 --errors-only

# Show only interfaces that are down
python interface_checker.py -H 192.168.1.1 -u admin -p admin123 --down-only
```

### Multi-Device Mode (Inventory File)

Scan multiple devices using a YAML inventory file:

```bash
# Use default inventory file (inventory.yml)
python interface_checker_multi.py

# Specify a custom inventory file
python interface_checker_multi.py -i my_devices.yml

# Use 10 concurrent threads
python interface_checker_multi.py -i inventory.yml -t 10

# Custom output directory
python interface_checker_multi.py -i inventory.yml -o reports/
```

### Inventory File Format

Create a YAML file with your device details:

```yaml
devices:
  - device_type: cisco_ios
    host: 192.168.1.1
    username: admin
    password: admin123

  - device_type: cisco_nxos
    host: 192.168.1.10
    username: admin
    password: admin123

  - device_type: arista_eos
    host: 192.168.1.20
    username: admin
    password: admin123
```

## Command-Line Options

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--host` | `-H` | Single device hostname or IP | — |
| `--username` | `-u` | SSH username | (interactive) |
| `--password` | `-p` | SSH password | (interactive) |
| `--device-type` | `-d` | Netmiko device type | `cisco_ios` |
| `--inventory` | `-i` | Path to YAML inventory file | `inventory.yml` |
| `--output` | `-o` | Output directory for reports | `output` |
| `--format` | `-f` | Output format: text, csv, json | `text` |
| `--errors-only` | — | Show only interfaces with errors | `False` |
| `--down-only` | — | Show only down interfaces | `False` |
| `--threads` | `-t` | Concurrent threads (multi-device) | `5` |

## Sample Output

### Text Report

```
====================================================================================================
  INTERFACE CHECKER REPORT
  Device: R1-CORE
  Timestamp: 2026-04-08T14:32:15.482910
====================================================================================================

  SUMMARY: 8 interfaces | 5 Healthy | 2 Warnings | 1 Down
----------------------------------------------------------------------------------------------------

Interface                 IP Address         Status     Protocol   In Errors    Out Errors   CRC        Health
----------------------------------------------------------------------------------------------------
GigabitEthernet0/0        10.0.0.1           up         up         0            0            0          HEALTHY
GigabitEthernet0/1        10.0.1.1           up         up         152          0            48         WARNING
GigabitEthernet0/2        10.0.2.1           up         up         0            0            0          HEALTHY
GigabitEthernet0/3        unassigned         admin down down       0            0            0          DOWN
Serial0/0/0               172.16.0.1         up         up         0            37           0          WARNING
Serial0/0/1               172.16.1.1         up         up         0            0            0          HEALTHY
Loopback0                 1.1.1.1            up         up         0            0            0          HEALTHY
Loopback1                 10.255.255.1       up         up         0            0            0          HEALTHY
```

### Health Classification

| Health Status | Meaning |
|---------------|---------|
| **HEALTHY** | Interface is up with zero errors |
| **WARNING** | Interface is up but has input/output/CRC errors |
| **DOWN** | Interface is administratively down or protocol is down |

## Supported Device Types

| Platform | Netmiko Device Type |
|----------|-------------------|
| Cisco IOS/IOS-XE | `cisco_ios` |
| Cisco NX-OS | `cisco_nxos` |
| Cisco IOS-XR | `cisco_xr` |
| Cisco ASA | `cisco_asa` |
| Arista EOS | `arista_eos` |
| Juniper JunOS | `juniper_junos` |
| Aruba/HP | `hp_procurve` |

## Troubleshooting

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| Connection timeout | Device unreachable or SSH not enabled | Verify SSH connectivity with `ssh user@host` |
| Authentication failed | Wrong username/password | Double-check credentials; verify local/TACACS auth |
| TextFSM parsing errors | Unsupported command output format | Script falls back to raw parsing automatically |
| Permission denied | User lacks privilege level | Ensure user has `show` command access (priv level 1+) |
| Empty output | No interfaces matched filters | Try without `--errors-only` or `--down-only` flags |

## References

- [Netmiko Documentation](https://github.com/ktbyers/netmiko)
- [NTC Templates (TextFSM)](https://github.com/networktocode/ntc-templates)
- [Network ThinkTank Blog](https://networkthinktank.blog)
- [Python argparse Documentation](https://docs.python.org/3/library/argparse.html)

## License

This project is provided as-is for educational purposes. Feel free to modify and use in your own network environments.

---

**NetworkThinkTank Labs** — Building hands-on networking labs for engineers, by engineers.  
🌐 [networkthinktank.blog](https://networkthinktank.blog) | 🐙 [GitHub](https://github.com/NetworkThinkTank-Labs)

