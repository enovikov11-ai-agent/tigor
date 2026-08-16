  mosquitto:
    image: eclipse-mosquitto:2
    restart: unless-stopped
    container_name: mosquitto
    volumes:
      - /hdd/mosquitto/data:/mosquitto/data
      - /hdd/mosquitto/log:/mosquitto/log
      - /hdd/mosquitto/config:/mosquitto/config
    user: "1000:1000"
    security_opt:
      - no-new-privileges:true
    networks:
      - zigbee

  zigbee2mqtt:
    image: ghcr.io/koenkk/zigbee2mqtt:latest
    restart: unless-stopped
    container_name: zigbee2mqtt
    depends_on:
      - mosquitto
    volumes:
      - /hdd/zigbee2mqtt/data:/app/data
      - /run/udev:/run/udev:ro
    user: "1000:1000"
    security_opt:
      - no-new-privileges:true
    devices:
      - /dev/serial/by-id/usb-ZEPHYR_Zigbee_NCP_693A288EEE80B89C-if00:/dev/serial/by-id/usb-ZEPHYR_Zigbee_NCP_693A288EEE80B89C-if00
    environment:
      - TZ=Europe/Belgrade
    networks:
      - zigbee
    group_add:
      - dialout