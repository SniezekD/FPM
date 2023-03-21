FROM ubuntu:20.04

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

#install OF2006
RUN curl -s https://dl.openfoam.com/add-debian-repo.sh | sudo bash
RUN wget -q -O - https://dl.openfoam.com/add-debian-repo.sh | sudo bash
RUN apt-get update -y
RUN apt-get install openfoam2006-default -y --fix-missing

#install python3.10
RUN add-apt-repository ppa:deadsnakes/ppa
RUN apt install python3.10 -y
#instal pip
RUN apt-get update -y
RUN apt install python3-pip -y

RUN pip3 install numpy==1.23.4 matplotlib pandas numpy-stl h5py scipy pyvista==0.37.0
RUN pip3 install ipython

RUN apt install python-is-python3 -y
#install swak4Foam
WORKDIR /home/damian/openfoam2206
RUN hg clone http://hg.code.sf.net/p/openfoam-extend/swak4Foam swak4Foam
# ADD swak4foam /home/damian/openfoam2206/
WORKDIR /home/damian/openfoam2206/swak4Foam
RUN . /usr/lib/openfoam/openfoam2006/etc/bashrc && ./Allwmake

RUN apt-get install gnuplot -y

RUN apt-get install dos2unix -y

WORKDIR /home/damian/MGR/IFPM
ADD IFPM /home/damian/MGR/IFPM
# RUN ls -l
# RUN sed -i 's/\r$//' run_simpleFoam.sh 
RUN dos2unix run_simpleFoam.sh
RUN dos2unix run_meshing2D.sh
RUN dos2unix run_meshing.sh
RUN dos2unix prep_model.sh

# ADD IFPM /home/damian/MGR/IFPM
ADD OF_Model /home/damian/MGR/wd/OF_Model

RUN useradd damian

# RUN chown damian /home/damian -R
# RUN usermod -a -G sudo damian

ENV OMPI_ALLOW_RUN_AS_ROOT=1
ENV OMPI_ALLOW_RUN_AS_ROOT_CONFIRM=1

ENTRYPOINT ["tail", "-f", "/dev/null"]
