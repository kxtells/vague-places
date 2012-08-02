import datetime

class cReport():
    points = 0;
    alpha = 1;
    optalpha = 1;
    date = str(datetime.datetime.now());
    countries = [];
    country_val = [];
    live = False;
    WKT = "";

    def set_country_count(self,places):
        """
            For all the countries counts the places extracted
        """
        self.points = len(places);
        for p in places:
            try:
                index = self.countries.index(p.country)
                self.country_val[index] += 1
            except:
                self.countries.append(p.country)
                self.country_val.append(0)

    def print_report(self):
        print self.date;
        print self.points;
        print str(self.alpha)+" "+str(self.optalpha);
        print self.live;
        print self.WKT;
        pass;

    def write_report(self,fileh):
        pass;

    def set_alphas(self,alpha,optalpha):
        self.alpha = alpha;
        self.optalpha = optalpha;

    def set_wkt(self,wkt):
        self.WKT = wkt;

    def set_live(self,live):
        self.live = live;
