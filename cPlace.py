class cPlace():
    """
        Class containing information of a place
        \details Entity simply used as a container of information.
    """
    
    def __init__(self,name,lat,lon,abstract,country):
        """
            Class constructor
            \param name
            \param lat
            \param lon
            \param abstract
            \param country
        """
        self.name = name
        self.lat = lat
        self.lon = lon
        self.text = abstract
        self.country = country
