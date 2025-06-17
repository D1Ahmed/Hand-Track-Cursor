import cv2
import mediapipe as mp
import socket
import struct
import time
import math
import pyautogui  # For screen size

# Smoothing and speed control
prev_x, prev_y = 0, 0
alpha = 0.7        # Smoothing (0 < alpha < 1)
speed_factor = 1.8  # >1 = faster cursor, <1 = slower cursor

# MediaPipe setup
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=1)
mp_draw = mp.solutions.drawing_utils
cap = cv2.VideoCapture(1)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)

# Screen size
screen_width, screen_height = pyautogui.size()

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

            # Get raw hand landmark position
            raw_cx = handLms.landmark[12].x * w
            raw_cy = handLms.landmark[12].y * h

            # Apply smoothing
            smoothed_cx = prev_x * alpha + raw_cx * (1 - alpha)
            smoothed_cy = prev_y * alpha + raw_cy * (1 - alpha)

            prev_x, prev_y = smoothed_cx, smoothed_cy

            # Scale to screen with speed factor
            screen_cx = int((smoothed_cx / w) * screen_width * speed_factor)
            screen_cy = int((smoothed_cy / h) * screen_height * speed_factor)

            # Clamp to screen bounds
            screen_cx = min(max(screen_cx, 0), screen_width - 1)
            screen_cy = min(max(screen_cy, 0), screen_height - 1)

            try:
                client_socket.sendall(struct.pack('>ii', screen_cx, screen_cy))
            except Exception as e:
                print(f"❌ Cursor send error: {e}")
                break

            # Gesture landmarks
            thumb_tip = handLms.landmark[4]
            index_tip = handLms.landmark[8]
            pinky_tip = handLms.landmark[20]
            thumb_base = handLms.landmark[5]
            now = time.time()

            # 👆 Click Gesture
            if math.hypot((thumb_tip.x - index_tip.x) * w, (thumb_tip.y - index_tip.y) * h) < 30:
                if now - hand_tracker.last_click < 0.4:
                    try:
                        client_socket.send(b'DCLICK')
                        print("🖱️ Double click gesture triggered")
                    except Exception as e:
                        print("❌ Double-click send error:", e)
                    hand_tracker.last_click = 0
                elif now - hand_tracker.last_click > 1:
                    try:
                        client_socket.send(b'LCLICK')
                        print("🖱️ Left click gesture triggered")
                    except Exception as e:
                        print("❌ Left-click send error:", e)
                    hand_tracker.last_click = now

            # 🤚 Right Click Gesture
            if math.hypot((thumb_tip.x - pinky_tip.x) * w, (thumb_tip.y - pinky_tip.y) * h) < 30 and now - hand_tracker.last_click > 1:
                try:
                    client_socket.send(b'RCLICK')
                    hand_tracker.last_click = now
                    print("🖱️ Right click gesture triggered")
                except Exception as e:
                    print("❌ Right-click send error:", e)

            # 👍 Scroll Gesture
            if abs(thumb_tip.x - thumb_base.x) < 0.1:
                if thumb_tip.y < thumb_base.y and now - hand_tracker.last_scroll > 1:
                    try:
                        client_socket.send(b'SCROLL_UP')
                        hand_tracker.last_scroll = now
                        print("⬆️ Scroll up gesture")
                    except Exception as e:
                        print("❌ Scroll up send error:", e)
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
