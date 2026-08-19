import java.io.IOException;
import java.net.DatagramPacket;
import java.net.DatagramSocket;
import java.net.InetAddress;
import java.nio.charset.Charset;
import java.util.Random;

public class ChannelProber {
    private final static Random random = new Random();

    private final static int BASIC_SIZE = 65000;
    private final static int MAX_PACKET_SIZE = 65300;
    private final static long FRAME_DELAY = 30;

    private final static Charset ascii = Charset.forName("US-ASCII");

    private static byte[] makeMessage(int length) {
        byte[] randomBytes = new byte[length];
        random.nextBytes(randomBytes);

        String timestamp = String.valueOf(System.nanoTime());
        String randomString = new String(randomBytes, ascii);

        return (timestamp + "@" + randomString).getBytes(ascii);
    }

    @SuppressWarnings("resource")
    public static void main(String[] args) throws Exception {
        if (args.length != 2) {
            System.out.println("Usage: ChannelProber host port");
            return;
        }

        InetAddress sendHost = InetAddress.getByName(args[0]);
        int sendPort = Integer.parseInt(args[1]);
        DatagramSocket socket = new DatagramSocket();

        Thread receceiverThread = new Thread(new Runnable() {

            @Override
            public void run() {
                while (true) {
                    try {
                        byte[] receivingBuffer = new byte[MAX_PACKET_SIZE];
                        DatagramPacket receivingPacket = new DatagramPacket(receivingBuffer, receivingBuffer.length);
                        socket.receive(receivingPacket);
                        String receivedData = new String(receivingPacket.getData());

                        String[] parsedData = receivedData.split("@", 2);
                        long twoWayLatencyNs = System.nanoTime() - Long.parseLong(parsedData[0]);

                        System.out.println("{ \"twoWayLatencyNs\": " + String.valueOf(twoWayLatencyNs)
                                + ", \"packetSize\": " + parsedData[1] + " }");
                    } catch (IOException e) {
                        e.printStackTrace();
                    }
                }
            }

        });

        receceiverThread.start();

        long currentTime = System.nanoTime();

        while (true) {
            byte[] message = makeMessage(BASIC_SIZE);
            DatagramPacket packet = new DatagramPacket(message, message.length, sendHost, sendPort);
            socket.send(packet);

            long sendingProcessDurationNs = System.nanoTime() - currentTime;

            long sleep = FRAME_DELAY - (long) (sendingProcessDurationNs / 1e6);

            System.out.println("{ \"sendingProcessDurationNs\": " + String.valueOf(sendingProcessDurationNs)
                    + ", \"packetSize\": " + packet.getLength() + " }");

            if (sleep > 0) {
                Thread.sleep(sleep);
            }

            currentTime = System.nanoTime();
        }
    }
}
