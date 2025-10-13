import json
from pathlib import Path
from typing import Any, Dict, List, Union

RELEVANT_COMMANDS = {
    "SCHEDULE_TAKEOFF",
    "SCHEDULE_SET_XY_SPEED",
    "SCHEDULE_WAIT_FOR_PERIOD",
    "SCHEDULE_FLY_TO_XY",
    "SCHEDULE_FLY_TO_Z",
}

def load_path(path_file: Union[str, Path]) -> Dict[str, Any]:
    """
    Load path JSON file.

    Args:
        path_file (str | Path): Path to JSON file describing the path.
    Returns:
        dict: Parsed path data.
    """
    path = Path(path_file)
    if not path.exists():
        raise FileNotFoundError(f"Path file not found: {path_file}")

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def extract_commands(path_data: List[Dict]) -> List[Dict]:
    """
    Extract and normalize the commands relevant for flight analysis.

    Args:
        path_data (list of dict): Parsed JSON path data.
    Returns:
        list of dict: Normalized commands for calculation.
    """
    commands = []
    current_speed = None
    last_position = {"x": 0.0, "y": 0.0, "z": 0.0}

    for cmd in path_data:
        cmd_type = cmd.get("type")
        args = cmd.get("arguments", {})

        if cmd_type not in RELEVANT_COMMANDS:
            continue

        if cmd_type == "SCHEDULE_WAIT_FOR_PERIOD":
            commands.append({"type": "WAIT", "duration": float(args.get("period", 0.0))})

        elif cmd_type == "SCHEDULE_SET_XY_SPEED":
            current_speed = float(args.get("speed", current_speed or 0.0))
            commands.append({"type": "SET_SPEED", "speed": current_speed})

        elif cmd_type == "SCHEDULE_TAKEOFF":
            x, y, z = float(args.get("x", 0.0)), float(args.get("y", 0.0)), float(args.get("z", 0.0))
            speed = float(args.get("max_speed_xy", current_speed or 0.0))
            last_position.update({"x": x, "y": y, "z": z})
            commands.append({"type": "TAKEOFF", "x": x, "y": y, "z": z, "speed": speed})

        elif cmd_type == "SCHEDULE_FLY_TO_XY":
            x, y = float(args.get("x", last_position["x"])), float(args.get("y", last_position["y"]))
            commands.append({"type": "MOVE_XY", "x": x, "y": y, "z": last_position["z"], "speed": current_speed or 0.0})
            last_position.update({"x": x, "y": y})

        elif cmd_type == "SCHEDULE_FLY_TO_Z":
            z = float(args.get("z", last_position["z"]))
            commands.append({"type": "MOVE_Z", "z": z, "x": last_position["x"], "y": last_position["y"], "speed": current_speed or 0.0})
            last_position.update({"z": z})

    return commands