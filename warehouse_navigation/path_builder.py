from typing import List, Tuple, Dict

def generate_drone_path(
    coordinates: List[Tuple[float, float, float]],
    offset: Tuple[float, float, float] = (0.0, 0.0, 0.0),
    wait_period: int = 2,
) -> List[Dict]:
    """
    Convert a list of 3D coordinates into structured drone schedule commands.
    Only add Z commands when altitude changes.
    Starts from the origin (0,0,0) as the first waypoint.

    Args:
        coordinates: List of (x, y, z) coordinates in warehouse system.
        offset: (x, y, z) the starting point in the warehouse
        wait_period: default wait time after movements (seconds).

    Returns:
        List of dicts with drone commands.
    """
    flight_path = []

    if not coordinates:
        return flight_path

    # Apply offset & Y-axis inversion
    adjusted_coords = [
        (round(x - offset[0], 2), round(-(y - offset[1]), 2), round(z - offset[2], 2)) for x, y, z in coordinates
    ]

    print(adjusted_coords)

    # Start from origin
    prev_x, prev_y, prev_z = 0.0, 0.0, 0.0

    # Initial takeoff to the altitude of the first waypoint
    first_x, first_y, first_z = adjusted_coords[0]
    flight_path.append({
        "type": "SCHEDULE_TAKEOFF",
        "arguments": {"z": first_z}
    })
    flight_path.append({
        "type": "SCHEDULE_WAIT_FOR_PERIOD",
        "arguments": {"period": wait_period}
    })
    prev_z = first_z  # Update previous Z after takeoff
    prev_x, prev_y = first_x, first_y  # Move to the first waypoint
    flight_path.append({
        "type": "SCHEDULE_FLY_TO_XY",
        "arguments": {"x": first_x, "y": first_y}
    })
    flight_path.append({
        "type": "SCHEDULE_WAIT_FOR_PERIOD",
        "arguments": {"period": wait_period}
    })

    # Process remaining waypoints
    for curr_x, curr_y, curr_z in adjusted_coords[1:]:
        dx = curr_x - prev_x
        dy = curr_y - prev_y

        # XY movement (relative)
        if dx != 0 or dy != 0:
            flight_path.append({
                "type": "SCHEDULE_FLY_TO_XY",
                "arguments": {"x": curr_x, "y": curr_y}
            })
            flight_path.append({
                "type": "SCHEDULE_WAIT_FOR_PERIOD",
                "arguments": {"period": wait_period}
            })

        if curr_z != prev_z:
            flight_path.append({
                "type": "SCHEDULE_FLY_TO_Z",
                "arguments": {"z": curr_z}
            })
            flight_path.append({
                "type": "SCHEDULE_WAIT_FOR_PERIOD",
                "arguments": {"period": wait_period}
            })

        prev_x, prev_y, prev_z = curr_x, curr_y, curr_z

    return flight_path


