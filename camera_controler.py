import cv2
import mediapipe as mp
import numpy as np
import time

mp_drawing = mp.solutions.drawing_utils
mp_pose = mp.solutions.pose

# Initialization
previous_shoulder_y = 0  # Assuming starting in a standing position
jump_in_progress = False
jump_counter = 0
crouch_counter = 0


def detect_movement(landmarks):
    global previous_shoulder_y, jump_in_progress, jump_counter, crouch_counter

    # Calculate the average y-coordinate of both shoulders
    shoulder_y = (landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].y +
                  landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value].y) / 2

    # Calculate the average y-coordinate of both ankles
    ankle_y = (landmarks[mp_pose.PoseLandmark.LEFT_ANKLE.value].y +
               landmarks[mp_pose.PoseLandmark.RIGHT_ANKLE.value].y) / 2

    # Detect jump (significant upward movement)
    if not jump_in_progress and previous_shoulder_y - shoulder_y > 0.05:  # Threshold for jump start
        jump_in_progress = True
    elif jump_in_progress and shoulder_y - previous_shoulder_y > 0.05:  # Threshold for jump end
        jump_in_progress = False
        jump_counter += 1

    # Calculate the distance between shoulders and ankles
    distance = ankle_y - shoulder_y
    # Detect crouch (significant downward movement)
    # Assuming a lower threshold indicates a crouch
    if distance < 0.8:
        crouch_counter += 1

    previous_shoulder_y = shoulder_y
    return jump_counter, crouch_counter


# Video Feed
cap = cv2.VideoCapture(0)

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

            jumps, crouches = detect_movement(landmarks)

        except:
            pass

        # Display jump and crouch count
        cv2.putText(image, f'Jumps: {jumps}', (10, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
        cv2.putText(image, f'Crouches: {crouches}', (10, 100),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)

        cv2.imshow('Mediapipe Feed', image)

        if cv2.waitKey(10) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
