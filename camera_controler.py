# import, set up 'correct' paths for silicon macs
import mediapipe as mp
import cv2
import os
import paho.mqtt.client as mqtt
import threading
home_dir = os.path.expanduser("~")
camera_optn = 0

if home_dir == "/Users/nat":
    mediapipe_dylibs_path = "/Users/nat/Documents/coding/bris_hack_2024/venv/lib/python3.9/site-packages/mediapipe/.dylibs"
    os.environ["DYLD_LIBRARY_PATH"] = mediapipe_dylibs_path + \
        ":" + os.environ.get("DYLD_LIBRARY_PATH", "")
    camera_optn = 1

# MQTT setup
broker_address = 'localhost'  # Define broker address
port = 1883  # Default MQTT port
keepalive = 60  # Keepalive interval

mqtt_client = mqtt.Client()  # Create MQTT client
# Connect to the MQTT broker
mqtt_client.connect(broker_address, port, keepalive)
# Start the loop in a separate thread
threading.Thread(target=mqtt_client.loop_forever).start()
mqtt_client.subscribe("robot/userInput")


def publish_state(message):
    mqtt_client.publish("robot/userInput", message)


mp_drawing = mp.solutions.drawing_utils
mp_pose = mp.solutions.pose

# Initialisation
previous_shoulder_y = 0
jump_in_progress = False
jump_counter = 0

previous_frame_crouch = False
crouch_counter = 0


def draw_connections(image, landmarks):
    # Render detections
    mp_drawing.draw_landmarks(image, landmarks, mp_pose.POSE_CONNECTIONS,
                              mp_drawing.DrawingSpec(
                                  color=(245, 117, 66), thickness=2, circle_radius=2),
                              mp_drawing.DrawingSpec(
                                  color=(245, 66, 230), thickness=2, circle_radius=2)
                              )


def detect_movement(landmarks):
    global previous_shoulder_y, jump_in_progress, jump_counter, previous_frame_crouch, crouch_counter

    # Calculate the average y-coordinate of both shoulders
    shoulder_y = (landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].y +
                  landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value].y) / 2

    # Detect jump
    if not jump_in_progress and previous_shoulder_y - shoulder_y > 0.05:  # Threshold for jump start
        jump_in_progress = True
        publish_state('up')
    elif jump_in_progress and shoulder_y - previous_shoulder_y > 0.05:  # Threshold for jump end
        jump_in_progress = False
        jump_counter += 1

    previous_shoulder_y = shoulder_y

    # For crouch detection based on wrist below knee
    left_wrist_y = landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value].y
    right_wrist_y = landmarks[mp_pose.PoseLandmark.RIGHT_WRIST.value].y
    left_knee_y = landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value].y
    right_knee_y = landmarks[mp_pose.PoseLandmark.RIGHT_KNEE.value].y

    # Detect crouch when wrist is below either knee
    crouch_detected = left_wrist_y > left_knee_y or right_wrist_y > right_knee_y

    if crouch_detected and not previous_frame_crouch:
        crouch_counter += 1
        publish_state('down')

    previous_frame_crouch = crouch_detected

    hip_y = (landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].y +
             landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value].y) / 2
    knee_y = (landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value].y +
              landmarks[mp_pose.PoseLandmark.RIGHT_KNEE.value].y) / 2

    # and (knee_y - shoulder_y) > some_threshold:
    if shoulder_y < hip_y < knee_y and not jump_in_progress:
        publish_state('standing')

    return jump_counter, crouch_counter


# Video Feed
cap = cv2.VideoCapture(camera_optn)

# Initialize jumps and crouches before the try block
jumps, crouches = 0, 0

# Setup mediapipe instance
with mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5) as pose:
    while cap.isOpened():
        ret, frame = cap.read()

        # Recolor image to RGB
        image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image.flags.writeable = False

        # Make detection
        results = pose.process(image)

        # Recolor back to BGR
        image.flags.writeable = True
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

        try:
            landmarks = results.pose_landmarks.landmark

            detect_movement(landmarks)

        except:
            pass

        # Display jump and crouch count
        cv2.putText(image, f'Jumps: {jump_counter}', (10, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
        cv2.putText(image, f'Crouches: {crouch_counter}', (10, 100),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)

        draw_connections(image, results.pose_landmarks)

        cv2.imshow('Mediapipe Feed', image)

        if cv2.waitKey(10) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
