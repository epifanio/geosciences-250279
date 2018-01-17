FROM epinux/base-notebook

MAINTAINER Massimo Di Stefano  <epiesasha@me.com>

USER root

ADD cdn.debian.net_debian_dists_sid_contrib_source_Sources.gz /var/lib/apt/lists/

RUN apt-get clean && apt-get update && \
    apt-get install -y --no-install-recommends \
    grass-core # grass-dev build-essential

#RUN apt-get clean && apt-get update && \
#    apt-get install -y --no-install-recommends \
#    netcdf-bin \
#    grass-core \
#    gdal-bin \
#    mapserver-bin \
#    dans-gdal-scripts \
#    python-gdal \
#    python3-gdal \
#    libgdal20-2.1.2-grass \
#    librasterlite2-1 \
#    libspatialite7 \
#    spatialite-bin \
#    python-mapscript \
#    cgi-mapserver \
#    shapelib \
#    gpx2shp \
#    gpsbabel \
#    ossim-core \
#    geographiclib-tools \
#    python3-geographiclib \
#    python-geographiclib \
#    fiona \
#    python-fiona \
#    python-rasterio \
#    python-geopandas \
#    python-shapely \
#    python-geopy \
#    python-owslib \
#    python-geojson \
#    python-netcdf4 \
#    python-grib \
#    python3-fiona \
#    python3-rasterio \
#    rasterio \
#    python3-geopandas \
#    python3-shapely \
#    python3-geopy \
#    python3-owslib \
#    python3-geojson \
#    python3-netcdf4 \
#    python3-grib \
#    proj-bin \
#    python3-mpltoolkits.basemap


# script for xvfb-run.  all docker commands will effectively run under this via the entrypoint
RUN printf "#\041/bin/sh \n rm -f /tmp/.X99-lock && xvfb-run -s '-screen 0 1600x1200x16' \$@" >> /usr/local/bin/xvfbrun.sh && \
    chmod +x /usr/local/bin/xvfbrun.sh


#RUN pip3 install xray && \
#    pip3 install pygeoif &&\
#    pip3 install pyepsg && \
#    pip3 install geocoder && \
#    pip3 install czml && \
#    pip3 install cesiumpy && \
#    pip2 install xray && \
#    pip2 install pygeoif &&\
#    pip2 install pyepsg && \
#    pip2 install geocoder && \
#    pip2 install czml && \
#    pip2 install cesiumpy && \
#    pip2 install ipyleaflet && pip3 install ipyleaflet && \
#    pip3 install -U pyproj && pip install -U pyproj && \
#    pip3 install geopy && pip install geopy

RUN pip3 install ipyleaflet
RUN jupyter nbextension enable --py ipyleaflet --sys-prefix

#RUN git clone https://github.com/rmenegaux/bayeshack

USER epinux
RUN jupyter nbextension enable --py widgetsnbextension

ENV PATH /usr/lib/grass72/bin:/home/epinux/.grass7/addons/bin:/home/epinux/.grass7/addons/scripts:$PATH
ENV GRASS_PNG_AUTO_WRITE TRUE
ENV GRASS_PNG_COMPRESSION 9
ENV GRASS_TRANSPARENT TRUE
ENV GRASS_TRUECOLOR TRUE
ENV GISBASE /usr/lib/grass72
ENV GISDBASE /home/epinux/grassdata
ENV GISRC /home/epinux/.grass7/rc
ENV LD_LIBRARY_PATH /usr/lib/grass72/lib/
ENV GRASS_ADDON_BASE /home/epinux/.grass7/addons
ENV PYTHONPATH /usr/lib/grass72/etc/python:$PYTHONPATH
RUN mkdir /home/epinux/.grass7
#ADD GRASS/rc /home/epinux/.grass7/rc
ADD GRASS /home/epinux/.grass7
ADD geosciences-250279.ipynb /home/epinux/work/

USER root
RUN apt-get -y install unzip
RUN wget http://epinux.com/epinux_data/grassdata.zip && \
unzip grassdata.zip && \
rm -rf grassdata.zip && mv /home/epinux/work/home/epinux/grassdata /home/epinux/ && rm -rf /home/epinux/work/home/epinux/
RUN chmod a+x /usr/lib/grass72/bin && chmod a+x /usr/lib/grass72/bin/r.out.png
RUN chown -R epinux /home/epinux
RUN updatedb

USER epinux
