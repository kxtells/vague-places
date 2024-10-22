import datetime

class cReport():
    """
        \brief Report printing class
        \details Class to record information about the execution and finally print it.
    """
    #__NPOINTS = 0;
    __alpha = 1;
    __optalpha = 1;
    __date = str(datetime.datetime.now());
    __countries = [];
    __country_val = [];
    __live = False;
    __WKTashape = "";
    __WKTchull = "";
    __query = "";
    __ofilename = "";

    def set_country_count(self,places):
        """
            \brief For a set of places, counts the places in each country.
        """
        self.__NPOINTS = len(places);
        for p in places:
            try:
                index = self.__countries.index(p.country)
                self.__country_val[index] += 1
            except:
                self.__countries.append(p.country)
                self.__country_val.append(1)


    def __report_str(self):
        """
            Generate a String with the report
        """
        report_list = []
        report_list.append(self.__print_title());

        report_list.append(self.__print_banner("DATASET"))
        if(self.__live):
            report_list.append("DBpedia Live "+str(self.__date))
        else:
            report_list.append("DBpedia Last release version")

        report_list.append("QUERY: "+str(self.__query).ljust(20))
        report_list.append("Retrieved Points:\t"+str(self.__NPOINTS).ljust(20))
        report_list.append("Skipped Points:\t"+str(self.__NPOINTS - sum(self.__country_val)).ljust(20))
        report_list.append("FILE:\t"+str(self.__ofilename).ljust(20))
        report_list.append("")
        report_list.append("country".rjust(30)+"|".rjust(5)+"total_points".rjust(5))

        for i,c in enumerate(self.__countries):
            report_list.append(str(c).rjust(30)+"|".rjust(5)+str(self.__country_val[i]).rjust(5))


        report_list.append(self.__print_banner("GEOMETRIES"))
        report_list.append("---- Alpha Shape WKT ---")
        report_list.append(self.__WKTashape)
        report_list.append("Alpha:"+str(self.__alpha).ljust(20))
        report_list.append("Optimal Alpha: "+str(self.__optalpha).ljust(20))
        report_list.append("")
        report_list.append("---- Convex Hull Shape WKT ---")
        report_list.append(self.__WKTchull)
        report_list.append("")

        return "\n".join(report_list)


    def print_report(self):
        """
            \brief Prints the report to the standart output
        """
        print self.__report_str()

    def __print_title(self):
        return "\n".join([
        "",
        "###########################################",
        "# REPORT GENERATED BY vagueplaces.py",
        "#  "+str(self.__date).center(40),
        "#",
        "###########################################",
        "",
        ])

    def __print_banner(self,text):
        return "\n".join([
        "",
        "###########################################",
        "#",
        "#"+str(text).center(40),
        "#",
        "###########################################",
        "",
        ])

    def write_report(self, filename):
        """
            \todo Implement write_report to file
        """
        try:
            with open(filename, "wb") as fileh:
                fileh.write(self.__report_str())

            return True
        except Exception as e:
            print e
            return False

    def set_alphas(self,alpha,optalpha):
        """
            \brief Sets the report alpha values
            \param alpha used alpha
            \param optalpha Optimal alpha
        """
        self.__alpha = alpha;
        self.__optalpha = optalpha;

    def set_wkt_ashape(self,wkt):
        """
            \brief sets the WKT for the alpha shape
        """
        self.__WKTashape = wkt;

    def set_wkt_chull(self,wkt):
        """
            \brief sets the WKT for the convex hull
        """
        self.__WKTchull = wkt;

    def set_query(self,query):
        self.__query = query;

    def set_points_filename(self,ofile):
        """
            \brief Sets the path to the points file
            \param ofile String path
        """
        self.__ofilename = ofile;

    def set_live(self,live):
        """
            \brief sets if DBpedia live is the used DBpedia version
            \param live Boolean
        """
        self.__live = live;
