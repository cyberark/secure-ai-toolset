import os

import toml


def main():
    """Increment the patch version number in pyproject.toml.

    This function:
    1. Reads the current version from pyproject.toml.
    2. Increments the patch version by 1.
    3. Writes the new version back to pyproject.toml.
    4. Prints the new version to the console.
    """
    file_path = os.path.join(os.path.dirname(__file__), os.pardir,
                             "pyproject.toml")
    with open(file_path) as f:
        pyproject = toml.load(f)

    version = pyproject["project"]["version"]
    major, minor, patch = map(int, version.split("."))
    patch += 1
    new_version = f"{major}.{minor}.{patch}"

    pyproject["project"]["version"] = new_version

    with open(file_path, "w") as f:
        toml.dump(pyproject, f)

    print(f"Version incremented to {new_version}")


if __name__ == "__main__":
    main()
