from dataclasses import fields
from pkg_resources import require
import pandas as pd
import sys
import logging
import loopresources as lr
from pathlib import Path
logger = logging.getLogger(__name__)
def desurvey_drillholes(collar : str, survey : str, interval_data : list, point_data : list,fields : list):
    """
    Desurvey drillholes and resample data    
    """
    collardf = pd.read_csv(collar)
    surveydf = pd.read_csv(survey)  
    dhdb = lr.DrillHoleDB(collar=collardf,survey=surveydf)
    desurvey_all = False
    if fields == 'all':
        desurvey_all = True
        fields = []
    if interval_data and len(interval_data) > 0:
        for interval_data_file in interval_data:

            filename = Path(interval_data_file).stem
            dhdb.add_table(name=filename,table=pd.read_csv(interval_data_file))
            if desurvey_all:
                fields += [c for c in dhdb.tables['interval'][filename].columns if c not in lr.DhConfig.fields]
    if point_data and len(point_data) > 0:
        for point_data_file in point_data:
            filename = Path(point_data_file).stem
            dhdb.add_table(name=filename,table=pd.read_csv(point_data_file))
            if desurvey_all:
                fields += [c for c in dhdb.tables['point'][filename].columns if c not in lr.DhConfig.fields]
    results = dhdb.resample_table(fields)
    if args.output:
        extension = Path(args.output).suffix
        if extension == '.geoh5':
            lr.add_points_to_geoh5(filename=args.output,points=results,group='loop',fields=fields)

    results.to_csv(args.output,index=False)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Desurvey drillholes and resample data')
    parser.add_argument('mode', type=str, help='mode: desurvey',default='desurvey')

    parser.add_argument('-c','--collar', type=str, help='collar file')
    parser.add_argument('-s','--survey', type=str, help='survey file')
    parser.add_argument('-i','--interval_data', type=str, help='interval data file',nargs='+')
    parser.add_argument('-p','--point_data', type=str, help='point data file',nargs='+')
    parser.add_argument('-o','--output', type=str, help='output file')
    parser.add_argument('-v','--verbose', action='store_true', help='verbose')
    parser.add_argument('-cc','--config', type=str, help='config file')
    parser.add_argument('-f','--fields', type=str, help='fields to desurveying',default='all')
    args = parser.parse_args()
    if args.config:
        lr.DhConfig.from_file(args.config)
    if 'desurvey' in args.mode:
        if len(args.collar) == 0:
            logger.error("No collar file provided")
            sys.exit(1)
        if len(args.survey) == 0:
            logger.error("No survey file provided")
            sys.exit(1)
        
        
        desurvey_drillholes(args.collar,args.survey,args.interval_data,args.point_data,fields=args.fields)

    