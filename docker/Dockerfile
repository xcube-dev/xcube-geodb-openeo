FROM continuumio/miniconda3:4.12.0

LABEL maintainer="xcube-team@brockmann-consult.de"
LABEL name=xcube_geodb_openeo

ARG GEODB_OPENEO_VERSION=0.0.1.dev0

RUN conda install -n base -c conda-forge mamba pip

WORKDIR /tmp
ADD environment.yml /tmp/environment.yml
ADD . /tmp/
RUN mamba env update -n base
RUN . activate base

RUN git clone https://github.com/dcs4cop/xcube.git
WORKDIR /tmp/xcube
RUN git checkout forman-676-server_redesign
RUN mamba env update -n base
RUN pip install -e .

WORKDIR /tmp
RUN pip install -e .

CMD ["python", "-m", "xcube.cli.main", "--loglevel=DETAIL", "--traceback", "serve2", "-vvv", "-c", "config/config.yml"]