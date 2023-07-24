from __future__ import print_function 
from ipygrass.episg import *
import grass.script as grass
from collections import OrderedDict
import uuid
import sys
import os
import operator
import numpy as  np
import matplotlib.pyplot as plt
from grass.script import array as garray
from IPython.display import display, Image
from ipywidgets import interact, interactive, fixed
from ipywidgets import widgets
from IPython.display import clear_output
from osgeo import gdal, osr
import re
import collections
from spectral import *
import spectral.io.envi as envi
spectral.settings.show_progress = False
import warnings
from ipygrass.gisutils import grouper

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


class DictTable1(dict):
    # Overridden dict class which takes a dict in the form {'a': 2, 'b': 3},
    # and renders an HTML Table in IPython Notebook.
    def _repr_html_(self):
        html = ["<table width=100%>"]
        for key, value in self.items():
            html.append("<tr>")
            html.append("<td>{0}</td>".format(key))
            html.append("<td>{0}</td>".format(value))
            html.append("</tr>")
        html.append("</table>")
        return ''.join(html)
    
    
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


def spectralPlot(c):
    for i in range(c.shape[0]):
        plt.plot(c[i])


def list2dict2(command, sep='=', htable=True):
    l = [(x.split(sep)[0].strip(), str(''.join(x.split(sep)[1:]).strip())) for x in command]
    if htable:
        try:
            od = OrderedDict(l)
            return DictTable(od) 
        except IndexError:
            if sep == '=':
                sep = ':'
            else:
                sep = '='
            try:
                od = OrderedDict(l)
                return DictTable(od) 
            except IndexError:
                message = 'WORNING: IndexError, probably using the wrong separator "%s" for: \n %s' % (sep, command)
                warnings.warn(message)
            #return None
    if not htable:
        return l    
        
