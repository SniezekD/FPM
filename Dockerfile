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

#install OF2206
RUN curl -s https://dl.openfoam.com/add-debian-repo.sh | sudo bash
RUN wget -q -O - https://dl.openfoam.com/add-debian-repo.sh | sudo bash
RUN apt-get update -y
RUN apt-get install openfoam2006-default -y
# RUN sh -c "wget -O - https://dl.openfoam.org/gpg.key | apt-key add -"
# RUN add-apt-repository http://dl.openfoam.org/ubuntu
# RUN apt-get update
# RUN apt-get -y install openfoam7

# ENV of2206='. /usr/lib/openfoam/openfoam2206/etc/bashrc'

#install python3.10
RUN add-apt-repository ppa:deadsnakes/ppa
RUN apt install python3.10 -y
#instal pip
RUN apt-get update -y
RUN apt install python3-pip -y

RUN pip3 install numpy matplotlib pandas numpy-stl h5py scipy
RUN pip3 install ipython

RUN apt install python-is-python3 -y
#install swak4Foam
WORKDIR /home/damian/openfoam2206
RUN hg clone http://hg.code.sf.net/p/openfoam-extend/swak4Foam swak4Foam
# ADD swak4foam /home/damian/openfoam2206/
WORKDIR /home/damian/openfoam2206/swak4Foam
# RUN ls -l && sleep 100
RUN . /usr/lib/openfoam/openfoam2006/etc/bashrc && ./Allwmake
# RUN echo 'alias of7=". /opt/openfoam7/etc/bashrc"' >> ~/.bashrc
# RUN . /opt/openfoam7/etc/bashrc
# RUN  ./AllwmakeAll

RUN apt-get install gnuplot -y

WORKDIR /home/damian

ADD IFPM2D /home/damian/MGR/IFPM2D
ADD IFPM3D /home/damian/MGR/IFPM3D
ADD OF_Model /home/damian/MGR/OF_Model

RUN useradd damian

RUN chown damian /home/damian -R
RUN usermod -a -G sudo damian

ENV OMPI_ALLOW_RUN_AS_ROOT=1
ENV OMPI_ALLOW_RUN_AS_ROOT_CONFIRM=1

# USER damian
# RUN echo 'alias python="python3"' >> ~/.bashrc


ENTRYPOINT ["tail", "-f", "/dev/null"]