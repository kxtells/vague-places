"""
 Batch dbpedia country point files generator
 \author Jordi Castells
 \date 8 December 2016

 A helper tool to split an already downloaded dbpedia csv file into different
 smaller files, separed by the second column that is assumed to be a dbo:Country
 resource.

 csv file is expected :
 name;country;wikipediaURL;x;y;WKT
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

parser = argparse.ArgumentParser(description='Filter an input dataset into smaller files (by country)')


parser.add_argument('--outDir', default=None, dest='outDir',help='Directory where to store the country points outputs')
parser.add_argument('--pointFile', default=None, dest='points',help='input file with points to split in smaller files')

parser.add_argument('--nospinner', default=False, dest='nospinner',help='Deactivate live feedback via shell. For batch operations', action="store_true")
#parser.add_argument('--country', default=None, dest='countryFilter', help='Filter by country')


args = parser.parse_args()

def slugify(value, allow_unicode=False):
    """
    Force a valid filename
    """
    import re
    value = re.sub("http://dbpedia.org/resource/","",value)
    return re.sub(r'[^\x00-\x7F]+','', value)

# ###########################
#
#  INITIALIZATIONS
#
# ###########################


#Spinner
S = cSpinner.cSpinner()
if not args.nospinner:
    S.start()

csv.field_size_limit(sys.maxsize)

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


def read_countries_from_csv(filename):
    """
        Reads a CSV points file
        "name;WKT;Country;Abstract"

	We read this information apart because reading the whole
	file can destroy our memory
    """
    data = []
    total = 0
    failed = 0

    totalL = sum(1 for line in open(filename))
    with open(filename, 'rb') as csvfile:
        preader = csv.DictReader(csvfile, delimiter=';', quotechar='"')
        for row in preader:
            S.set_msg("Reading Countries: %s/%s. FAILED: %s"%(total,totalL,failed))
            total+=1

            if "http://dbpedia.org/resource/" not in row["country"]:
                failed+=1
                continue

            if row["country"] not in data:
                #country = re.sub("http://dbpedia.org/resource/","", row["country"])
                #country = re.sub("http://dbpedia.org/resource/","", country)
                country = row["country"]
                data.append(country)

    return data


def extract_countries_to_files(filename, outdir, countryNames):
    """
        retrieves all the points from a filename that match a countryName
        and stores those points to another file
        "name;WKT;Country;Abstract"
    """
    data = []
    total = 0
    fileHandles = {}

    for countryName in countryNames:
        fileout = os.path.join(args.outDir, "%s_points.csv" % slugify(countryName))
        handle = open(fileout, 'wb')
        handle.write("name;country;wikipediaURL;x;y;WKT\n")
    	pwriter = csv.writer(handle, delimiter=';', quotechar='"')
        fileHandles[countryName] = [handle, pwriter]

    totalL = sum(1 for line in open(filename))
    with open(filename, 'rb') as infile:
    	preader = csv.DictReader(infile, delimiter=';', quotechar='"')
    	for row in preader:
    	    S.set_msg("Filtering & splitting %s"% total)
    	    total+=1
            if row["country"] in fileHandles.keys():
                #os is the file. 1 is the csv parser
    	        fileHandles[row["country"]][1].writerow([row["name"],row["country"],row["URL"],row["x"],row["y"],row["WKT"]])

    for name, handle in fileHandles.items():
        handle[0].close()
 
def extract_country_to_file(filename, fileout, countryName):
    """
        retrieves all the points from a filename that match a countryName
        and stores those points to another file
        "name;WKT;Country;Abstract"
    """
    data = []
    total = 0
    with open(filename, 'rb') as infile:
        with open(fileout, 'wb') as outfile:
            preader = csv.DictReader(infile, delimiter=';', quotechar='"')
            pwriter = csv.writer(outfile, delimiter=';', quotechar='"')
            for row in preader:
                S.set_msg("Filtering %s: %s"%(countryName, total))
                total+=1
                if countryName in row["country"]:
                    pwriter.writerow([row["name"],row["country"],row["URL"],row["x"],row["y"],row["WKT"]])


def get_country_points(filename, countryName):
    """
        retrieves all the points from a filename that match a countryName
        "name;WKT;country;Abstract"
    """

    data = []
    total = 0
    with open(filename, 'rb') as csvfile:
        preader = csv.DictReader(csvfile, delimiter=';', quotechar='"')
        for row in preader:
            S.set_msg("Obtaining %s: %s"%(countryName, total))
            total+=1
            if countryName in row["country"]:
                data.append(row)

    return data

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

    if not os.path.exists(args.outDir):
        os.mkdir(args.outDir)

    S.set_msg("Parsing input")
    #CREATE A NICE TEMPFILE for CGAL from the input data
    tmpfile = tempfile.NamedTemporaryFile(prefix='vagueplace',delete=True);

    #Can't use this since it's using a lot of memory. This approach was getting
    #everything in RAM and then start processing. We have to do something slower
    #but less memory hungry
    #datain          = read_points_csv(args.points)


    # First get the countries
    S.set_msg("Generating country list")
    countries  = read_countries_from_csv(args.points)
    extract_countries_to_files(args.points, args.outDir, countries)
    #for country in countries:
    #    # For each country split the output in different files that we will
    #    # read one by one to generate the output files
    #    fileout = os.path.join(args.outDir, "%s_points.csv" % slugify(country))
    #    extract_countries_to_files(args.points, fileout, country)
    #    print
    sys.exit(1)
    #places, errors  = parse_input_to_place(datain)

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
    ###data = (p.country for p in places)
    ###data = set(data)
    ###for c in data:
    ###    cdata = []
    ###    country_points = (p for p in places if p.country == c)
    ###    for cp in country_points:
    ###        cdata.append(cp)

    ###    tmpfile = tempfile.NamedTemporaryFile(prefix='countryData',delete=True);
    ###    write_file_cgal(cdata, tmpfile)

    ###    for alphaVal in args.alphas:
    ###        S.set_msg("Shaping %s %s" % (c, alphaVal))
    ###        fileName = os.path.join(args.outDir, "alphaShape_%s_%s.csv" % (c, alphaVal))
    ###        with open(fileName, 'wb') as fileh:
    ###            polygons = gen_alpha_shape(tmpfile, alphaVal)
    ###            write_file_wkt_csv(polygons, fileh)


except Exception as e:
    print e
finally:
    finish_program()
