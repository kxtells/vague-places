"""
 Batch Shape Generator
 Vagueplaces Generator
 \author Jordi Castells
 \date 8 December 2016

 A helper tool to generate a bunch of alpha shape csv files to be imported in
 GIS tools like qgis.

 Takes an input CSV file with Country, Name and WKT. And for each different
 Country generates an alpha shape of those points for the given alphas.
"""


import os
import re
import sys
import csv
import argparse
import signal
import tempfile
import xml, warnings

import cSpinner
import cPlace
import cReport
import geom_functions as GEOM


# ###########################
#
#  ARGUMENT PARSING
#
# ###########################

parser = argparse.ArgumentParser(description='Batch generate alphas from a retrieved set of points')

parser.add_argument('alphas', type=float, metavar='alphas',
        help="Alpha values to generate", nargs='+')

parser.add_argument('--outDir', default=None, dest='outDir',help='Directory where to store the alpha shape outputs')


parser.add_argument('--pointFile', default=None, dest='points',help='input file with points to alpha shape')

#parser.add_argument('--country', default=None, dest='countryFilter', help='Filter by country')


args = parser.parse_args()


# ###########################
#
#  INITIALIZATIONS
#
# ###########################


#Spinner
S = cSpinner.cSpinner()
S.set_msg("Shaping")
S.start()

def gen_alpha_shape(cgalfile, alpha):
    """
        External system execution of alpha_shaper to generate a WKT alpha shape file.
        Expects a CGAL file with lon lat corrdinates and the first line an integer
        of the total number of lines to read

        returns the well known text of this alpha shape polygons
    """
    opt_alpha, wkt_polygons = GEOM.alpha_shape(cgalfile,alpha);
    return wkt_polygons.splitlines()

def finish_program():
    S.stop()
    sys.exit(0)


def write_file_wkt_csv(wkt_polygons, fileh):
    """
        Write a file with wkt polygons
    """
    fileh.write("id;wkt\n")

    for i,polygon in enumerate(wkt_polygons):
        fileh.write("%s;%s\n" %(i,polygon))

def write_file_cgal(places, fileh):
    """
        Writes a file to be read by cgal alpha_shape generator from a read
        csvDictionary

        returns the number of added points
    """
    #Now write the file
    fileh.write(str(len(places))+"\n")
    for p in places:
        fileh.write(p.lon+" "+p.lat+"\n")

def read_points_csv(filename):
    """
        Reads a CSV points file
        "name;WKT;Country;Abstract"

        Returns a reader object that can be looped returning a dictionary
        for each row.
    """
    data = []
    with open(filename, 'rb') as csvfile:
        preader = csv.DictReader(csvfile, delimiter=';', quotechar='"')
        for row in preader:
            data.append(row)

    return data

def parse_input_to_place(dataList):
    """
        Parse the set of readed points from a csv to a list of places @ref cPlace
    """

    places = []
    skipped = []

    for row in dataList:
        wkt = row["WKT"]
        match = re.search(".*POINT\(([0-9.-]*) ([0-9.-]*)\)", wkt)
        if not match:
            skipped.append(row)
        else:
            place = cPlace.cPlace(row["name"],
                    match.group(2),match.group(1),
                    row["Abstract"],row["Country"])
            places.append(place)

    return places,skipped

# ###########################
#
#  SIGNAL HANDLING
#
# ###########################
def kill_handler(signal, frame):
    print 'Kill Signal Recieved'
    finish_program()

signal.signal(signal.SIGINT, kill_handler)

# ###########################
#
#  START
#
# ###########################

#Open Points file
try:

    S.set_msg("Parsing input")
    #CREATE A NICE TEMPFILE for CGAL from the input data
    tmpfile = tempfile.NamedTemporaryFile(prefix='vagueplace',delete=True);

    datain          = read_points_csv(args.points)
    places, errors  = parse_input_to_place(datain)

    #first the whole dataset
    #write_file_cgal(places, tmpfile)

    #if not os.path.exists(args.outDir):
    #    os.mkdir(args.outDir)

    #for alphaVal in args.alphas:
    #    S.set_msg("Shaping %s" % alphaVal)
    #    fileName = os.path.join(args.outDir, "alphaShape_%s.csv" % alphaVal)
    #    with open(fileName, 'wb') as fileh:
    #        polygons = gen_alpha_shape(tmpfile, alphaVal)
    #        write_file_wkt_csv(polygons, fileh)


    #Now country by country
    data = (p.country for p in places)
    data = set(data)
    for c in data:
        cdata = []
        country_points = (p for p in places if p.country == c)
        for cp in country_points:
            cdata.append(cp)

        tmpfile = tempfile.NamedTemporaryFile(prefix='countryData',delete=True);
        write_file_cgal(cdata, tmpfile)

        for alphaVal in args.alphas:
            S.set_msg("Shaping %s %s" % (c, alphaVal))
            fileName = os.path.join(args.outDir, "alphaShape_%s_%s.csv" % (c, alphaVal))
            with open(fileName, 'wb') as fileh:
                polygons = gen_alpha_shape(tmpfile, alphaVal)
                write_file_wkt_csv(polygons, fileh)


except Exception as e:
    print e
finally:
    finish_program()
