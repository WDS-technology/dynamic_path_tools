from typing import List, Dict, Any
from math import sqrt

def get_commands_count(commands: List[Dict]) -> Dict[str, int]:
    """
    Count occurrences of each command type in the path commands.

    Args:
        commands (list[dict]): List of command dictionaries from the path.

    Returns:
        dict: A dictionary with command types as keys and their counts as values.

    """
    counts = {}
    for cmd in commands:
        cmd_type = cmd["type"]
        counts[cmd_type] = counts.get(cmd_type, 0) + 1
    return counts


def get_flight_speed(commands: List[Dict[str, Any]]) -> float:
    """
    Extract the average XY flight speed from path commands.

    Looks for:
    - SCHEDULE_SET_XY_SPEED (explicit speed set)
    - SCHEDULE_TAKEOFF (max_speed_xy)

    Args:
        commands (list[dict]): List of command dictionaries from the path.

    Returns:
        float: The flight speed in m/s. Defaults to 1.0 if not found.
    """
    for cmd in commands:
        cmd_type = cmd.get("type")
        args = cmd.get("arguments", {})

        if cmd_type == "SCHEDULE_SET_XY_SPEED":
            speed = args.get("speed")
            if speed and speed > 0:
                return float(speed)

        elif cmd_type == "SCHEDULE_TAKEOFF":
            max_speed = args.get("max_speed_xy")
            if max_speed and max_speed > 0:
                return float(max_speed)

    # Default speed if none is set
    return 1.0

def calculate_total_wait(commands: List[Dict]) -> float:
    """
    Sum all WAIT command durations in seconds.
    """
    return sum(cmd.get("duration", 0.0) for cmd in commands if cmd["type"] == "WAIT")

def calculate_distances(commands: List[Dict]) -> Dict[str, float]:
    """
    Calculate horizontal distance and vertical up/down distances.
    """
    horizontal = 0.0
    vertical_up = 0.0
    vertical_down = 0.0
    last_pos = {"x": 0.0, "y": 0.0, "z": 0.0}

    for cmd in commands:
        if cmd["type"] in {"MOVE_XY", "MOVE_Z"} or cmd["type"] == "TAKEOFF":
            dx = cmd.get("x", last_pos["x"]) - last_pos["x"]
            dy = cmd.get("y", last_pos["y"]) - last_pos["y"]
            dz = cmd.get("z", last_pos["z"]) - last_pos["z"]

            # horizontal distance only considers XY
            horizontal += sqrt(dx**2 + dy**2)

            if dz > 0:
                vertical_up += dz
            elif dz < 0:
                vertical_down += -dz

            last_pos.update({"x": cmd.get("x", last_pos["x"]),
                             "y": cmd.get("y", last_pos["y"]),
                             "z": cmd.get("z", last_pos["z"])})

    return {"horizontal": horizontal, "vertical_up": vertical_up, "vertical_down": vertical_down, "total": horizontal + vertical_up + vertical_down}
