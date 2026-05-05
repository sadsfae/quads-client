"""Argument parsing utilities for QUADS Client"""
import os


def parse_host_list_file(file_path):
    """
    Parse a host list file and return list of hostnames

    Args:
        file_path: Path to file containing hostnames (one per line)

    Returns:
        List of hostnames

    Raises:
        ValueError: If file cannot be read or is empty
    """
    expanded_path = os.path.expanduser(file_path)
    if not os.path.exists(expanded_path):
        raise ValueError(f"Host list file not found: {file_path}")

    with open(expanded_path, "r") as f:
        hosts = [line.strip() for line in f if line.strip() and not line.startswith("#")]

    if not hosts:
        raise ValueError(f"Host list file is empty: {file_path}")

    return hosts


def parse_schedule_ssm_args(args):
    """
    Parse SSM schedule command arguments

    Syntax: schedule <count|hosts|host-list path> description <desc> [OPTIONS]

    Args:
        args: Command arguments string

    Returns:
        dict with keys: count, host_list, description, wipe, vlan, qinq, model, ram

    Raises:
        ValueError: If arguments are invalid
    """
    parts = args.strip().split()
    if len(parts) < 3:
        raise ValueError("Usage: schedule <count|hosts|host-list path> description <desc> [options]")

    result = {
        "count": None,
        "host_list": None,
        "description": None,
        "wipe": True,  # Default: wipe enabled
        "vlan": None,
        "qinq": 0,
        "model": None,
        "ram": None,
    }

    # Parse first positional argument (count/hosts/host-list)
    first_arg = parts[0]
    if first_arg.isdigit():
        # Count mode
        result["count"] = int(first_arg)
    elif first_arg == "host-list":
        # Host-list mode
        if len(parts) < 2:
            raise ValueError("host-list requires a file path")
        result["host_list"] = parse_host_list_file(parts[1])
        parts = parts[1:]  # Consume the file path
    elif "," in first_arg:
        # Comma-separated hosts
        result["host_list"] = [h.strip() for h in first_arg.split(",") if h.strip()]
    else:
        # Single host
        result["host_list"] = [first_arg]

    # Parse remaining arguments
    i = 1
    while i < len(parts):
        if parts[i] == "description" and i + 1 < len(parts):
            # Collect description until next keyword
            desc_parts = []
            i += 1
            while i < len(parts) and parts[i] not in ["nowipe", "vlan", "qinq", "model", "ram"]:
                desc_parts.append(parts[i])
                i += 1
            result["description"] = " ".join(desc_parts)
        elif parts[i] == "nowipe":
            result["wipe"] = False
            i += 1
        elif parts[i] == "vlan" and i + 1 < len(parts):
            result["vlan"] = int(parts[i + 1])
            i += 2
        elif parts[i] == "qinq" and i + 1 < len(parts):
            result["qinq"] = int(parts[i + 1])
            i += 2
        elif parts[i] == "model" and i + 1 < len(parts):
            result["model"] = parts[i + 1]
            i += 2
        elif parts[i] == "ram" and i + 1 < len(parts):
            result["ram"] = int(parts[i + 1])
            i += 2
        else:
            i += 1

    if not result["description"]:
        raise ValueError("description is required")

    return result


def parse_schedule_admin_args(args):
    """
    Parse admin schedule command arguments

    Syntax: schedule <cloud> <hosts|host-list path> <start> <end>

    Args:
        args: Command arguments string

    Returns:
        dict with keys: cloud, host_list, start, end

    Raises:
        ValueError: If arguments are invalid
    """
    parts = args.strip().split()
    if len(parts) < 4:
        raise ValueError("Usage: schedule <cloud> <hosts|host-list path> <start> <end>")

    result = {
        "cloud": parts[0],
        "host_list": None,
        "start": parts[-2],  # Second to last
        "end": parts[-1],  # Last
    }

    # Parse hosts argument (between cloud and dates)
    if parts[1] == "host-list":
        if len(parts) < 5:
            raise ValueError("host-list requires a file path")
        result["host_list"] = parse_host_list_file(parts[2])
    elif "," in parts[1]:
        # Comma-separated hosts
        result["host_list"] = [h.strip() for h in parts[1].split(",") if h.strip()]
    else:
        # Single host
        result["host_list"] = [parts[1]]

    return result


def parse_extend_args(args):
    """
    Parse extend command arguments

    Syntax: extend <cloud|hostname> weeks <N>
            extend <cloud|hostname> date <YYYY-MM-DD HH:MM>

    Args:
        args: Command arguments string

    Returns:
        dict with keys: target, mode, weeks, date

    Raises:
        ValueError: If arguments are invalid
    """
    parts = args.strip().split()
    if len(parts) < 3:
        raise ValueError("Usage: extend <cloud|hostname> weeks <N> OR extend <cloud|hostname> date <YYYY-MM-DD HH:MM>")

    result = {
        "target": parts[0],
        "mode": parts[1],
        "weeks": None,
        "date": None,
    }

    if parts[1] == "weeks":
        try:
            result["weeks"] = int(parts[2])
        except (ValueError, IndexError):
            raise ValueError("weeks requires a number")
    elif parts[1] == "date":
        # Handle quoted date: date "2026-05-17 22:00" or date 2026-05-17 22:00
        date_str = " ".join(parts[2:]).strip('"')
        if not date_str:
            raise ValueError("date requires a value in format YYYY-MM-DD HH:MM")
        result["date"] = date_str
    else:
        raise ValueError("Second argument must be 'weeks' or 'date'")

    return result
