import cv2
import numpy as np
from PyQt6.QtGui import QImage, QPixmap
from collections import deque
from statistics import mode

class PostureDetector:
    def __init__(self, headless=False):
        self.cap = None
        self.current_feedback = "No posture data"
        self.posture_buffer = deque(maxlen=30)
        self.mediapipe_available = False
        self.headless = headless

        # Try to import mediapipe
        try:
            import mediapipe as mp
            self.mp_pose = mp.solutions.pose
            self.pose = self.mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)
            self.mp_drawing = mp.solutions.drawing_utils
            self.mediapipe_available = True
        except ImportError as e:
            print(f"MediaPipe import error: {e}")
            print("Running in fallback mode without pose detection")

        # Fallback mode parameters
        self.motion_threshold = 50
        self.prev_frame = None
        self.movement_buffer = deque(maxlen=30)

    def initialize_camera(self):
        try:
            self.cap = cv2.VideoCapture(0)
            if not self.cap.isOpened():
                print("Error: Could not open camera.")
                return False
            return True
        except Exception as e:
            print(f"Camera initialization error: {e}")
            return False

    def calculate_movement(self, frame):
        """Fallback method: Detect movement to estimate posture changes"""
        if self.prev_frame is None:
            self.prev_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            return 0

        current_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        frame_diff = cv2.absdiff(self.prev_frame, current_frame)
        movement = np.mean(frame_diff)

        self.prev_frame = current_frame
        return movement

    def get_frame(self):
        if self.cap is None or not self.cap.isOpened():
            print("Camera not initialized or not opened.")
            return None, "Camera not initialized", None, None, None

        try:
            ret, frame = self.cap.read()
            if not ret:
                print("Failed to capture frame from camera.")
                return None, "Failed to capture frame", None, None, None

            # Resize frame
            frame = cv2.resize(frame, (640, 480))
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            back_angle = None
            forward_lean = None
            shoulder_diff = None

            if self.mediapipe_available:
                try:
                    # MediaPipe pose detection
                    results = self.pose.process(frame_rgb)
                    if results.pose_landmarks:
                        if not self.headless:
                            self.mp_drawing.draw_landmarks(
                                frame_rgb,
                                results.pose_landmarks,
                                self.mp_pose.POSE_CONNECTIONS
                            )
                        feedback, back_angle, forward_lean, shoulder_diff = self.analyze_pose(results.pose_landmarks.landmark)
                    else:
                        feedback = "No pose detected"
                except Exception as e:
                    print(f"Pose detection error: {e}")
                    feedback = "Pose detection error"
            else:
                # Fallback movement-based detection
                movement = self.calculate_movement(frame)
                self.movement_buffer.append(movement)
                avg_movement = sum(self.movement_buffer) / len(self.movement_buffer)

                if avg_movement > self.motion_threshold:
                    feedback = "Movement detected - possible posture change"
                else:
                    feedback = "Limited movement detected"

            if not self.headless:
                try:
                    h, w, ch = frame_rgb.shape
                    qt_image = QImage(frame_rgb.data, w, h, ch * w, QImage.Format.Format_RGB888)
                    qt_pixmap = QPixmap.fromImage(qt_image)  # Convert QImage to QPixmap
                except Exception as e:
                    print(f"QPixmap/QImage creation error: {e}")
                    qt_pixmap = None
            else:
                qt_pixmap = None

            self.current_feedback = feedback
            self.posture_buffer.append(feedback)

            return qt_pixmap, feedback, back_angle, forward_lean, shoulder_diff
        except Exception as e:
            print(f"General error in get_frame: {e}")
            return None, f"Frame processing error: {e}", None, None, None

    def analyze_pose(self, landmarks):
        """Analyze pose landmarks and return feedback"""
        try:
            # Extract key points
            left_shoulder = [landmarks[self.mp_pose.PoseLandmark.LEFT_SHOULDER.value].x,
                           landmarks[self.mp_pose.PoseLandmark.LEFT_SHOULDER.value].y]
            right_shoulder = [landmarks[self.mp_pose.PoseLandmark.RIGHT_SHOULDER.value].x,
                            landmarks[self.mp_pose.PoseLandmark.RIGHT_SHOULDER.value].y]
            left_hip = [landmarks[self.mp_pose.PoseLandmark.LEFT_HIP.value].x,
                       landmarks[self.mp_pose.PoseLandmark.LEFT_HIP.value].y]

            # Calculate metrics
            shoulder_diff = abs(left_shoulder[1] - right_shoulder[1])
            forward_lean = abs(left_shoulder[0] - left_hip[0])
            back_angle = np.arctan2(left_shoulder[1] - left_hip[1], left_shoulder[0] - left_hip[0]) * 180 / np.pi

            # Analyze posture
            issues = []
            if shoulder_diff > 0.05:
                issues.append("Uneven shoulders")
            if forward_lean > 0.1:
                issues.append("Forward lean")

            feedback = "Bad posture: " + ", ".join(issues) if issues else "Good posture"
            return feedback, back_angle, forward_lean, shoulder_diff

        except Exception as e:
            print(f"Pose analysis error: {e}")
            return "Pose analysis error", None, None, None

    def get_aggregated_posture(self):
        """Calculate the most common posture status from the buffer"""
        if len(self.posture_buffer) > 0:
            try:
                return mode(self.posture_buffer)
            except:
                return list(self.posture_buffer)[-1]
        return "No posture data"

    def release(self):
        """Clean up resources"""
        if self.cap is not None and self.cap.isOpened():
            self.cap.release()
        if self.mediapipe_available:
            try:
                self.pose.close()
            except:
                pass