class General(object):

    
    def run_command(*args, **kwargs):
        return grass.run_command(*args, **kwargs)


    def read_multifeature(lista, htable=False):
        out = [i for i in grouper(lista, 17, fillvalue='  ')] 
        if htable:
            out = [DictTable(i) for i in out]
        return out
    
    def read_command(*args, **kwargs):
        if 'sep' in list(kwargs.keys()):
            sep = kwargs['sep']
            kwargs.pop('sep')
        else:
            sep = '='
        if 'sort' in list(kwargs.keys()):
            sort = True
            kwargs.pop('sort')
        else:
            sort = False
        if 'htable' in list(kwargs.keys()):
            htable = True
            kwargs.pop('htable')
        else:
            htable=False
        if 'std' in list(kwargs.keys()):
            std = True
            kwargs.pop('std')
        else:
            std=False
        command = grass.read_command(*args, **kwargs)

        if std:
            command = command.strip().split('\n')
            return command
        env = command.strip().replace("'", '').replace(";", "")
        if env.count('\n') >= 2:
            env = env.split('\n')
        else:
            env = env.split(' ')
        if sort:
            env.sort(key=natural_keys)
        return list2dict2(env, sep=sep, htable=htable)

    
    def gisenv(self):
        return self.list2dict(grass.read_command('g.gisenv'))

    def region(self, res=None, raster=None, region=None, save=None, bounds=None, flags='ap'):
        if bounds:
            s = bounds['s']
            n = bounds['n']
            w = bounds['w']
            e = bounds['e']
            if not res:
                if save:
                    grass.run_command('g.region', s=str(s), n=str(n), w=str(w), e=str(e), flags=flags, save=save, overwrite=True) 
            if res:
                if save:
                    grass.run_command('g.region', s=str(s), n=str(n), w=str(w), e=str(e), flags=flags, res=res, save=save, overwrite=True) 
            # return self.list2dict(grass.read_command('g.region', flags='p'), sep=":")
        if res == 'default':
            nsres = float(self.list2dict(grass.read_command('g.region', flags=flags), sep=":")['nsres'])
            ewres = float(self.list2dict(grass.read_command('g.region', flags=flags), sep=":")['ewres'])
            defaultres = (nsres+ewres)/2.
            if save:
                grass.run_command('g.region', flags=flags, res=defaultres, save=save, overwrite=True)
            grass.run_command('g.region', flags=flags, res=defaultres)
            # return self.list2dict(grass.read_command('g.region', flags=flags, res=defaultres), sep=": ")
        if raster and not res:
            if save:
                grass.run_command('g.region', flags=flags, raster=raster, save=save, overwrite=True)
            # return self.list2dict(grass.read_command('g.region', flags=flags, raster=raster), sep=": ")
        if res and not raster and not bounds:
            if save:
                grass.run_command('g.region', flags=flags, res=res, save=save, overwrite=True)
            grass.run_command('g.region', flags=flags, res=res, overwrite=True)
            # return self.list2dict(grass.read_command('g.region', flags=flags, res=res), sep=": ")
        if raster and res:
            if save:
                grass.run_command('g.region', flags=flags, raster=raster, res=res, save=save, overwrite=True)
            # return self.list2dict(grass.read_command('g.region', flags=flags, raster=raster, res=res), sep=": ")
        if not res and not raster and not bounds:
            if save:
                grass.run_command('g.region', flags=flags, save=save, overwrite=True)
            # return self.list2dict(grass.read_command('g.region', flags=flags), sep=": ")
        if region:
            grass.run_command('g.region', flags=flags, region=region)
        return self.list2dict(grass.read_command('g.region', flags='p'), sep=": ")

    def glist(self, type='raster'):
        return self.string2list(grass.read_command('g.list', type=type))
    
    def list2dict(self, command, sep='=', sort=True, dict=True):
        env = command.strip().replace("'", '').replace(";", "")
        if env.count('\n') >= 2:
            env = env.split('\n')
        else:
            env = env.split(' ')
        if sort:
            env.sort(key=natural_keys)
        if dict:
            return DictTable(OrderedDict((x.split(sep)[0].strip(), str(x.split(sep)[1].strip())) for x in env))
        else:
            return [(x.split(sep)[0].strip(), str(x.split(sep)[1].strip())) for x in env]
    
    def string2list(self, command):
        return command.strip().split("\n")
    
    def grasslayercheck(self, layer, type='raster', verbose=False):
        grasslayers = self.glist(type=type)
        # !g.list raster
        if layer not in grasslayers:
            if verbose:
                print("grass layer: %s not found" % layer)
            return False
        else:
            return True

    def grasslayerscheck(self, layers, verbose=False):
        if all(self.grasslayercheck(layer) for layer in layers):
            return True
        else:
            matchinglayers = [layer for layer in layers if self.grasslayercheck(layer)]
            missinglayers = len(layers) - len(matchinglayers)
            if verbose:
                print('Not all the layers where found, Num layer missing: %s \n Matching layers: %s' % (missinglayers, matchinglayers))
            return False
        
    def findEPSG(self, epsg='/usr/share/proj/epsg', searchin='title', searchfor=[], output='c'):
        epsgdata = guioption(epsg, searchin)
        candidates = [title for title in list(epsgdata) if all(target in title for target in searchfor)]
        for match in candidates:
            print(match, ':', rep3(epsg, searchin, match, output) )

    def listloc2(self):
        return DictTable(
        OrderedDict((i,
        sorted(
            [k for k in str(os.listdir(os.path.join(os.environ['GISDBASE'],
                                                    i))).replace('[',
                                                                 '').replace(']',
                                                                             '').replace("'",
                                                                                         "").split(", ")])
        ) for i in sorted(os.listdir(os.environ['GISDBASE']))))

    def listloc3(self):
        locdict = OrderedDict()
        for i in sorted(os.listdir(os.environ['GISDBASE'])):
            if os.path.isdir(os.path.join(os.environ['GISDBASE'], i)):
                if 'PERMANENT' in os.listdir(os.path.join(os.environ['GISDBASE'], i)):
                    locdict[i] = sorted([k for k in str(os.listdir(os.path.join(os.environ['GISDBASE'],
                                                                                i))).replace('[',
                                                                                             '').replace(']',
                                                                                                         '').replace(
                        "'",
                        "").split(", ")])
        return DictTable(locdict)


    def listloc(self):
        return DictTable(OrderedDict((i, sorted([k for k in os.listdir(os.path.join(os.environ['GISDBASE'], i)) if os.path.isdir(os.path.join(os.environ['GISDBASE'], i, k))])) for i in sorted(os.listdir(os.environ['GISDBASE']))))

    
    def selectraster(self):
        self.rasterlayers=self.glist()
        self.rasterlist_options = sorted(self.rasterlayers)
        self.rasterlist = widgets.Dropdown(
            options=self.rasterlist_options,
            value=self.rasterlist_options[-1],
            description='Select Raster Layer:',
            )
        self.rasterlist.observe(self.on_rasterlayer_change, names='value')
        display(self.rasterlist)
        return self.rasterlist

    def on_rasterlayer_change(self, rasterlayername):
        print(rasterlayername['new'])
        grass.run_command('g.region', flags='ap', raster=rasterlayername['new'])
        # region = grass.read_command('g.region', flags='ap', raster=rasterlayername['new'])
        clear_output()
        display(self.list2dict(grass.read_command('g.region', flags='p'), sep=": "))
        return self.rasterlist

    def wizard(self):
        self.locations = self.listloc()
        self.location_options = sorted(list(self.locations.keys()))
        
        self.locationlist = widgets.Dropdown(
            options=self.location_options,
            value=self.location_options[-1],
            description='Set Location:',
            )

        self.maplist = widgets.Dropdown(
            options=self.locations[self.locationlist.value],
            value=list(self.locations[self.locationlist.value])[-1],
            description='Set Mapset:',
            )
        self.locationlist.observe(self.on_locations_change, names='value')
        self.maplist.observe(self.on_mapset_change, names='value')
        # display(self.locationlist)
        # display(self.maplist)
        return [self.locationlist, self.maplist]

    def on_locations_change(self, locationame):
        print(self.locationlist.value)
        grass.run_command('g.mapset', location=self.locationlist.value, mapset='PERMANENT')
        self.maplist.options=self.locations[self.locationlist.value]
        clear_output()
        display(self.maplist.value)
        display(self.gisenv())        
    
    def on_mapset_change(self, mapset):
        print(self.maplist.value)
        grass.run_command('g.mapset', location=self.locationlist.value, mapset=self.maplist.value)
        clear_output()
        display(self.gisenv())

    
