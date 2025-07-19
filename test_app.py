#!/usr/bin/env python3
"""
임신 기록 어시스턴트 테스트 스크립트
주요 모듈들이 정상적으로 작동하는지 확인
"""

import sys
import os

def test_imports():
    """필수 모듈들의 import 테스트"""
    print("📦 모듈 import 테스트 중...")
    
    try:
        import streamlit as st
        print("✅ Streamlit 모듈 정상")
    except ImportError as e:
        print(f"❌ Streamlit 모듈 오류: {e}")
        return False
    
    try:
        import cv2
        print("✅ OpenCV 모듈 정상")
    except ImportError as e:
        print(f"❌ OpenCV 모듈 오류: {e}")
        return False
    
    try:
        import pytesseract
        print("✅ pytesseract 모듈 정상")
    except ImportError as e:
        print(f"❌ pytesseract 모듈 오류: {e}")
        return False
    
    try:
        from PIL import Image
        print("✅ Pillow 모듈 정상")
    except ImportError as e:
        print(f"❌ Pillow 모듈 오류: {e}")
        return False
    
    try:
        import numpy as np
        print("✅ NumPy 모듈 정상")
    except ImportError as e:
        print(f"❌ NumPy 모듈 오류: {e}")
        return False
    
    return True

def test_modules():
    """자체 제작 모듈들 테스트"""
    print("\n🔧 자체 모듈 테스트 중...")
    
    try:
        from modules.database import DatabaseManager
        db = DatabaseManager()
        print("✅ DatabaseManager 모듈 정상")
    except Exception as e:
        print(f"❌ DatabaseManager 모듈 오류: {e}")
        return False
    
    try:
        from modules.pregnancy_test_analyzer import PregnancyTestAnalyzer
        analyzer = PregnancyTestAnalyzer()
        print("✅ PregnancyTestAnalyzer 모듈 정상")
    except Exception as e:
        print(f"❌ PregnancyTestAnalyzer 모듈 오류: {e}")
        return False
    
    try:
        from modules.ultrasound_analyzer import UltrasoundAnalyzer
        analyzer = UltrasoundAnalyzer()
        print("✅ UltrasoundAnalyzer 모듈 정상")
    except Exception as e:
        print(f"❌ UltrasoundAnalyzer 모듈 오류: {e}")
        return False
    
    try:
        from modules.utils import save_uploaded_file, display_gallery
        print("✅ Utils 모듈 정상")
    except Exception as e:
        print(f"❌ Utils 모듈 오류: {e}")
        return False
    
    return True

def test_database():
    """데이터베이스 기능 테스트"""
    print("\n💾 데이터베이스 테스트 중...")
    
    try:
        from modules.database import DatabaseManager
        
        # 테스트용 DB 생성
        db = DatabaseManager("test.db")
        
        # 테스트 레코드 저장
        test_record = {
            'type': 'pregnancy_test',
            'result': '테스트 결과',
            'image_path': 'test/path.jpg',
            'analysis_date': '2024-01-01T00:00:00'
        }
        
        record_id = db.save_record(test_record)
        print(f"✅ 레코드 저장 성공 (ID: {record_id})")
        
        # 레코드 조회
        records = db.get_records()
        if records:
            print(f"✅ 레코드 조회 성공 ({len(records)}개)")
        else:
            print("❌ 레코드 조회 실패")
            return False
        
        # 레코드 삭제
        db.delete_record(record_id)
        print("✅ 레코드 삭제 성공")
        
        # 테스트 DB 파일 삭제
        if os.path.exists("test.db"):
            os.remove("test.db")
        
        return True
        
    except Exception as e:
        print(f"❌ 데이터베이스 테스트 오류: {e}")
        return False

def test_directories():
    """필요한 디렉토리 확인"""
    print("\n�� 디렉토리 구조 확인 중...")
    
    required_dirs = ['modules', 'uploads']
    
    for dir_name in required_dirs:
        if os.path.exists(dir_name):
            print(f"✅ {dir_name} 디렉토리 존재")
        else:
            print(f"⚠️ {dir_name} 디렉토리 생성 중...")
            os.makedirs(dir_name, exist_ok=True)
    
    required_files = [
        'app.py',
        'requirements.txt',
        'modules/__init__.py',
        'modules/database.py',
        'modules/pregnancy_test_analyzer.py',
        'modules/ultrasound_analyzer.py',
        'modules/utils.py'
    ]
    
    for file_name in required_files:
        if os.path.exists(file_name):
            print(f"✅ {file_name} 파일 존재")
        else:
            print(f"❌ {file_name} 파일 누락")
            return False
    
    return True

def main():
    """메인 테스트 함수"""
    print("🍼 임신 기록 어시스턴트 테스트 시작\n")
    
    test_results = []
    
    # 각 테스트 실행
    test_results.append(("디렉토리 구조", test_directories()))
    test_results.append(("모듈 Import", test_imports()))
    test_results.append(("자체 모듈", test_modules()))
    test_results.append(("데이터베이스", test_database()))
    
    # 결과 요약
    print("\n" + "="*50)
    print("📊 테스트 결과 요약")
    print("="*50)
    
    passed = 0
    for test_name, result in test_results:
        status = "✅ 통과" if result else "❌ 실패"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n총 {len(test_results)}개 테스트 중 {passed}개 통과")
    
    if passed == len(test_results):
        print("\n🎉 모든 테스트 통과! 애플리케이션 실행 준비 완료")
        print("\n실행 명령어:")
        print("streamlit run app.py")
    else:
        print(f"\n⚠️ {len(test_results) - passed}개 테스트 실패")
        print("README.md 파일의 설치 가이드를 확인해주세요.")

if __name__ == "__main__":
    main()
