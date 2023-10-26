import pandas as pd
import numpy as np
from typing import Optional
import tqdm
import logging
from . import DhConfig
from . import desurvey
from . import resample_interval, resample_point, desurvey_point

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
        self.required_columns = [
            DhConfig.sample_from,
            DhConfig.sample_to,
            DhConfig.holeid,
        ]
        self.holes = [
            hole
            for hole in self.collar[DhConfig.holeid].unique()
            if hole in self.survey[DhConfig.holeid].unique()
        ]
        self.columns = {}
        if (
            self.survey[DhConfig.azimuth].max() - self.survey[DhConfig.azimuth].min()
        ) > 2 * np.pi:
            logger.warn("azimuths are in degrees, converting to radians")
            self.survey[DhConfig.azimuth] = np.deg2rad(self.survey[DhConfig.azimuth])
        if (self.survey[DhConfig.dip].max() - self.survey[DhConfig.dip].min()) > np.pi:
            logger.warn("dips are in degrees, converting to radians")
            self.survey[DhConfig.dip] = np.deg2rad(self.survey[DhConfig.dip])
        # if DhConfig.add_ninty:
        #     logger.warn("adding 90 to azimuths")
        #     self.survey[DhConfig.azimuth] += np.pi/2

    @property
    def collar(self) -> pd.DataFrame:
        return self._collar

    @collar.setter
    def collar(self, collar: pd.DataFrame):
        self._collar = collar

    def add_table(self, name: str, table: pd.DataFrame, type="interval"):
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
        for col in self.required_columns:
            if col not in table.columns:
                raise Exception(f"Column {col} not in table")
        for col in [c for c in table.columns if c not in self.required_columns]:
            if col in self.columns:
                raise Exception(
                    f"Column {col} already assocaited with {self.columns[col]}. \n \
                    Rename this column and try again"
                )
            self.columns[col] = table

        self.tables[type][name] = table

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

        for h in tqdm.tqdm(holes):
            try:
                r_ = desurvey(
                    self.collar.loc[self.collar[DhConfig.holeid] == h],
                    self.survey.loc[self.survey[DhConfig.holeid] == h],
                    interval,
                )
            except Exception as e:
                print(e)
                continue
            for t in self.tables["interval"].values():
                cols = list(set(list(t.columns)) & set(columns))
                r_ = resample_point(r_, t.loc[t[DhConfig.holeid] == h], cols)
                r_[DhConfig.holeid] = h
            results.append(r_)
            for t in self.tables["point"].values():
                cols = list(set(list(t.columns)) & set(columns))

                if len(r_) > 1 and t.loc[t[DhConfig.holeid] == h].shape[0] > 0:
                    r = desurvey_point(r_, t.loc[t[DhConfig.holeid] == h], cols)
                    r[DhConfig.holeid] = h
                    results.append(r)
        if len(results) > 0:
            return pd.concat(results, ignore_index=True)
        else:
            raise Exception("No results found")

    # def desurvey(self, columns: list) -<
