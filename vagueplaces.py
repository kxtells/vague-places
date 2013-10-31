"""
 Vagueplaces Generator
 \author Jordi Castells
 \date 10 August 2012
 \mainpage

  This software is implemented as a Final project of a Geoinformatics Master course at ITC Faculty of Geo-Information Science and Earth Observation.

"""
from SPARQLWrapper import SPARQLWrapper, SPARQLExceptions, JSON
import argparse
import sys
import signal
import os
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

parser = argparse.ArgumentParser(description='CSV generation with name;point;country querying dbpedia')

parser.add_argument('--query', action='store', dest='stringval', default=None,nargs='+',
                    help='List of keywords to filter from the Abstract results. Interpreted as Logical disjunction')

parser.add_argument('--alpha',type=float,default=0.1,dest='floatval')

parser.add_argument('CSV_POINT_OUTPUT', type=argparse.FileType('wb', 0),
                    help='Retrieved points file out as CSV.')

parser.add_argument('--live', action='store_true',default=False,
                    dest='live_bool',
                    help='Use Dbpedia live SPARQL endpoint instead of last released version')

parser.add_argument('--verbose', action='store_true', default=False,
                    dest='debug_bool',
                    help='Verbose output')

arguments  = parser.parse_args()


# ###########################
#
#  INITIALIZATIONS
#
# ###########################
query_list = arguments.stringval
OF = arguments.CSV_POINT_OUTPUT
alpha = arguments.floatval
isdebug = arguments.debug_bool
islive = arguments.live_bool
RESULTS_QUERY = 500000
PLACES = []

#sparql endpoint
if islive:
    #sparql = SPARQLWrapper("http://live.dbpedia.org/sparql")
    sparql = SPARQLWrapper("http://dbpedia-live.openlinksw.com/sparql")
else:
    sparql = SPARQLWrapper("http://dbpedia.org/sparql")

#Spinner
S = cSpinner.cSpinner()
S.set_msg("loading")
S.start()

#report
REPORT = cReport.cReport();
REPORT.set_query(str(query_list));
REPORT.set_points_filename(os.path.realpath(str(OF.name)));

# ###########################
#
#  FUNCTIONS
#
# ###########################
def european_countries():
    """
        Retrieve an europe country list from DBpedia with URIs.
        @return List with country URIS
    """
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

    if isinstance(results, xml.dom.minidom.Document):
        warnings.warn("Expecting JSON, XML returned")
        finish_program()

    return results["results"]["bindings"]

def get_points(country_uri,query_list,offset,limit):
    """
        Retrieve a list of points from DBpedia matching the input.
        \param country_uri country to query
        \param query_list substring to check in the Abstract
        \param offset Offset to start retrieving
        \param limit Limit of lines to retrieve
        \return List with points with title,geolat,geolong
    """
    regex_list = []
    for q in query_list:
        regex_list.append("""regex(?abstract,\" """+str(q)+"""\","i") """)

    query = "||".join(regex_list)

    querystr = """
        SELECT DISTINCT ?title,?geolat,?geolong
        WHERE{
          ?place rdf:type dbpedia-owl:Place .
          ?place dbpedia-owl:country <""" + country_uri + """> .
          ?place foaf:name ?title .
          ?place geo:lat ?geolat .
          ?place geo:long ?geolong .
          ?place dbpedia-owl:abstract ?abstract .
          FILTER ("""+ query +""")
        }
        OFFSET """ + str(offset) + """
        LIMIT """ + str(limit)+ """
        """

    sparql.setQuery(querystr)

    country_results = sparql.query().convert()
    return country_results["results"]["bindings"]

def gen_heatmap():
    """
         \todo gen_heatmap is not implemented
    """
    pass

def gen_convex_hull():
    """
        Generate the convex hull for the report
    """
    plist = []

    for p in PLACES:
        plist.append((float(p.lon),float(p.lat)))

    REPORT.set_wkt_chull(GEOM.convex_hull(plist))

def gen_alpha_shape(cgalfile,alpha):
    """
        External system execution of alpha_shaper to generate a WKT alpha shape file.
        Expects a CGAL file with lon lat corrdinates and the first line an integer
        of the total number of lines to read
    """
    opt_alpha,wkt_polygons = GEOM.alpha_shape(cgalfile,alpha);
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
for country in european_countries():
    country_uri = country["place"]["value"]
    country_name = country_uri.rpartition('/')[-1]
    total_results = 0
    offset = 0
    query_results = 1

    S.set_msg(country_name)

    while query_results > 0:
        try:
            country_results = get_points(country_uri,query_list,offset,RESULTS_QUERY)

            for result in country_results:
                title = result["title"]["value"].encode('ascii','ignore')
                lat = result ["geolat"]["value"]
                lon = result["geolong"]["value"]
                country = country_name
                #abstract = result["abstract"]["value"].encode('ascii','ignore')
                abstract = ""
                if(lat!='NAN' and lon != 'NAN'):
                    PLACES.append(cPlace.cPlace(title,lat,lon,abstract,country))

            query_results = len(country_results)
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
    # ###########################
    #
    #  POLYGON GENERATION
    #
    # ###########################
    tmpfile = tempfile.NamedTemporaryFile(prefix='vagueplace',delete=False);
    write_file(tmpfile,'cgal')

    gen_alpha_shape(tmpfile,alpha);
    gen_convex_hull();

    # ###########################
    #
    #  REPORT PRINTING
    #
    # ###########################
    REPORT.print_report();


    # ###########################
    #
    #  FILE WRITING
    #
    # ###########################
    S.pause();
    write_file(OF,'csv')

    # ###########################
    #
    #  CLOSURE
    #
    # ###########################
else:
    print "No results for this query"

finish_program()
