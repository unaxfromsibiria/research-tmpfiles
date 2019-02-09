FROM        debian:buster-slim
ARG         SERVER
ARG         PUB_SSH_PORT
RUN         apt-get update && apt-get install -y ssh curl && apt-get clean
RUN         mkdir /root/.ssh
WORKDIR     /root/
RUN         echo "Host *" > .ssh/config && echo " StrictHostKeyChecking no" >> .ssh/config
RUN         ssh-keygen -t rsa -N '' -f .ssh/id_rsa && echo 'Your public key:' && cat .ssh/id_rsa.pub && echo 'copy to server authorized_keys'
RUN         echo  ssh -p ${PUB_SSH_PORT} -N -L 0.0.0.0:4128:127.0.0.1:3128 tunuser@${SERVER} -N >> /bin/open-ssh.sh && chmod 750 /bin/open-ssh.sh
RUN         cat /bin/open-ssh.sh

EXPOSE 4128

ENTRYPOINT /bin/open-ssh.sh
