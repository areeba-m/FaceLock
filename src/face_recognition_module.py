"""
Facial recognition module using face_recognition library
Handles face detection, encoding, and matching
"""
import cv2
import face_recognition
import numpy as np
from typing import List, Optional, Tuple
from config.settings import (
    FACE_RECOGNITION_TOLERANCE,
    FACE_ENCODING_MODEL,
    MIN_FACE_SIZE
)


class FaceRecognitionModule:
    """Handles facial recognition operations"""
    
    def __init__(self):
        self.tolerance = FACE_RECOGNITION_TOLERANCE
        self.model = FACE_ENCODING_MODEL
    
    def detect_faces(self, frame: np.ndarray) -> List[Tuple]:
        """
        Detect faces in a frame
        Returns list of (top, right, bottom, left) tuples
        """
        # Convert BGR to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Detect face locations
        face_locations = face_recognition.face_locations(rgb_frame, model='hog')
        
        # Filter small faces
        valid_faces = []
        for face_loc in face_locations:
            top, right, bottom, left = face_loc
            width = right - left
            height = bottom - top
            
            if width >= MIN_FACE_SIZE[0] and height >= MIN_FACE_SIZE[1]:
                valid_faces.append(face_loc)
        
        return valid_faces
    
    def get_face_encoding(self, frame: np.ndarray, face_location: Tuple) -> Optional[np.ndarray]:
        """
        Extract facial embedding from a detected face
        """
        try:
            # Convert BGR to RGB
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Get face encoding
            encodings = face_recognition.face_encodings(
                rgb_frame,
                [face_location],
                model=self.model
            )
            
            if encodings:
                return encodings[0]
            return None
        except Exception as e:
            print(f"Error extracting face encoding: {e}")
            return None
    
    def compare_faces(self, known_encodings: List[np.ndarray], unknown_encoding: np.ndarray) -> bool:
        """
        Compare unknown face encoding against known encodings
        Returns True if match found within tolerance
        """
        if not known_encodings or unknown_encoding is None:
            return False
        
        # Calculate face distances
        distances = face_recognition.face_distance(known_encodings, unknown_encoding)
        
        # Check if any distance is below tolerance
        return np.any(distances <= self.tolerance)
    
    def get_best_match_distance(self, known_encodings: List[np.ndarray], 
                                unknown_encoding: np.ndarray) -> float:
        """
        Get the minimum distance between unknown face and known faces
        """
        if not known_encodings or unknown_encoding is None:
            return float('inf')
        
        distances = face_recognition.face_distance(known_encodings, unknown_encoding)
        return float(np.min(distances))
    
    def draw_face_box(self, frame: np.ndarray, face_location: Tuple, 
                      label: str = "", color: Tuple = (0, 255, 0)) -> np.ndarray:
        """
        Draw bounding box around detected face
        """
        top, right, bottom, left = face_location
        
        # Draw rectangle
        cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
        
        # Draw label
        if label:
            cv2.rectangle(frame, (left, bottom - 35), (right, bottom), color, cv2.FILLED)
            cv2.putText(frame, label, (left + 6, bottom - 6),
                       cv2.FONT_HERSHEY_DUPLEX, 0.6, (255, 255, 255), 1)
        
        return frame
    
    def capture_face_sample(self, frame: np.ndarray) -> Optional[Tuple[np.ndarray, Tuple]]:
        """
        Capture a single face sample from frame
        Returns (encoding, face_location) tuple or None
        """
        face_locations = self.detect_faces(frame)
        
        if len(face_locations) != 1:
            return None
        
        face_location = face_locations[0]
        encoding = self.get_face_encoding(frame, face_location)
        
        if encoding is not None:
            return (encoding, face_location)
        
        return None
    
    def get_face_landmarks(self, frame: np.ndarray, face_location: Tuple) -> Optional[dict]:
        """
        Get facial landmarks for a detected face
        Used for blink detection and pose estimation
        """
        try:
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            landmarks = face_recognition.face_landmarks(rgb_frame, [face_location])
            
            if landmarks:
                return landmarks[0]
            return None
        except Exception as e:
            print(f"Error extracting face landmarks: {e}")
            return None


# Singleton instance
face_recognition_module = FaceRecognitionModule()