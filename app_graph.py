from warehouse_navigation import load_warehouse_map, build_graph, shortest_path, plot_path, find_closest_node, generate_drone_path

warehouse_map = load_warehouse_map("warehouse_map.json")

G, pos_to_node = build_graph(warehouse_map)

start_node = "P17_W3"
end_node = "P15_W2"

path, file_content = shortest_path(G, start_node, end_node)
print("Calculated path:", (path, file_content))

print("Calculated path with coordinates:")
for node_id in path:
    coord = G.nodes[node_id]["pos"] 
    print(f"{node_id} -> {coord}")

plot_path(G, path, title=f"Path from {start_node} to {end_node}")

ret_val = find_closest_node(G, ( -15.0, 3.9, 2.4))


path3, file_content = shortest_path(G, start_node, end_node, return_coords=True)

generated_path = generate_drone_path(
    coordinates=path3,
    offset=(-4, 1.0, 2.2),
    wait_period=2
)

print("Generated drone path commands:")
print(generated_path)

import json
with open("drone_path.json", "w") as f:
    json.dump(generated_path, f, indent=2)

with open("the_output_yaml.yaml", "w") as f:
    f.write(file_content if file_content else "# No YAML content found")