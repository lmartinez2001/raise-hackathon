import os
from smolagents import Tool


class FileTreeTool(Tool):
    name = "get_file_tree"
    description = (
        "Recursively scan a directory from a given root path and return "
        "its file/directory architecture as a nested dictionary, with optional depth limit."
    )
    inputs = {
        "root_path": {
            "type": "string",
            "description": "Path to the root directory to scan.",
        },
        "max_depth": {
            "type": "number",
            "description": "Maximum depth to traverse (0 = only root).",
        },
    }
    output_type = "object"

    def forward(self, root_path: str, max_depth: int) -> dict:
        """
        Args:
            root_path: Path to start scanning.
            max_depth: Maximum depth to scan (-1 = no limit, 0 = only root folder).
        Returns:
            A nested dict representing directory architecture.
        """
        if not os.path.exists(root_path):
            raise ValueError(f"Path does not exist: {root_path!r}")
        abs_root = os.path.abspath(root_path)

        def scan(path: str, current_depth: int) -> dict:
            node = {
                "name": os.path.basename(path) or path,
                "type": "directory",
                "children": [],
            }
            if max_depth >= 0 and current_depth >= max_depth:
                return node
            try:
                entries = sorted(os.listdir(path))
            except PermissionError as e:
                raise RuntimeError(f"Permission denied: {e}")
            for entry in entries:
                full = os.path.join(path, entry)
                if os.path.isdir(full):
                    node["children"].append(scan(full, current_depth + 1))
                else:
                    node["children"].append({"name": entry, "type": "file"})
            return node

        return scan(abs_root, 0)


# TEST
if __name__ == "__main__":
    get_file_tree_tool = FileTreeTool()
    root = input("Enter the root path to scan: ")
    depth = input("Enter max depth: ")
    try:
        file_tree = get_file_tree_tool.forward(root, int(depth))
        print(file_tree)
    except Exception as e:
        print(f"Error: {e}")
