import os
import json

def folder_to_dict(path):
    """Recursively create a dictionary representing folder structure."""
    folder_dict = {"name": os.path.basename(path), "type": "folder", "children": []}
    try:
        for item in os.listdir(path):
            item_path = os.path.join(path, item)
            if os.path.isdir(item_path):
                folder_dict["children"].append(folder_to_dict(item_path))
            else:
                folder_dict["children"].append({"name": item, "type": "file"})
    except PermissionError:
        pass  # Skip folders/files you cannot access
    return folder_dict

# ----- SET FOLDER TO SCAN -----
root_path = r"C:\Programs\NX_c"

if not os.path.exists(root_path):
    print("The path does not exist. Please check and try again.")
    exit()

# ----- CREATE FOLDER STRUCTURE -----
folder_structure = folder_to_dict(root_path)

# ----- SAVE JSON IN SAME FOLDER -----
json_path = os.path.join(root_path, "folder_structure.json")
with open(json_path, "w") as f:
    json.dump(folder_structure, f, indent=4)

print(f"Folder structure saved to: {json_path}")
