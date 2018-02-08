import sys
import os
import tempfile
import shutil
import uuid

import subprocess
import grass.script as grass
from osgeo import gdal, osr
from collections import OrderedDict
from pyproj import Proj
import json

from ipyleaflet import (
    Map,
    Marker,
    TileLayer, ImageOverlay,
    Polyline, Polygon, Rectangle, Circle, CircleMarker,
    GeoJSON,
    DrawControl
)

from IPython.display import display, HTML, Image, Markdown, Latex
from IPython.display import clear_output
from ipywidgets import interact, interactive, fixed
from ipywidgets import widgets
import json
import base64


def which(program):
    import os
    def is_exe(fpath):
        return os.path.isfile(fpath) and os.access(fpath, os.X_OK)

    fpath, fname = os.path.split(program)
    if fpath:
        if is_exe(program):
            return program
    else:
        for path in os.environ["PATH"].split(os.pathsep):
            path = path.strip('"')
            exe_file = os.path.join(path, program)
            if is_exe(exe_file):
                return exe_file

    return None

class Grass2vector(object):
    def __init__(self, layers, tmpdir=None, name=False):
        self.layers = layers
        self.checkogr2ogr()
        self.tmpdir = tmpdir
        self.name=name
        
    def checkogr2ogr(self):
        ogr2ogr = which('ogr2ogr')
        if not ogr2ogr:
            print('you need ogr2ogr')
            return None
        else:
            return ogr2ogr        

    def grasslayercheck(self, layer):
        grasslayers = grass.read_command('g.list', type='vector').decode().strip().split('\n')
        if layer not in grasslayers:
            print("grass layer: %s not found" % i)
            return False
        else:
            return True

    def grass2geojson(self, glayer):
        if self.tmpdir:
            if not os.path.exists(self.tmpdir):
                os.makedirs(self.tmpdir)
            # else:
            #    os.mkdir(tempfile.mkdtemp(dir="%s" % self.tmpdir))
            if self.name:
                self.tmpname = os.path.join(self.tmpdir, str(glayer))
            else:
                self.tmpname = os.path.join(self.tmpdir, str(uuid.uuid1()))
        else:
            if self.name:
                self.tmpname = glayer
            else:
                self.tmpname = uuid.uuid1()
        print(self.tmpname)
        if self.checkogr2ogr() and self.grasslayercheck(glayer):
            # set grass region for the input file
            grass.run_command('g.region', vector=glayer, flags='ap')
            grass.run_command('v.out.ogr', input=glayer,
                              output=str(self.tmpname),
                              format='ESRI_Shapefile', overwrite=True)
            #self.checkogr2ogr(), '-f', 'GeoJSON', '-t_srs', 'crs:84', '%s.geojson' % str(self.tmpname), '%s/%s.shp' % (self.tmpname,self.tmpname)
            subprocess.check_call([self.checkogr2ogr(),
                                   '-f', 'GeoJSON', 
                                   '-t_srs', 'crs:84',
                                   '%s.geojson' % str(self.tmpname),
                                   '%s/%s.shp' % (self.tmpname,self.tmpname)])
            jsonname = str(self.tmpname) + '.geojson'
            return jsonname
        else:
            return None
        
    def makejson(self, html=False):
        gl = OrderedDict()
        for i in self.layers:
            if self.grasslayercheck(i):
                gl[i] = self.vectorinfo(self.grass2geojson(i))
                if html:
                    gl[i]['html'] = self.maphtml(gl[i])
        return gl

    
    def vectorinfo(self, jsonname):
        with open(jsonname) as f:
            data = json.load(f)
        g = GeoJSON(data=data)
        return {'geojson': jsonname, 'vlayer':g}
        
