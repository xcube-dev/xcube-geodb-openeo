FROM continuumio/miniconda3:23.5.2-0

LABEL maintainer="xcube-team@brockmann-consult.de"
LABEL name=xcube_geodb_openeo

RUN conda install -n base -c conda-forge 'mamba>=1.5.2' pip

#ADD environment.yml /tmp/environment.yml
ADD . /tmp/
WORKDIR /tmp
RUN mamba env update -n base
RUN . activate base

RUN git clone https://github.com/dcs4cop/xcube.git
WORKDIR /tmp/xcube
RUN mamba env update -n base
RUN pip install -e .

WORKDIR /tmp/
RUN git clone https://github.com/dcs4cop/xcube-geodb.git
WORKDIR /tmp/xcube-geodb
RUN pip install -e .

WORKDIR /tmp/
RUN pip install -e .

CMD ["python", "-m", "xcube.cli.main", "--loglevel=DETAIL", "--traceback", "serve", "-vvv", "-c", "/etc/config/config.yml"]