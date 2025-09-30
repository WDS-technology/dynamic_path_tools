from pathlib import Path
from .config_loader import load_config
from .path_parser import load_path, extract_commands
from .calculations import calculate_total_wait, calculate_distances, get_flight_speed, get_commands_count
from .utils import _format_time

def run_estimation(config_file: str | Path) -> dict:
    """
    Run the full estimation pipeline, including calibrated time vs battery.

    Args:
        config_file (str | Path): Path to YAML config file.

    Returns:
        dict: A dictionary containing the flight path analysis results.
    """
    config = load_config(config_file)
    path_file = config.get("path_file")
    battery_time_min = config.get("battery_time_minutes")
    landing_duration_min = config.get("landing_phase_duration_minutes", 0)

    if not path_file:
        raise ValueError("Config must include 'path_file'")
    if battery_time_min is None or battery_time_min <= 0:
        raise ValueError("Config must include positive 'battery_time_minutes'")

    path_data = load_path(path_file)
    commands = extract_commands(path_data)

    # Extract average flight speed from the path
    avg_speed = get_flight_speed(commands)
    if avg_speed <= 0:
        raise ValueError("Flight speed must be greater than 0")

    # Get calibration factors for this speed
    calibration = config.get("calibration", {}).get("speeds", {})
    factors = calibration.get(avg_speed, {"horizontal": 1.0, "vertical_up": 1.0, "vertical_down": 1.0, "wait": 1.0})

    total_wait = calculate_total_wait(commands) * factors.get("wait", 1.0)
    distances = calculate_distances(commands)

    # Apply calibration factors
    time_horizontal = distances["horizontal"] / avg_speed * factors.get("horizontal", 1.0)
    time_vertical_up = distances["vertical_up"] / avg_speed * factors.get("vertical_up", 1.0)
    time_vertical_down = distances["vertical_down"] / avg_speed * factors.get("vertical_down", 1.0)

    total_time_sec = time_horizontal + time_vertical_up + time_vertical_down + total_wait

    commands_count = get_commands_count(commands)

    command_delays = config.get("command_delays_seconds", {})
    total_command_delay_sec = sum(
        commands_count.get(cmd_type, 0) * delay
        for cmd_type, delay in command_delays.items()
    )

    total_time_sec += total_command_delay_sec
    total_time_with_landing_sec = total_time_sec + landing_duration_min * 60
    total_time_min = total_time_with_landing_sec / 60

    is_enough_battery = True if total_time_min <= battery_time_min else False

    results = {
        "path_file": path_file,
        "command_counts": commands_count,
        "average_speed": f"{avg_speed:.2f}",
        "distances_m": {
            "horizontal": f"{distances['horizontal']:.2f}",
            "vertical_up": f"{distances['vertical_up']:.2f}",
            "vertical_down": f"{distances['vertical_down']:.2f}",
        },
        "flight_duration": _format_time(total_time_with_landing_sec),
        "max_flight_duration": _format_time(battery_time_min * 60),
        "is_enough_battery": is_enough_battery,
    }

    return results
