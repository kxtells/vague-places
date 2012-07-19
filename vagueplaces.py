from SPARQLWrapper import SPARQLWrapper, SPARQLExceptions, JSON
import argparse
import sys
import threading
import time
import cSpinner

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
RESULTS_QUERY = 500000

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
#  START
#
############################

header = "name;WKT;Country;Abstract\n"
OF.write(header)

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
                OF.write(result["title"]["value"].encode("utf-8") + ";POINT(" + result["geolong"]["value"] +" "+ result["geolat"]["value"] +");" + country_name + ";"+result["abstract"]["value"].encode('ascii','ignore')+"\n")
        
            query_results = len(country_results["results"]["bindings"])
            offset = offset + RESULTS_QUERY
            total_results += query_results
    
        except Exception as inst:
            print type(inst)
            print "EXCEPTION"

    if isdebug: print country_uri, total_results

############################
#
#  CLOSURE
#
############################
OF.close()
S.stop()
