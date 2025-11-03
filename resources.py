from dataclasses import fields
import pandas as pd
import sys
import logging
import loopresources as lr
from pathlib import Path
logger = logging.getLogger(__name__)
def desurvey_drillholes(collar : str, survey : str, interval_data : list, point_data : list, fields : list, output : str = None):
    """
    Desurvey drillholes and resample data using DrillholeDatabase
    """
    # Load collar and survey using new DrillholeDatabase
    dhdb = lr.DrillholeDatabase.from_csv(collar, survey)
    desurvey_all = False
    if fields == 'all':
        desurvey_all = True
        fields = []
    # Add interval tables
    if interval_data and len(interval_data) > 0:
        for interval_data_file in interval_data:
            filename = Path(interval_data_file).stem
            df = pd.read_csv(interval_data_file)
            dhdb.add_interval_table(name=filename, df=df)
            if desurvey_all:
                fields += [c for c in df.columns if c not in lr.DhConfig.fields()]
    # Add point tables
    if point_data and len(point_data) > 0:
        for point_data_file in point_data:
            filename = Path(point_data_file).stem
            df = pd.read_csv(point_data_file)
            dhdb.add_point_table(name=filename, df=df)
            if desurvey_all:
                fields += [c for c in df.columns if c not in lr.DhConfig.fields()]
    # For demonstration, desurvey all interval tables and concatenate
    results = []
    for table_name in dhdb.intervals:
        res = dhdb.desurvey_intervals(table_name)
        if not fields:
            results.append(res)
        else:
            results.append(res[[c for c in res.columns if c in fields]])
    if results:
        results_df = pd.concat(results, ignore_index=True)
        if output:
            extension = Path(output).suffix
            if extension == '.geoh5':
                lr.add_points_to_geoh5(filename=output, points=results_df, group='loop', fields=fields)
            results_df.to_csv(output, index=False)
        else:
            print(results_df)
    else:
        logger.warning('No results to output.')

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Desurvey drillholes and resample data')
    parser.add_argument('mode', type=str, help='mode: desurvey', default='desurvey')
    parser.add_argument('-c','--collar', type=str, help='collar file')
    parser.add_argument('-s','--survey', type=str, help='survey file')
    parser.add_argument('-i','--interval_data', type=str, help='interval data file', nargs='+')
    parser.add_argument('-p','--point_data', type=str, help='point data file', nargs='+')
    parser.add_argument('-o','--output', type=str, help='output file')
    parser.add_argument('-v','--verbose', action='store_true', help='verbose')
    parser.add_argument('-cc','--config', type=str, help='config file')
    parser.add_argument('-f','--fields', type=str, help='fields to desurveying', default='all')
    args = parser.parse_args()
    if args.config:
        lr.DhConfig.from_file(args.config)
    if 'desurvey' in args.mode:
        if not args.collar:
            logger.error("No collar file provided")
            sys.exit(1)
        if not args.survey:
            logger.error("No survey file provided")
            sys.exit(1)
        desurvey_drillholes(args.collar, args.survey, args.interval_data, args.point_data, fields=args.fields, output=args.output)

