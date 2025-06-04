FROM ubuntu:22.04

USER root

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update -y
RUN apt install software-properties-common -y
RUN apt install unzip -y
RUN apt install zip -y
RUN apt-get install mercurial -y
RUN apt-get install bison -y
RUN apt-get update -y
RUN apt-get install flex -y

RUN apt-get update -y
RUN apt install sudo -y
RUN apt-get install mpi -y
RUN apt-get install nano -y
RUN apt-get install wget -y
RUN apt-get install curl -y
RUN apt-get install gnuplot -y
RUN apt-get install dos2unix -y

#install OpenFOAM12
RUN sh -c "wget -O - https://dl.openfoam.org/gpg.key > /etc/apt/trusted.gpg.d/openfoam.asc"
RUN add-apt-repository http://dl.openfoam.org/ubuntu
RUN apt-get update -y
RUN apt -y install openfoam12
RUN echo "alias of12='source /opt/openfoam12/etc/bashrc'" >> $HOME/.bashrc

#install OF2306
RUN curl -s https://dl.openfoam.com/add-debian-repo.sh | sudo bash
RUN wget -q -O - https://dl.openfoam.com/add-debian-repo.sh | sudo bash
RUN apt-get update -y
RUN apt-get install openfoam2306-default -y --fix-missing

#install python3.11
RUN add-apt-repository ppa:deadsnakes/ppa
RUN apt install python3.11 -y
#instal pip
RUN apt-get update -y
RUN apt install python3-pip -y
RUN apt install python-is-python3 -y

ENV OMPI_ALLOW_RUN_AS_ROOT=1
ENV OMPI_ALLOW_RUN_AS_ROOT_CONFIRM=1
ENV OMPI_MCA_btl_vader_single_copy_mechanism="none"

# Add poetry environment for python
RUN pip install poetry
WORKDIR /home/repos/FPM/
ADD poetry.lock /home/repos/FPM/poetry.lock
ADD pyproject.toml /home/repos/FPM/pyproject.toml
COPY . /home/repos/FPM/

WORKDIR /home/