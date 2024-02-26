# import, set up 'correct' paths for silicon macs 
import os
home_dir = os.path.expanduser("~")
camera_optn = 0

if home_dir == "/Users/nat":
    mediapipe_dylibs_path = "/Users/nat/Documents/coding/bris_hack_2024/venv/lib/python3.9/site-packages/mediapipe/.dylibs"
    os.environ["DYLD_LIBRARY_PATH"] = mediapipe_dylibs_path + ":" + os.environ.get("DYLD_LIBRARY_PATH", "")
    camera_optn = 1

import cv2
import mediapipe as mp
import numpy as np
import asyncio

mp_drawing = mp.solutions.drawing_utils
mp_pose = mp.solutions.pose

def draw_connections(image, landmarks):
    # Render detections
    mp_drawing.draw_landmarks(image, landmarks, mp_pose.POSE_CONNECTIONS,
                        mp_drawing.DrawingSpec(
                            color=(245, 117, 66), thickness=2, circle_radius=2),
                        mp_drawing.DrawingSpec(
                            color=(245, 66, 230), thickness=2, circle_radius=2)
                        )

class Person():
    def __init__(self, setup_time) -> None:
        """
        Create a new Person instance
        Args:
            setup_time : in seconds, how long to wait before recording
                the default max / min head heights.
        """
        
        self.cap = cv2.VideoCapture(camera_optn) # video feed
        self.pose = mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)

        self.head_height = 0.5 # 0 bottom to 1 top
        self.thigh = None
        self.nose = None

        self.landmarks = None
        
        asyncio.create_task(self.set_head_extremeties(setup_time))

    async def set_head_extremeties(self, setup_time):
        """
        Wait setup_time seconds, then record max min head heights.
        Args:
            setup_time : in seconds, how long to wait before recording
        """
        
        await asyncio.sleep(setup_time) 

        landmarks, _ = self.get_landmarks()
        landmarks = landmarks.landmark
        
        # set max as nose
        self.nose = landmarks[0].y

        # set min as half way between hips and knees
        hip_avg =  (landmarks[23].y + landmarks[24].y) / 2
        knee_avg = (landmarks[25].y + landmarks[26].y) / 2
        self.thigh = (hip_avg + knee_avg) / 2

        print(f"setup complete: nose {self.nose}, thigh {self.thigh}")

    def get_player_height(self, landmark):
        """
        Returns the height of the player, min 0
        """
        
        # return 0 if the head max / mins are not set yet
        if self.thigh is None or self.nose is None:
            print("thigh or nose is none, player height: 0")
            return 0
        
        head = landmark[0].y

        height = (head - self.nose) / (self.thigh - self.nose)

        # set min at 0 before returning
        height = max(0, height)
        print(f"got player height: {height}")
        return height
    
    def get_landmarks(self):
        """
        Returns landmarks, image
        """

        ok, frame = self.cap.read()
        if not ok:
            raise Exception("failed to read from camera")

        # Recolor image to RGB
        image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image.flags.writeable = False

        # Make detection
        results = self.pose.process(image)
        
        # Recolor back to BGR
        image.flags.writeable = True
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

        if results.pose_landmarks:
            print("got landmarks successfully")
            return results.pose_landmarks, image




async def main():
    height = 0
    person = Person()
    
    while True:
        try:
            landmarks, image = person.get_landmarks()
            height = person.get_player_height(landmarks.landmark)
            print(f"height {height}, nose {person.nose}, thigh {person.thigh}, head now {landmarks.landmark[0].y}")
            # display drawn landmarks
            draw_connections(image, landmarks)
        
        except Exception as err:
            raise Exception
            await asyncio.sleep(0.2)
            continue


        # Calculate the dimensions for the black box
        image_height, _, _ = image.shape
        box_point = int(image_height * height)
        box_top_left = (0, box_point)
        box_bottom_right = (50, box_point + 50)

        # Draw the black box
        cv2.rectangle(image, box_top_left, box_bottom_right, (0, 0, 0), -1)  # -1 fills the rectangle
        
        cv2.imshow('Mediapipe Feed', image)

        if cv2.waitKey(10) & 0xFF == ord('q'):
            break

        await asyncio.sleep(0.01)


if __name__ == "__main__":
    asyncio.run(main())