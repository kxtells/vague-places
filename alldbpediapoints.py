from SPARQLWrapper import SPARQLWrapper, SPARQLExceptions, JSON
import argparse
import sys
import threading
import time
import signal
import warnings
import xml

############################
#
#  ARGUMENT PARSING
#
############################

parser = argparse.ArgumentParser(description='CSV generation with name;point;country querying dbpedia')

parser.add_argument('--output', type=argparse.FileType('wb', 0), dest='fileout', default='dbpedia.csv',
                    help='File out. [default dbpedia.csv]')

parser.add_argument('--live', action='store_true',default=False,
                    dest='live_bool',
                    help='Use Dbpedia live SPARQL endpoint instead of last released version')

arguments  = parser.parse_args()


############################
#
#  CLASSES
#
############################
class cSpinner(threading.Thread):
    """
        Print things to one line dynamically
    """
    chars = ["\\","|","/","-"]
    index = 0
    keeprunning = True
    paused = False
    count = 0
    total = 0

    def run(self):
        while self.keeprunning:
            if self.paused:
                time.sleep(1)
                continue

            self.printing(str(self.count)+"/"+str(self.total)+" "+self.chars[self.index%len(self.chars)])
            time.sleep(0.1)
            self.index +=1

    def printing(self,data):
        sys.stdout.write("\r\x1b[K"+data.__str__())
        sys.stdout.flush()

    def stop(self):
        self.keeprunning = False

    def set_total(self,val):
        self.total = val

    def set_count(self,val):
        self.count = val

    def set_char_array(self,charray):
        self.chars = charray

    def pause(self):
        self.paused = True

    def resume(self):
        self.paused = False

############################
#
#  INITIALIZATIONS
#
############################
OF = arguments.fileout
islive = arguments.live_bool
RESULTS_QUERY = 20000

if islive:
    sparql = SPARQLWrapper("http://live.dbpedia.org/sparql")
else:
    sparql = SPARQLWrapper("http://dbpedia.org/sparql")

sparql.setReturnFormat(JSON)

#Spinner
S = cSpinner()

############################
#
#  FUNCTIONS
#
############################
def finish_program():
    OF.close()
    S.stop()
    sys.exit(0)

def wait_to_continue():
    S.pause()

    waiter = cSpinner()
    waiter.set_char_array(["Waiting.","Waiting..","Waiting..."])
    waiter.start()
    time.sleep(300)
    waiter.stop()

    S.resume()

def get_total_dbpedia_points(islive):
    """ Count the total number of dbpedia points """

    if islive:
        sparql = SPARQLWrapper("http://live.dbpedia.org/sparql")
    else:
        sparql = SPARQLWrapper("http://dbpedia.org/sparql")

    sparql.setReturnFormat(JSON)

    sparql.setQuery("""
                    SELECT (COUNT(*) AS ?count)
                    WHERE{
                      ?place rdf:type dbo:Place .
                      ?place foaf:name ?title .
                      ?place geo:lat ?geolat .
                      ?place geo:long ?geolong .
                    }
            """)

    results_array = sparql.query().convert()

    total = results_array["results"]["bindings"][0]["count"]["value"]

    return total


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

print "Counting total entries"
S.set_total(get_total_dbpedia_points(islive));
S.start()

header = "name;country;URL;x;y;WKT\n"
OF.write(header)

total_results = 0
query_results = 1
offset = 0

while query_results > 0:
    try:
        sparql.setQuery("""
            SELECT ?title,?geolat,?geolong, ?country, ?wikiurl
            WHERE{
              ?place rdf:type dbo:Place .
              ?place foaf:name ?title .
              ?place geo:lat ?geolat .
              ?place geo:long ?geolong .
              ?place prov:wasDerivedFrom ?wikiurl .
              ?place dbo:country ?country .
            }
            OFFSET """ + str(offset) + """
            LIMIT """ + str(RESULTS_QUERY)+ """
            """)

        results_array = sparql.query().convert()
        for result in results_array["results"]["bindings"]:
            OF.write(result["title"]["value"].encode("utf-8") +
                    result["country"]["value"].encode("utf-8") +
                    result["wikiurl"]["value"].encode("utf-8") +
                    result["geolat"]["value"].encode("utf-8") +
                    result["geolong"]["value"].encode("utf-8") +
                    ";POINT(" + result["geolong"]["value"] +" "+ result["geolat"]["value"] +");" + "\n"
                    )

        query_results = len(results_array["results"]["bindings"])
        offset = offset + query_results
        total_results += query_results
        S.set_count(total_results) #set spinner count

    except Exception as inst:
        #If exception happens, I assume is a network problem exception. Wait 5 minutes and retry
        sys.stdout.write("\r\x1b[K"+str(inst))
        print
        wait_to_continue()

############################
#
#  CLOSURE
#
############################
print "Program Finished"
finish_program()
