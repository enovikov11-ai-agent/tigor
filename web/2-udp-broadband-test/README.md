<h3>Преднастройка</h3>

`sudo apt install default-jdk`  

<h3>Запуск ServerEchoer нативно</h3>

Копируем `ServerEchoer.java` на сервер  
Компилим `javac ServerEchoer.java`  
Запускаем `java ServerEchoer 1234`  
Нужно чтобы 1234 UDP порт был разрешен в фаерволле  

Он будет ловить сообщения и отбивать обратно закодированный туда таймстемп и размер пакета  

<h3>Запуск ServerEchoer в docker</h3>

`sudo docker-compose up -d`

<h3>Запуск ChannelProber нативно</h3>

На клиенте `javac ChannelProber.java`  
Запускаем `java ChannelProber ser.ver.i.p 1234`  
Нужно чтобы 1234 UDP порт был разрешен в фаерволле  

Будет раз в 30мс кидать 65КБ пакеты и писать сколько времени заняло хождение его туда и обратно и сколько отправка. Все в наносекундах в виде JSON строк в stdout  

<h3>Интересные ссылки</h3>

Отправка udp пакетов в x86 asm https://github.com/Drqonic/ASM-Flooder/blob/master/UDP.asm  

<h3>WIP</h3>

У клиента есть два буфера, которые периодически меняются местами

он раз в 30мс отправляет сообщение заданного размера и записывает его id(timestamp), gps, 2G/3G/4G
когда приходит ответ он записывает confirmedAtNs

раз в 30 сообщений, буфер выгружается в лог, переключается на другой и зануляется
в этот момент подсчитывается latency и packet loss  и показывается на экране

gradle init --type kotlin-application --dsl kotlin  