import java.awt.*;
import java.awt.event.InputEvent;
import java.io.*;
import java.net.ServerSocket;
import java.net.Socket;
import java.nio.ByteBuffer;

class HandControlledMouse {
    public static void main(String[] args) {
        try {
            Robot robot = new Robot();
            Dimension screenSize = Toolkit.getDefaultToolkit().getScreenSize();

            ServerSocket server = new ServerSocket(5050);
            System.out.println("Waiting for Python connection...");
            Socket client = server.accept();
            System.out.println("✅ Connected to Python!");

            DataInputStream dis = new DataInputStream(client.getInputStream());

            while (true) {
                // Read exactly 8 bytes for cursor position
                byte[] coords = new byte[8];
                dis.readFully(coords);
                int x = ByteBuffer.wrap(coords, 0, 4).getInt();
                int y = ByteBuffer.wrap(coords, 4, 4).getInt();

                int screenX = (int)((x / 640.0) * screenSize.width);
                int screenY = (int)((y / 480.0) * screenSize.height);
                robot.mouseMove(screenX, screenY);

                // Check if there's more data available (i.e. a command)
                if (dis.available() > 0) {
                    byte[] cmdBuf = new byte[dis.available()];
                    dis.readFully(cmdBuf);
                    String command = new String(cmdBuf).trim();

                    switch (command) {
                        case "LCLICK":
                            robot.mousePress(InputEvent.BUTTON1_DOWN_MASK);
                            robot.mouseRelease(InputEvent.BUTTON1_DOWN_MASK);
                            System.out.println("🖱️ Left click performed");
                            break;
                        case "SCROLL_UP":
                            robot.mouseWheel(-1); // Negative for scroll up
                            System.out.println("⬆️ Scrolled Up");
                            break;
                        case "SCROLL_DOWN":
                            robot.mouseWheel(1); // Positive for scroll down
                            System.out.println("⬇️ Scrolled Down");
                            break;
                        default:
                            System.out.println("⚠️ Unknown command: " + command);
                    }
                }
            }
        } catch (Exception e) {
            e.printStackTrace();
        }
    }
}
