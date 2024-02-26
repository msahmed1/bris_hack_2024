# import files and set up 'correct' paths for silicon macs
import math
import mediapipe as mp
import cv2
import sys
import os
# Add the root directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from mqtt_client import MQTTClient

home_dir = os.path.expanduser("~")
camera_optn = 0

if home_dir == "/Users/nat":
    mediapipe_dylibs_path = "/Users/nat/Documents/coding/bris_hack_2024/venv/lib/python3.9/site-packages/mediapipe/.dylibs"
    os.environ["DYLD_LIBRARY_PATH"] = mediapipe_dylibs_path + \
        ":" + os.environ.get("DYLD_LIBRARY_PATH", "")
    camera_optn = 1

# MQTT setup
mqtt_client =  MQTTClient()

# Initialisation
previous_shoulder_y = 0
jump_in_progress = False
jump_counter = 0

previous_frame_crouch = False
crouch_counter = 0

mp_drawing = mp.solutions.drawing_utils
mp_pose = mp.solutions.pose

history = []
previous_frame_standing = False
standing_detected = False

previous_frame_stationary = False
previous_frame_in_start_pose = False

# Draw connections between landmarks on body
def draw_skeleton_on_body(image, landmarks):
    # Render detections
    mp_drawing.draw_landmarks(image, landmarks, mp_pose.POSE_CONNECTIONS,
                              mp_drawing.DrawingSpec(
                                  color=(245, 117, 66), thickness=2, circle_radius=2),
                              mp_drawing.DrawingSpec(
                                  color=(245, 66, 230), thickness=2, circle_radius=2)
                              )

def detect_jumping(landmarks):
    global previous_shoulder_y, jump_in_progress, jump_counter

    # Calculate the average y-coordinate of both shoulders
    shoulder_y = (landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].y +
                  landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value].y) / 2

    # Detect jump when shoulder moves up quickly compared to previous frame
    threshold=0.05
    if not jump_in_progress and previous_shoulder_y - shoulder_y > threshold:  # Threshold for jump start
        jump_in_progress = True
        mqtt_client.publish_state('up')
        print("jump detected")
    elif jump_in_progress and shoulder_y - previous_shoulder_y > threshold:  # Threshold for jump end
        jump_in_progress = False
        jump_counter += 1

    previous_shoulder_y = shoulder_y

def detect_crouching(landmarks):
    global previous_frame_crouch, crouch_counter

    # Detect crouch when wrist is below either knee
    left_wrist_y = landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value].y
    right_wrist_y = landmarks[mp_pose.PoseLandmark.RIGHT_WRIST.value].y
    left_knee_y = landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value].y
    right_knee_y = landmarks[mp_pose.PoseLandmark.RIGHT_KNEE.value].y

    crouch_detected = left_wrist_y > left_knee_y or right_wrist_y > right_knee_y

    if crouch_detected and not previous_frame_crouch:
        crouch_counter += 1
        mqtt_client.publish_state('down')
        print("crouch detected")
    previous_frame_crouch = crouch_detected

def detect_standing(landmarks):
    global previous_frame_standing, standing_detected

    # Detect standing when shoulders are above hips and hips are above knees
    shoulder_y = (landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].y +
                  landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value].y) / 2
    hip_y = (landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].y +
             landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value].y) / 2
    knee_y = (landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value].y +
              landmarks[mp_pose.PoseLandmark.RIGHT_KNEE.value].y) / 2
    
    standing_detected = shoulder_y < hip_y < knee_y and not jump_in_progress # and (knee_y - shoulder_y) > some_threshold:

    if standing_detected and not previous_frame_standing:  
        mqtt_client.publish_state('standing')
        print("standing detected")

    previous_frame_standing = standing_detected

def detect_stationary(landmarks):
    # Check if landmarks have not moved significantly based on history.
    global history, previous_frame_stationary

    current_positions = [(landmark.x, landmark.y) for landmark in landmarks]

    if not history:
        history.append(current_positions)
        return False
    
    # Calculate deltas for each landmark comparing to the last frame
    # Compare x and y coordinates of each landmark to find the distance between the two points
    deltas = [((current[0] - previous[0])**2 + (current[1] - previous[1])**2)**0.5 for current, previous in zip(current_positions, history[-1])]
    max_delta = max(deltas)

    history.append(current_positions)
    history_len_limit = 4
    if len(history) > history_len_limit:
        history.pop(0)

    threshold=0.05
    is_stationary = max_delta < threshold

    if is_stationary and not previous_frame_stationary:
        mqtt_client.publish_state('standing')
        print("stationary detected")
    
    previous_frame_stationary = is_stationary

def calculate_angle(point1, point2, point3):
    # Calculate the angle at point2 using the law of cosines given points in the order: point1, point2, point3.
    a = math.sqrt((point1.x - point2.x) ** 2 + (point1.y - point2.y) ** 2)
    b = math.sqrt((point3.x - point2.x) ** 2 + (point3.y - point2.y) ** 2)
    c = math.sqrt((point1.x - point3.x) ** 2 + (point1.y - point3.y) ** 2)
    
    angle = math.acos((a**2 + b**2 - c**2) / (2 * a * b))
    return math.degrees(angle)

def detect_start_pose(landmarks):
    # Check if the user is in the start pose which is defined by having the arms stretched out at 90 degrees relative to the body.
    global previous_frame_in_start_pose
    
    left_shoulder = landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value]
    right_shoulder = landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value]
    left_hip = landmarks[mp_pose.PoseLandmark.LEFT_HIP.value]
    right_hip = landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value]
    left_elbow = landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value]
    right_elbow = landmarks[mp_pose.PoseLandmark.RIGHT_ELBOW.value]
    
    # Calculate angles at the shoulders
    left_angle = calculate_angle(left_hip, left_shoulder, left_elbow)
    right_angle = calculate_angle(right_hip, right_shoulder, right_elbow)
    
    # Check if both angles are close to 90 degrees
    threshold = 10
    angle_threshold = threshold # Define how close to 90 degrees the angles should be
    in_start_pose = abs(90 - left_angle) < angle_threshold and abs(90 - right_angle) < angle_threshold
    
    if in_start_pose and not previous_frame_in_start_pose:
        mqtt_client.publish_state('start_pose')
        print("Start pose detected")
    
    previous_frame_in_start_pose = in_start_pose

# Video Feed
cap = cv2.VideoCapture(camera_optn)

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

        # Resize the frame to new dimensions
        desired_width = 640
        desired_height = 360
        resized_image = cv2.resize(image, (desired_width, desired_height))

        try:
            landmarks = results.pose_landmarks.landmark
            detect_crouching(landmarks)
            detect_jumping(landmarks)
            # detect_standing(landmarks)
            detect_stationary(landmarks)
            detect_start_pose(landmarks)
        except:
            pass

        # Display jump and crouch count for debugging
        cv2.putText(resized_image, f'Jumps: {jump_counter}', (10, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
        cv2.putText(resized_image, f'Crouches: {crouch_counter}', (10, 100),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)

        draw_skeleton_on_body(resized_image, results.pose_landmarks)

        cv2.imshow('Mediapipe Feed', resized_image)

        if cv2.waitKey(10) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
