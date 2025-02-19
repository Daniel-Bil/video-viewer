import cv2
import numpy as np
import rembg
import mediapipe as mp

def remove_background_function(frame):
    out = rembg.remove(frame)
    # Convert RGBA to RGB (remove alpha channel)
    frame_rgb = cv2.cvtColor(out, cv2.COLOR_RGBA2RGB)
    return frame_rgb


mp_face_detection = mp.solutions.face_detection
face_detection = mp_face_detection.FaceDetection(model_selection=1, min_detection_confidence=0.5)

def blur_faces(frame):
    """Detect faces using Mediapipe and apply a blur effect."""
    frame = np.array(frame, dtype=np.uint8).copy()  # Ensure frame is writable
    h, w, _ = frame.shape

    # Convert frame to RGB (Mediapipe needs RGB input)
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # Detect faces
    results = face_detection.process(rgb_frame)

    # Apply blur to detected faces
    if results.detections:
        for detection in results.detections:
            bbox = detection.location_data.relative_bounding_box
            x, y, w_bbox, h_bbox = (
                int(bbox.xmin * w),
                int(bbox.ymin * h),
                int(bbox.width * w),
                int(bbox.height * h),
            )

            # Ensure the bounding box is within image dimensions
            x, y, w_bbox, h_bbox = max(0, x), max(0, y), min(w, w_bbox), min(h, h_bbox)

            # Extract and blur face
            face_region = frame[y:y + h_bbox, x:x + w_bbox].copy()
            blurred_face = cv2.GaussianBlur(face_region, (51, 51), 40)
            frame[y:y + h_bbox, x:x + w_bbox] = blurred_face  # Replace face with blurred version

    return frame
