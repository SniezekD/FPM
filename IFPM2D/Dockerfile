FROM ubuntu:22.04

USER root

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update -y
RUN apt install software-properties-common -y

RUN apt install sudo -y
RUN apt-get install mpi -y
RUN apt-get install nano -y
RUN apt-get install wget -y
RUN apt-get install curl -y

#install OF2206
RUN curl -s https://dl.openfoam.com/add-debian-repo.sh | sudo bash
RUN wget -q -O - https://dl.openfoam.com/add-debian-repo.sh | sudo bash
# RUN sh -c "wget -O - https://dl.openfoam.org/gpg.key > /etc/apt/trusted.gpg.d/openfoam.asc"
# RUN add-apt-repository http://dl.openfoam.org/ubuntu
# RUN add-apt-repository "http://dl.openfoam.org/ubuntu dev"
RUN apt-get update -y
RUN apt-get install openfoam2206-default -y

ENV of2206='. /usr/lib/openfoam/openfoam2206/etc/bashrc'

#install python3.10
RUN add-apt-repository ppa:deadsnakes/ppa
RUN apt install python3.10 -y
#instal pip
RUN apt-get update -y
RUN apt install python3-pip -y

RUN pip3 install numpy matplotlib pandas numpy-stl h5py scipy
RUN pip3 install ipython

RUN apt-get install gnuplot -y

WORKDIR /home/damian

ADD IFPM /home/damian/MGR/IFPM
ADD OF_Model /home/damian/MGR/OF_Model

RUN useradd damian

RUN chown damian /home/damian -R
RUN usermod -a -G sudo damian

USER damian

ENTRYPOINT ["tail", "-f", "/dev/null"]