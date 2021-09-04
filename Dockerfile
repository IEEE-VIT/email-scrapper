FROM ubuntu
RUN apt update
RUN apt upgrade
RUN apt install -y python3-pip
RUN apt install -y wget
RUN wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
RUN DEBIAN_FRONTEND=noninteractive apt install -y ./google-chrome-stable_current_amd64.deb
RUN apt install -y xvfb
WORKDIR /usr/bin
RUN apt install unzip
RUN wget https://chromedriver.storage.googleapis.com/92.0.4515.107/chromedriver_linux64.zip
RUN unzip chromedriver_linux64.zip
RUN rm chromedriver_linux64.zip
RUN mkdir email-scraper
WORKDIR /home/email-scraper
COPY .env .
COPY requirements.txt .
RUN pip3 install -r requirements.txt
RUN mkdir src
WORKDIR /home/email-scraper/src
COPY src .
ENTRYPOINT [ "python3", "main.py" ]