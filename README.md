# AGCD masking

This directory contains command line programs for masking AGCD data.

## Software environment

The scripts in this repository depend on the
[regionmask](https://regionmask.readthedocs.io),
[clisops](https://clisops.readthedocs.io), and
[cmdline-provenance](https://cmdline-provenance.readthedocs.io) libraries
and their dependencies.

A copy of the scripts and a software environment with those libraries installed
can be accessed or created in a number of ways (see below):

### For members of the CSIRO Climate Innovation Hub...

If you're a member of the `wp00` project on NCI
(i.e. if you're part of the CSIRO Climate Innovation Hub),
the easiest way to use the scripts is to use the cloned copy at `/g/data/wp00/shared_code/agcd-masking/`.
They can be run using the Python environment at `/g/data/wp00/users/dbi599/miniconda3/envs/cih/bin/python`.

For example, to view the help information for the `apply_mask.py` script
a member of the `wp00` project could run the following at the command line:

```
/g/data/wp00/users/dbi599/miniconda3/envs/cih/bin/python /g/data/wp00/shared_code/qqscale/apply_mask.py -h
```

### For members of the Australian Climate Service...

If you're a member of the `xv83` project on NCI
(i.e. if you're part of the Australian Climate Service),
you'll need to clone this GitHub repository.

```
git clone git@github.com:climate-innovation-hub/agcd-masking.git
cd agcd-masking
```

You can then run the scripts at the command line
using the Python environment at `/g/data/xv83/dbi599/miniconda3/envs/masking`. e.g.:

```
/g/data/xv83/dbi599/miniconda3/envs/masking/bin/python apply_mask.py -h
```

### For everyone else...

If you don't have access to a Python environment with the required packages
pre-installed you'll need to create your own.
For example:

```
conda install -c conda-forge regionmask clisops cmdline_provenance 
```

You can then clone this GitHub repository and run the help option
on one of the command line programs to check that everything is working.
For example:

```
git clone git@github.com:climate-innovation-hub/agcd-masking.git
cd agcd-masking
python apply_mask.py -h
```

## Producing precipitation weights

In parts of regional Australia there are large distances between rain gauges
for which daily values are available.
This means there are grid point values in the AGCD daily gridded precipitation data
that haven't been influenced by actual precipitation observations.
For many analyses (e.g. trends, return periods) it can be a good idea to mask these grid points
because they seem to have artificial / unrealistic characteristics (e.g. variability).

To help with this masking,
the AGCD dataset includes precipitation weight files assign the following values
at each grid point and time step:  
- 0: Observations have no influence on analysed value  
- 1: Observations have minimal influence  
- 3: Observations influence the analysed value  

The `agcd_weight_fraction.py` script can be used to calculate the fraction of days at each grid point
that had good observational (i.e. rain guage) coverage.

```
python agcd_weight_fraction.py -h
```

```
usage: agcd_weight_fraction.py [-h] [infiles ...] outfile

Command line program for calculating AGCD observation coverage.

AGCD precipitation weight files assign the following values
at each grid point and time step:
  0: Observations have no influence on analysed value
  1: Observations have minimal influence
  3: Observations influence the analysed value

This script calculates the fraction of days where observations influence the data.
In other words, it counts the fraction of days where the weight value is 3.
These fractions can be used to mask grid points that had little/no influence from
observations over a period of interest. 

positional arguments:
  infiles     input AGCD weights files
  outfile     output file name

options:
  -h, --help  show this help message and exit
```

For example, 

```
python agcd_weight_fraction.py /g/data/zv2/agcd/v1/precip/weight/r005/01day/agcd_v1_precip_weight_r005_daily_19[6,7]*.nc agcd_v1_precip_weight_r005_obs-fraction_1960-1979.nc
```

The resulting file is plotted in `obs_weight_fraction.ipynb`,
which also includes other plots exploring the behaviour of grid points
that are never influenced by observations.

![obs fraction example](obs_fraction_example.png)


## Applying a mask

The `apply_mask.py` script then takes a weight fraction file and masks any grid points below a specified fraction.
It is also possible to pass the script a shapefile to mask all ocean points.
A shapefile describing the Australian land boundary can be found in the Australian Community Reference Climate Data Collection
[shapefile collection](https://github.com/aus-ref-clim-data-nci/shapefiles).

```
python apply_mask.py -h
```

```
usage: apply_mask.py [-h] --variables [VARIABLES ...] [--obs_fraction_file OBS_FRACTION_FILE]
                     [--obs_fraction_threshold OBS_FRACTION_THRESHOLD] [--shapefile SHAPEFILE] [--shape_overlap SHAPE_OVERLAP]
                     [infiles ...] outfile

Command line program for applying a mask/s to AGCD data.

positional arguments:
  infiles               input AGCD file names
  outfile               output file name

options:
  -h, --help            show this help message and exit
  --variables [VARIABLES ...]
                        variables to mask
  --obs_fraction_file OBS_FRACTION_FILE
                        File containing fraction of days influenced by obs (see agcd_weight_fraction.py)
  --obs_fraction_threshold OBS_FRACTION_THRESHOLD
                        Obs fraction below which points are masked [default = 0.9]
  --shapefile SHAPEFILE
                        Shapefile for masking (e.g. Australia coastline)
  --shape_overlap SHAPE_OVERLAP
                        Fraction grid cells must overlap shape to be included [default: include if centre in shape]

```

For example,

```
python apply_mask.py your_data.nc your_data_masked.nc --variables precip --obs_fraction_file agcd_v1_precip_weight_r005_obs-fraction_1960-1979.nc --shapefile /g/data/ia39/aus-ref-clim-data-nci/shapefiles/data/australia/australia.shp
```

By default, any grid cell whose centre point is within the shape defined by the shapefile is included.
The `--shape_overlap` option can be used to specify what fraction of a grid cell must overlap with the shape to be included,
but beware that this option is much more memory intensive.

