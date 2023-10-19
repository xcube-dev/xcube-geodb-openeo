#FROM continuumio/miniconda3:23.5.2-0
ARG MICROMAMBA_VERSION=1.3.1
FROM mambaorg/micromamba:${MICROMAMBA_VERSION}

LABEL maintainer="xcube-team@brockmann-consult.de"
LABEL name=xcube_geodb_openeo

FROM mambaorg/micromamba:1.5.1
COPY --chown=$MAMBA_USER:$MAMBA_USER env.yaml /tmp/env.yaml
RUN micromamba install --yes --file /tmp/env.yaml && \
    micromamba clean --all --yes
ARG MAMBA_DOCKERFILE_ACTIVATE=1

RUN micromamba install -n base -c conda-forge pip

ADD environment.yml /tmp/environment.yml
ADD . /tmp/
WORKDIR /tmp
RUN micromamba env update -n base
#RUN . activate base

RUN git clone https://github.com/dcs4cop/xcube.git
WORKDIR /tmp/xcube
#RUN micromamba env update -n base
RUN pip install -e .

WORKDIR /tmp/
RUN git clone https://github.com/dcs4cop/xcube-geodb.git
WORKDIR /tmp/xcube-geodb
RUN pip install -e .

WORKDIR /tmp/
RUN pip install -e .

RUN python -m xcube.cli.main --loglevel=DETAIL --traceback serve -vvv -c /etc/config/config.yml

#CMD ["python", "-m", "xcube.cli.main", "--loglevel=DETAIL", "--traceback", "serve", "-vvv", "-c", "/etc/config/config.yml"]