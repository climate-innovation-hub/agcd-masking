"""Command line program for calculating AGCD observation coverage.

AGCD precipitation weight files assign the following values
at each grid point and time step:
  0: Observations have no influence on analysed value
  1: Observations have minimal influence
  3: Observations influence the analysed value

This script calculates the fraction of days where observations influence the data.
In other words, it counts the fraction of days where the weight value is 3.
These fractions can be used to mask grid points that had little/no influence from
observations over a period of interest. 
"""

import argparse

import numpy as np
import xarray as xr
import dask.diagnostics
import cmdline_provenance as cmdprov
    

dask.diagnostics.ProgressBar().register()


def main(args):
    """Run the program."""
    ds = xr.open_mfdataset(args.infiles)
    count = (ds['weight'] > 1.0).sum('time', keep_attrs=True)
    fraction = count / len(ds['time'])
    output_ds = fraction.to_dataset(name='fraction')
    output_ds['fraction'].attrs = {'long_name': 'fraction of times influenced by observations'}
    output_ds.attrs['history'] = cmdprov.new_log()
    output_ds.to_netcdf(args.outfile)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )     
    parser.add_argument("infiles", type=str, nargs='*', help="input AGCD weights files")
    parser.add_argument("outfile", type=str, help="output file name")
    args = parser.parse_args()
    main(args)
