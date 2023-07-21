FROM epinux/mbio_lab

ENV DEBIAN_FRONTEND noninteractive

# define versions to be used (PDAL is not available on Ubuntu/Debian, so we compile it here)
# https://github.com/PDAL/PDAL/releases

ENV SHELL /bin/bash
ENV LC_ALL "en_US.UTF-8"
ENV GRASS_SKIP_MAPSET_OWNER_CHECK 1

# https://proj.org/usage/environmentvars.html#envvar-PROJ_NETWORK
ENV PROJ_NETWORK=ON

ENV NB_DIR=/home/jovyan/notebooks
ENV JUPYTER_ENABLE_LAB=yes
ENV GRANT_SUDO=yes

#ADD geosciences-250279.ipynb /root/home/work/
#ADD geosciences-250279-binder-dev.ipynb /home/epinux/work/
#COPY ipygrass/ /home/epinux/work/ipygrass/
#RUN mkdir /home/epinux/work/tmp
#ENV PYTHONPATH /home/epinux/work/ipygrass:$PYTHONPATH

#USER root
# RUN wget https://epinux.com/index.php/s/MCsgoGzC2LCZ9PJ/download -O grassdata.zip
#RUN chown -R epinux /home/epinux
#RUN chmod -R 777 /home/epinux/work/data
#RUN apt-get update && apt-get install python3-geographiclib
#RUN updatedb

