import pandas as pd
import numpy as np
import tqdm
import logging
from . import DhConfig
from . import desurvey, DrillHole
from . import resample_point, desurvey_point

logger = logging.getLogger(__name__)


class DrillHoleDB:
    def __init__(
        self,
        collar: pd.DataFrame,
        survey: pd.DataFrame,
    ):
        """A class to interface with a database of drillholes
        where the drillholes share a holeid key.

        Parameters
        ----------
        collar : pd.DataFrame
            dataframe containing the start collar of the drillhole
        survey : pd.DataFrame
            table of the survey locations
        """
        self._collar = None
        self._survey = None
        self._table = None
        self.collar = collar
        self.survey = survey
        self.tables = {"point": {}, "interval": {}}
        self.required_columns_interval = [
            DhConfig.sample_from,
            DhConfig.sample_to,
            DhConfig.holeid,
        ]
        self.required_columns_point = [DhConfig.depth, DhConfig.holeid]
        self.holes = [
            hole
            for hole in self.collar[DhConfig.holeid].unique()
            if hole in self.survey[DhConfig.holeid].unique()
        ]
        self.columns = {}
        if (self.survey[DhConfig.azimuth].max() - self.survey[DhConfig.azimuth].min()) > 2 * np.pi:
            logger.warn("azimuths are in degrees, converting to radians")
            self.survey[DhConfig.azimuth] = np.deg2rad(self.survey[DhConfig.azimuth])
        if (self.survey[DhConfig.dip].max() - self.survey[DhConfig.dip].min()) > np.pi:
            logger.warn("dips are in degrees, converting to radians")
            self.survey[DhConfig.dip] = np.deg2rad(self.survey[DhConfig.dip])

    def _check(self):
        if self.collar is None:
            raise Exception("No collar data")
        if self.survey is None:
            raise Exception("No survey data")
        if DhConfig.total_depth not in self.collar.columns:
            raise ValueError("No total depth column in collar")
        if DhConfig.holeid not in self.collar.columns:
            raise ValueError("No holeid column in collar")
        if DhConfig.holeid not in self.survey.columns:
            raise ValueError("No holeid column in survey")
        if DhConfig.depth not in self.survey.columns:
            raise ValueError("No depth column in survey")
        if DhConfig.dip not in self.survey.columns:
            raise ValueError("No dip column in survey")
        if DhConfig.azimuth not in self.survey.columns:
            raise ValueError("No azimuth column in survey")

    @property
    def collar(self) -> pd.DataFrame:
        return self._collar

    @collar.setter
    def collar(self, collar: pd.DataFrame):
        self._collar = collar

    def __getitem__(self, hole: str) -> pd.DataFrame:
        """Get the drillhole data for a specific hole

        Parameters
        ----------
        hole : str
            hole id

        Returns
        -------
        pd.DataFrame
            dataframe with the drillhole data
        """
        if hole not in self.holes:
            raise ValueError(f"Hole {hole} not in database")
        return DrillHole(
            collar=self.collar.loc[self.collar[DhConfig.holeid] == hole],
            survey=self.survey.loc[self.survey[DhConfig.holeid] == hole],
            holeid=hole,
            database=self,
        )

    def add_table(
        self,
        name: str,
        table: pd.DataFrame,
        type="interval",
        depth_col=None,
        from_col=None,
        to_col=None,
    ):
        """Add samples along the drillhole, these could be lithology
        or assay data. Need to have a sample_from and sample_to column
        and a holeid column.

        Parameters
        ----------
        name : str
            unique name to identify the table, e.g. 'assay'
        table : pd.DataFrame
            table form with required headings
        """
        if type == "interval":
            if from_col is not None:
                table = table.rename(columns={from_col: DhConfig.sample_from})
            if to_col is not None:
                table = table.rename(columns={to_col: DhConfig.sample_to})
            required_columns = self.required_columns_interval
        elif type == "point":
            if depth_col is not None:
                table = table.rename(columns={depth_col: DhConfig.depth})
            required_columns = self.required_columns_point
        else:
            raise ValueError("Type must be either 'interval' or 'point'")
        for col in required_columns:
            if col not in table.columns:
                raise Exception(f"Column {col} not in table")
        for col in [c for c in table.columns if c not in required_columns]:
            if col in self.columns:
                raise Exception(
                    f"Column {col} already assocaited with {self.columns[col]}. \n \
                    Rename this column and try again"
                )
            self.columns[col] = name

        self.tables[type][name] = table

    def desurvey_points(self, columns: list) -> pd.DataFrame:
        """Desurvey the point data in the tables along the drillholes


        Parameters
        ----------
        columns : list
            list of the columns to be desurveyed, these are searched in the table columns

        Returns
        -------
        pd.DataFrame
            resulting table with the columns desurveyed
        """
        self._check()
        results = []
        holes = []
        for c in columns:
            for t in self.tables["point"].values():
                if c in t.columns:
                    holes += t[DhConfig.holeid].unique().tolist()
        holes = list(set(holes))
        for h in tqdm.tqdm(holes):
            try:
                if self.survey.loc[self.survey[DhConfig.holeid] == h].shape[0] == 0:
                    continue
                r = desurvey(
                    self.collar.loc[self.collar[DhConfig.holeid] == h],
                    self.survey.loc[self.survey[DhConfig.holeid] == h],
                )
            except Exception as e:
                if DhConfig.debug:
                    raise e
                print(e, h)
                continue
            for t in self.tables["point"].values():
                cols = list(set(t.columns) & set(columns))
                r = desurvey_point(r, t.loc[t[DhConfig.holeid] == h], cols)
                r[DhConfig.holeid] = h
                results.append(r)
        if len(results) > 0:
            return pd.concat(results)
        else:
            raise Exception("No results found")

    def resample_table(self, columns: list, interval: float = 1.0) -> pd.DataFrame:
        """Resample the data in the tables along the drillholes at specific intervals


        Parameters
        ----------
        columns : list
            list of the columns to be resampled, these are searched in the table columns
        interval : float, optional
            step size of the interval, by default 1.0

        Returns
        -------
        pd.DataFrame
            resulting table with the columns resampled
        """
        self._check()
        results = []
        holes = []
        # find the holes which have logging related to the tables we are
        # interested in
        for c in columns:
            for t in self.tables["interval"].values():
                if c in t.columns:
                    holes += t[DhConfig.holeid].unique().tolist()
            for t in self.tables["point"].values():
                if c in t.columns:
                    holes += t[DhConfig.holeid].unique().tolist()
        holes = list(set(holes))
        # sanity check
        for h in tqdm.tqdm(holes):
            try:
                if self.survey.loc[self.survey[DhConfig.holeid] == h].shape[0] == 0:
                    continue
                r_ = desurvey(
                    self.collar.loc[self.collar[DhConfig.holeid] == h],
                    self.survey.loc[self.survey[DhConfig.holeid] == h],
                    interval,
                )
            except Exception as e:
                if DhConfig.debug:
                    raise e
                print(e, h)
                continue
            for t in self.tables["interval"].values():
                cols = list(set(t.columns) & set(columns))
                r_ = resample_point(r_, t.loc[t[DhConfig.holeid] == h], cols)
                r_[DhConfig.holeid] = h
                results.append(r_)
        if len(results) > 0:
            return pd.concat(results)
        else:
            raise Exception("No results found")
