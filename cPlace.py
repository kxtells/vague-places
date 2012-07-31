class cPlace():
    """
        Class containing information of a place
    """
    def __init__(self,name,lat,lon,abstract,country):
        self.name = name
        self.lat = lat
        self.lon = lon
        self.text = abstract
        self.country = country
