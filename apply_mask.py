"""Command line program for applying a mask/s to AGCD data."""

import logging
import argparse
import math

import geopandas as gp
import xarray as xr
from clisops.core.subset import subset_shape
import cmdline_provenance as cmdprov
import regionmask
import numpy as np
import dask.diagnostics


def subset_shape_by_overlap_fraction(ds, shape, fraction, trim_edges=True):
    """Subset a shape according to grid cell overlap fraction"""
    
    assert fraction > 0
    assert fraction <= 1.0
    mask = fraction_overlap_mask(shape, ds['lon'].values, ds['lat'].values, fraction)
    
    ds = ds.where(mask)
    if trim_edges:
        ds_trimmed = ds.dropna("lat", how="all")
        ds_trimmed = ds_trimmed.dropna("lon", how="all")
        min_lat = ds_trimmed['lat'].values.min()
        max_lat = ds_trimmed['lat'].values.max()
        min_lon = ds_trimmed['lon'].values.min()
        max_lon = ds_trimmed['lon'].values.max()
        ds = ds.sel({'lat': slice(min_lat, max_lat), 'lon': slice(min_lon, max_lon)})    

    return ds


def fraction_overlap_mask(shapes_gp, lons, lats, min_overlap):
    """Create a 3D boolean array for grid cells over the shape overlap threshold.
    
    Parameters
    ----------
    shapes_gp : geopandas GeoDataFrame
        Shapes/regions
    lons : numpy ndarray
        Grid longitude values
    lats : numpy ndarray
        Grid latitude values
    threshold : float
        Minimum fractional overlap

    Returns
    -------
    mask_3D : xarray DataArray
        Three dimensional (i.e. region/lat/lon) boolean array
    """

    assert min_overlap > 0.0, "Minimum overlap must be fractional value > 0"
    assert min_overlap <= 1.0, "Minimum overlap must be fractional value <= 1.0"
    _check_regular_grid(lons)
    _check_regular_grid(lats)

    shapes_rm = regionmask.from_geopandas(shapes_gp)
    fraction = overlap_fraction(shapes_rm, lons, lats)
    fraction = _squeeze_and_drop_region(fraction)
    mask_3D = fraction > min_overlap

    return mask_3D


def overlap_fraction(shapes_rm, lons, lats):
    """Calculate the fraction of overlap of regions with lat/lon grid cells.
    
    Parameters
    ----------
    shapes_rm : regionmask.Regions
        Shapes/regions
    lons : numpy ndarray
        Grid longitude values
    lats : numpy ndarray
        Grid latitude values

    Returns
    -------
    mask_sampled : xarray DataArray
        Three dimensional (i.e. region/lat/lon) array of overlap fractions

    Notes
    -----
    From https://github.com/regionmask/regionmask/issues/38
    Assumes an equally spaced lat/lon grid
    """

    # sample with 10 times higher resolution
    lons_sampled = _sample_coord(lons)
    lats_sampled = _sample_coord(lats)

    mask = shapes_rm.mask(lons_sampled, lats_sampled)
    isnan = np.isnan(mask.values)
    numbers = np.unique(mask.values[~isnan])
    numbers = numbers.astype(np.int)

    mask_sampled = list()
    for num in numbers:
        # coarsen the mask again
        mask_coarse = (mask == num).coarsen(lat=10, lon=10).mean()
        mask_coarse = mask_coarse.assign_coords({"lat": lats, "lon": lons})
        mask_sampled.append(mask_coarse)

    mask_sampled = xr.concat(
        mask_sampled, dim="region", compat="override", coords="minimal"
    )
    mask_sampled = mask_sampled.assign_coords(region=("region", numbers))

    return mask_sampled


def _squeeze_and_drop_region(ds):
    """Squeeze and drop region dimension if necessary."""

    ds = ds.squeeze()
    try:
        if ds["region"].size <= 1:
            ds = ds.drop("region")
    except KeyError:
        pass

    return ds


def _sample_coord(coord):
    """Sample coordinates for the fractional overlap calculation."""

    d_coord = coord[1] - coord[0]
    n_cells = len(coord)
    left = coord[0] - d_coord / 2 + d_coord / 20
    right = coord[-1] + d_coord / 2 - d_coord / 20

    return np.linspace(left, right, n_cells * 10)


def _check_regular_grid(dim_values):
    """Check that a grid (e.g. lat or lon) has uniform spacing."""

    spaces = np.diff(dim_values)
    min_spacing = np.max(spaces)
    max_spacing = np.min(spaces)
    assert math.isclose(
        min_spacing, max_spacing, rel_tol=0.01,
    ), "Grid spacing must be uniform"


def main(args):
    """Run the program."""
    
    logging.basicConfig(level=logging.INFO)
    dask.diagnostics.ProgressBar().register()

    ds = xr.open_dataset(args.infile)
    logging.info(f'Array size: {ds[args.variables[0]].shape}')
    logging.info(f'Chunk size: {ds[args.variables[0]].chunksizes}')

    if args.shapefile:
        shape = gp.read_file(args.shapefile)
        if args.shape_overlap:
            ds = subset_shape_by_overlap_fraction(ds, shape, args.shape_overlap)
        else:
            ds = subset_shape(ds, shape=shape)
            
    if args.obs_fraction_file:
        ds_frac = xr.open_dataset(args.obs_fraction_file)
        da_selection = ds_frac['fraction'] > args.obs_fraction_threshold 
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
        "--obs_fraction_threshold",
        type=float,
        default=0.9,
        help='Obs fraction below which points are masked [default = 0.9]',
    )
    parser.add_argument(
        "--shapefile",
        type=str,
        default=None,
        help='Shapefile for masking (e.g. Australia coastline)',
    )
    parser.add_argument(
        "--shape_overlap",
        type=float,
        default=None,
        help='Fraction grid cells must overlap shape to be included [default: include if centre in shape]',
    )
    args = parser.parse_args()
    main(args)
