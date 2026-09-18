import os


def create_folder(name: str) -> str:
    """Create a new folder with the given name.

    Args:
        name: Name of the folder to create.
    """

    if not name or not name.strip():
        return "Folder name cannot be empty."

    name = name.strip()

    try:
        os.makedirs(name, exist_ok=True)
        return f"Created folder '{name}'."

    except Exception as error:
        return f"Could not create folder '{name}': {error}"


def create_file(name: str, content: str = "") -> str:
    """Create a new file with the given name and optional text content.

    Args:
        name: Name of the file to create.
        content: Text content to write into the file.
    """

    if not name or not name.strip():
        return "File name cannot be empty."

    name = name.strip()

    try:
        with open(name, "w", encoding="utf-8") as file:
            file.write(content)

        return f"Created file '{name}'."

    except Exception as error:
        return f"Could not create file '{name}': {error}"


def read_file(name: str) -> str:
    """Read and return the contents of a file.

    Args:
        name: Name of the file to read.
    """

    if not name or not name.strip():
        return "File name cannot be empty."

    name = name.strip()

    if not os.path.exists(name):
        return f"File '{name}' does not exist."

    if not os.path.isfile(name):
        return f"'{name}' is not a file."

    try:
        with open(name, "r", encoding="utf-8") as file:
            content = file.read()

        if not content:
            return f"File '{name}' is empty."

        return content

    except Exception as error:
        return f"Could not read file '{name}': {error}"


def edit_file(name: str, content: str) -> str:
    """Edit an existing file by overwriting it with new content.

    Args:
        name: Name of the file to edit.
        content: The complete new text content to write into the file.
    """

    if not name or not name.strip():
        return "File name cannot be empty."

    name = name.strip()

    if not os.path.exists(name):
        return f"File '{name}' does not exist. Use create_file instead."

    if not os.path.isfile(name):
        return f"'{name}' is not a file."

    try:
        with open(name, "w", encoding="utf-8") as file:
            file.write(content)

        return f"Successfully updated file '{name}'."

    except Exception as error:
        return f"Could not edit file '{name}': {error}"

if __name__ == "__main__":
    create_file("test.txt", "Old Content")
    print(edit_file("test.txt", "New Content"))
    print(read_file("test.txt"))