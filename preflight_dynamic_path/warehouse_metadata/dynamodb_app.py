import boto3

def get_shelf_position(shelf_id: str, table_name: str = "Shelves"):
    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table(table_name)

    try:
        response = table.get_item(Key={"id": shelf_id})
        
        if "Item" not in response:
            print(f"Shelf with id '{shelf_id}' not found.")
            return None
            
        item = response["Item"]

        position = item.get("position", {})
        x = position.get("x")
        y = position.get("y")
        z = position.get("z")

        return {
            "x": int(x) if x is not None else None,
            "y": int(y) if y is not None else None,
            "z": int(z) if z is not None else None,
        }

    except Exception as e:
        print(f"Error fetching shelf: {e}")
        return None


if __name__ == "__main__":
    shelf_id = input("Enter shelf id: ").strip()
    pos = get_shelf_position(shelf_id)

    if pos:
        print(f"Position of shelf {shelf_id}: {pos}")
