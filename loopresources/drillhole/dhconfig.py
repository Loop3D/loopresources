"""Configuration and defaults for the drillhole module.

This module provides the DhConfig class which centralizes default column
names and flags used by the drillhole subpackage. The class stores
class-level defaults that can be overridden via ``from_config`` or
``from_file`` when a project-specific configuration is required.
"""


class DhConfig(object):
    """Configuration for drillhole column mappings and flags.

    The attributes are defined as class-level defaults and represent the
    column names (or behaviour flags) used across the drillhole module.

    Attributes:
        holeid (str): Column name for hole identifier. Default "HOLEID".
        sample_to (str): Column name for sample end. Default "SAMPTO".
        sample_from (str): Column name for sample start. Default "SAMPFROM".
        x (str): Column name for Easting. Default "EAST".
        y (str): Column name for Northing. Default "NORTH".
        z (str): Column name for elevation / reduced level. Default "RL".
        azimuth (str): Column name for azimuth. Default "AZIMUTH".
        dip (str): Column name for dip or inclination. Default "DIP".
        depth (str): Column name for depth along hole. Default "DEPTH".
        total_depth (str): Column name for reported total depth. Default "DEPTH".
        debug (bool): Debugging flag. Default False.
        positive_dips_down (bool): Interpret positive dip values as pointing downwards.
    """

    holeid = "HOLEID"
    sample_to = "SAMPTO"
    sample_from = "SAMPFROM"
    x = "EAST"
    y = "NORTH"
    z = "RL"
    azimuth = "AZIMUTH"
    dip = "DIP"
    depth = "DEPTH"
    total_depth = "DEPTH"
    debug = False
    positive_dips_down = True
    alpha = "ALPHA"
    beta = "BETA"
    gamma = "GAMMA"
    @classmethod
    def from_config(cls, config):
        """Create a DhConfig from a mapping-like config object.

        Args:
            config (Mapping[str, Any]): Mapping containing keys that match the
                attribute names of DhConfig (for example, 'holeid', 'x', 'y', etc.).

        Returns:
            type: The DhConfig class with attributes set from the provided config.

        Notes:
            This method updates class-level attributes so callers should be
            aware that the change is global to the DhConfig class.
        """
        cls.holeid = config["holeid"]
        cls.sample_to = config["sample_to"]
        cls.sample_from = config["sample_from"]
        cls.x = config["x"]
        cls.y = config["y"]
        cls.z = config["z"]
        cls.azimuth = config["azimuth"]
        cls.dip = config["dip"]
        cls.add_ninty = config["add_ninty"]
        cls.depth = config["depth"]
        cls.total_depth = config["total_depth"]
        cls.alpha = config.get("alpha", "ALPHA")
        cls.beta = config.get("beta", "BETA")
        return cls

    @classmethod
    def from_file(cls, file):
        """Create a DhConfig from a JSON file.

        Args:
            file (str): Path to a JSON file containing configuration keys.

        Returns:
            type: The DhConfig class with attributes set from the JSON file.
        """
        import json

        with open(file) as f:
            config = json.load(f)
        return cls.from_config(config)

    @classmethod
    def to_json(cls, filename=None):
        """Write the config to a JSON string or file and return the JSON string.

        Args:
            filename (str, optional): If provided, the JSON representation will be
                written to this file path.

        Returns:
            str: JSON string representation of the current DhConfig values.
        """
        import json

        if filename:
            with open(filename, "w") as f:
                json.dump(cls.as_dict(), f)
        return json.dumps(cls.as_dict())

    @classmethod
    def as_dict(cls):
        """Return the DhConfig as a dictionary.

        Returns:
            dict: Mapping of DhConfig attribute names to their current values.
        """
        return {
            "holeid": cls.holeid,
            "sample_to": cls.sample_to,
            "sample_from": cls.sample_from,
            "x": cls.x,
            "y": cls.y,
            "z": cls.z,
            "azimuth": cls.azimuth,
            "dip": cls.dip,
            "add_ninty": cls.add_ninty,
            "depth": cls.depth,
            "total_depth": cls.total_depth,
            "alpha": cls.alpha,
            "beta": cls.beta,
        }

    def __repr__(self) -> str:
        """Return an unambiguous string representation of the DhConfig."""
        return (
            f"DhConfig(holeid={self.holeid}, sample_to={self.sample_to}, "
            f"sample_from={self.sample_from}, x={self.x}, y={self.y}, z={self.z}, "
            f"azimuth={self.azimuth}, dip={self.dip}, add_ninty={self.add_ninty}, "
            f"depth={self.depth}, total_depth={self.total_depth})"
            f"alpha={self.alpha}, beta={self.beta})"
        )

    def __str__(self) -> str:
        """Return a human-readable formatted string representation of the DhConfig."""
        return (
            "DhConfig - Column Mapping\n"
            "==========================\n"
            f"Hole ID:         {self.holeid}\n"
            f"Sample From:     {self.sample_from}\n"
            f"Sample To:       {self.sample_to}\n"
            f"X Coordinate:    {self.x}\n"
            f"Y Coordinate:    {self.y}\n"
            f"Z Coordinate:    {self.z}\n"
            f"Azimuth:         {self.azimuth}\n"
            f"Dip:             {self.dip}\n"
            f"Depth:           {self.depth}\n"
            f"Total Depth:     {self.total_depth}\n"
            f"Add 90°:         {self.add_ninty}\n"
            f"Positive Dips Down: {self.positive_dips_down}\n"
            f"Dip is Inclination: {self.dip_is_inclination}\n"
            f"Alpha:           {self.alpha}\n"
            f"Beta:            {self.beta}\n"
        )

    @classmethod
    def fields(cls):
        """Return list of field names used by the DhConfig.

        The returned list contains the commonly required column names in the
        order typically expected by other drillhole utilities.

        Returns:
            list[str]: List of column/field names.
        """
        return [
            cls.sample_to,
            cls.sample_from,
            cls.x,
            cls.y,
            cls.z,
            cls.azimuth,
            cls.dip,
            cls.depth,
            cls.total_depth,
        ]
