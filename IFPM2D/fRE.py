import numpy as np

def calcf(dP : float, u: float, Lrho : float = 6.4e3) -> float:
    return -dP / (Lrho*u**2)

def calcRePrim(u : float, nu: float = 1e-6)-> float:
    return u / nu

def readDPfromFile(inletPath : str, outletPath : str) -> float:
        inletFile   = open(inletPath, 'r')
        outletFile  = open(outletPath, 'r')

        inletLastLine = inletFile.readlines()[-1]
        inletPressure = inletLastLine.split()[-1]
        inletPressure = float(inletPressure)

        outletLastLine = outletFile.readlines()[-1]
        outletPressure = outletLastLine.split()[-1]
        outletPressure = float(outletPressure)

        return inletPressure - outletPressure


postProcessPath = "/home/damian/MGR/2D/OF_Model/postProcessing/"
postProcessAvDat = "/0/surfaceFieldValue.dat"
outletPostProcessPath = postProcessPath + "OutletPAverage" + postProcessAvDat
inletPostProcessPath = postProcessPath + "InletPAverage" + postProcessAvDat

print(outletPostProcessPath)
print(inletPostProcessPath)