import java.net.DatagramPacket;
import java.net.DatagramSocket;

public class ServerEchoer {
    private final static int MAX_PACKET_SIZE = 66000;

    @SuppressWarnings("resource")
    public static void main(String[] args) throws Exception {
        if (args.length != 1) {
            System.out.println("Usage: ServerEchoer port");
            return;
        }

        int listenPort = Integer.parseInt(args[0]);
        DatagramSocket socket = new DatagramSocket(listenPort);

        while (true) {
            byte[] receivingBuffer = new byte[MAX_PACKET_SIZE];
            DatagramPacket receivingPacket = new DatagramPacket(receivingBuffer, receivingBuffer.length);
            socket.receive(receivingPacket);
            String receivedData = new String(receivingPacket.getData());
            String[] parsedData = receivedData.split("@", 2);

            byte[] sendingBuffer = (parsedData[0] + "@" + receivingPacket.getLength()).getBytes();
            DatagramPacket sendingPacket = new DatagramPacket(sendingBuffer, sendingBuffer.length,
                    receivingPacket.getAddress(), receivingPacket.getPort());
            socket.send(sendingPacket);
        }
    }
}
