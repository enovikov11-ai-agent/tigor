Toy car controlled over internet  

You need:  
- Android smartphone to use in car
- USG OTG cable
- Any smartphone/PC to control car
- Own ubuntu server, accesible from internet
- [optional] domain for server
- Arduino Leonardo
- Mechanical platform of car
- Servo motor
- DC motor
- Motor shield

Howto:
- Upload this repo to server and run `node ./server/`
- Connect servo to 9 pin
- Front motor pin to 12
- Back motor pin to 13
- Upload firmware from `arduino`
- Build android app and upload to device
- Open app and configure server URL
- Connect arduino to smartphone
- Allow opening app on connection
- Navigate to server URL from device and control car