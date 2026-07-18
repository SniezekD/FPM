FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive
ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8

RUN apt-get update && apt-get install -y --no-install-recommends \
        ca-certificates \
        curl \
        wget \
        gnupg \
        software-properties-common \
        sudo \
        gnuplot \
        dos2unix \
        openmpi-bin \
        python3 \
        python3-venv \
        python3-pip \
        pipx \
    && rm -rf /var/lib/apt/lists/*

RUN curl -s https://dl.openfoam.com/add-debian-repo.sh | bash \
    && apt-get update \
    && apt-get install -y --no-install-recommends openfoam2306-default \
    && rm -rf /var/lib/apt/lists/*
RUN echo "alias of2306='source /usr/lib/openfoam/openfoam2306/etc/bashrc'" \
        >> /etc/bash.bashrc

ENV OMPI_ALLOW_RUN_AS_ROOT=1
ENV OMPI_ALLOW_RUN_AS_ROOT_CONFIRM=1
ENV OMPI_MCA_btl_vader_single_copy_mechanism=none

ARG UID=1000
ARG GID=1000

# ubuntu:24.04 ships a default 'ubuntu' user at UID/GID 1000. Remove it so we can
# create our user at the HOST's UID/GID (--build-arg) for clean bind-mount ownership.
RUN userdel -r ubuntu 2>/dev/null || true; \
    getent group ${GID} >/dev/null || groupadd -g ${GID} defaultuser; \
    useradd -u ${UID} -g ${GID} -ms /bin/bash defaultuser && \
    usermod -aG sudo defaultuser && \
    mkdir -p /home/repos/FPM && \
    chown -R ${UID}:${GID} /home/repos

USER defaultuser
ENV PATH="/home/defaultuser/.local/bin:${PATH}"
RUN pipx install poetry

WORKDIR /home/repos/FPM

COPY --chown=defaultuser:defaultuser pyproject.toml poetry.lock README.md ./
RUN poetry env use python3.12 && poetry install --no-root

COPY --chown=defaultuser:defaultuser fpm ./fpm
COPY --chown=defaultuser:defaultuser scripts ./scripts
RUN poetry install