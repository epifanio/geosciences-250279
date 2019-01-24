FROM epinux/grass-notebook

MAINTAINER Massimo Di Stefano  <epiesasha@me.com>

USER epinux

ADD geosciences-250279.ipynb /home/epinux/work/
#ADD geosciences-250279-binder-dev.ipynb /home/epinux/work/
COPY ipygrass/ /home/epinux/work/ipygrass/
RUN mkdir /home/epinux/work/tmp
ENV PYTHONPATH /home/epinux/work/ipygrass:$PYTHONPATH

USER root
RUN wget wget https://epinux.com/index.php/s/MCsgoGzC2LCZ9PJ/download -O grassdata.zip && \
unzip grassdata.zip && \
rm -rf grassdata.zip && mv /home/epinux/work/home/epinux/grassdata /home/epinux/ && rm -rf /home/epinux/work/home/epinux/
RUN chown -R epinux /home/epinux
RUN chmod -R 777 /home/epinux/work/data
RUN apt-get update && apt-get install python3-geographiclib
RUN updatedb

USER epinux
