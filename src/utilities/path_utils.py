import os

__all__ = ['PathUtils']


def _get_project_root() -> str:
    """
    Returns the root directory of the project.

    Time Complexity: O(n)
    Space Complexity: O(1)
    """

    current_path = os.path.abspath(__file__)
    while not os.path.exists(os.path.join(current_path, 'src')):
        current_path = os.path.dirname(current_path)
    return current_path


class PathUtils:

    @staticmethod
    def get_full_file_path(filename: str) -> str:
        """
        Returns the full file path given a filename.

        Args:
            filename (str): The name of the file.

        Returns:
            str: The full file path.

        Time Complexity: O(n)
        Space Complexity: O(1)
        """

        return os.path.join(_get_project_root(), filename)
