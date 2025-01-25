# posture_detection.py
import cv2
import mediapipe as mp
import numpy as np
from PIL import Image, ImageTk
from collections import deque
from statistics import mode

class PostureDetector:
    def __init__(self):
        self.mp_pose = mp.solutions.pose
        self.pose = self.mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)
        self.mp_drawing = mp.solutions.drawing_utils
        self.cap = None
        self.current_feedback = "No posture data"
        # Add buffer for storing posture data
        self.posture_buffer = deque(maxlen=30)  # Store last 30 readings

    def initialize_camera(self):
        self.cap = cv2.VideoCapture(0)
        return self.cap.isOpened()

    def calculate_angle(self, a, b, c):
        a = np.array(a)
        b = np.array(b)
        c = np.array(c)
        
        radians = np.arctan2(c[1] - b[1], c[0] - b[0]) - np.arctan2(a[1] - b[1], a[0] - b[0])
        angle = np.abs(radians * 180.0 / np.pi)
        if angle > 180.0:
            angle = 360 - angle
        return angle

    def check_posture(self, landmarks):
        left_shoulder = [landmarks[self.mp_pose.PoseLandmark.LEFT_SHOULDER.value].x,
                        landmarks[self.mp_pose.PoseLandmark.LEFT_SHOULDER.value].y]
        right_shoulder = [landmarks[self.mp_pose.PoseLandmark.RIGHT_SHOULDER.value].x,
                         landmarks[self.mp_pose.PoseLandmark.RIGHT_SHOULDER.value].y]
        left_hip = [landmarks[self.mp_pose.PoseLandmark.LEFT_HIP.value].x,
                   landmarks[self.mp_pose.PoseLandmark.LEFT_HIP.value].y]
        right_hip = [landmarks[self.mp_pose.PoseLandmark.RIGHT_HIP.value].x,
                    landmarks[self.mp_pose.PoseLandmark.RIGHT_HIP.value].y]
        left_knee = [landmarks[self.mp_pose.PoseLandmark.LEFT_KNEE.value].x,
                    landmarks[self.mp_pose.PoseLandmark.LEFT_KNEE.value].y]
        
        left_back_angle = self.calculate_angle(left_shoulder, left_hip, left_knee)
        shoulder_diff = abs(left_shoulder[1] - right_shoulder[1])
        forward_lean = abs(left_shoulder[0] - left_hip[0])
        
        feedback = []
        
        if left_back_angle < 172:
            feedback.append("Slouching")
        if shoulder_diff > 0.05:
            feedback.append("Uneven Shoulders")
        if forward_lean > 0.1:
            feedback.append("Forward Head Posture")
        
        return "Bad Posture: " + ", ".join(feedback) if feedback else "Good Posture", left_back_angle, forward_lean, shoulder_diff

    def get_frame(self):
        if self.cap is None or not self.cap.isOpened():
            return None, "Camera not initialized", None, None, None

        ret, frame = self.cap.read()
        if not ret:
            return None, "Failed to capture frame", None, None, None

        frame = cv2.resize(frame, (640, 360))
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        results = self.pose.process(frame_rgb)
        
        if results.pose_landmarks:
            self.mp_drawing.draw_landmarks(frame_rgb, results.pose_landmarks, self.mp_pose.POSE_CONNECTIONS)
            feedback, back_angle, forward_lean, shoulder_diff = self.check_posture(results.pose_landmarks.landmark)
            self.current_feedback = feedback
            # Add feedback to buffer
            self.posture_buffer.append(feedback)
        else:
            feedback, back_angle, forward_lean, shoulder_diff = "No posture data", None, None, None
        
        image = Image.fromarray(frame_rgb)
        photo = ImageTk.PhotoImage(image=image)
        return photo, self.current_feedback, back_angle, forward_lean, shoulder_diff

    def get_aggregated_posture(self):
        """Calculate the most common posture status from the buffer"""
        if len(self.posture_buffer) > 0:
            try:
                return mode(self.posture_buffer)
            except:
                return list(self.posture_buffer)[-1]  # Return latest if no mode
        return "No posture data"

    def release(self):
        if self.cap is not None and self.cap.isOpened():
            self.cap.release()