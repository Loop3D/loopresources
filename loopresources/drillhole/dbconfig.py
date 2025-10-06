"""Database backend configuration for DrillholeDatabase.

This module provides configuration options for choosing between
in-memory (pandas) or file-based (SQLite) storage backends.
"""


class DbConfig:
    """Configuration class for database backend selection."""

    def __init__(self, backend: str = "memory", db_path: str = None, project_name: str = None):
        """Initialize database configuration.

        Parameters
        ----------
        backend : str, optional
            Database backend type: 'memory' (default) or 'file'
        db_path : str, optional
            Path to SQLite database file (required if backend='file')
        project_name : str, optional
            Name of the project to associate with this database
        """
        if backend not in ["memory", "file"]:
            raise ValueError(f"Invalid backend '{backend}'. Must be 'memory' or 'file'")

        if backend == "file" and db_path is None:
            raise ValueError("db_path is required when backend='file'")

        self.backend = backend
        self.db_path = db_path
        self.project_name = project_name

    def __repr__(self) -> str:
        """Return repr string for DbConfig."""
        return (
            f"DbConfig(backend='{self.backend}', "
            f"db_path='{self.db_path}', "
            f"project_name='{self.project_name}')"
        )
