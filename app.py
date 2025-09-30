from pathlib import Path
import json
from preflight_dynamic_path import (
    run_estimation,
    aurora_get_shelf_position,
    dynamodb_get_shelf_position,
)


def main():
    config_path = Path("./examples/config.yaml")
    results = run_estimation(config_path)
    print("=== Flight Estimation Results ===")
    print(json.dumps(results, indent=4))

    shelf_id = "1307101"

    aurora_pos = aurora_get_shelf_position(shelf_id)
    dynamodb_pos = dynamodb_get_shelf_position(shelf_id)

    print("\n=== Shelf Positions ===")
    print(f"AuroraDB shelf {shelf_id}: {aurora_pos}")
    print(f"DynamoDB shelf {shelf_id}: {dynamodb_pos}")


if __name__ == "__main__":
    main()
