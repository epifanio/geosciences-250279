FROM epinux/mbio_lab

USER root
RUN apt-get autoremove -y
RUN apt-get clean -y

USER jovyan

# define versions to be used (PDAL is not available on Ubuntu/Debian, so we compile it here)
# https://github.com/PDAL/PDAL/releases

# ENV SHELL /bin/bash
ENV LC_ALL "en_US.UTF-8"
ENV GRASS_SKIP_MAPSET_OWNER_CHECK 1

# https://proj.org/usage/environmentvars.html#envvar-PROJ_NETWORK
ENV PROJ_NETWORK=ON

ENV NB_DIR=/home/jovyan/notebooks
# ENV JUPYTER_ENABLE_LAB=yes
# ENV GRANT_SUDO=yes