class Grass2img(object):
    def __init__(self, layers, tmpdir=None, name=False):
        self.layers = layers
        self.checkgdaldem()
        self.tmpdir = tmpdir
        self.name=name

    def checkgdaldem(self):
        gdaldem = which('gdaldem')
        #gdaldem=('/usr/local/Cellar/gdal2/2.1.3_1/bin/gdaldem')
        if not gdaldem:
            print('you need gdaldem')
            return None
        else:
            return gdaldem

    def grasslayercheck(self, layer):
        grasslayers = grass.read_command('g.list', type='raster').decode().strip().split('\n')
        # !g.list raster
        if layer not in grasslayers:
            print("grass layer: %s not found" % i)
            return False
        else:
            return True

    def grass2jpg(self, glayer):
        if self.tmpdir:
            if not os.path.exists(self.tmpdir):
                os.makedirs(self.tmpdir)
            # else:
            #    os.mkdir(tempfile.mkdtemp(dir="%s" % self.tmpdir))
            if self.name:
                self.tmpname = os.path.join(self.tmpdir, str(glayer))
            else:
                self.tmpname = os.path.join(self.tmpdir, str(uuid.uuid1()))
        else:
            if self.name:
                self.tmpname = glayer
            else:
                self.tmpname = uuid.uuid1()

        if self.checkgdaldem() and self.grasslayercheck(glayer):
            # set grass region for the input file
            grass.run_command('g.region', rast=glayer, flags='ap')
            # export as GTiff, with resonable byte depth to allow elevation data export
            grass.run_command('r.out.gdal', input=glayer,
                              output=str(self.tmpname) + '.tif',
                              format='GTiff', type='Float32', flags='f', overwrite=True)
            # export GRASS color table used by gdaldem
            grass.run_command('r.colors.out', map=glayer,
                              rules=str(self.tmpname) + '.txt', overwrite=True)
            # use gdaldem to generate a JPEG with proper color table
            subprocess.check_call([self.checkgdaldem(),
                                   'color-relief',
                                   '-of', 'JPEG', '%s.tif' % str(self.tmpname),
                                   '%s.txt' % self.tmpname, '%s.jpg' % str(self.tmpname)])
            imagename = str(self.tmpname) + '.jpg'
            return imagename
        else:
            return None

    def rasterinfo(self, imagename):
        rasterdata = gdal.Open(imagename)
        projInfo = rasterdata.GetProjection()
        if projInfo == "":
            print("need projection")
            return
        else:
            # extract projection information in proj4+ string format
            spatialRef = osr.SpatialReference()
            spatialRef.ImportFromWkt(projInfo)
            spatialRefProj = spatialRef.ExportToProj4()
            proj = str(spatialRefProj)
        datuminfo = dict((n, v) for n, v in (a.split('=') for a in proj.split()[:-1]))
        # extract rows, cols, bounds and center from the raster image
        geoinformation = rasterdata.GetGeoTransform()
        rows = rasterdata.RasterYSize
        cols = rasterdata.RasterXSize

        LL = (geoinformation[0], (geoinformation[3] + (rows * geoinformation[5])))
        UR = (geoinformation[0] + (cols * geoinformation[1]), geoinformation[3])
        C = (LL[0] + ((cols * geoinformation[1]) / 2),
             LL[1] - ((rows * geoinformation[5]) / 2))
        C_lon, C_lat = C[0], C[1]
        LL_lon, LL_lat = LL[0], LL[1]
        UR_lon, UR_lat = UR[0], UR[1]
        # use pyproj to transform the image center and bounds from the
        # original projection to WGS84
        if datuminfo['+proj'] != 'longlat':
            myProj = Proj(proj)
            LL_lon, LL_lat = myProj(LL[0], LL[1], inverse=True)
            UR_lon, UR_lat = myProj(UR[0], UR[1], inverse=True)
            C_lon, C_lat = myProj(C[0], C[1], inverse=True)
        return {'LL': (LL_lat, LL_lon),
                'UR': (UR_lat, UR_lon),
                'C': (C_lat, C_lon),
                'raster': imagename,
                'proj': proj}

    def makeimg(self, html=False):
        gl = OrderedDict()
        for i in self.layers:
            if self.grasslayercheck(i):
                gl[i] = self.rasterinfo(self.grass2jpg(i))
                if html:
                    gl[i]['html'] = self.maphtml(gl[i])
        return gl
    
    
    def makeimg_parallel(self, imagelist):
        pool = multiprocessing.Pool()
        res1 = pool.map(makeimg, imagelist)
        pool.close()

    def maphtml(self, mapinfo):
        zoom = 12
        image = mapinfo['raster']
        clat, clon = mapinfo['C']
        ll_lat, ll_lon = mapinfo['LL']
        ur_lat, ur_lon = mapinfo['UR']

        maptemplate = """<!DOCTYPE html>
        <html>
        <head>
            <meta charset='utf-8'>
            <title>Leaflet.Control.FullScreen Demo</title>
            <link rel="stylesheet" href="http://cdn.leafletjs.com/leaflet/v0.7.7/leaflet.css" />
            <style type="text/css">
                #map { width: 700px; height: 433px; }
                .fullscreen-icon { background-image: url(icon-fullscreen.png); }
                #map:-webkit-full-screen { width: 10ds0%% !important; height: 10ds0%% !important; z-index: 99999; }
                #map:-ms-fullscreen { width: 10d0%% !important; height: 10ds0%% !important; z-index: 99999; }
                #map:full-screen { width: 10ds0%% !important; height: 10ds0%% !important; z-index: 99999; }
                #map:fullscreen { width: 10ds0%% !important; height: 10ds0%% !important; z-index: 99999; }
                .leaflet-pseudo-fullscreen { position: fixed !important; width: 100%% !important; height: 100%% !important; top: 0px !important; left: 0px !important; z-index: 99999; }
            </style>
            <script src="http://cdn.leafletjs.com/leaflet/v0.7.7/leaflet.js"></script>
            <script src="Control.FullScreen.js"></script>
        </head>
        <body>

        <div id="map"></div>

        <script>
            var base = new L.TileLayer('https://api.tiles.mapbox.com/v4/{id}/{z}/{x}/{y}.png?access_token=pk.eyJ1IjoibWFwYm94IiwiYSI6ImNpandmbXliNDBjZWd2M2x6bDk3c2ZtOTkifQ._QA7i5Mpkd_m30IGElHziw', {
                maxZoom: 19,
                id: 'mapbox.streets'
            });

            var map = new L.Map('map', {
                layers: [base],
                center: new L.LatLng(%s, %s),
                zoom: %s,
                fullscreenControl: true,
                fullscreenControlOptions: { // optional
                    title:"Show me the fullscreen !",
                    titleCancel:"Exit fullscreen mode"
                    }
            });

            var imageUrl = '%s',
            imageBounds = [[%s, %s], [%s, %s]];
            L.imageOverlay(imageUrl, imageBounds).addTo(map);
            // detect fullscreen toggling
            map.on('enterFullscreen', function(){
                if(window.console) window.console.log('enterFullscreen');
            });
            map.on('exitFullscreen', function(){
                if(window.console) window.console.log('exitFullscreen');
            });
        </script>
        </body>
        </html>""" % (clat, clon, zoom, image, ll_lat, ll_lon, ur_lat, ur_lon)
        #map = open('map.html', 'w')
        #map.write(maptemplate)
        #map.close()
        return maptemplate


