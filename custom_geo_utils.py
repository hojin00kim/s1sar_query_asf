import datetime
import geojson
import json
import numpy as np
import os
import pyproj
import rasterio
import shapely
import shapely.wkt
import subprocess

from datetime import datetime, timedelta
from functools import partial
from osgeo import gdal
from rasterio.mask import mask
from shapely.ops import transform
from shapely.geometry import shape


def find_files(root_dir, extension, switch=False):
    """
    find files in directories with a certain extension
    
    Parameters
    root_dir: string
        path to the root directory
    extension: string
        file extension ".tif"

    Returns
        path of all files 
    """
    filepath = []
    for path, dirs, files in os.walk(root_dir):
        #print path, dirs\n",
        for fname in files:
            if fname.endswith(extension):
                filepath.append(os.path.join(path, fname))
        if switch==False:
            break
    return filepath

def read_mask_image(raster_path, mask_feature):
    """
    read image and mask (or crop) using geometry
    
    Arguments:
    raster_path : string
        path to the image 
    mask_feature : shapely geometry
        shapely geometry
        
    Returns:
    band_ma : nd_array
       numpy nd array cropped by field geometry
    band_na_transform: tuple
       geotransform that reflects field geometry 
    """
    with rasterio.Env():
        with rasterio.open(raster_path) as src:
            band = src.read()
            profile = src.profile
            band_ma, band_ma_transform = mask(src, mask_feature, nodata=0, crop=True,
                                              all_touched=False, invert=False)
    return band_ma, profile, band_ma_transform

def reproject_raster_gdalwarp(infile_path, outfile_path, s_epsg, t_epsg, resolution):
    """
    resample raster to a fine resolution (10m)
    
    Parameters:
    
        input_shp: string
            path to a shapefile
        input_raster: string
            path to a input raster file
    
    Returns: None
        output_raster: 
    """
    cmd = "gdalwarp " + \
          "-of GTiff " + \
          "-tr " + resolution + ' ' + resolution + ' ' + \
          "-s_srs EPSG:" + s_epsg + ' ' + \
          "-t_srs EPSG:" + t_epsg + ' ' + \
          infile_path + ' ' + \
          outfile_path
    subprocess.check_call(cmd, shell=True)

def get_utm_zone(latitude, longitude):
    """
    compute utm zone and weather it is in North or South given by a lat/lon coordinate

    Arguments
      longitude : float
      latitude : float

    Returns
      utm_zone, is_north : list (or list like)
      utm zone number and N or S string

    """

    utm_zone = int(1 + (longitude + 180.0) / 6.0)

    is_north = 0
    if (latitude < 0.0):
        is_north = "S";
    else:
        is_north = "N";

    return utm_zone, is_north

def convert_wkt_to_geometry(geometry_wkt):
    """ 
    Convert wkt string to a shapely.geometry.polygon.Polygon object
    
    Arguments
      geometry_wkt : wkt string

    Returns
      geom: shapely geometry object

    """
    
    geom = shapely.wkt.loads(geometry_wkt)

    return geom


def compute_centroid_from_geometry(geometry_wkt):
    """
    compute centroid of a geometry; can be polygon, point

    Arguments
      geometry : str
      geojson geometry string

    Returns
      y, x: latitude and longitude of centroid

    """

    geometry = shapely.wkt.loads(geometry_wkt)
    x = geometry.centroid.x
    y = geometry.centroid.y

    return y, x

def convert_geojson_to_wkt(boundary):
    """
    Returns wkt geometry from geojson 

    Arguments:
    ----------
    geojson : json
        geojson 

    Returns:
    -------
    geometry wkt : wkt 
    """    
    
    s = json.dumps(boundary)
    # convert to geojson.geometry.Polygon
    geo = geojson.loads(s)
    # Feed to shape() to convert to shapely.geometry.polygon.Polygon
    geom = shape(geo)
    # get a WKTrepresentation
    return geom.wkt
    
def convert_geom_latlon_to_utm_na(geometry, utmzone):
    """
    reproject geometry in wgs84 lat/lon to utm projection for nothern hemisphere
    
    Arguments
    geometry: wkt string
        wkt format geometry string
    utmzone: string or int
        2 digit utmzone
    
    Return: None 
    """
    source_crs = 'epsg:4326'
    target_crs = 'epsg:326{}'.format(utmzone)

    project = partial(
        pyproj.transform,
        pyproj.Proj(init = source_crs), # source coordinate system
        pyproj.Proj(init = target_crs)) # destination coordinate system

    utm_geom = transform(project, geometry)  # apply projection
    return utm_geom

def convert_geom_latlon_to_utm_sa(geometry, utmzone):
    """
    reproject geometry in wgs84 lat/lon to utm projection for southern hemisphere
    
    Arguments
    geometry: wkt string
        wkt format geometry string
    utmzone: string or int
        2 digit utmzone
    
    Return: None 
    """

    source_crs = 'epsg:4326'
    target_crs = 'epsg:327{}'.format(utmzone)

    project = partial(
        pyproj.transform,
        pyproj.Proj(init = source_crs), # source coordinate system
        pyproj.Proj(init = target_crs)) # destination coordinate system

    utm_geom = transform(project, geometry)  # apply projection
    return utm_geom

def convert_geom_utm_to_latlog(geometry, inputcrs):
    """
    reproject geometry in utm projection to wgs84 lat/lon to 
    
    Arguments
    geometry: wkt string
        wkt format geometry string
    inputcrs: string 
        format of 'epsg:xxxxx', for example UTM projection for zone 15 NA is epsg:32615
    
    Return: None 
    """
    source_crs = inputcrs
    target_crs = 'epsg:4326'

    project = partial(
        pyproj.transform,
        pyproj.Proj(init = source_crs), # source coordinate system
        pyproj.Proj(init = target_crs)) # destination coordinate system

    latlon_geom = transform(project, geometry)  # apply projection
    return latlon_geom

def gdal_convert_raster_to_shp(input_raster, output_shp):
    """
    convert raster file to ESRI shapefile
    
    Arguments
    input_raster: string
        path to a input raster file
    
    Return: None 
    """
    cmd = "gdal_polygonize.py " + \
          input_raster + " " + \
          output_shp
    subprocess.check_call(cmd, shell=True)
    
def read_mask_image(raster_path, mask_feature):
    """
    read image and mask (or crop) using geometry
    
    Arguments:
    raster_path : string
        path to the image 
    mask_feature : shapely geometry
        shapely geometry
        
    Returns:
    band_ma : nd_array
        numpy nd array cropped by field geometry
    profile : rasterio object 
        raster profile of the input file
    band_na_transform: tuple
       geotransform that reflects field geometry 
    """
    with rasterio.Env():
        with rasterio.open(raster_path) as src:
            band = src.read()
            profile = src.profile
            band_ma, band_ma_transform = mask(src, mask_feature, nodata=0, crop=True,
                                              all_touched=False, invert=False)
    return band_ma, profile, band_ma_transform


def get_country_state(aoi): 
    """
    Returns the reverse geocode for the input aoi. 

    Arguments:
    ----------
    aoi : shapely geometry
          polygon field geometry.

    Returns:
    -------
    rev_geocode : 
              reverse geocode for the  where the polygon geometry is from 
    """    
    
    cntr = aoi.centroid
    cntr = cntr.__geo_interface__['coordinates']
    rev_geocode = reverse_geocode_coords(cntr[::-1])
    return rev_geocode




