# import datetime
import json
import os
import re
import requests
import pandas as pd
import sys
import shapely.wkt
import urllib

from datetime import datetime, timedelta

'''
This worker queries data products from https://api.daac.asf.alaska.edu 
'''

# Global constants
url = "https://api.daac.asf.alaska.edu/services/search/param?"
dtreg = re.compile(r'S1[AB].*?_(\d{4})(\d{2})(\d{2})')

def get_image_date_from_granule(granule):

    '''
    Returns the date typle (YYYY,MM,DD) give the granule of the product
    @param granule - granule of the product
    @return: (YYYY,MM,DD) tuple
    '''
    match = dtreg.search(granule)
    if match:
        return (match.group(1),match.group(2),match.group(3))
    return ("0000","00","00")

def get_file_type():
    '''
    What filetype does this download
    '''
    return "zip"


def wkt_to_url(geometry_wkt):
    """
    convert string geometry well known text format to url parse
    
    @param geometry - wkt format shapely geometry
    @return url parse converted geometry
    """
    if "POLYGON" in geometry_wkt:
        geom_geo = shapely.wkt.loads(geometry_wkt)
        geom_bounds = geom_geo.buffer(0.0001).envelope
        url_geometry = urllib.parse.quote(geom_bounds.wkt)
    else:
        url_geometry = urllib.parse.quote(geometry_wkt)

    return url_geometry
    
        
def build_query(start, end, platform, beam_mode, geometry, mapping='S1-IW_SLC'):
    '''
    Builds a query for the system
    @param start - start time in 
    @param end - end time in "NOW" format
    @param type - type in "slc" format
    @param bounds - bounds to query
    @return query for talking to the system
    '''  
    if mapping=="S1_IW_SLC":
        q=url
        q+="platform="+platform
        q+="&beamMode="+beam_mode
        q+='&processingLevel=SLC'
        q+='&intersectsWith='+geometry
        start = datetime.strptime(start, '%Y-%m-%d').isoformat()+'UTC'
        end = datetime.strptime(end, '%Y-%m-%d').isoformat()+'UTC'
        q+="&start="+start+"&end="+end
        q+="&output=json"   # csv, json
    elif mapping=="S1_GRD":
        q=url
        q+="platform="+platform
        q+="&beamMode="+beam_mode
        q+='&processingLevel=GRD_HS,GRD_HD'#,GRD_MS,GRD_MD,GRD_FS,GRD_FD'
        q+='&intersectsWith='+geometry
        start = datetime.strptime(start, '%Y-%m-%d').isoformat()+'UTC'
        end = datetime.strptime(end, '%Y-%m-%d').isoformat()+'UTC'
        q+="&start="+start+"&end="+end
        q+="&output=json"   #csv, json
    return q
        
def list_all(query):
    '''
    Lists the server for all products matching a query. 
    NOTE: this function also updates the global JSON querytime persistence file
    @param session - session to use for listing
    @param query - query to use to list products
    @return list of (granule, link, direction, beam, footprint, imageDate) tuples
    '''
    print("Listing: "+query)
    
    session = requests.session()
    response = session.get(query)
    title = None
    found = []
    print(response)
    if response.status_code != 200:
        print("Error: %s\n%s" % (response.status_code,response.text))
    #parse the granules and download links
    json_data = json.loads(response.text)
    found = []
    for item in json_data[0]:
        granule = item['granuleName']
        link = item['downloadUrl']
        direction = item['flightDirection']
        beam = item['beamMode']
        footprint = item['stringFootprint']
        imageDate = item['sceneDate']
        found.append((granule, link, direction, beam, footprint, imageDate))
    return found

def found_list_to_df(query):
    '''
    convert lists from the query to pandas dataframe. 
   
    @param found_list - list of (granule, link, direction, beam, footprint, imageDate) tuples
    @return df (granule, link, direction, beam, footprint, imageDate) columns
    '''
    
    found = list_all(query)
    
    granule = [item[0] for item in found]
    downloadUrl = [item[1] for item in found]
    flightDirection = [item[2] for item in found]
    beamMode = [item[3] for item in found]
    footPrint = [item[4] for item in found]
    imageDate = [item[5] for item in found]
    
    df = pd.DataFrame({'granule_name': granule, 
                       'download_url': downloadUrl,
                       'flight_direction': flightDirection,
                       'beam_mode': beamMode,
                       'footprint': footPrint,
                       'image_date': imageDate})
    
    return df