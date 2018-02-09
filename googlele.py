import numpy as np
import urllib.request
import simplejson

#.00005 or 1/20000 increments
topLeftLatLon = [39.724788, -105.154405]
botRightLatLon = [39.721670, -105.151328]

# N to S range
parallelRange = (np.arange(botRightLatLon[0], topLeftLatLon[0], (1/20000)))

# E to W range
meridianRange = (np.arange(topLeftLatLon[1], botRightLatLon[1], (1/20000)))

pair = np.zeros(2)
domain = np.zeros((3,np.shape(parallelRange)[0],np.shape(meridianRange)[0]))

m = 0 #Rows
n = 0 #Columns

while m < np.shape(meridianRange)[0]:
    n = 0 #Columns
    while n < np.shape(parallelRange)[0]:
        domain.T[m][n][1] = meridianRange[m]
        domain.T[m][n][0] = parallelRange[n]

        # long = str(meridianRange[m])
        # lat = str(parallelRange[n])

        # response = urllib.request.urlopen("https://maps.googleapis.com/maps/api/elevation/json?locations=" + str(lat) + "," + str(long) + "&key=AIzaSyCehLK-fJxEZbT9Zej6kKLk8pTAz_iXkp8")
        # data = simplejson.load(response)
        domain.T[m][n][2] = 3 # data["results"][0]["elevation"]

        n = n + 1
    m = m + 1

print(np.shape(domain.T))
