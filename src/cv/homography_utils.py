"""Homography utilities for court calibration."""

import cv2
import numpy as np
from typing import List, Tuple, Dict, Optional
import json
from pathlib import Path

from ..utils.io import save_json, load_json
from ..utils.paths import SITE_DATA


class CourtCalibrator:
    """Tennis court calibration using homography."""
    
    def __init__(self):
        # Standard tennis court dimensions (in meters)
        # Full court is 23.77m x 10.97m
        self.court_points_3d = np.array([
            [0, 0],          # Bottom left corner
            [23.77, 0],      # Bottom right corner  
            [23.77, 10.97],  # Top right corner
            [0, 10.97]       # Top left corner
        ], dtype=np.float32)
        
        # Service boxes and key court lines
        self.service_line_y = 6.40  # Distance from net to service line
        self.net_y = 5.485  # Half court length
        
        self.homography_matrix = None
        self.court_corners_2d = None
    
    def detect_court_lines(self, image: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """Detect court lines using edge detection."""
        
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Apply Gaussian blur
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # Edge detection
        edges = cv2.Canny(blurred, 50, 150, apertureSize=3)
        
        # Detect lines using Hough transform
        lines = cv2.HoughLinesP(
            edges, 
            rho=1, 
            theta=np.pi/180, 
            threshold=100,
            minLineLength=100,
            maxLineGap=10
        )
        
        if lines is None:
            return []
        
        # Filter for long, relatively straight lines
        filtered_lines = []
        for line in lines:
            x1, y1, x2, y2 = line[0]
            length = np.sqrt((x2-x1)**2 + (y2-y1)**2)
            if length > 200:  # Only keep long lines
                filtered_lines.append((x1, y1, x2, y2))
        
        return filtered_lines
    
    def find_court_corners(self, lines: List[Tuple[int, int, int, int]], 
                          image_shape: Tuple[int, int]) -> Optional[np.ndarray]:
        """Find court corners from detected lines."""
        
        if len(lines) < 4:
            print("Not enough lines detected for court corner detection")
            return None
        
        h, w = image_shape[:2]
        
        # For demonstration, use approximate court corners
        # In a real implementation, this would use line intersection logic
        corners = np.array([
            [w * 0.1, h * 0.8],   # Bottom left
            [w * 0.9, h * 0.8],   # Bottom right
            [w * 0.9, h * 0.2],   # Top right
            [w * 0.1, h * 0.2]    # Top left
        ], dtype=np.float32)
        
        return corners
    
    def calibrate_court(self, image: np.ndarray, 
                       manual_corners: Optional[np.ndarray] = None) -> bool:
        """Calibrate court using detected or manual corners."""
        
        if manual_corners is not None:
            self.court_corners_2d = manual_corners
        else:
            # Auto-detect court lines and corners
            lines = self.detect_court_lines(image)
            self.court_corners_2d = self.find_court_corners(lines, image.shape)
        
        if self.court_corners_2d is None:
            return False
        
        # Compute homography matrix
        self.homography_matrix = cv2.getPerspectiveTransform(
            self.court_corners_2d, 
            self.court_points_3d
        )
        
        return True
    
    def pixel_to_court_coords(self, pixel_coords: np.ndarray) -> np.ndarray:
        """Transform pixel coordinates to court coordinates."""
        
        if self.homography_matrix is None:
            raise ValueError("Court not calibrated. Call calibrate_court first.")
        
        # Reshape for homography transform
        if len(pixel_coords.shape) == 1:
            pixel_coords = pixel_coords.reshape(1, -1)
        
        # Apply homography
        court_coords = cv2.perspectiveTransform(
            pixel_coords.reshape(-1, 1, 2).astype(np.float32),
            self.homography_matrix
        )
        
        return court_coords.reshape(-1, 2)
    
    def court_to_pixel_coords(self, court_coords: np.ndarray) -> np.ndarray:
        """Transform court coordinates to pixel coordinates."""
        
        if self.homography_matrix is None:
            raise ValueError("Court not calibrated. Call calibrate_court first.")
        
        # Inverse homography
        inverse_homography = np.linalg.inv(self.homography_matrix)
        
        # Reshape for homography transform
        if len(court_coords.shape) == 1:
            court_coords = court_coords.reshape(1, -1)
        
        # Apply inverse homography
        pixel_coords = cv2.perspectiveTransform(
            court_coords.reshape(-1, 1, 2).astype(np.float32),
            inverse_homography
        )
        
        return pixel_coords.reshape(-1, 2)
    
    def draw_court_overlay(self, image: np.ndarray) -> np.ndarray:
        """Draw court overlay on image."""
        
        if self.homography_matrix is None:
            return image.copy()
        
        overlay = image.copy()
        
        # Draw court boundary
        court_boundary_pixels = self.court_to_pixel_coords(self.court_points_3d)
        
        pts = court_boundary_pixels.reshape((-1, 1, 2)).astype(np.int32)
        cv2.polylines(overlay, [pts], True, (0, 255, 0), 2)
        
        # Draw net line
        net_line_court = np.array([[0, self.net_y], [23.77, self.net_y]])
        net_line_pixels = self.court_to_pixel_coords(net_line_court)
        
        pt1 = tuple(net_line_pixels[0].astype(int))
        pt2 = tuple(net_line_pixels[1].astype(int))
        cv2.line(overlay, pt1, pt2, (255, 0, 0), 2)
        
        # Draw service lines
        service_lines_court = [
            np.array([[6.40, 0], [6.40, 10.97]]),      # Left service line
            np.array([[17.37, 0], [17.37, 10.97]])     # Right service line
        ]
        
        for service_line in service_lines_court:
            service_line_pixels = self.court_to_pixel_coords(service_line)
            pt1 = tuple(service_line_pixels[0].astype(int))
            pt2 = tuple(service_line_pixels[1].astype(int))
            cv2.line(overlay, pt1, pt2, (0, 0, 255), 1)
        
        return overlay
    
    def save_calibration(self, filepath: Path) -> bool:
        """Save calibration data to file."""
        
        if self.homography_matrix is None:
            return False
        
        calibration_data = {
            'homography_matrix': self.homography_matrix.tolist(),
            'court_corners_2d': self.court_corners_2d.tolist(),
            'court_points_3d': self.court_points_3d.tolist()
        }
        
        return save_json(calibration_data, filepath)
    
    def load_calibration(self, filepath: Path) -> bool:
        """Load calibration data from file."""
        
        calibration_data = load_json(filepath)
        if calibration_data is None:
            return False
        
        try:
            self.homography_matrix = np.array(calibration_data['homography_matrix'])
            self.court_corners_2d = np.array(calibration_data['court_corners_2d'])
            self.court_points_3d = np.array(calibration_data['court_points_3d'])
            return True
        except KeyError:
            return False


def create_manual_calibration_points(image_width: int, image_height: int) -> np.ndarray:
    """Create manual calibration points for demonstration."""
    
    # Return reasonable court corner estimates
    # In a real application, these would be user-selected points
    corners = np.array([
        [image_width * 0.15, image_height * 0.85],   # Bottom left
        [image_width * 0.85, image_height * 0.85],   # Bottom right
        [image_width * 0.85, image_height * 0.25],   # Top right
        [image_width * 0.15, image_height * 0.25]    # Top left
    ], dtype=np.float32)
    
    return corners


def estimate_ball_speed(positions: List[Tuple[float, float]], 
                       timestamps: List[float], 
                       calibrator: CourtCalibrator) -> float:
    """Estimate ball speed from tracked positions."""
    
    if len(positions) < 2:
        return 0.0
    
    # Convert pixel positions to court coordinates
    pixel_coords = np.array(positions)
    court_coords = calibrator.pixel_to_court_coords(pixel_coords)
    
    # Calculate distances and time differences
    total_distance = 0.0
    total_time = 0.0
    
    for i in range(1, len(court_coords)):
        # Distance in meters
        distance = np.linalg.norm(court_coords[i] - court_coords[i-1])
        # Time in seconds
        time_diff = timestamps[i] - timestamps[i-1]
        
        if time_diff > 0:
            total_distance += distance
            total_time += time_diff
    
    # Speed in m/s
    speed_ms = total_distance / total_time if total_time > 0 else 0.0
    
    # Convert to km/h
    speed_kmh = speed_ms * 3.6
    
    return speed_kmh


def draw_trajectory(image: np.ndarray, 
                   positions: List[Tuple[float, float]], 
                   color: Tuple[int, int, int] = (0, 255, 255)) -> np.ndarray:
    """Draw ball trajectory on image."""
    
    result = image.copy()
    
    # Draw trajectory line
    if len(positions) > 1:
        points = np.array(positions, dtype=np.int32)
        cv2.polylines(result, [points], False, color, 2)
    
    # Draw position markers
    for i, pos in enumerate(positions):
        x, y = int(pos[0]), int(pos[1])
        radius = max(2, 5 - i // 3)  # Smaller for older positions
        cv2.circle(result, (x, y), radius, color, -1)
    
    return result