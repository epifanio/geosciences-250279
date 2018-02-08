import re
import collections
from osgeo import gdal, osr
from episg import *
from itertools import zip_longest
import numpy as np

def getcoords(transects):
    if type(transects[0]) == tuple:
        transects = [i[0] for i in transects]
    coords = {}
    count = 0
    for group in grouper(transects[10:], 4, fillvalue=None):
        count += 1
        coords[count] = ','.join([','.join(i.strip().split(" ")).strip() for i in group[1:-1]]) 
    return coords

def getprofile(p):
    profile = np.asarray([[float(j) for j in x.split()] for x in p if '*' not in x])
    return profile


def grouper(iterable, n, fillvalue=None):
    args = [iter(iterable)] * n
    return zip_longest(*args, fillvalue=fillvalue)


def atoi(text):
    return int(text) if text.isdigit() else text


def natural_keys(text):
    """
    :param text:
    :return:
    from:
    http://stackoverflow.com/questions/5967500/how-to-correctly-sort-a-string-with-a-number-inside
    alist.sort(key=natural_keys) sorts in human order
    http://nedbatchelder.com/blog/200712/human_sorting.html
    (See Toothy's implementation in the comments)
    """
    return [ atoi(c) for c in re.split('(\d+)', text) ]

    
class DictTable(collections.OrderedDict):
    def _repr_html_(self):
        html = ["<table width=100%>"]
        for key, value in self.items():
            html.append("<tr>")
            html.append("<td>{0}</td>".format(key))
            html.append("<td>{0}</td>".format(value))
            html.append("</tr>")
        html.append("</table>")
        return ''.join(html)
    
    
def string2list(command):
    return command.decode().strip().split("\n")

def list2table(env, sep, sort=True):
    env = list(env)
    if sort:
        env.sort(key=natural_keys)
    return DictTable(collections.OrderedDict((x.split(sep)[0].strip(), str(x.split(sep)[1].strip())) for x in env))

def list2dict(command, sep='=', sort=True, ):
    env = command.decode().strip().replace("'", '').replace(";", "")
    if env.count('\n') >= 2:
        env = env.split('\n')
    else:
        env = env.split(' ')
    if sort:
        env.sort(key=natural_keys)
    return DictTable(collections.OrderedDict((x.split(sep)[0].strip(), str(x.split(sep)[1].strip())) for x in env))

def findEPSG(self, epsg='/usr/share/proj/epsg', searchin='title', searchfor=[], output='c'):
    epsgdata = guioption(epsg, searchin)
    candidates = [title for title in list(epsgdata) if all(target in title for target in searchfor)]
    for match in candidates:
        print(match, ':', rep3(epsg, searchin, match, output) )

def getbounds(gdaldata, cellsize=False):
    datafile = gdal.Open(gdaldata)
    cols = datafile.RasterXSize
    rows = datafile.RasterYSize
    geoinformation = datafile.GetGeoTransform()
    w = geoinformation[0]
    n = geoinformation[3]
    x_size = geoinformation[1]
    y_size = geoinformation[5]
    projInfo = datafile.GetProjection()
    spatialRef = osr.SpatialReference()
    spatialRef.ImportFromWkt(projInfo)
    spatialRefProj = spatialRef.ExportToProj4()
    if spatialRef.GetUTMZone() < 30:
        e = w-(cols*y_size)
    else:
        e = w+(cols*y_size)
    s = n-(rows*x_size)
    if cellsize:
        return x_size, y_size
    return {'s': s, 'n': n, 'w': w, 'e': e}