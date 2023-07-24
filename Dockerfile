FROM epinux/mbio_lab
# source for the image:
#  https://github.com/epifanio/PDAL_MBIO.git

USER jovyan

RUN git clone https://github.com/epifanio/geosciences-250279 /home/jovyan/work/geoscience-250279
ENV PYTHONPATH=/usr/local/grass84/etc/python/:/home/jovyan/work/geoscience-250279/ipygrass/:$PYTHONPATH

