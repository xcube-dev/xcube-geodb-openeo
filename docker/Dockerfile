FROM continuumio/miniconda3:4.12.0

LABEL maintainer="xcube-team@brockmann-consult.de"
LABEL name=xcube_geodb_openeo

ARG GEODB_OPENEO_VERSION=0.0.1.dev0

RUN conda install -n base -c conda-forge mamba pip

WORKDIR /tmp
ADD environment.yml /tmp/environment.yml
RUN mamba env update -n base
RUN mamba install -n base -y -c conda-forge
RUN source activate base

RUN echo "postgrest_url=${postgrest_url}" >> config.yml
RUN echo "postgrest_port=${postgrest_port}" >> config.yml
RUN echo "client_id=${client_id}" >> config.yml
RUN echo "client_secret=${client_secret}" >> config.yml
RUN echo "auth_domain=${auth_domain}" >> config.yml

RUN xcube.cli.main --loglevel=DETAIL --traceback serve2 -vvv -c config.yml