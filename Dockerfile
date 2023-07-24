FROM epinux/mbio_lab

ENV DEBIAN_FRONTEND noninteractive
ENV PYTHONPATH=/usr/local/grass84/etc/python/:/home/jovyan/work/P1/ipygrass/:$PYTHONPATH
ENV GRASSBIN=/usr/local/bin/grass

ENV SHELL /bin/bash
ENV LC_ALL "en_US.UTF-8"
ENV GRASS_SKIP_MAPSET_OWNER_CHECK 1

# https://proj.org/usage/environmentvars.html#envvar-PROJ_NETWORK
ENV PROJ_NETWORK=ON

ENV NB_DIR=/home/jovyan/notebooks
ENV JUPYTER_ENABLE_LAB=yes
# ENV GRANT_SUDO=yes

USER root
RUN conda install -y -c conda-forge ipyleaflet
RUN pip install geographiclib
RUN pip install spectral

USER jovyan
