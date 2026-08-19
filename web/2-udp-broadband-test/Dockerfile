FROM openjdk:7

COPY ServerEchoer.java /root
WORKDIR /root

RUN javac ServerEchoer.java

CMD ["java", "ServerEchoer", "1234"]