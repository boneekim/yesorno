import streamlit as st
from PIL import Image
import numpy as np

# 페이지 설정
st.set_page_config(
    page_title="임신 테스트 확인",
    page_icon="🤱",
    layout="centered"
)

# 제목
st.title("임신 테스트 확인 🤱")
st.markdown("---")
st.markdown("### 임신테스트기 사진을 업로드하여 결과를 확인해보세요")

# OpenCV 사용 가능 여부 확인
try:
    import cv2
    OPENCV_AVAILABLE = True
except ImportError:
    OPENCV_AVAILABLE = False

# 분석 방법 선택
st.subheader("🔍 분석 방법 선택")
if OPENCV_AVAILABLE:
    analysis_method = st.radio(
        "분석 방법을 선택해주세요:",
        ["🎨 간단한 색상 분석 (빠름)", "🔬 정밀한 선 감지 분석 (정확함)"],
        help="색상 분석은 빠르지만 기본적이고, 선 감지 분석은 더 정확하지만 시간이 조금 더 걸립니다."
    )
    use_opencv = "정밀한 선 감지" in analysis_method
else:
    st.info("💡 OpenCV가 설치되지 않아 간단한 색상 분석만 사용 가능합니다.")
    use_opencv = False

# 개선된 색상 분석 함수
def improved_color_analysis(image):
    """개선된 색상 기반 분석 - 더 엄격한 기준"""
    img_array = np.array(image.convert('RGB'))
    height, width = img_array.shape[:2]
    
    # 더 정확한 빨간색/분홍색 감지 (범위를 더 엄격하게)
    red_mask = (
        (img_array[:,:,0] > 140) & 
        (img_array[:,:,1] < 60) & 
        (img_array[:,:,2] < 60) &
        (img_array[:,:,0] - img_array[:,:,1] > 80) &  # R-G 차이가 커야 함
        (img_array[:,:,0] - img_array[:,:,2] > 80)    # R-B 차이가 커야 함
    )
    
    pink_mask = (
        (img_array[:,:,0] > 160) & 
        (img_array[:,:,1] > 80) & (img_array[:,:,1] < 140) & 
        (img_array[:,:,2] > 80) & (img_array[:,:,2] < 140) &
        (img_array[:,:,0] - img_array[:,:,1] > 40) &  # 빨간색이 더 강해야 함
        (img_array[:,:,0] - img_array[:,:,2] > 40)
    )
    
    colored_pixels = np.sum(red_mask) + np.sum(pink_mask)
    total_pixels = height * width
    colored_ratio = colored_pixels / total_pixels
    
    # 색상 픽셀들이 집중된 영역이 있는지 확인 (선 형태인지)
    concentration_score = 0
    if colored_pixels > 0:
        # 색상 픽셀들의 분포를 확인
        red_coords = np.where(red_mask | pink_mask)
        if len(red_coords[0]) > 0:
            # 색상 픽셀들이 수직선을 이루는지 확인
            y_coords = red_coords[0]
            x_coords = red_coords[1]
            
            # x좌표별로 그룹화해서 수직선 형태인지 확인
            unique_x = np.unique(x_coords)
            for x in unique_x:
                y_in_x = y_coords[x_coords == x]
                if len(y_in_x) > height * 0.1:  # 높이의 10% 이상
                    concentration_score += len(y_in_x)
    
    concentration_ratio = concentration_score / total_pixels if total_pixels > 0 else 0
    
    # 더 엄격한 판정 기준
    if colored_ratio > 0.02 and concentration_ratio > 0.005:  # 2% + 집중도
        confidence = min(0.85, colored_ratio * 30 + concentration_ratio * 100)
        return {
            'is_pregnant': True,
            'message': '임신으로 추정됩니다',
            'confidence': confidence,
            'method': '개선된 색상 분석',
            'details': f'색상 비율: {colored_ratio:.3%}, 집중도: {concentration_ratio:.3%}',
            'disclaimer': '개선된 색상 분석 결과입니다. 정확한 진단은 의료진에게 문의하세요.'
        }
    elif colored_ratio > 0.015 and concentration_ratio > 0.003:  # 중간 수준
        confidence = min(0.75, colored_ratio * 25 + concentration_ratio * 80)
        return {
            'is_pregnant': True,
            'message': '임신 가능성이 있습니다 (약한 신호)',
            'confidence': confidence,
            'method': '개선된 색상 분석',
            'details': f'색상 비율: {colored_ratio:.3%}, 집중도: {concentration_ratio:.3%}',
            'disclaimer': '약한 신호가 감지되었습니다. 정확한 진단은 의료진에게 문의하세요.'
        }
    else:
        confidence = max(0.7, 0.9 - colored_ratio * 10)
        return {
            'is_pregnant': False,
            'message': '비임신으로 추정됩니다',
            'confidence': confidence,
            'method': '개선된 색상 분석',
            'details': f'색상 비율: {colored_ratio:.3%}, 집중도: {concentration_ratio:.3%}',
            'disclaimer': '색상 신호가 부족합니다. 의심스러우면 의료진에게 문의하세요.'
        }

