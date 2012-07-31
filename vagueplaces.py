from SPARQLWrapper import SPARQLWrapper, SPARQLExceptions, JSON
import argparse
import sys
import threading
import time
import signal
import cSpinner
import cPlace
from libs import heatmap

############################
#
#  ARGUMENT PARSING
#
############################

parser = argparse.ArgumentParser(description='CSV generation with name;point;country querying dbpedia')

parser.add_argument('--query', action='store', dest='querystring', default=None,
                    help='Query to filter from the Abstract results')

parser.add_argument('--output', type=argparse.FileType('wb', 0), dest='fileout', default='dbpedia.csv',
                    help='File out. [default dbpedia.csv]')

parser.add_argument('--live', action='store_true',default=False,
                    dest='live_bool',
                    help='Use Dbpedia live SPARQL endpoint instead of last released version')

parser.add_argument('--verbose', action='store_true', default=False,
                    dest='debug_bool',
                    help='Verbose output')

arguments  = parser.parse_args()


############################
#
#  INITIALIZATIONS
#
############################
query = arguments.querystring
OF = arguments.fileout
isdebug = arguments.debug_bool
islive = arguments.live_bool
RESULTS_QUERY = 500000
PLACES = []

# Europe Country List
if islive:
    sparql = SPARQLWrapper("http://live.dbpedia.org/sparql")
else:
    sparql = SPARQLWrapper("http://dbpedia.org/sparql")

sparql.setReturnFormat(JSON)

sparql.setQuery("""
                PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
                PREFIX yago: <http://dbpedia.org/class/yago/>
                PREFIX dbpedia-owl: <http://dbpedia.org/ontology/>

                SELECT ?place WHERE {
                    ?place rdf:type yago:EuropeanCountries .
                    ?place rdf:type dbpedia-owl:Country
                }
                """
)

results = sparql.query().convert()

for country in results["results"]["bindings"]:
    country_uri = country["place"]["value"]
    country_name = country_uri.rpartition('/')[-1]

#Spinner
S = cSpinner.cSpinner()
S.start()


############################
#
#  FUNCTIONS
#
############################
def gen_heatmap():
    pass

def finish_program():
    OF.close()
    S.stop()
    sys.exit(0)

def write_file_cgal(fileh):
    """ 
        Writes a file to be read by cgal alpha_shape generator 
    """
    fileh.write(len(PLACES))
    for p in PLACES:
        fileh.write(p.lat+" "+p.lon)

def write_file_csv(fileh):
    """ 
        Writes a CSV file to be opened by a GIS software. WKT 
    """
    header = "name;WKT;Country;Abstract\n"
    fileh.write(header)

    for p in PLACES:
        fileh.write(p.name+"; POINT("+p.lon+" "+p.lat+");"+p.country+";"+p.text)

def write_file(fileh,wf):
    """ 
        Write a file (fileh) with the format (wf). Accepting csv and cgal
    """
    if wf == 'cgal':
        write_file_cgal(fileh)
    elif wf == 'csv':
        write_file_csv(fileh)

############################
#
#  SIGNAL HANDLING
#
############################
def kill_handler(signal, frame):
    print 'Kill Signal Recieved'
    finish_program()

signal.signal(signal.SIGINT, kill_handler)

############################
#
#  START
#
############################


for country in results["results"]["bindings"]:
    country_uri = country["place"]["value"]
    country_name = country_uri.rpartition('/')[-1]
    total_results = 0
    query_results = 1
    offset = 0
    while query_results > 0:
        try:
            sparql.setQuery("""
                SELECT ?title,?geolat,?geolong,?abstract
                WHERE{
                  ?place rdf:type dbpedia-owl:Place .
                  ?place dbpedia-owl:country <""" + country_uri + """> .
                  ?place foaf:name ?title .
                  ?place geo:lat ?geolat .
                  ?place geo:long ?geolong .
                  ?place dbpedia-owl:abstract ?abstract .
                  FILTER ( regex(?abstract,\" """ + str(query) + """\","i") )
                }
                OFFSET """ + str(offset) + """
                LIMIT """ + str(RESULTS_QUERY)+ """
                """)

            country_results = sparql.query().convert()

            for result in country_results["results"]["bindings"]:
                title = result["title"]["value"].encode('ascii','ignore')
                lat = result ["geolat"]["value"]
                lon = result["geolong"]["value"]
                country = country_name
                abstract = result["abstract"]["value"].encode('ascii','ignore')
                PLACES.append(cPlace.cPlace(title,lat,lon,abstract,country))

            query_results = len(country_results["results"]["bindings"])
            offset = offset + query_results
            total_results += query_results

        except Exception as inst:
            print type(inst)
            print "EXCEPTION"

    if isdebug: print country_uri, total_results

############################
#
#  FILE WRITING
#
############################
write_file(OF,'csv')

############################
#
#  CLOSURE
#
############################
finish_program()
