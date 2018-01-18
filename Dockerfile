FROM epinux/grass-notebook

MAINTAINER Massimo Di Stefano  <epiesasha@me.com>

USER epinux

ADD geosciences-250279.ipynb /home/epinux/work/

USER root
RUN wget http://epinux.com/epinux_data/grassdata.zip && \
unzip grassdata.zip && \
rm -rf grassdata.zip && mv /home/epinux/work/home/epinux/grassdata /home/epinux/ && rm -rf /home/epinux/work/home/epinux/
RUN chown -R epinux /home/epinux
RUN chmod -R 777 /home/epinux/work/data
RUN updatedb

USER epinux
