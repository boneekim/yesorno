import os
import streamlit as st
from datetime import datetime
from PIL import Image
import hashlib

def save_uploaded_file(uploaded_file, upload_dir="uploads"):
    """
    업로드된 파일을 지정된 디렉토리에 저장
    
    Args:
        uploaded_file: Streamlit의 UploadedFile 객체
        upload_dir: 저장할 디렉토리 경로
        
    Returns:
        str: 저장된 파일의 경로
    """
    # 업로드 디렉토리 생성
    os.makedirs(upload_dir, exist_ok=True)
    
    # 파일명 생성 (중복 방지를 위해 timestamp와 hash 사용)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_hash = hashlib.md5(uploaded_file.getvalue()).hexdigest()[:8]
    file_extension = os.path.splitext(uploaded_file.name)[1]
    
    filename = f"{timestamp}_{file_hash}{file_extension}"
    file_path = os.path.join(upload_dir, filename)
    
    # 파일 저장
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getvalue())
    
    return file_path

def display_gallery(records, week_filter=None):
    """
    이미지 갤러리 표시
    
    Args:
        records: 데이터베이스 기록 리스트
        week_filter: 주차 필터 (선택사항)
    """
    if not records:
        st.info("📭 갤러리에 표시할 이미지가 없습니다.")
        return
    
    # 필터링
    if week_filter and week_filter != "전체":
        filtered_records = []
        for record in records:
            if record.get('gestational_age'):
                try:
                    week = record['gestational_age'].split('주')[0]
                    if week.isdigit() and int(week) == week_filter:
                        filtered_records.append(record)
                except:
                    continue
        records = filtered_records
    
    if not records:
        st.info(f"📭 {week_filter}주차에 해당하는 이미지가 없습니다.")
        return
    
    # 갤러리 표시 (3열 그리드)
    cols_per_row = 3
    for i in range(0, len(records), cols_per_row):
        cols = st.columns(cols_per_row)
        
        for j in range(cols_per_row):
            if i + j < len(records):
                record = records[i + j]
                
                with cols[j]:
                    # 이미지 표시
                    if os.path.exists(record['image_path']):
                        try:
                            image = Image.open(record['image_path'])
                            st.image(image, use_column_width=True)
                        except:
                            st.error("이미지를 불러올 수 없습니다.")
                    
                    # 정보 표시
                    st.caption(f"📅 {record['analysis_date'][:10]}")
                    
                    if record['type'] == 'ultrasound':
                        if record.get('gestational_age'):
                            st.caption(f"🕒 {record['gestational_age']}")
                        if record.get('gender'):
                            st.caption(f"👶 {record['gender']}")
                    else:
                        if record.get('result'):
                            st.caption(f"🔍 {record['result']}")

def format_date(date_string):
    """
    날짜 문자열을 사용자 친화적 형식으로 변환
    
    Args:
        date_string: ISO 형식의 날짜 문자열
        
    Returns:
        str: 포맷된 날짜 문자열
    """
    try:
        dt = datetime.fromisoformat(date_string.replace('Z', '+00:00'))
        return dt.strftime("%Y년 %m월 %d일 %H:%M")
    except:
        return date_string

def validate_image(uploaded_file):
    """
    업로드된 이미지 파일 유효성 검사
    
    Args:
        uploaded_file: Streamlit의 UploadedFile 객체
        
    Returns:
        tuple: (is_valid, error_message)
    """
    if uploaded_file is None:
        return False, "파일이 업로드되지 않았습니다."
    
    # 파일 크기 확인 (10MB 제한)
    max_size = 10 * 1024 * 1024  # 10MB
    if uploaded_file.size > max_size:
        return False, "파일 크기가 10MB를 초과합니다."
    
    # 파일 형식 확인
    allowed_types = ['png', 'jpg', 'jpeg']
    file_extension = uploaded_file.name.split('.')[-1].lower()
    if file_extension not in allowed_types:
        return False, f"지원하지 않는 파일 형식입니다. ({', '.join(allowed_types)} 만 지원)"
    
    # 이미지 파일인지 확인
    try:
        image = Image.open(uploaded_file)
        image.verify()
        return True, ""
    except:
        return False, "유효한 이미지 파일이 아닙니다."

def create_thumbnail(image_path, thumbnail_size=(150, 150)):
    """
    이미지 썸네일 생성
    
    Args:
        image_path: 원본 이미지 경로
        thumbnail_size: 썸네일 크기 (가로, 세로)
        
    Returns:
        PIL.Image: 썸네일 이미지 객체
    """
    try:
        image = Image.open(image_path)
        image.thumbnail(thumbnail_size, Image.Resampling.LANCZOS)
        return image
    except:
        return None

def clean_old_files(upload_dir="uploads", days_old=30):
    """
    오래된 업로드 파일들 정리
    
    Args:
        upload_dir: 업로드 디렉토리
        days_old: 삭제할 파일의 기준 일수
    """
    if not os.path.exists(upload_dir):
        return
    
    import time
    current_time = time.time()
    cutoff_time = current_time - (days_old * 24 * 60 * 60)
    
    for filename in os.listdir(upload_dir):
        file_path = os.path.join(upload_dir, filename)
        
        if os.path.isfile(file_path):
            file_time = os.path.getmtime(file_path)
            if file_time < cutoff_time:
                try:
                    os.remove(file_path)
                    print(f"삭제됨: {file_path}")
                except OSError:
                    print(f"삭제 실패: {file_path}")

def export_records_to_csv(records):
    """
    기록들을 CSV 형식으로 내보내기
    
    Args:
        records: 데이터베이스 기록 리스트
        
    Returns:
        str: CSV 형식의 문자열
    """
    import csv
    import io
    
    if not records:
        return ""
    
    output = io.StringIO()
    
    # CSV 헤더 정의
    fieldnames = ['분석일자', '타입', '결과', '임신주수', '성별', '병원', '측정치', '메모']
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    
    writer.writeheader()
    
    for record in records:
        writer.writerow({
            '분석일자': record.get('analysis_date', ''),
            '타입': '임신테스트기' if record.get('type') == 'pregnancy_test' else '초음파',
            '결과': record.get('result', ''),
            '임신주수': record.get('gestational_age', ''),
            '성별': record.get('gender', ''),
            '병원': record.get('hospital', ''),
            '측정치': record.get('measurements', ''),
            '메모': record.get('memo', '')
        })
    
    return output.getvalue()

def get_week_number(gestational_age_text):
    """
    임신 주수 텍스트에서 주 번호 추출
    
    Args:
        gestational_age_text: 임신 주수 텍스트 (예: "12주 3일")
        
    Returns:
        int: 주 번호, 추출 실패시 None
    """
    if not gestational_age_text:
        return None
    
    try:
        # "12주 3일" 또는 "12w3d" 형식에서 주 번호 추출
        import re
        week_match = re.search(r'(\d+)[주w]', gestational_age_text)
        if week_match:
            return int(week_match.group(1))
    except:
        pass
    
    return None

def create_progress_chart(records):
    """
    임신 진행 차트 생성 (주차별)
    
    Args:
        records: 초음파 기록 리스트
        
    Returns:
        dict: 차트 데이터
    """
    chart_data = {}
    
    for record in records:
        if record.get('type') == 'ultrasound' and record.get('gestational_age'):
            week = get_week_number(record['gestational_age'])
            if week:
                date = record.get('analysis_date', '')[:10]  # YYYY-MM-DD 형식
                chart_data[week] = date
    
    return chart_data
