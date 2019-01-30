FROM        debian:buster-slim
RUN         apt-get update && apt-get install -y squid openssh-server curl && apt-get clean
RUN         useradd -m -s /bin/false -c "ssh tunnel user" tunuser
RUN         mkdir /home/tunuser/.ssh && mkdir /var/run/sshd
ARG         PUB_SSH_KEYS
COPY        ${PUB_SSH_KEYS} /home/tunuser/.ssh/authorized_keys
RUN         tr -dc A-Za-z0-9 < /dev/urandom | head -c32 | xargs echo "tunuser:$1" | chpasswd
RUN         cat /etc/squid/squid.conf | grep -v '^#' > /etc/squid/main.squid.conf
RUN         echo 'access_log none' >> /etc/squid/main.squid.conf
RUN         echo 'cache_log /dev/null' >> /etc/squid/main.squid.conf
RUN         echo 'logfile_rotate 0' >> /etc/squid/main.squid.conf
RUN         echo 'PermitRootLogin no' >> /etc/ssh/sshd_config
RUN         echo '#!/bin/bash' > /bin/tunproxy_run.sh
RUN         echo 'squid -f /etc/squid/main.squid.conf && /usr/sbin/sshd -D' >> /bin/tunproxy_run.sh
RUN         chmod 700 /bin/tunproxy_run.sh

EXPOSE 22

ENTRYPOINT /bin/tunproxy_run.sh

# This is http proxy server by ssh tunnel. 
# how to check on your host
# 1) Copy your keys and build image as
# cp ~./.ssh/authorized_keys ./my_kyes
# or create empty file for test
# docker build --no-cache --build-arg PUB_SSH_KEY=./my_keys -t tunproxy .
# rm my_keys
# PUB_SSH_KEYS it's path of your public ssh keys
# 2) Run for test
# docker run -d -p <external ssh port>:22 --name tunproxy_server tunproxy
# 3) Check tunnel to the ssh server on container
# ssh -p <external ssh port> -N -L <your localhost http proxy port>:127.0.0.1:3128 tunuser@127.0.0.1 -N
# 4) Check does it work
# curl -x http://127.0.0.1:<your localhost http proxy port> https://api.ipify.org/?format=json
# 5) Stop and remove
# docker container stop tunproxy_server
# docker container rm tunproxy_server
# 6) Setup this server into your vps:
# docker run --restart=always -d -p 8080:22 --name tunproxy_server tunproxy
# and put in autoload:
# ssh -p 8080 -N -L 3128:127.0.0.1:3128 tunuser@127.0.0.1 -N
