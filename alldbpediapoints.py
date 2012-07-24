from SPARQLWrapper import SPARQLWrapper, SPARQLExceptions, JSON
import argparse
import sys
import threading
import time
import signal 

############################
#
#  ARGUMENT PARSING 
#
############################

parser = argparse.ArgumentParser(description='CSV generation with name;point;country querying dbpedia')

parser.add_argument('--output', type=argparse.FileType('wb', 0), dest='fileout', default='dbpedia.csv',
                    help='File out. [default dbpedia.csv]')

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
RESULTS_QUERY = 20000 

sparql = SPARQLWrapper("http://dbpedia.org/sparql")
sparql.setReturnFormat(JSON)

#Spinner
S = cSpinner()
S.start()
S.set_total(585801); #as DbPedia 3.6

# Query to get the total count
#SELECT COUNT(*)
#WHERE{
#  ?place rdf:type dbpedia-owl:Place .
#  ?place foaf:name ?title .
#  ?place geo:lat ?geolat .
#  ?place geo:long ?geolong .
#}

############################
#
#  FUNCTIONS
#
############################
def wait_to_continue():
    S.pause()
    
    waiter = cSpinner()
    waiter.set_char_array(["Waiting.","Waiting..","Waiting..."])
    waiter.start()
    time.sleep(300)
    waiter.stop()

    S.resume()

def finish_program():
    OF.close()
    S.stop()
    sys.exit(0)

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

header = "name;WKT\n"
OF.write(header)

total_results = 0 
query_results = 1
offset = 0

while query_results > 0:
    try:
        sparql.setQuery("""
            SELECT ?title,?geolat,?geolong,?abstract
            WHERE{
              ?place rdf:type dbpedia-owl:Place .
              ?place foaf:name ?title .
              ?place geo:lat ?geolat .
              ?place geo:long ?geolong .
            }
            OFFSET """ + str(offset) + """
            LIMIT """ + str(RESULTS_QUERY)+ """
            """)

        results_array = sparql.query().convert()
        for result in results_array["results"]["bindings"]:
            OF.write(result["title"]["value"].encode("utf-8") + ";POINT(" + result["geolong"]["value"] +" "+ result["geolat"]["value"] +");" + "\n")
    
        query_results = len(results_array["results"]["bindings"])
        offset = offset + RESULTS_QUERY
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
finish_program()
