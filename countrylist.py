"""
 Print the different countries present in a csv file generated by dbpedia extractors
 Vagueplaces Generator
 \author Jordi Castells
 \date 18 December 2016
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

parser = argparse.ArgumentParser(description='print a country list from a downloaded CSV')

parser.add_argument('--pointFile', default=None, dest='points',help='input file with points to alpha shape.')
parser.add_argument('--nospinner', default=False, dest='nospinner',help='Deactivate live feedback via shell. For batch operations', action="store_true")


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

def finish_program():
    S.stop()
    sys.exit(0)

def read_countries_from_csv(filename):
    """
        Reads a CSV points file
        "name;WKT;Country;Abstract"

	We read this information apart because reading the whole
	file can destroy our memory
    """
    data = {}
    total = 0
    failed = 0

    totalL = sum(1 for line in open(filename))
    with open(filename, 'rb') as csvfile:
        preader = csv.DictReader(csvfile, delimiter=';', quotechar='"')
        for row in preader:
            S.set_msg("Reading Countries: %s/%s. FAILED: %s"%(total,totalL,failed))
            total+=1

            #skip incorrectly parsed points
            if "http://dbpedia.org/resource/" not in row["country"]:
                failed+=1
                continue

            if row["country"] not in data:
                #country = re.sub("http://dbpedia.org/resource/","", row["country"])
                #country = re.sub("http://dbpedia.org/resource/","", country)
                data[row["country"]] = 1
                #data.append(country)
            else:
                data[row["country"]] += 1

    rdata = []
    for key,val in data.iteritems():
        if val > 3:
            rdata.append(key)

    return rdata


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

    #Can't use this since it's using a lot of memory. This approach was getting
    #everything in RAM and then start processing. We have to do something slower
    #but less memory hungry


    # First get the countries
    S.set_msg("Generating country list")
    countries  = read_countries_from_csv(args.points)
    for country in countries:
        print country
    sys.exit(1)

except Exception as e:
    print e
finally:
    finish_program()
