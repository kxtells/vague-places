from SPARQLWrapper import SPARQLWrapper, SPARQLExceptions, JSON
import argparse
import sys

############################
#
#  ARGUMENT PARSING 
#
############################

parser = argparse.ArgumentParser(description='CSV generation with name;point;country querying dbpedia')

parser.add_argument('--query', action='store', dest='querystring', default=None,
                    help='Query')

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
RESULTS_QUERY = 10000


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

header = "name;WKT;Country\n"
OF.write(header)

for country in results["results"]["bindings"]:
    country_uri = country["place"]["value"]
    country_name = country_uri.rpartition('/')[-1]
    total_results = 1
    offset = 0
    
    while total_results > 0:
        if isdebug: print country_uri, offset
        try:
            sparql.setQuery("""
              SELECT ?title (MIN(?geolat) AS ?geolat) (MIN(?geolong) AS ?geolong)
              WHERE {
                ?place rdf:type <http://dbpedia.org/ontology/Place> .
                ?place dbpedia-owl:country <""" + country_uri + """> .
                ?place foaf:name ?title .
                ?place geo:lat ?geolat .
                ?place geo:long ?geolong .
              }
              GROUP BY ?title
              OFFSET """ + str(offset) + """
              LIMIT """ + str(RESULTS_QUERY)+ """
            """)

            country_results = sparql.query().convert()

            for result in country_results["results"]["bindings"]:
                OF.write(result["title"]["value"].encode("utf-8") + ";POINT(" + result["geolong"]["value"] +" "+ result["geolat"]["value"] +");" + country_name + "\n")
        
            total_results = len(country_results["results"]["bindings"])
            offset = offset + RESULTS_QUERY
    
        except Exception as inst:
            print type(inst)
            print "EXCEPTION"

############################
#
#  CLOSURE
#
############################
OF.close()
