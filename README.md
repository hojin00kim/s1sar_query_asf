# SAR Query To NASA ASF Server

### With this notebook, Sentinel-1 SAR can be queried and downloaded from NASA ASF server

#### Main process includes 

1. Get S2 Tile ID that intersects field geometry
    * find_intersection_s2_tile_geom.ipynb
    * input csv file that contain field geometry
2. Query SAR through NASA ASF (Alaska Satellite Facility) 
    * query_s1_asf.ipynb
    * output file contains
        1. native granule name
        2. download url from ASF
        3. satellite flight direction
        4. image date in ISO format (yyyy-mm-ddT00:00:00.0000)

There are 3 custom function files; asf_query.py and custom_geo_utils.py
* asf_query.py - need to run query_s1_asf.ipynb
* custom_geo_utils.py - misc geospatial functions

