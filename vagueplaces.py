from SPARQLWrapper import SPARQLWrapper, SPARQLExceptions, JSON
import argparse
import sys
import signal
import os
import tempfile

import cSpinner
import cPlace
import cReport
import geom_functions as GEOM

############################
#
#  ARGUMENT PARSING
#
############################

parser = argparse.ArgumentParser(description='CSV generation with name;point;country querying dbpedia')

parser.add_argument('--query', action='store', dest='querystring', default=None,
                    help='Query to filter from the Abstract results')

#parser.add_argument('--format', action='store', dest='formatstring', default='csv',
#                    help='Format of the output file [csv,cgal]. default is csv')

parser.add_argument('--output', type=argparse.FileType('wb', 0), dest='fileout', default='dbpedia.csv',
                    help='Retrieved points file out as CSV. [default dbpedia.csv]')

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
#oformat = arguments.formatstring
OF = arguments.fileout
isdebug = arguments.debug_bool
islive = arguments.live_bool
RESULTS_QUERY = 500000
PLACES = []

#sparql endpoint
if islive:
    sparql = SPARQLWrapper("http://live.dbpedia.org/sparql")
else:
    sparql = SPARQLWrapper("http://dbpedia.org/sparql")



#Spinner
S = cSpinner.cSpinner()
S.set_msg("loading")
S.start()

#report
REPORT = cReport.cReport();
REPORT.set_query(str(query));
REPORT.set_points_filename(os.path.realpath(str(OF.name)));

############################
#
#  FUNCTIONS
#
############################
def european_countries():
    # Europe Country List
        
    sparql.setReturnFormat(JSON)
    
    sparql.setQuery("""
                    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
                    PREFIX yago: <http://dbpedia.org/class/yago/>
                    PREFIX dbpedia-owl: <http://dbpedia.org/ontology/>
    
                    SELECT DISTINCT ?place WHERE {
                        ?place rdf:type yago:EuropeanCountries .
                        ?place rdf:type dbpedia-owl:Country
                    }
                    """
    )

    results = sparql.query().convert()
    return results["results"]["bindings"]

def gen_heatmap():
    
    pass

def gen_convex_hull():
    """
        Generate the convex hull for the report
    """
    plist = []
    
    for p in PLACES:
        plist.append((float(p.lon),float(p.lat)))

    REPORT.set_wkt_chull(GEOM.convex_hull(plist))

def gen_alpha_shape(cgalfile):
    """
        External system execution of alpha_shaper to generate a WKT alpha shape file.
        Expects a CGAL file with lon lat corrdinates and the first line an integer
        of the total number of lines to read
    """
    alpha,opt_alpha,wkt_polygons = GEOM.alpha_shape(cgalfile);
    REPORT.set_alphas(alpha,opt_alpha)
    REPORT.set_wkt_ashape(wkt_polygons)

def finish_program():
    OF.close()
    S.stop()
    sys.exit(0)

def write_file_cgal(fileh):
    """ 
        Writes a file to be read by cgal alpha_shape generator 
    """
    fileh.write(str(len(PLACES))+"\n")
    for p in PLACES:
        fileh.write(p.lon+" "+p.lat+"\n")

def write_file_csv(fileh):
    """ 
        Writes a CSV file to be opened by a GIS software. WKT 
    """
    header = "name;WKT;Country;Abstract\n"
    fileh.write(header)

    for p in PLACES:
        fileh.write(p.name+"; POINT("+p.lon+" "+p.lat+");"+p.country+";"+p.text+"\n")

def write_file(fileh,wf):
    """ 
        Write a file (fileh) with the format (wf). Accepting csv and cgal
    """
    if wf.lower() == 'cgal':
        write_file_cgal(fileh)
    elif wf.lower() == 'csv':
        write_file_csv(fileh)
    fileh.close()


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
for country in european_countries():
    country_uri = country["place"]["value"]
    country_name = country_uri.rpartition('/')[-1]
    total_results = 0
    query_results = 1
    
    S.set_msg(country_name)

    offset = 0
    while query_results > 0:
        try:
            sparql.setQuery("""
                SELECT DISTINCT ?title,?geolat,?geolong
                WHERE{
                  ?place rdf:type dbpedia-owl:Place .
                  ?place dbpedia-owl:country <""" + country_uri + """> .
                  ?place foaf:name ?title .
                  ?place geo:lat ?geolat .
                  ?place geo:long ?geolong .
                  ?place dbpedia-owl:abstract ?abstract .
                  FILTER ( regex(?abstract,\" """ + str(query) +"""\","i") )
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
                #abstract = result["abstract"]["value"].encode('ascii','ignore')
                abstract = ""
                if(lat!='NAN' and lon != 'NAN'):
                    PLACES.append(cPlace.cPlace(title,lat,lon,abstract,country))

            query_results = len(country_results["results"]["bindings"])
            offset = offset + query_results
            total_results += query_results
        except Exception as inst:
            print type(inst)
            print "EXCEPTION"

    
    if isdebug: 
        sys.stdout.write("\r\x1b[K"+country_uri+" "+str(total_results)+"\n")
        sys.stdout.flush()

REPORT.set_country_count(PLACES);

if (len(PLACES) > 0):
    ############################
    #
    #  POLYGON GENERATION
    #
    ############################
    tmpfile = tempfile.NamedTemporaryFile(prefix='vagueplace',delete=False);
    write_file(tmpfile,'cgal')
    
    gen_alpha_shape(tmpfile);
    gen_convex_hull();
    
    ############################
    #
    #  REPORT PRINTING
    #
    ############################
    REPORT.print_report();
    
    
    ############################
    #
    #  FILE WRITING
    #
    ############################
    S.pause();
    write_file(OF,'csv')
    
    ############################
    #
    #  CLOSURE
    #
    ############################
else:
    print "No results for this query"

finish_program()
