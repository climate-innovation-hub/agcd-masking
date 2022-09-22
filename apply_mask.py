"""Command line program for applying a mask/s to AGCD data."""

import logging
import argparse

import numpy as np
import xarray as xr
import geopandas as gp
import cmdline_provenance as cmdprov
import regionmask
import dask.diagnostics
    

def select_shapefile_regions(ds, shapes, lat_dim="lat", lon_dim="lon"):
    """Select region/s using a shapefile.

    Parameters
    ----------
    ds : xarray DataArray or Dataset
    shapes : geopandas GeoDataFrame
        Shapes/regions
    lat_dim: str, default 'lat'
        Name of the latitude dimension in ds
    lon_dim: str, default 'lon'
        Name of the longitude dimension in ds

    Returns
    -------
    ds : xarray DataArray or Dataset

    Notes
    -----
    Grid cells are selected if their centre point falls within the shape.
    
    regionmask requires the names of the horizontal spatial dimensions
    to be 'lat' and 'lon'
    """

    new_dim_names = {}
    if not lat_dim == "lat":
        new_dim_names[lat_dim] = "lat"
    if not lon_dim == "lon":
        new_dim_names[lon_dim] = "lon"
    if new_dim_names:
        ds = ds.rename_dims(new_dim_names)
    assert "lat" in ds.coords, "Latitude coordinate must be called lat"
    assert "lon" in ds.coords, "Longitude coordinate must be called lon"

    lons = ds["lon"].values
    lats = ds["lat"].values

    mask = regionmask.mask_geopandas(shapes, lons, lats)
    mask = mask.rename("region")

    mask = _nan_to_bool(mask)
    ds = ds.where(mask)
    ds = ds.dropna("lat", how="all")
    ds = ds.dropna("lon", how="all")

    return ds


def _nan_to_bool(mask):
    """Convert array of NaNs and floats to booleans.

    Parameters
    ----------
    mask : xarray DataArray
        Data array of NaN's and floats

    Returns
    -------
    mask : xarray DataArray
        Data array of True (where floats were) and False (where NaNs were) values
    """

    assert type(mask) == xr.core.dataarray.DataArray
    if mask.values.dtype != "bool":
        mask = xr.where(mask.notnull(), True, False)

    return mask


def main(args):
    """Run the program."""
    
    logging.basicConfig(level=logging.INFO)
    dask.diagnostics.ProgressBar().register()

    ds = xr.open_dataset(args.infile, chunks='auto')
    #ds = ds.chunk({'lat': -1, 'lon': -1})
    logging.info(f'Array size: {ds[args.variables[0]].shape}')
    logging.info(f'Chunk size: {ds[args.variables[0]].chunksizes}')

    if args.land_boundary:
        land_boundary = gp.read_file(args.land_boundary)
        ds = select_shapefile_regions(ds, land_boundary)  
    if args.obs_fraction_file:
        ds_frac = xr.open_dataset(args.obs_fraction_file)
        da_selection = ds_frac['fraction'] > args.fraction_threshold 
        for var in args.variables:
            ds[var] = ds[var].where(da_selection) 
    ds.attrs['history'] = cmdprov.new_log(infile_logs={args.infile: ds.attrs['history']})
    ds.to_netcdf(args.outfile)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )     
    parser.add_argument("infile", type=str, help="input AGCD file name")
    parser.add_argument("variables", type=str, nargs='*', help="variables")
    parser.add_argument("outfile", type=str, help="output file name")
    parser.add_argument(
        "--obs_fraction_file",
        type=str,
        default=None,
        help='File containing fraction of days influenced by obs (see agcd_weight_fraction.py)',
    )
    parser.add_argument(
        "--fraction_threshold",
        type=float,
        default=0.9,
        help='Obs fraction below which points are masked [default = 0.9]',
    )
    parser.add_argument(
        "--land_boundary",
        type=str,
        default=None,
        help='Shapefile for masking ocean points',
    )
    args = parser.parse_args()
    main(args)
