import numpy as np
import pandas as pd
import itertools
import urllib.request
import simplejson
import plotly.offline as offline
import plotly.plotly as py
import plotly.graph_objs as go
from math import sin, cos, sqrt, atan2, radians
from http import client


def parallelDistance(lat1, lat2):
    # Calculate the distance of the parallel span
    R = 6373.0 # approximate radius of earth in km
    dlon = 0
    dlat = abs(lat2 - lat1)
    a = sin(dlat / 2)**2 + cos(lat2) * cos(lat1) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    parallel_distance = R * c
    return parallel_distance

def meridianDistance(lat1, lon1, lat2, lon2):
    # Calculate the distance of the meridian span
    R = 6373.0 # approximate radius of earth in km
    dlon = abs(lon2 - lon1)
    dlat = 0
    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    meridian_distance = R * c
    return meridian_distance
    
def haversine(lat1, lon1, lat2, lon2):
    # Calculate the distance of the meridian span
    R = 6373.0 # approximate radius of earth in km
    dlon = abs(lon2 - lon1)
    dlat = abs(lat2 - lat1)
    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    meridian_distance = R * c
    return meridian_distance

def USGS10mElev(lat,lon):
    usgs = client.HTTPConnection('ned.usgs.gov')
    usgs.request('GET','/epqs/pqs.php?x=%.6f&y=%.6f&units=FEET&output=xml'% (lon, lat))
    result = usgs.getresponse()
    xml = result.read()
    if result.status == 200:
        return float(xml[xml.find(b'<Elevation>')+11:xml.find(b'</Elevation>')-1])
    else: return xml

# FIXME make raising layer exceptions into functions
layer_exception = Exception("Coordinate layer must be populated before additional layers can be stacked")

class Region:

    def __init__(self, name):
        self.name = name
        NW_lat = float(input("NW corner latitude: "))
        NW_lon = float(input("NW corner longitude: "))
        SE_lat = float(input("SE corner latitude: "))
        SE_lon = float(input("SE corner longitude: "))
        self.perim = (NW_lat, NW_lon, SE_lat, SE_lon)
        self.stepSize = 5
        self.Coords = pd.DataFrame()
        self.Elev = pd.DataFrame()

    # Creates a pandas DataFrame of the latitude/longitude coordinates for the
    # region. Step Size (stepSize) is in meters (great circle.)
    def add_CoordLayer(self, stepSize):
        self.stepSize = stepSize

        NW_lat = self.perim[0]
        NW_lon = self.perim[1]
        SE_lat = self.perim[2]
        SE_lon = self.perim[3]

        NW_lat_rad = radians(NW_lat)
        NW_lon_rad = radians(NW_lon)
        SE_lat_rad = radians(SE_lat)
        SE_lon_rad = radians(SE_lon)
 
        # Calculate the number of steps for the parallel span
        parallel_distance = parallelDistance(NW_lat_rad, SE_lat_rad) * 1000
        parallel_steps = parallel_distance / stepSize

        # Calculate the number of steps for the meridian span
        meridian_distance = meridianDistance(NW_lat_rad, NW_lon_rad, SE_lat_rad, SE_lon_rad) * 1000
        meridian_steps = meridian_distance / stepSize

        # N to S range
        parallelRange = np.linspace(SE_lat, NW_lat, parallel_steps)
        # E to W range
        meridianRange = np.linspace(NW_lon, SE_lon, meridian_steps)

        # Create 1D list of tuples with all unique lat/lon combos
        latLonTuples = list(itertools.product(parallelRange, meridianRange))

        # Convert 1D to 2D list for DataFrame
        latLonList2D = []
        rowList = []
        for tuples in latLonTuples:
            rowList += [tuples]
            if len(rowList) == len(meridianRange):
                latLonList2D += [rowList]
                rowList = []

        # Generate DataFrame
        coordMatrix = pd.DataFrame(latLonList2D)
        self.Coords = self.Coords.append(coordMatrix)

    # Scales a layer so that each cell is one distance unit apart and data
    # accuracy is explicit
    # TODO make sure querys are located at USGS data points
    # TODO make seperate attribute for each elevLayer type
    def block_ElevLayer(self):
        # If coordinate layer hasn't been populated, raise exception
        if self.Coords.empty:
            raise layer_exception

        elev_array = self.Elev.values
        elev_array = np.repeat(elev_array, self.stepSize, axis=0)
        elev_array = np.repeat(elev_array, self.stepSize, axis=1)
        self.Elev = pd.DataFrame(elev_array)

    # Creates a pandas DataFrame of the 2 dimensional elevation array for the region
    # TODO create seperate function for Google query, then a master function w kwarg for source
    def add_ElevLayer(self):
        # If coordinate layer hasn't been populated, raise exception
        if self.Coords.empty:
            raise layer_exception

        # Cycle through Coord layer to request elevations from Google's API
        row = 0
        elevList2D = []
        while row < self.Coords.shape[0]: 
            column = 0
            rowList = []
            while column < self.Coords.shape[1]:
                lat = (self.Coords.iloc[row][column][0])
                lon = (self.Coords.iloc[row][column][1])

                
                # Make request to Google API for elevation data
                # response = urllib.request.urlopen("https://maps.googleapis.com/maps/api/elevation/json?locations=" + lat + "," + lon + "&key=AIzaSyCehLK-fJxEZbT9Zej6kKLk8pTAz_iXkp8")
                # responseData = simplejson.load(response)
                # rowList += [responseData["results"][0]["elevation"]]
                rowList += [USGS10mElev(lat, lon)]
                column += 1            
            elevList2D += [rowList]
            row += 1

        # Generate DataFrame
        elevMatrix = pd.DataFrame(elevList2D)
        self.Elev = self.Elev.append(elevMatrix)

    # Creates a surface plot of the self.Elev data as an html file
    def ElevVis(self):
        # If coordinate layer hasn't been populated, raise exception
        if self.Coords.empty:
            raise layer_exception

        name = str(input("plot name:"))

        z_data = self.Elev

        data = [
            go.Surface(
                z=z_data.values
            )
        ]
        layout = go.Layout(
            title=name,
            autosize=False,
            width=1000,
            height=1000,
            margin=dict(
                l=65,
                r=50,
                b=65,
                t=90
            )
        )
        fig = go.Figure(data=data, layout=layout)
        offline.plot(fig, filename=(name + ".html"))
