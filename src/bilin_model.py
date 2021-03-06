#
# MODULE FOR BILINMODEL CLASS, USED FOR BUILDING A BILINEARLY INTERPOLATED MODEL
# OF A TERRAIN SURFACE. BILINMODEL IS A SUBCLASS OF SUBREGION.
#
# Author: Cory Kennedy
#
# Date: 7/6/2018

import numpy as np
import pandas as pd
from scipy.interpolate import interp2d
import subregion

class BilinModel(subregion.SubRegion):

    def __init__(self, NW_corner, SE_corner, data='10m', **kwargs):
        '''
            NW_corner, SE_corner parameters are lat/lon tuples
	'''
        self.SubRegion = subregion.SubRegion(NW_corner, SE_corner, data=data)
        X = self.SubRegion.LON_ARR # array of longitude vals W > E
        Y = self.SubRegion.LAT_ARR # array of latitude vals N > S
        Z = self.SubRegion.elev.values # elevation vals as a 2d array

        # Build the function for bilinear interpolation
        newfunc = interp2d(X, Y, Z, kind='linear')

        # Domain space now has 10x the values within the same region
        xnew = np.linspace(np.amin(X), np.amax(X), X.shape[0]*10)
        ynew = np.linspace(np.amax(Y), np.amin(Y), Y.shape[0]*10)

        # Get bilin interpolated 2d array from function
        z_bilin = newfunc(xnew, ynew)
        self.LAT_ARR = np.flip(ynew, 0) # flip y axis after interpolation
        self.LON_ARR = xnew
        self.elev = pd.DataFrame(z_bilin, index=self.LAT_ARR, columns=self.LON_ARR)