class Raster(object):
    def ingdal(self, input, output, flags='oe', overwrite=True):
        grass.run_command('r.in.gdal', input=input, output=output, flags=flags, quiet=True, overwrite=overwrite)
        
    def makeprofiles(coords):
        layer=coords['layer']
        resolution=coords['resolution']
        coordinates = coords['coordinates']
        p = grass.read_command('r.profile', 
                               input=layer, 
                               coordinates=coordinates, 
                               resolution=resolution, 
                               flags='g').strip().split('\n')
        return p
        
        
    def univar(self, input, flags="ge"):
        if General().grasslayercheck(input):
            univar = grass.read_command('r.univar', map=input, flags=flags)
            return General().list2dict(univar, sep='=')
        else:
            print('input map %s not found' % input)
        
    def mapcalc(self):
        pass

    def fillnull(self, layername, avg=9, output='None'):
        if not output:
            output = layername+'_nullfilled'
        try:
            grass.run_command('r.mask', flags='r')
        except ValueError:
            print('no mask to remove')
        tmporary_unique_filename = str(uuid.uuid4())
        grass.run_command('r.neighbors', input=layername, output=tmporary_unique_filename, 
                          size=9, method='average', overwrite='overwrite')
        grass.run_command('r.mask', raster=tmporary_unique_filename)
        grass.run_command('r.fillnulls', input=layername, output=output, 
                          quiet=True, overwrite=True) 
        grass.run_command('r.colors.matplotlib', flags='e', map=output, color='RdYlBu_r')
        grass.run_command('r.null', map=output, setnull=0)
        grass.run_command('g.remove', type='raster', name=tmporary_unique_filename, flags='f')
        grass.run_command('r.mask', flags='r')

    def info(self, map, flags='r'):
        if General().grasslayercheck(map):
            return General().list2dict(grass.read_command('r.info',
                                                          map=map,
                                                          flags=flags),
                                       sep="=")
        else:
            print('input map %s not found' % input)

    def rastack(self, layers):
        if all(General().grasslayercheck(layer) for layer in layers):
            dim=len(layers)
            rl = garray.array()
            imagegroup = np.empty((rl.shape[0], rl.shape[1], dim), dtype='float')
            for i, v in enumerate(layers):
                rl.read(v)
                imagegroup[:, :, i] = rl
            return imagegroup
        else:
            matchinglayers = [layer for layer in layers if General().grasslayercheck(layer)]
            # set(layers) & set(matchinglayers)
            missinglayers = len(layers) - len(matchinglayers)
            print('Not all the layers where found, Num layer missing: %s \n Matching layers: %s' % (missinglayers,
                                                                                                    matchinglayers))
        
    def cellsize(self, map):
        if General().grasslayercheck(map):
            nsew_res = grass.read_command('g.region', raster=map, flags='m').strip().split('\n')[6:8]
            return np.mean([float(i.split('=')[1]) for i in nsew_res])
        else:
            print('input map %s not found' % map)
    
    def zoffset(self, map1, map2, offset):
        layers = [map1, map2]
        if all(General().grasslayercheck(layer) for layer in layers):
            grass.run_command('r.mapcalc',
                              expression='%s = %s+abs(%s)' % (map1, map2, offset),
                              overwrite=True)
        else:
            matchinglayers = [layer for layer in layers if General().grasslayercheck(layer)]
            # set(layers) & set(matchinglayers)
            missinglayers = len(layers) - len(matchinglayers)
            print('Not all the layers where found, Num layer missing: %s \n Mathing layers: %s' % (missinglayers,
                                                                                                   matchinglayers))

    def hypso2(self, grasslayer, report=True, flags='ac'):
        if not General().grasslayercheck(grasslayer):
            print('Input map %s not found' % grasslayer)
            return
        grass.run_command('r.hypso', map=grasslayer, flags=flags, image=grasslayer)

    def hypso(self, grasslayer, report=True, plot=True):
        if not General().grasslayercheck(grasslayer):
            print('Input map %s not found' % grasslayer)
            return
        self.grasslayer=grasslayer
        stats = grass.read_command('r.stats',
                                   input=grasslayer,
                                   sep='space',
                                   nv='*',
                                   nsteps='255',
                                   flags='inc').split('\n')[:-1]

        res = self.cellsize(grasslayer)

        zn = np.zeros((len(stats), 6), float)
        kl = np.zeros((len(stats), 2), float)
        prc = np.zeros((9, 2), float)

        for i in range(len(stats)):
            if i == 0:
                zn[i, 0], zn[i, 1] = map(float, stats[i].split(' '))
                zn[i, 2] = zn[i, 1]
            else:
                zn[i, 0], zn[i, 1] = map(float, stats[i].split(' '))
                zn[i, 2] = zn[i, 1] + zn[i-1, 2]
        
        totcell = sum(zn[:,1])

        for i in range(len(stats)):
            zn[i, 3] = 1 - (zn[i, 2] / sum(zn[:, 1]))
            zn[i, 4] = zn[i, 3] * (((res**2)/1000000)*sum(zn[:, 1]))
            zn[i, 5] = ((zn[i, 0] - min(zn[:, 0])) / (max(zn[:, 0]) - min(zn[:, 0])))
            kl[i, 0] = zn[i, 0]
            kl[i, 1] = 1 - (zn[i, 2] / totcell)
        
        # quantiles
        prc[0, 0], prc[0, 1] = self._findintH(kl, 0.025), 0.025
        prc[1, 0], prc[1, 1] = self._findintH(kl, 0.05), 0.05
        prc[2, 0], prc[2, 1] = self._findintH(kl, 0.1), 0.1
        prc[3, 0], prc[3, 1] = self._findintH(kl, 0.25), 0.25
        prc[4, 0], prc[4, 1] = self._findintH(kl, 0.5), 0.5
        prc[5, 0], prc[5, 1] = self._findintH(kl, 0.75), 0.75
        prc[6, 0], prc[6, 1] = self._findintH(kl, 0.9), 0.9
        prc[7, 0], prc[7, 1] = self._findintH(kl, 0.95), 0.95
        prc[8, 0], prc[8, 1] = self._findintH(kl, 0.975), 0.975
        
        if plot:
            self._plot(zn[:,3],
                       zn[:,5],
                       self.grasslayer+'_Hypsometric.png',
                       '-',
                       '$\\frac{A_i}{A}$',
                       '$\\frac{Z_i}{Z_{max}}$',
                       'Hypsometric Curve')
        
        if report:
            print("===========================")
            print("Hypsometric | quantiles"    )
            print("===========================")
            print('%.0f' %self._findintH(kl,0.025) , "|", 0.025)
            print('%.0f' %self._findintH(kl,0.05) , "|", 0.05)
            print('%.0f' %self._findintH(kl,0.1) , "|", 0.1)
            print('%.0f' %self._findintH(kl,0.25) , "|", 0.25)
            print('%.0f' %self._findintH(kl,0.5) , "|", 0.5)
            print('%.0f' %self._findintH(kl,0.75) , "|", 0.75)
            print('%.0f' %self._findintH(kl,0.9) , "|", 0.9)
            print('%.0f' %self._findintH(kl,0.975) , "|", 0.975)
            print("===========================")
            print("Tot. cells", "|", totcell)
            print("===========================")
            print("Cell size [m]", "|", res)
            print("===========================")

    def _findintH(self, kl,f):
        Xf = np.abs(kl-f)
        Xf = np.where(Xf==Xf.min())
        Xf = int(Xf[0])
        z1 = kl[Xf][0] 
        z2 = kl[Xf-1][0]
        f1 = kl[Xf][1] 
        f2 = kl[Xf-1][1] 
        z = z1 + ((z2 - z1) / (f2 - f1)) * (f - f1)
        return z

    def _plot(self, x, y, image, type, xlabel, ylabel, title):
        plt.plot(x, y, type)
        plt.ylabel(ylabel)
        plt.xlabel(xlabel)
        plt.xlim(min(x), max(x))
        plt.ylim(min(y), max(y))
        plt.title(title)
        plt.grid(True)
        plt.savefig(image)
        try:
            plt.show()
        except:
            print("You may need to run: %matplotlib inline")
            print("the plot will be saved in %s" % image)
        #plt.savefig(image)
        plt.close('all') 

    def width(self, grasslayer, report=False, plot=False):
        if not General().grasslayercheck(grasslayer):
            print('Input map %s not found' % grasslayer)
            return
        self.grasslayer=grasslayer
        stats = grass.read_command('r.stats', 
                                   input=grasslayer, 
                                   sep='space', 
                                   nv='*', 
                                   nsteps='255', 
                                   flags='Anc').split('\n')[:-1]

        res = self.cellsize(grasslayer)

        zn = np.zeros((len(stats), 4), float)
        kl = np.zeros((len(stats), 2), float)
        prc = np.zeros((9, 2), float)

        for i in range(len(stats)):
            if i == 0:
                zn[i, 0],  zn[i, 1] = map(float, stats[i].split(' '))
                zn[i, 1] = zn[i, 1]
                zn[i, 2] = zn[i, 1] * res
            if i != 0:
                zn[i, 0],  zn[i, 1] = map(float, stats[i].split(' '))
                zn[i, 2] = zn[i, 1] + zn[i-1, 2]
                zn[i, 3] = zn[i, 1] * (res**2)
            
        totcell = sum(zn[:, 1])
        totarea = totcell * (res**2)
        maxdist = max(zn[:, 0])
 
        for i in range(len(stats)):
            kl[i, 0] = zn[i, 0]
            kl[i, 1] = zn[i, 2] / totcell

        for i in range(len(stats)):
            kl[i, 0] = zn[i, 0]
            kl[i, 1] = zn[i, 2] / totcell

        # quantiles
        prc[0, 0], prc[0,1] = self._findintW(kl, 0.05), 0.05
        prc[1, 0], prc[1,1] = self._findintW(kl, 0.15), 0.15
        prc[2, 0], prc[2,1] = self._findintW(kl, 0.3), 0.3
        prc[3, 0], prc[3,1] = self._findintW(kl, 0.4), 0.4
        prc[4, 0], prc[4,1] = self._findintW(kl, 0.5), 0.5
        prc[5, 0], prc[5,1] = self._findintW(kl, 0.6), 0.6
        prc[6, 0], prc[6,1] = self._findintW(kl, 0.7), 0.7
        prc[7, 0], prc[7,1] = self._findintW(kl, 0.85), 0.85
        prc[8, 0], prc[8,1] = self._findintW(kl, 0.95), 0.95
        
        if plot:
            self._plot(zn[:, 0], zn[:, 3], self.grasslayer+'_width_function.png', '-', 'x', 'W(x)', 'Width Function')
            
        if report:
            print("===========================")
            print("Width Function | quantiles")
            print("===========================")
            print('%.0f' %self._findintW(kl,0.05), "|", 0.05)
            print('%.0f' %self._findintW(kl,0.15), "|", 0.15)
            print('%.0f' %self._findintW(kl,0.3), "|", 0.3)
            print('%.0f' %self._findintW(kl,0.4), "|", 0.4)
            print('%.0f' %self._findintW(kl,0.5), "|", 0.5)
            print('%.0f' %self._findintW(kl,0.6), "|", 0.6)
            print('%.0f' %self._findintW(kl,0.7), "|", 0.7)
            print('%.0f' %self._findintW(kl,0.85), "|", 0.85)
            print('%.0f' %self._findintW(kl,0.95), "|", 0.95)
            print("===========================")
            print("Tot. cells", "|", totcell)
            print("===========================")
            print("Tot. area", "|", totarea)
            print("===========================")
            print("Max distance", "|", maxdist)
            print("===========================")            

    def _findintW(self, kl, f):
        Xf = np.abs(kl-f); Xf = np.where(Xf==Xf.min())
        z1 = kl[int(Xf[0])][0]
        z2 = kl[int(Xf[0]-1)][0]
        f1 = kl[int(Xf[0])][1]
        f2 = kl[int(Xf[0]-1)][1]
        z = z1 + ((z2 - z1) / (f2 - f1)) * (f - f1)
        return z

    def getflatarray(self, map):
        data = garray.array()
        data.read(map, null=np.nan)
        data = data.flatten()
        data = data[~np.isnan(data)]
        return data

    def histo(self, map, stats=False, color='Greys_r'):
        if General().grasslayercheck(map):
            data = self.getflatarray(map)
            plt.style.use('ggplot')
            cm = plt.cm.get_cmap(color)
            Y, X = np.histogram(data, 50)
            x_span = X.max()-X.min()
            c = [cm(((x-X.min())/x_span)) for x in X]
            plt.bar(X[:-1], Y, color=c, width=X[1]-X[0])
            plt.grid(True)
            image = map+'_Histogram.png'
            plt.savefig(image)
            try:
                plt.show()
            except ValueError:
                print("You may need to run: %matplotlib inline")
                print("the plot will be saved in %s" % image)
            plt.close('all')
            if stats:
                mapstats = {'Max': np.nanmax(data),
                            'Min': np.nanmin(data),
                            'Median': np.nanmedian(data),
                            'Mean': np.nanmean(data),
                            'Percentile': np.nanpercentile(data, [0, 25, 50, 75, 100]),
                            'StD': np.nanstd(data),
                            'Variance': np.nanvar(data)}
                display(DictTable(mapstats))
        else:
            print('map %s not found' % map)

    def catover(self, base, cover, output=None, clean=False):
        # from https://www.getdatajoy.com/examples/python-plots/box-plots
        layers = [base, cover]
        if all(General().grasslayercheck(layer) for layer in layers):
            result=OrderedDict()
            # for i[0].strip() in grass.read_command('r.category', map=cover).decode().strip().replace('\t',' ').split('\n'):
            for i in [j.split(' ')[0].strip() for j in grass.read_command('r.category', map=cover).strip().replace('\t', ' ').split('\n')]:
                if not output:
                    outputname=base+'_'+i
                else:
                    outputname=output+'_'+i
                grass.run_command('r.mapcalc', 
                                  expression = '%s=if(%s==%s, %s, null())' % (outputname, cover, i, base), 
                                  overwrite=True)
                data = self.getflatarray(outputname)
                result[outputname] = data
                if clean:
                    pattern=output+'_*'
                    grass.run_command('g.remove', type='raster', pattern=pattern, flags='f')
            return result
        else:
            matchinglayers = [layer for layer in layers if General().grasslayercheck(layer)]
            # set(layers) & set(matchinglayers)
            missinglayers = len(layers) - len(matchinglayers)
            print('Not all the layers where found, Num layer missing: %s \n Mathing layers: %s' % (missinglayers, matchinglayers) )

    def boxplot(self, data, save=True, plot=True):
        if type(data) != collections.OrderedDict:
            print('bad input')
            return
        else:
            import pandas as pd
            df = pd.DataFrame(dict([(k, pd.Series(v)) for k, v in data.items()]))
            print(df)
        plt.style.use('ggplot')
        names = list(data.keys())
        locations = [i for i in range(len(names))]
        box_colours = ['SkyBlue' for i in range(len(names))]

        dataset = [data[i] for i in data]

        plt.figure()
        plot2 = plt.boxplot(dataset, 
                            widths=0.7,
                            notch=True,             # adds median notch
                            positions=locations,    # boxes locations
                            patch_artist=True,
                            )
        plt.grid(axis='y',          # set y-axis grid lines
                 linestyle='--',     # use dashed lines
                 which='major',      # only major ticks
                 color='grey',  # line colour
                 alpha=0.7)          # make lines semi-translucent

        for box, colour in zip(plot2['boxes'], box_colours):
            plt.setp(box, color='SkyBlue', 
                     linewidth=1.5, 
                     facecolor=colour)
    
        plt.setp(plot2['whiskers'], color='DarkMagenta', linewidth=1.5)
        plt.setp(plot2['caps'], color='DarkMagenta', linewidth=1.5)
        plt.setp(plot2['fliers'], color='OrangeRed', marker='o', markersize=5)
        plt.setp(plot2['medians'], color='OrangeRed', linewidth=1.5)

        plt.xticks(locations,               # tick marks
                   names,                   # labels
                   rotation='vertical')     # rotate the labels

        plt.ylabel('Data')                  # y-axis label
        plt.title('Box and Whisker Plots')  # plot title
        plt.grid(True)
        if save:
            image = 'boxplot.png'
            plt.savefig(image)
        if plot:
            plt.show()                          # render the plot
        
    def proj(self, layer, location, mapset, reproj=False, flags=False):
        
        if flags == 'p':
            sep = ':'
        if flags == 'g':
            sep = '='
        if flags:
            return General().list2dict(
            grass.read_command('r.proj',
                               input=layer,
                               location=location,
                               mapset=mapset,
                               flags=(flags)
                               ),
                sep=sep, sort=False)
        if reproj:
            region=General().list2dict(
            grass.read_command('r.proj', 
                               input=layer,
                               location=location,
                               mapset=mapset, 
                               flags=('g')
                              ), 
                sep='=')
            grass.run_command('g.region', 
                              n=region['n'], 
                              s=region['s'], 
                              w=region['w'], 
                              e=region['e'], 
                              rows=region['rows'], 
                              cols=region['cols'])
            
            grass.run_command('r.proj', 
                              input=layer, 
                              location=location, 
                              mapset=mapset, 
                              memory=800, 
                              overwrite=True)
        
    def makemorfo(self, input, nnwin=9, pmwin=15,
                  st=0.1,
                  ct=0.0001,
                  exp=0.0,
                  zs=1.0,
                  resolution=None, overwrite=True, remove=False):
        r_elevation = input
        if resolution is not None:
            grass.run_command('g.region', rast = r_elevation, flags = 'ap')
        else :
            grass.run_command('g.region', rast = r_elevation, res=resolution, flags = 'ap')
        suffix = str(r_elevation)+'_'
        xavg = suffix+'avg'
        xmin = suffix+'min'
        xmax = suffix+'max'
        xslope = suffix+'slope'
        xprofc = suffix+'profc'
        xcrosc = suffix+'crosc'
        xminic = suffix+'minic'
        xmaxic = suffix+'maxic'
        xlongc = suffix+'longc'
        xer = suffix+'er'
        img = [suffix+'avg',
               suffix+'min',
               suffix+'max',
               suffix+'er',
               suffix+'slope',
               suffix+'profc',
               suffix+'crosc',
               suffix+'minic',
               suffix+'maxic',
               suffix+'longc']
        if remove is True:
            rast = '%s,%s,%s,%s,%s,%s,%s,%s,%s' % (xavg, xmin, xmax, xslope, xprofc, xcrosc, xminic, xmaxic, xlongc)
            grass.run_command('g.remove',
                              type='rast',
                              name=rast,
                              flags='f')
        else:
            grass.run_command('r.neighbors',
                              input=r_elevation,
                              output=xavg,
                              size=nnwin,
                              method='average',
                              overwrite=overwrite)
            print("average done")
            grass.run_command('r.neighbors',
                              input=r_elevation,
                              output=xmin,
                              size=nnwin,
                              method='minimum',
                              overwrite=overwrite)
            print("minimum done")
            grass.run_command('r.neighbors',
                              input=r_elevation,
                              output=xmax,
                              size=nnwin,
                              method='maximum',
                              overwrite=overwrite)
            print("maximum done")
            grass.run_command('r.mapcalc',
                              expression='%s = 1.0 * (%s - %s)/(%s - %s)' % (xer, xavg, xmin, xmax, xmin),
                              overwrite=True)
            # !r.fillnulls input={xer} output={xer} --o --q
            print("er done")

            grass.run_command('r.param.scale',
                              input=r_elevation,
                              output=xslope,
                              size=pmwin,
                              slope_tolerance=st,
                              curvature_tolerance=ct,
                              method='slope',
                              exponent=exp,
                              zscale=zs,
                              overwrite=True)
            print("slope done")
            grass.run_command('r.param.scale',
                              input=r_elevation,
                              output=xprofc,
                              size=pmwin,
                              slope_tolerance=st,
                              curvature_tolerance=ct,
                              method='profc',
                              exponent=exp,
                              zscale=zs,
                              overwrite=True)
            print("profc done")
            grass.run_command('r.param.scale',
                              input=r_elevation,
                              output=xcrosc,
                              size=pmwin,
                              slope_tolerance=st,
                              curvature_tolerance=ct,
                              method='crosc',
                              exponent=exp,
                              zscale=zs,
                              overwrite=True)
            print("crosc done")
            grass.run_command('r.param.scale',
                              input=r_elevation,
                              output=xminic,
                              size=pmwin,
                              slope_tolerance=st,
                              curvature_tolerance=ct,
                              method='minic',
                              exponent=exp,
                              zscale=zs,
                              overwrite=True)
            print("minic done")
            grass.run_command('r.param.scale',
                              input=r_elevation,
                              output=xmaxic,
                              size=pmwin,
                              slope_tolerance=st,
                              curvature_tolerance=ct,
                              method='maxic',
                              exponent=exp,
                              zscale=zs,
                              overwrite=True)
            print("maxic done")
            grass.run_command('r.param.scale',
                              input=r_elevation,
                              output=xlongc,
                              size=pmwin,
                              slope_tolerance=st,
                              curvature_tolerance=ct,
                              method='longc',
                              exponent=exp,
                              zscale=zs,
                              overwrite=True)
            print("longc done")
            vrange = grass.read_command('r.info', map=xslope, flags='r')
            #if sys.version_info.major >= 3:
            #    vrange = vrange.decode()
            vmin = vrange.strip().split('\n')[0].split('=')[1]
            vmax = vrange.strip().split('\n')[1].split('=')[1]
            grass.run_command('r.mapcalc', expression='%s = (%s/%s)' % (xslope, xslope, vmax), overwrite=True)
            print("xslope done")
        return img

    def writeGarray(self, m, mapname):
        clust = garray.array()
        clust[...] = m
        grass.run_command('g.remove', type='raster', name=mapname)
        clust.write(mapname)
        print("newmap: %s, written to GRASS MAPSET" % mapname)
    
    def getKmeans(self, imagegroup='', k=5, samps=150, bands="all", outputmap=''):
        if bands == "all":
            (m1, c1) = kmeans(imagegroup[:, :, :], k, samps)
        if bands != "all":
            (m1, c1) = kmeans(imagegroup[:, :, range(0, bands)], k, samps)
        self.writeGarray(m=m1, mapname=outputmap)
        return m1, c1
    
    
    def legend(self, raster, outfile, width=400, height=100, at=(40,50,10,90), units='', digits=0):
        try:
            grass.run_command('d.mon', stop='cairo')
        except:
            pass
        os.environ['GRASS_GNUPLOT'] = 'gnuplot -persist'
        os.environ['GRASS_PROJSHARE'] = '/usr/share/proj'
        os.environ['GRASS_RENDER_FILE_READ'] = 'TRUE'
        os.environ['GRASS_RENDER_TRUECOLOR'] = 'TRUE'
        os.environ['GRASS_RENDER_TRANSPARENT'] = 'TRUE'
        os.environ['GRASS_HTML_BROWSER'] = 'xdg-open'
        os.environ['GRASS_RENDER_FILE_COMPRESSION'] = '9'
        os.environ['GRASS_PAGER'] = 'more'
        os.environ['GRASS_RENDER_IMMEDIATE'] = 'cairo'
        os.environ['GRASS_RENDER_WIDTH'] = '%s' % width
        os.environ['GRASS_RENDER_HEIGHT'] = '%s' % height
        os.environ['GRASS_RENDER_FILE'] = '%s' % outfile
        grass.run_command('d.mon', start='cairo', width=width, height=height, overwrite=True)
        grass.run_command('d.legend', raster=raster, at='%s,%s,%s,%s' % (at[0], at[1], at[2], at[3]), units=units, digits=digits)
        grass.run_command('d.mon', stop='cairo')
        del os.environ['GRASS_RENDER_FILE']
        display(Image(outfile))
        

