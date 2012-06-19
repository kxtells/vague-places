from SPARQLWrapper import SPARQLWrapper, SPARQLExceptions, JSON

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

header = "name;WKT;Country"
print header

for country in results["results"]["bindings"]:
    country_uri = country["place"]["value"]
    country_name = country_uri.rpartition('/')[-1]
    total_results = 1
    offset = 0
    
    while total_results > 0:
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
              LIMIT 1000
            """)

            country_results = sparql.query().convert()

            for result in country_results["results"]["bindings"]:
                print(result["title"]["value"].encode("utf-8") + ";POINT(" + result["geolong"]["value"] +" "+ result["geolat"]["value"] +");" + country_name)
        
            total_results = len(country_results["results"]["bindings"])
            offset = offset + 10000
    
        except Exception as inst:
            print type(inst)
            print "EXCEPTION"