import json
def handle_draw(self, action, geo_json, **kwargs):
    print(action)
    #display(json.dumps(geo_json))


class Grass2Leaflet(object):
    def __init__(self, grassimg):
        self.grassimg = grassimg
        self.draw_control = None
        self.zoom = 15
        self.center = self.centermap()
        self.m = Map(default_tiles=TileLayer(opacity=1.0), center=self.center, zoom=self.zoom)

    def centermap(self):
        centerlat = []
        centerlon = []
        for i in self.grassimg:
            centerlat.append(self.grassimg[i]['C'][0])
            centerlon.append(self.grassimg[i]['C'][1])
        center = (sum(centerlat) / float(len(centerlat)), sum(centerlon) / float(len(centerlon)))
        return center

    def imgoverlays(self):
        self.leafletimg = OrderedDict()
        for i in self.grassimg:
            layer = ImageOverlay(url=self.grassimg[i]['raster'],
                                 bounds=(self.grassimg[i]['LL'], self.grassimg[i]['UR']))
            self.leafletimg[i] = layer

    def render(self, draw_control=None, caption=None):
        self.out = widgets.Output()
        self.imgoverlays()
        self.dc = None
        options = ['None']
        self.m.add_layer(self.leafletimg[list(self.grassimg.keys())[-1]])
        if len(self.grassimg) >= 2:
            self.maplist = widgets.Dropdown(
                options=options + list(self.grassimg.keys()),
                value=list(self.grassimg.keys())[-1],
                description='Select Layer:',
            )
            self.maplist.observe(self.on_value_change, names='value')
            display(self.maplist)
        if draw_control:
            self.dc = DrawControl()
            self.dc.on_draw(handle_draw)
            self.m.add_control(self.dc)
        display(self.m)
        self.lastdraw = widgets.Button(
            description='Print last draw',
            disabled=False,
            button_style='', # 'success', 'info', 'warning', 'danger' or ''
            tooltip='Print last draw',
            #icon='check'
            ) 
        self.lastdraw.on_click(self.on_button_clicked1)
        if not draw_control:
            self.lastdraw.disabled = True
        display(widgets.HBox([self.lastdraw, self.out]))
        if caption:
            display(HTML("<center><b>Figure %s:</b> %s<center>" % (caption[0], caption[1])))
        return {'map': self.m, 'drawer': self.dc}

    def on_value_change(self, layername):
        self.m.clear_layers()
        self.m.add_layer(TileLayer(opacity=1.0))
        if self.maplist.value != 'None':
            self.m.add_layer(self.leafletimg[layername['new']])
            
    def on_button_clicked1(self, b): 
        with self.out:
            clear_output()
            display(self.dc.last_draw)
            new_draw = GeoJSON(data=self.dc.last_draw)
            self.m.add_layer(new_draw)
            #display(dir(self.dc.layer))
            
    def handle_draw_output(self, json):
        display(json.dumps(geo_json))

    def main(self):
        self.imgoverlays()
        self.render()

