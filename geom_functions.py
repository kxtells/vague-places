from shapely.geometry import MultiPoint
import os
import subprocess

def convex_hull(latlon_list):
    """
       Generates the convex hull of a latlon list of tuples
       [(lat0,lon0),(lat1,lon1),...(latN,lonN)]
    """
    return MultiPoint(latlon_list).convex_hull.wkt

def alpha_shape(cgalfile):
    """
        External system execution of alpha_shaper to generate a WKT alpha shape file.
        Expects a CGAL file with lon lat corrdinates and the first line an integer
        of the total number of lines to read
    """
    alpha = 0.1;
    expath = os.path.join(os.path.dirname(os.path.realpath(__file__)),"alpha_shape/alpha_shaper");
    filpath = os.path.realpath(cgalfile.name);
    
    try:
        wkt_polygons = subprocess.check_output([expath,"-i",filpath,"-a",str(alpha)])
        opt_alpha = subprocess.check_output([expath,"-i",filpath,"--optimalalpha"])
    except:
        wkt_polygons = "Error Executing:"+str(expath)+" -i "+filpath+" -a "+str(alpha);
        alpha = 0
        opt_alpha = 0

    return (alpha,opt_alpha,wkt_polygons)

