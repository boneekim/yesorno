import pytesseract
import cv2
import numpy as np
from PIL import Image
import re
from datetime import datetime

class UltrasoundAnalyzer:
    """초음파 사진 분석 클래스"""
    
    def __init__(self):
        # Tesseract 설정 (Mac의 경우 경로 설정이 필요할 수 있음)
        # pytesseract.pytesseract.tesseract_cmd = '/usr/local/bin/tesseract'
        
        # 정규식 패턴들
        self.patterns = {
            'gestational_age': [
                r'GA\s*[:\-]?\s*(\d{1,2}[wW]\s*\d{1,2}[dD])',
                r'(\d{1,2}[wW]\s*\d{1,2}[dD])',
                r'(\d{1,2}주\s*\d{1,2}일)',
                r'GA\s*[:\-]?\s*(\d{1,2}\.\d+)',
            ],
            'gender': [
                r'[성별성][\s:]*([남여MF])[아성자]?',
                r'(Male|Female|BOY|GIRL)',
                r'([MF])\s*[성별]?',
            ],
            'measurements': [
                r'(BPD|HC|AC|FL|CRL|NT)\s*[:\-]?\s*(\d+\.?\d*)\s*(cm|mm)',
                r'(이두정경|머리둘레|복부둘레|대퇴골장|머리엉덩이길이)\s*[:\-]?\s*(\d+\.?\d*)\s*(cm|mm)',
            ],
            'hospital': [
                r'([가-힣]+(?:병원|의원|클리닉|산부인과))',
                r'([가-힣\s]+(?:Hospital|Clinic))',
            ],
            'date': [
                r'(\d{4}[-./]\d{1,2}[-./]\d{1,2})',
                r'(\d{1,2}[-./]\d{1,2}[-./]\d{4})',
                r'(\d{4}년\s*\d{1,2}월\s*\d{1,2}일)',
            ]
        }
    
    def analyze(self, image_path):
        """
        초음파 이미지를 분석하여 정보 추출
        
        Args:
            image_path (str): 이미지 파일 경로
            
        Returns:
            dict: 분석 결과
        """
        try:
            # 이미지 전처리
            processed_image = self._preprocess_image(image_path)
            
            # OCR 텍스트 추출
            extracted_text = self._extract_text(processed_image)
            
            # 정보 파싱
            parsed_data = self._parse_information(extracted_text)
            
            # 결과 구성
            result = {
                'data_found': bool(any(parsed_data.values())),
                'extracted_text': extracted_text,
                'gestational_age': parsed_data.get('gestational_age'),
                'gender': parsed_data.get('gender'),
                'measurements': parsed_data.get('measurements', []),
                'hospital': parsed_data.get('hospital'),
                'date': parsed_data.get('date')
            }
            
            return result
            
        except Exception as e:
            return {
                'data_found': False,
                'extracted_text': f"오류: {str(e)}",
                'error': str(e)
            }
    
    def _preprocess_image(self, image_path):
        """이미지 전처리 - OCR 정확도 향상을 위해"""
        # 이미지 읽기
        image = cv2.imread(image_path)
        
        # 그레이스케일 변환
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # 노이즈 제거
        denoised = cv2.fastNlMeansDenoising(gray)
        
        # 대비 향상
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        enhanced = clahe.apply(denoised)
        
        # 크기 조정 (OCR 정확도 향상)
        height, width = enhanced.shape
        if height < 300 or width < 300:
            scale_factor = max(300/height, 300/width)
            new_width = int(width * scale_factor)
            new_height = int(height * scale_factor)
            enhanced = cv2.resize(enhanced, (new_width, new_height), interpolation=cv2.INTER_CUBIC)
        
        return enhanced
    
    def _extract_text(self, image):
        """OCR을 사용하여 텍스트 추출"""
        # 여러 OCR 설정으로 시도
        configs = [
            '--psm 6',  # 단일 균일한 텍스트 블록
            '--psm 8',  # 단일 단어
            '--psm 11', # 희소한 텍스트
            '--psm 12', # 희소한 텍스트 (OSD 없음)
        ]
        
        best_text = ""
        max_confidence = 0
        
        for config in configs:
            try:
                # 한글 + 영어 인식
                text = pytesseract.image_to_string(
                    image, 
                    lang='kor+eng',
                    config=config
                )
                
                # 신뢰도 확인 (텍스트 길이로 대략 판단)
                confidence = len(text.strip())
                
                if confidence > max_confidence:
                    max_confidence = confidence
                    best_text = text
                    
            except Exception as e:
                continue
        
        return best_text
    
    def _parse_information(self, text):
        """추출된 텍스트에서 정보 파싱"""
        parsed = {}
        
        # 임신 주수 추출
        for pattern in self.patterns['gestational_age']:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                parsed['gestational_age'] = self._normalize_gestational_age(matches[0])
                break
        
        # 성별 추출
        for pattern in self.patterns['gender']:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                parsed['gender'] = self._normalize_gender(matches[0])
                break
        
        # 측정 수치 추출
        measurements = []
        for pattern in self.patterns['measurements']:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if len(match) >= 3:
                    measurement = f"{match[0]}: {match[1]}{match[2]}"
                    measurements.append(measurement)
        
        if measurements:
            parsed['measurements'] = measurements
        
        # 병원명 추출
        for pattern in self.patterns['hospital']:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                parsed['hospital'] = matches[0].strip()
                break
        
        # 날짜 추출
        for pattern in self.patterns['date']:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                parsed['date'] = self._normalize_date(matches[0])
                break
        
        return parsed
    
    def _normalize_gestational_age(self, ga_text):
        """임신 주수 정규화"""
        # "12w3d" -> "12주 3일"
        if 'w' in ga_text.lower() and 'd' in ga_text.lower():
            ga_text = ga_text.replace('w', '주 ').replace('W', '주 ')
            ga_text = ga_text.replace('d', '일').replace('D', '일')
        
        return ga_text.strip()
    
    def _normalize_gender(self, gender_text):
        """성별 정규화"""
        gender_map = {
            'M': '남아', 'Male': '남아', 'BOY': '남아', '남': '남아',
            'F': '여아', 'Female': '여아', 'GIRL': '여아', '여': '여아'
        }
        
        gender_text = gender_text.strip().upper()
        return gender_map.get(gender_text, gender_text)
    
    def _normalize_date(self, date_text):
        """날짜 정규화"""
        # 다양한 날짜 형식을 표준 형식으로 변환
        try:
            # YYYY-MM-DD 형식으로 변환 시도
            if '-' in date_text or '/' in date_text or '.' in date_text:
                date_text = date_text.replace('/', '-').replace('.', '-')
                parts = date_text.split('-')
                
                if len(parts) == 3:
                    # YYYY-MM-DD 형식인지 확인
                    if len(parts[0]) == 4:
                        return f"{parts[0]}-{parts[1].zfill(2)}-{parts[2].zfill(2)}"
                    # DD-MM-YYYY 형식인지 확인
                    elif len(parts[2]) == 4:
                        return f"{parts[2]}-{parts[1].zfill(2)}-{parts[0].zfill(2)}"
            
            return date_text
            
        except Exception:
            return date_text
