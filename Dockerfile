FROM epinux/grass-notebook

MAINTAINER Massimo Di Stefano  <epiesasha@me.com>

USER epinux

ADD geosciences-250279.ipynb /home/epinux/work/
#ADD geosciences-250279-binder-dev.ipynb /home/epinux/work/
COPY ipygrass/ /home/epinux/work/ipygrass/
RUN mkdir /home/epinux/work/tmp
ENV PYTHONPATH /home/epinux/work/ipygrass:$PYTHONPATH

USER root
# RUN wget https://epinux.com/index.php/s/MCsgoGzC2LCZ9PJ/download -O grassdata.zip
RUN chown -R epinux /home/epinux
RUN chmod -R 777 /home/epinux/work/data
RUN apt-get update && apt-get install python3-geographiclib
RUN updatedb

USER epinux
