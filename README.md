# Dynamic Path Tools

This library provides tools for estimating drone flight times and navigating within a warehouse environment.

## Installation

1.  Clone the repository:
    ```bash
    git clone <repository-url>
    cd drone_flight_estimator
    ```

2.  Install the required Python packages:
    ```bash
    pip install -r requirements.txt
    ```

## Core Functionalities

### Flight Time Estimation

To estimate the flight time of a drone based on a series of commands, you can use the `run_estimation` function.

**Function:** `run_estimation(config_path)`

*   `config_path`: Path to a YAML configuration file.

**Configuration File (`config.yaml`):

The configuration file defines the parameters for the flight estimation.

```yaml
path_file: "/path/to/your/commands.json"
battery_time_minutes: 15
landing_phase_duration_minutes: 0

command_delays_seconds:
  WAIT: 0
  TAKEOFF: 0.5
  MOVE_XY: 2.5
  MOVE_Z: 2.6
  SET_SPEED: 0

calibration:
  speeds:
    0.5:
      horizontal: 1.0
      vertical_up: 1.0
      vertical_down: 1.0
      wait: 1.0
    1.0:
      horizontal: 1.0
      vertical_up: 1.0
      vertical_down: 1.0
      wait: 1.0
    1.5:
      horizontal: 1.0
      vertical_up: 1.0
      vertical_down: 1.0
      wait: 1.0
```

**Example Usage:**

```python
from pathlib import Path
from preflight_dynamic_path import run_estimation
import json

config_path = Path("examples/config.yaml")
results = run_estimation(config_path)

print(json.dumps(results, indent=4))
```

### Database Integration

You can also retrieve shelf positions from an Aurora or DynamoDB database.

**Functions:**

*   `aurora_get_shelf_position(shelf_id)`
*   `dynamodb_get_shelf_position(shelf_id)`

**Example Usage:**

```python
from preflight_dynamic_path import aurora_get_shelf_position, dynamodb_get_shelf_position

shelf_id = "1307101"

aurora_pos = aurora_get_shelf_position(shelf_id)
dynamodb_pos = dynamodb_get_shelf_position(shelf_id)

print(f"AuroraDB shelf {shelf_id}: {aurora_pos}")
print(f"DynamoDB shelf {shelf_id}: {dynamodb_pos}")
```

### Warehouse Navigation

This functionality allows you to build a graph of your warehouse and find the shortest path between two points.

#### Generating the Warehouse Map

The `warehouse_map_generator.py` script is used to create the `warehouse_map.json` file, which defines the layout of the warehouse. This file is then used by the graph builder.

**Script:** `warehouse_navigation/warehouse_map_generator.py`

**Example Usage:**

```bash
python warehouse_navigation/warehouse_map_generator.py
```

This will generate a `warehouse_map.json` file in the root directory.

**Warehouse Structure Explanation:**

The warehouse is composed of multiple **passages**, each containing several **navigation points**. These navigation points are defined by their `position_x`, `position_y`, and `position_z` coordinates, along with an `order` within their respective passage.

A key concept is the **intersection waypoint**. Each passage has one navigation point designated as an intersection. These intersection waypoints are crucial for connecting adjacent passages. Specifically, an intersection waypoint in one passage is connected to the corresponding intersection waypoint in the adjacent passage, allowing for seamless navigation between passages.

Within each passage, navigation points are interconnected based on their `order`. For example, a point with `order` 3 is connected to a point with `order` 4, and vice-versa. This bidirectional connection applies to all adjacent points within a passage, ensuring that the drone can move freely along the passage.

This structured approach, combining intra-passage connections based on `order` and inter-passage connections via intersection waypoints, forms the complete navigable graph of the warehouse. To create new warehouse mappings, you can modify the `INTERSECTION_X_VALUES` and `WAYPOINTS_YZ` lists in `warehouse_navigation/warehouse_map_generator.py` to define the desired layout and connections.

#### Building the Graph and Finding Paths

**Functions:**

*   `load_warehouse_map(file_path)`: Loads the warehouse map from a JSON file.
*   `build_graph(warehouse_map)`: Builds a graph from the warehouse map.
*   `shortest_path(graph, start_node, end_node)`: Finds the shortest path between two nodes in the graph.
*   `plot_path(graph, path, title)`: Plots the given path on the graph.

**Example Usage:**

```python
from warehouse_navigation import load_warehouse_map, build_graph, shortest_path, plot_path

# Load warehouse map
warehouse_map = load_warehouse_map("warehouse_map.json")

# Build the graph
G = build_graph(warehouse_map)

# Define start and end nodes
start_node = "P1_W8"
end_node = "P14_W1"

# Calculate shortest path
path = shortest_path(G, start_node, end_node)
print("Calculated path:", path)

# Plot the path
plot_path(G, path, title=f"Path from {start_node} to {end_node}")
```