class Imagery(object):
    
    def group(self, maplist, group, subgroup):
        if group in General().glist(type='group'):
            print("group %s already present" % group)
            return
        if General().grasslayerscheck(maplist):
            imagegroup = ','.join(i for i in maplist)
            grass.run_command('i.group',  group=group, subgroup=subgroup, input=maplist)
        else:
            print('not all the maps were found')
            return 
            
    def cluster(self, group, subgroup, signaturefile, classes, min_size, iterations, reportfile, overwrite):
        if not subgroup:
            subgroup=group
        if not overwrite:
            overwrite=False
        try:
            grass.run_command('i.cluster', 
                              group=group, 
                              subgroup=subgroup, 
                              signaturefile=signaturefile, 
                              classes=classes, 
                              min_size=min_size, 
                              iterations=iterations, 
                              reportfile=reportfile,
                              overwrite=overwrite)
        except:
            print('cjeck if the signature and/or the reportfile file already exist')
        
    def maxlik(self, group, subgroup, signaturefile, output, reject, overwrite):
        if not overwrite:
            overwrite=False
        grass.run_command('i.maxlik', 
                          group=group, 
                          subgroup=subgroup, 
                          signaturefile=signaturefile, 
                          output=output, 
                          reject=reject,
                          overwrite=overwrite)