def makemap(layers, caption=None, zoom=10):
    fig = Grass2img(layers).makeimg()
    leaflet_widget = Grass2Leaflet(fig).render(caption=caption)
    leaflet_widget['map'].center = (fig[list(fig.keys())[0]]['C'])
    leaflet_widget['map'].zoom = zoom
    
    
def makefigure(layers, output='', caption=None, legend=False, clean=True, embed=True):
    html = "<center><table><tr>"
    for i in layers:
        if not output:
            output = uuid.uuid1()
        outname=str(output)+i+'.png'
        rasterlist = grass.read_command('g.list', type='raster').decode().strip().split('\n')
        if i in rasterlist:
            grass.run_command('r.out.png', input=i, output=outname, flags='t', overwrite=True)
        else:
            grass.run_command('v.out.png', input=i, output=outname, overwrite=True)
        if embed:
            imageFile = open(outname, "rb")
            imagebyte = base64.b64encode(imageFile.read())
            imagestr = imagebyte.decode()
            html+="""<td><p><img src="data:image/png;base64,%s" alt="" width='600'/></p></td>""" % imagestr
        else:
            html+="""<td><p><img src="%s" alt="" width='600'/></p></td>""" % outname
            clean = None
        if clean:
            os.remove(outname)
    html +="""</table><center>"""
    display(HTML(html)) 
    if caption:
        display(Markdown("<center><b>Figure %s:</b> %s<center>" % (caption[0], caption[1])))

def makelegend(raster, output='', width=400, height=100, at=(40,50,10,90), units='', digits=0, label=False, fontsize=12, labelnum=5, flags='v', clean=True, embed=True):
    try:
        grass.run_command('d.mon', stop='cairo')
    except:
        pass
    if not output:
        output = str(uuid.uuid1())+raster+'.png'
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
    os.environ['GRASS_RENDER_FILE'] = '%s' % output
    grass.run_command('d.mon', start='cairo', width=width, height=height, overwrite=True)
    grass.run_command('d.legend', 
                      flags=flags,
                      raster=raster, 
                      fontsize=fontsize,
                      labelnum=labelnum,
                      at='%s,%s,%s,%s' % (at[0], at[1], at[2], at[3]), units=units, digits=digits)
    grass.run_command('d.mon', stop='cairo')
    del os.environ['GRASS_RENDER_FILE']
    #outname = os.path.join(output,i+'.png')
    if embed:
        imageFile = open(output, "rb")
        imagebyte = base64.b64encode(imageFile.read())
        imagestr = imagebyte.decode()
        html = """<center><img src="data:image/png;base64,%s" alt="" width='%s' height='%s'/><center>""" % (imagestr, width, height)
    else:
        clean = None
        html = """<center><img src="%s" alt="" width='%s' height='%s'/><center>""" % (output, width, height)
    if clean:
        os.remove(output)
    
    if label:
        display(Markdown("<center><b>%s</b><center>" % label))
        #display(HTML("<center><b>%s</b></center>" % label))
    display(HTML(html))
    
    
    