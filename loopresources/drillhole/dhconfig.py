class DhConfig(object):
    """
    Configuration class for the drillhole module
    """

    holeid = "HOLEID"
    sample_to = "SAMPTO"
    sample_from = "SAMPFROM"
    x = "EAST"
    y = "NORTH"
    z = "RL"
    azimuth = "AZIMUTH"
    dip = "DIP"
    add_ninty = True
    depth = "DEPTH"
    total_depth = "DEPTH"
    debug = False
    positive_dips_down = True
    dip_is_inclination = False

    @classmethod
    def from_config(cls, config):
        """
        Create a DhConfig from a config object
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
        return cls

    @classmethod
    def from_file(cls, file):
        """
        Create a DhConfig from a json file
        """
        import json

        with open(file) as f:
            config = json.load(f)
        return cls.from_config(config)

    @classmethod
    def to_json(cls, filename=None):
        """
        Write the config to a json file
        """
        import json

        if filename:
            with open(filename, "w") as f:
                json.dump(cls.as_dict(), f)
        return json.dumps(cls.as_dict())

    @classmethod
    def as_dict(cls):
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
        }

    def __repr__(self) -> str:
        return (
            f"DhConfig(holeid={self.holeid}, sample_to={self.sample_to}, "
            f"sample_from={self.sample_from}, x={self.x}, y={self.y}, z={self.z}, "
            f"azimuth={self.azimuth}, dip={self.dip}, add_ninty={self.add_ninty}, "
            f"depth={self.depth}, total_depth={self.total_depth})"
        )

    def __str__(self) -> str:
        """Return a formatted string representation of the DhConfig."""
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
            f"Dip is Inclination: {self.dip_is_inclination}"
        )

    @classmethod
    def fields(cls):
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
