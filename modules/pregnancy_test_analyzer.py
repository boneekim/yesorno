import cv2
import numpy as np
from PIL import Image
import os

class PregnancyTestAnalyzer:
    """임신테스트기 사진 분석 클래스"""
    
    def __init__(self):
        self.confidence_threshold = 0.7
    
    def analyze(self, image_path):
        """
        임신테스트기 이미지를 분석하여 임신 여부를 판단
        
        Args:
            image_path (str): 이미지 파일 경로
            
        Returns:
            dict: 분석 결과
        """
        try:
            # 이미지 읽기
            image = cv2.imread(image_path)
            if image is None:
                raise ValueError("이미지를 읽을 수 없습니다.")
            
            # 그레이스케일 변환
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # 가우시안 블러 적용
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)
            
            # 이진화
            _, binary = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            # 선 감지 (Hough Line Transform)
            edges = cv2.Canny(binary, 50, 150, apertureSize=3)
            lines = cv2.HoughLinesP(edges, 1, np.pi/180, threshold=100, minLineLength=50, maxLineGap=10)
            
            # 수직선과 수평선 분류
            vertical_lines = []
            horizontal_lines = []
            
            if lines is not None:
                for line in lines:
                    x1, y1, x2, y2 = line[0]
                    
                    # 선의 각도 계산
                    angle = np.arctan2(y2 - y1, x2 - x1) * 180 / np.pi
                    angle = abs(angle)
                    
                    # 수직선 (80-100도 또는 -10~10도)
                    if (80 <= angle <= 100) or (-10 <= angle <= 10):
                        vertical_lines.append(line)
                    # 수평선 (0-20도 또는 160-180도)
                    elif (0 <= angle <= 20) or (160 <= angle <= 180):
                        horizontal_lines.append(line)
            
            # 색상 분석 (선이 있는 영역의 색상 강도)
            color_intensity = self._analyze_color_intensity(image, lines)
            
            # 임신 여부 판단
            line_count = len(vertical_lines) if lines is not None else 0
            is_pregnant = self._determine_pregnancy(line_count, color_intensity)
            
            # 결과 생성
            result = {
                'is_pregnant': is_pregnant,
                'message': self._generate_message(is_pregnant, line_count),
                'confidence': self._calculate_confidence(line_count, color_intensity),
                'line_count': line_count,
                'disclaimer': "조명이나 이미지 품질에 따라 오차가 있을 수 있습니다. 정확한 진단은 의료진에게 문의하세요."
            }
            
            return result
            
        except Exception as e:
            return {
                'is_pregnant': False,
                'message': f"분석 중 오류 발생: {str(e)}",
                'confidence': 0.0,
                'line_count': 0,
                'disclaimer': "이미지 분석에 실패했습니다. 다른 이미지로 시도해보세요."
            }
    
    def _analyze_color_intensity(self, image, lines):
        """선이 있는 영역의 색상 강도 분석"""
        if lines is None:
            return 0
        
        # HSV 색공간으로 변환
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        
        # 빨간색/분홍색 영역 마스크 생성
        lower_red1 = np.array([0, 50, 50])
        upper_red1 = np.array([10, 255, 255])
        lower_red2 = np.array([170, 50, 50])
        upper_red2 = np.array([180, 255, 255])
        
        mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
        mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
        red_mask = mask1 + mask2
        
        # 빨간색 픽셀 수 계산
        red_pixels = cv2.countNonZero(red_mask)
        total_pixels = image.shape[0] * image.shape[1]
        
        return red_pixels / total_pixels
    
    def _determine_pregnancy(self, line_count, color_intensity):
        """선의 개수와 색상 강도를 바탕으로 임신 여부 판단"""
        # 기본적으로 2개 이상의 선이 있으면 임신으로 판단
        if line_count >= 2:
            return True
        # 1개의 선이지만 색상 강도가 높으면 임신 가능성
        elif line_count == 1 and color_intensity > 0.01:
            return True
        else:
            return False
    
    def _generate_message(self, is_pregnant, line_count):
        """결과 메시지 생성"""
        if is_pregnant:
            if line_count >= 2:
                return "임신으로 추정됩니다 (2개 선 감지)"
            else:
                return "임신 가능성이 있습니다 (1개 선 감지)"
        else:
            return "비임신으로 추정됩니다"
    
    def _calculate_confidence(self, line_count, color_intensity):
        """신뢰도 계산"""
        if line_count >= 2:
            return min(0.9, 0.7 + color_intensity * 10)
        elif line_count == 1:
            return min(0.7, 0.5 + color_intensity * 10)
        else:
            return max(0.3, 0.8 - color_intensity * 5)