# 개선된 OpenCV 선 감지 분석 함수
def improved_opencv_analysis(image):
    """개선된 OpenCV 선 감지 분석 - 더 정확한 판정"""
    try:
        import cv2
        
        # PIL을 OpenCV 형식으로 변환
        img_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        height, width = img_cv.shape[:2]
        
        # 그레이스케일 변환
        gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
        
        # 가우시안 블러 적용
        blurred = cv2.GaussianBlur(gray, (3, 3), 0)
        
        # 적응적 이진화 (조명 변화에 더 강함)
        binary = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
        
        # 엣지 감지 (더 엄격한 설정)
        edges = cv2.Canny(binary, 100, 200, apertureSize=3)
        
        # Hough Line Transform (더 엄격한 설정)
        lines = cv2.HoughLinesP(edges, 1, np.pi/180, threshold=100, minLineLength=min(height, width)//4, maxLineGap=15)
        
        # 유효한 수직선 찾기 (더 엄격한 기준)
        valid_vertical_lines = []
        if lines is not None:
            for line in lines:
                x1, y1, x2, y2 = line[0]
                
                line_length = np.sqrt((x2-x1)**2 + (y2-y1)**2)
                
                # 선이 충분히 길어야 함 (높이의 최소 20%)
                if line_length < height * 0.2:
                    continue
                
                # 수직선 각도 계산 (더 엄격)
                if x2 - x1 != 0:
                    angle = np.arctan2(abs(y2 - y1), abs(x2 - x1)) * 180 / np.pi
                    # 거의 수직 (80-90도)이어야 함
                    if 80 <= angle <= 90:
                        # 선이 이미지 중앙 부분에 있어야 함
                        center_x = (x1 + x2) / 2
                        if width * 0.2 < center_x < width * 0.8:
                            valid_vertical_lines.append(line)
        
        # 색상 분석도 함께 수행 (더 엄격한 기준)
        color_result = improved_color_analysis(image)
        colored_ratio = float(color_result['details'].split('색상 비율: ')[1].split('%')[0].replace(',', '')) / 100
        
        # 종합 판정 (더 엄격한 기준)
        line_count = len(valid_vertical_lines)
        
        is_pregnant = False
        confidence = 0.6
        message = ""
        
        if line_count >= 2 and colored_ratio > 0.015:
            # 2개 이상의 명확한 선 + 충분한 색상
            is_pregnant = True
            confidence = min(0.95, 0.8 + colored_ratio * 15)
            message = f"임신으로 추정됩니다 ({line_count}개의 명확한 선 감지)"
        elif line_count == 1 and colored_ratio > 0.02:
            # 1개의 명확한 선 + 강한 색상
            is_pregnant = True
            confidence = min(0.85, 0.7 + colored_ratio * 12)
            message = f"임신 가능성이 높습니다 ({line_count}개 선 + 강한 색상)"
        elif line_count >= 1 and colored_ratio > 0.01:
            # 1개 선 + 중간 색상
            is_pregnant = True
            confidence = min(0.75, 0.6 + colored_ratio * 10)
            message = f"임신 가능성이 있습니다 ({line_count}개 선 감지)"
        elif colored_ratio > 0.025:
            # 선은 명확하지 않지만 매우 강한 색상
            is_pregnant = True
            confidence = min(0.8, 0.5 + colored_ratio * 8)
            message = "임신 가능성이 있습니다 (강한 색상 신호)"
        else:
            # 비임신
            is_pregnant = False
            confidence = max(0.75, 0.95 - colored_ratio * 8 - line_count * 0.1)
            message = "비임신으로 추정됩니다"
        
        return {
            'is_pregnant': is_pregnant,
            'message': message,
            'confidence': confidence,
            'method': '정밀 선 감지 + 색상 분석',
            'details': f'유효한 선: {line_count}개, 색상 비율: {colored_ratio:.3%}',
            'disclaimer': '개선된 선 감지와 색상 분석을 결합한 결과입니다. 정확한 진단은 의료진에게 문의하세요.'
        }
        
    except Exception as e:
        # OpenCV 분석 실패 시 개선된 색상 분석으로 대체
        return improved_color_analysis(image)

# 파일 업로더
uploaded_file = st.file_uploader(
    "임신테스트기 사진을 업로드해주세요",
    type=['png', 'jpg', 'jpeg'],
    help="지원 형식: PNG, JPG, JPEG (최대 10MB)"
)

if uploaded_file is not None:
    # 파일 크기 체크
    if uploaded_file.size > 10 * 1024 * 1024:  # 10MB
        st.error("❌ 파일 크기가 10MB를 초과합니다.")
    else:
        # 이미지 표시
        image = Image.open(uploaded_file)
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.image(image, caption="업로드된 임신테스트기", use_container_width=True)
        
        st.markdown("---")
        
        # 분석 버튼
        analyze_button_text = "🔍 임신 여부 분석하기"
        if use_opencv:
            analyze_button_text += " (정밀 분석)"
        else:
            analyze_button_text += " (빠른 분석)"
            
        if st.button(analyze_button_text, type="primary", use_container_width=True):
            with st.spinner("이미지를 분석 중입니다..."):
                try:
                    # 분석 방법 선택
                    if use_opencv and OPENCV_AVAILABLE:
                        result = improved_opencv_analysis(image)
                    else:
                        result = improved_color_analysis(image)
                    
                    st.markdown("---")
                    st.subheader("📊 분석 결과")
                    
                    # 결과 표시
                    if result['is_pregnant']:
                        if result['confidence'] > 0.8:
                            st.success(f"✅ {result['message']}")
                            st.balloons()
                        else:
                            st.warning(f"⚠️ {result['message']}")
                    else:
                        st.info(f"➖ {result['message']}")
                    
                    # 상세 정보
                    col1, col2 = st.columns(2)
                    with col1:
                        confidence_percent = int(result['confidence'] * 100)
                        st.metric("신뢰도", f"{confidence_percent}%")
                        st.progress(result['confidence'])
                    
                    with col2:
                        st.metric("분석 방법", result['method'])
                        st.caption(result['details'])
                    
                    # 신뢰도에 따른 추가 안내
                    if result['is_pregnant'] and result['confidence'] < 0.8:
                        st.info("🔍 신호가 약합니다. 며칠 후 재검사하거나 의료진에게 문의하세요.")
                    
                    # 주의사항
                    st.warning("⚠️ " + result['disclaimer'])
                    
                except Exception as e:
                    st.error(f"❌ 분석 중 오류가 발생했습니다: {str(e)}")
                    st.info("다른 이미지로 다시 시도해주세요.")

# 판정 기준 설명
st.markdown("---")
st.subheader("📋 AI 판정 기준 상세 설명")

# 판정 기준 탭
tab1, tab2, tab3 = st.tabs(["🎨 색상 분석 기준", "🔬 선 감지 분석 기준", "📊 신뢰도 해석"])

with tab1:
    st.markdown("""
    ### 🎨 개선된 색상 분석 판정 기준
    
    #### ✅ **임신 양성으로 판정**
    | 조건 | 색상 비율 | 집중도 | 결과 |
    |------|-----------|--------|------|
    | **강한 신호** | 2.0% 이상 | 0.5% 이상 | 임신으로 추정 (신뢰도 70-85%) |
    | **중간 신호** | 1.5% 이상 | 0.3% 이상 | 임신 가능성 있음 (신뢰도 60-75%) |
    
    #### ❌ **비임신으로 판정**
    | 조건 | 색상 비율 | 집중도 | 결과 |
    |------|-----------|--------|------|
    | **약한 신호** | 2.0% 미만 | 0.5% 미만 | 비임신으로 추정 (신뢰도 70-90%) |
    
    #### 🔍 **색상 감지 기준**
    - **빨간색**: R > 140, G < 60, B < 60, R-G > 80, R-B > 80
    - **분홍색**: R > 160, 80 < G < 140, 80 < B < 140, R-G > 40, R-B > 40
    - **집중도**: 색상 픽셀이 수직선 형태로 집중되어 있는 정도
    """)

with tab2:
    st.markdown("""
    ### 🔬 정밀한 선 감지 분석 판정 기준
    
    #### ✅ **임신 양성으로 판정**
    | 선 개수 | 색상 비율 | 신뢰도 | 결과 메시지 |
    |---------|-----------|--------|-------------|
    | **2개 이상** | 1.5% 이상 | 80-95% | "임신으로 추정됩니다 (X개의 명확한 선 감지)" |
    | **1개** | 2.0% 이상 | 70-85% | "임신 가능성이 높습니다 (1개 선 + 강한 색상)" |
    | **1개** | 1.0% 이상 | 60-75% | "임신 가능성이 있습니다 (1개 선 감지)" |
    | **0개** | 2.5% 이상 | 50-80% | "임신 가능성이 있습니다 (강한 색상 신호)" |
    
    #### ❌ **비임신으로 판정**
    | 조건 | 결과 |
    |------|------|
    | 유효한 선 없음 + 색상 2.5% 미만 | "비임신으로 추정됩니다" |
    
    #### 🔍 **유효한 선의 기준**
    - **길이**: 이미지 높이의 20% 이상
    - **각도**: 80-90도 (거의 수직)
    - **위치**: 이미지 중앙 영역 (20-80% 범위)
    - **선명도**: Canny 엣지 + Hough Transform으로 감지
    """)

with tab3:
    st.markdown("""
    ### 📊 신뢰도 해석 가이드
    
    #### 🟢 **높은 신뢰도 (80% 이상)**
    - **의미**: 매우 명확한 양성 신호
    - **권장 행동**: 의료진 상담 권장
    - **특징**: 2개 이상 선 + 강한 색상 또는 매우 강한 색상 신호
    
    #### 🟡 **중간 신뢰도 (60-79%)**
    - **의미**: 양성 가능성 있으나 약한 신호
    - **권장 행동**: 며칠 후 재검사 또는 의료진 상담
    - **특징**: 1개 선 + 중간 색상 또는 약한 색상 신호
    
    #### 🔵 **낮은 신뢰도 (60% 미만)**
    - **의미**: 불분명한 결과
    - **권장 행동**: 재촬영 후 재검사 권장
    - **특징**: 노이즈가 많거나 이미지 품질이 낮음
    
    #### ⚪ **비임신 신뢰도 (70-90%)**
    - **의미**: 양성 신호가 없음
    - **권장 행동**: 의심스러우면 며칠 후 재검사
    - **특징**: 유효한 선이나 색상 신호 부족
    """)

# 실제 임신테스트기 해석 가이드
st.markdown("---")
with st.expander("🔬 실제 임신테스트기 해석 방법 (참고용)"):
    st.markdown("""
    ### 📖 일반적인 임신테스트기 해석
    
    #### ✅ **양성 (임신)**
    - **2개 선**: 컨트롤 라인(C) + 테스트 라인(T) 모두 나타남
    - **선의 색상**: 분홍색 또는 빨간색 (제품에 따라 다름)
    - **선의 진하기**: 테스트 라인이 약해도 보이면 양성
    
    #### ❌ **음성 (비임신)**  
    - **1개 선**: 컨트롤 라인(C)만 나타남
    - **테스트 라인**: 전혀 보이지 않음
    
    #### ⚠️ **무효 결과**
    - **선 없음**: 컨트롤 라인도 나타나지 않음
    - **원인**: 테스트 실패, 유통기한 만료, 잘못된 사용법
    
    ### 📅 최적 검사 시기
    - **생리 예정일 이후**: 가장 정확한 결과
    - **아침 첫 소변**: hCG 농도가 가장 높음
    - **너무 이른 검사**: 위음성 가능성 있음
    
    ### ⚠️ **주의사항**
    - 본 AI 분석은 참고용이며, 정확한 진단은 의료진에게 문의
    - 약한 선도 양성으로 간주되지만 재검사 권장
    - 의심스러우면 혈액 검사나 의료진 상담 받기
    """)

# 사용법 안내
st.markdown("---")
with st.expander("📋 촬영 팁 및 사용법"):
    st.markdown("""
    ## 📸 더 정확한 촬영 팁
    - **조명**: 자연광 또는 밝은 백색광 사용
    - **배경**: 흰색 또는 밝은 무지 배경
    - **각도**: 테스트기를 완전히 수평으로 배치
    - **거리**: 테스트기가 화면의 60-80% 차지하도록
    - **초점**: 결과창이 선명하게 나오도록
    - **시간**: 결과 확인 시간 준수 (보통 3-5분)
    """)

# 면책 조항
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #666; font-size: 12px; padding: 20px; background-color: #f0f0f0; border-radius: 10px;'>
    <strong>⚠️ 의료 면책 조항</strong><br>
    본 애플리케이션은 보조 도구일 뿐이며, 의료진의 정확한 진단을 대체할 수 없습니다.<br>
    특히 약한 신호의 경우 며칠 후 재검사하거나 의료진에게 문의하시기 바랍니다.<br>
    정확한 진단과 상담은 반드시 의료진에게 문의하시기 바랍니다.
    </div>
    """, 
    unsafe_allow_html=True
)
