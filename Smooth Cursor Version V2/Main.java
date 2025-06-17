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

                int cameraWidth = 1920;
                int cameraHeight = 1080;

                int screenX = (int)((x / (double)cameraWidth) * screenSize.width);
                int screenY = (int)((y / (double)cameraHeight) * screenSize.height);
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

                        case "RCLICK":
                            robot.mousePress(InputEvent.BUTTON3_DOWN_MASK);
                            robot.mouseRelease(InputEvent.BUTTON3_DOWN_MASK);
                            System.out.println("Right click performed");
                            break;
                        case "SCROLL_UP":
                            robot.mouseWheel(-1); // Negative for scroll up
                            System.out.println("⬆️ Scrolled Up");
                            break;
                        case "SCROLL_DOWN":
                            robot.mouseWheel(1); // Positive for scroll down
                            System.out.println("⬇️ Scrolled Down");
                            break;
                        case "DCLICK":
                            robot.mousePress(InputEvent.BUTTON1_DOWN_MASK);
                            robot.mouseRelease(InputEvent.BUTTON1_DOWN_MASK);
                            Thread.sleep(100); // brief pause to simulate natural double-click
                            robot.mousePress(InputEvent.BUTTON1_DOWN_MASK);
                            robot.mouseRelease(InputEvent.BUTTON1_DOWN_MASK);
                            System.out.println("🖱️ Double click performed");
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