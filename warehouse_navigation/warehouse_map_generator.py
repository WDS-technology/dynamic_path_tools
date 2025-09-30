import json
from typing import List, Tuple, Dict

def generate_passages(
    x_values: List[float],
    yz_values: List[Tuple[float, float]]
) -> List[Dict]:
    """
    Generate a list of passage dictionaries for the warehouse map.

    Args:
        x_values: List of X coordinates for intersections.
        yz_values: List of Y,Z tuples for waypoints.

    Returns:
        List of passages as dictionaries.
    """
    passages = []
    for idx, x in enumerate(x_values, start=1):
        for order, (y, z) in enumerate(yz_values, start=1):
            passages.append({
                "passage_id": str(idx),
                "order": order,
                "position_x": x,
                "position_y": y,
                "position_z": z,
                "is_intersection": order == 5,
                "is_entrance": order in (4, 6)
            })
    return passages


def generate_warehouse_map(x_values: List[float], yz_values: List[Tuple[float, float]]) -> Dict:
    """
    Generate the complete warehouse map structure.
    """
    passages = generate_passages(x_values, yz_values)
    return {"passages": passages}


def save_warehouse_map(filename: str, warehouse_map: Dict):
    """
    Save the warehouse map to a JSON file.
    """
    with open(filename, "w") as f:
        json.dump(warehouse_map, f, indent=2)
    print(f"JSON has been saved to '{filename}'.")


if __name__ == "__main__":
    INTERSECTION_X_VALUES: List[float] = [
        -4, -9.73, -15.46, -21.19, -26.92, -32.65, -38.38, -44.11, -49.84,
        -55.57, -61.3, -67.03, -72.76, -78.49, -84.22, -89.95, -95.68,
        -101.41, -107.14, -112.87
    ]

    WAYPOINTS_YZ: List[Tuple[float, float]] = [
        (3.9, 2.4), (8.9, 2.4), (13.9, 2.4), (18.9, 2.4), (20.9, 2.4),
        (22.9, 2.4), (27.9, 2.4), (32.9, 2.4), (37.9, 2.4), (42.9, 2.4),
        (47.9, 2.4), (52.9, 2.4), (57.9, 2.4), (62.9, 2.4)
    ]

    warehouse_map_data = generate_warehouse_map(INTERSECTION_X_VALUES, WAYPOINTS_YZ)
    save_warehouse_map("warehouse_map.json", warehouse_map_data)
