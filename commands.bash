# pi server
sudo docker build  -t fastapi-pi . && sudo docker run --privileged  -d -p 8000:8000 fastapi-pi
# smart home 
sudo docker run -d --name home-assistant --restart unless-stopped -e TZ=Asia/Jerusalem -v /home/ben/home-assistant:/config --network=host ghcr.io/home-assistant/home-assistant:stable
