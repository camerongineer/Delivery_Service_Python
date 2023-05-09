import os

__all__ = ['PathUtils']


def _get_project_root() -> str:
    """Returns the absolute path to the root of the project."""
    current_path = os.path.abspath(__file__)
    while not os.path.exists(os.path.join(current_path, 'src')):
        current_path = os.path.dirname(current_path)
    return current_path


class PathUtils:
    @staticmethod
    def get_full_path_string(filename: str) -> str:
        return os.path.join(_get_project_root(), filename)
