import cv2
import mediapipe as mp
import socket
import struct
import time
import math

mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=1)
mp_draw = mp.solutions.drawing_utils
cap = cv2.VideoCapture(1)  # Use 0 or 1 depending on your webcam

# Socket setup
HOST = '127.0.0.1'
PORT = 5050
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect((HOST, PORT))
print("✅ Connected to Java server!")


class hand_tracker:
    last_click = 0
    last_scroll = 0


while True:
    success, frame = cap.read()
    if not success:
        break

    frame = cv2.flip(frame, 1)
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(frame_rgb)
    h, w, _ = frame.shape

    if results.multi_hand_landmarks:
        for handLms in results.multi_hand_landmarks:
            mp_draw.draw_landmarks(frame, handLms, mp_hands.HAND_CONNECTIONS)

            # 🟢 Use middle finger tip (12) to move cursor
            cx = int(handLms.landmark[12].x * w)
            cy = int(handLms.landmark[12].y * h)

            try:
                client_socket.sendall(struct.pack('>ii', cx, cy))
            except Exception as e:
                print(f"❌ Cursor send error: {e}")
                break

            # ✋ Left click gesture: thumb tip (4) and index tip (8)
            thumb_tip = handLms.landmark[4]
            index_tip = handLms.landmark[8]
            thumb_index_distance = math.hypot(
                (thumb_tip.x - index_tip.x) * w,
                (thumb_tip.y - index_tip.y) * h
            )

            now = time.time()

            if thumb_index_distance < 30 and now - hand_tracker.last_click > 1:
                try:
                    client_socket.send(b'LCLICK')
                    hand_tracker.last_click = now
                    print("🖱️ Left click gesture triggered")
                except Exception as e:
                    print("❌ Left-click send error:", e)

            # 👍 Scroll Gesture (Thumbs Up / Down using thumb vs base knuckle)
            thumb_base = handLms.landmark[5]  # index MCP joint
            if abs(thumb_tip.x - thumb_base.x) < 0.1:  # roughly vertical
                # Scroll Up
                if thumb_tip.y < thumb_base.y and now - hand_tracker.last_scroll > 1:
                    try:
                        client_socket.send(b'SCROLL_UP')
                        hand_tracker.last_scroll = now
                        print("⬆️ Scroll up gesture")
                    except Exception as e:
                        print("❌ Scroll up send error:", e)

                # Scroll Down
                elif thumb_tip.y > thumb_base.y and now - hand_tracker.last_scroll > 1:
                    try:
                        client_socket.send(b'SCROLL_DOWN')
                        hand_tracker.last_scroll = now
                        print("⬇️ Scroll down gesture")
                    except Exception as e:
                        print("❌ Scroll down send error:", e)

    cv2.imshow("🖐 MediaPipe Hand Tracking", frame)
    if cv2.waitKey(1) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()
client_socket.close()
