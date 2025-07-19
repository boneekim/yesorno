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

# 균형잡힌 색상 분석 함수
def balanced_color_analysis(image):
    """균형잡힌 색상 기반 분석 - 적절한 민감도"""
    img_array = np.array(image.convert('RGB'))
    height, width = img_array.shape[:2]
    
    # 적절한 빨간색/분홍색 감지
    red_mask = (
        (img_array[:,:,0] > 120) & 
        (img_array[:,:,1] < 80) & 
        (img_array[:,:,2] < 80) &
        (img_array[:,:,0] - img_array[:,:,1] > 50) &
        (img_array[:,:,0] - img_array[:,:,2] > 50)
    )
    
    pink_mask = (
        (img_array[:,:,0] > 140) & 
        (img_array[:,:,1] > 70) & (img_array[:,:,1] < 160) & 
        (img_array[:,:,2] > 70) & (img_array[:,:,2] < 160) &
        (img_array[:,:,0] - img_array[:,:,1] > 20) &
        (img_array[:,:,0] - img_array[:,:,2] > 20)
    )
    
    purple_mask = (
        (img_array[:,:,0] > 100) & 
        (img_array[:,:,2] > 100) & 
        (img_array[:,:,1] < 80) &
        (abs(img_array[:,:,0].astype(int) - img_array[:,:,2].astype(int)) < 60)
    )
    
    colored_pixels = np.sum(red_mask) + np.sum(pink_mask) + np.sum(purple_mask)
    total_pixels = height * width
    colored_ratio = colored_pixels / total_pixels
    
    # 색상 픽셀들이 집중된 영역이 있는지 확인
    concentration_score = 0
    if colored_pixels > 0:
        red_coords = np.where(red_mask | pink_mask | purple_mask)
        if len(red_coords[0]) > 0:
            y_coords = red_coords[0]
            x_coords = red_coords[1]
            
            unique_x = np.unique(x_coords)
            for x in unique_x:
                y_in_x = y_coords[x_coords == x]
                if len(y_in_x) > height * 0.08:
                    concentration_score += len(y_in_x)
    
    concentration_ratio = concentration_score / total_pixels if total_pixels > 0 else 0
    
    # 판정 기준
    if colored_ratio > 0.012 and concentration_ratio > 0.003:
        confidence = min(0.85, colored_ratio * 40 + concentration_ratio * 120)
        return {
            'is_pregnant': True,
            'message': '임신으로 추정됩니다',
            'confidence': confidence,
            'method': '균형잡힌 색상 분석',
            'details': f'색상 비율: {colored_ratio:.3%}, 집중도: {concentration_ratio:.3%}',
            'disclaimer': '색상 분석 결과입니다. 정확한 진단은 의료진에게 문의하세요.'
        }
    elif colored_ratio > 0.008 and concentration_ratio > 0.002:
        confidence = min(0.75, colored_ratio * 35 + concentration_ratio * 100)
        return {
            'is_pregnant': True,
            'message': '임신 가능성이 있습니다 (약한 신호)',
            'confidence': confidence,
            'method': '균형잡힌 색상 분석',
            'details': f'색상 비율: {colored_ratio:.3%}, 집중도: {concentration_ratio:.3%}',
            'disclaimer': '약한 신호가 감지되었습니다. 정확한 진단은 의료진에게 문의하세요.'
        }
    elif colored_ratio > 0.005:
        confidence = min(0.65, colored_ratio * 30 + concentration_ratio * 80)
        return {
            'is_pregnant': True,
            'message': '매우 약한 임신 신호 감지 (재검사 권장)',
            'confidence': confidence,
            'method': '균형잡힌 색상 분석',
            'details': f'색상 비율: {colored_ratio:.3%}, 집중도: {concentration_ratio:.3%}',
            'disclaimer': '매우 약한 신호입니다. 며칠 후 재검사하거나 의료진에게 문의하세요.'
        }
    else:
        confidence = max(0.65, 0.85 - colored_ratio * 8)
        return {
            'is_pregnant': False,
            'message': '비임신으로 추정됩니다',
            'confidence': confidence,
            'method': '균형잡힌 색상 분석',
            'details': f'색상 비율: {colored_ratio:.3%}, 집중도: {concentration_ratio:.3%}',
            'disclaimer': '색상 신호가 부족합니다. 의심스러우면 며칠 후 재검사해보세요.'
        }

# 개선된 OpenCV 선 감지 분석 함수
def improved_opencv_analysis(image):
    """개선된 OpenCV 선 감지 분석 - 선 감지 능력 향상"""
    try:
        import cv2
        
        # PIL을 OpenCV 형식으로 변환
        img_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        height, width = img_cv.shape[:2]
        
        # 그레이스케일 변환
        gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
        
        # 여러 방법으로 선 감지 시도
        valid_vertical_lines = []
        
        # 방법 1: 기본적인 이진화 + 선 감지
        blurred1 = cv2.GaussianBlur(gray, (3, 3), 0)
        _, binary1 = cv2.threshold(blurred1, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        edges1 = cv2.Canny(binary1, 50, 150, apertureSize=3)
        lines1 = cv2.HoughLinesP(edges1, 1, np.pi/180, threshold=60, minLineLength=height//8, maxLineGap=25)
        
        # 방법 2: 적응적 이진화 + 선 감지
        binary2 = cv2.adaptiveThreshold(blurred1, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
        edges2 = cv2.Canny(binary2, 80, 160, apertureSize=3)
        lines2 = cv2.HoughLinesP(edges2, 1, np.pi/180, threshold=70, minLineLength=height//8, maxLineGap=20)
        
        # 방법 3: 더 부드러운 블러 + 선 감지
        blurred3 = cv2.GaussianBlur(gray, (5, 5), 0)
        _, binary3 = cv2.threshold(blurred3, 127, 255, cv2.THRESH_BINARY)
        edges3 = cv2.Canny(binary3, 30, 100, apertureSize=3)
        lines3 = cv2.HoughLinesP(edges3, 1, np.pi/180, threshold=50, minLineLength=height//10, maxLineGap=30)
        
        # 모든 방법에서 감지된 선들을 통합
        all_lines = []
        for lines in [lines1, lines2, lines3]:
            if lines is not None:
                all_lines.extend(lines)
        
        # 유효한 수직선 찾기 (더 관대한 기준)
        if all_lines:
            for line in all_lines:
                x1, y1, x2, y2 = line[0]
                
                line_length = np.sqrt((x2-x1)**2 + (y2-y1)**2)
                
                # 선이 충분히 길어야 함 (높이의 10% 이상 - 더 완화)
                if line_length < height * 0.1:
                    continue
                
                # 수직선 각도 계산 (더 관대하게)
                if abs(x2 - x1) < 0.1:  # 거의 수직선
                    angle = 90
                else:
                    angle = np.arctan2(abs(y2 - y1), abs(x2 - x1)) * 180 / np.pi
                
                # 거의 수직 (70-90도 - 더 완화)이어야 함
                if 70 <= angle <= 90:
                    # 선이 이미지 적절한 위치에 있어야 함 (더 관대하게)
                    center_x = (x1 + x2) / 2
                    if width * 0.1 < center_x < width * 0.9:
                        # 중복 제거 (비슷한 위치의 선들)
                        is_duplicate = False
                        for existing_line in valid_vertical_lines:
                            ex1, ey1, ex2, ey2 = existing_line[0]
                            existing_center_x = (ex1 + ex2) / 2
                            if abs(center_x - existing_center_x) < width * 0.05:  # 5% 이내면 중복
                                is_duplicate = True
                                break
                        
                        if not is_duplicate:
                            valid_vertical_lines.append(line)
        
        # 색상 분석도 함께 수행
        color_result = balanced_color_analysis(image)
        colored_ratio = float(color_result['details'].split('색상 비율: ')[1].split('%')[0].replace(',', '')) / 100
        
        # 종합 판정 (선 감지를 우선시)
        line_count = len(valid_vertical_lines)
        
        is_pregnant = False
        confidence = 0.6
        message = ""
        
        # 선 감지를 우선적으로 고려
        if line_count >= 2:
            # 2개 이상의 선 - 색상과 관계없이 높은 신뢰도
            is_pregnant = True
            if colored_ratio > 0.008:
                confidence = min(0.95, 0.85 + colored_ratio * 10)
                message = f"임신으로 추정됩니다 ({line_count}개의 명확한 선 감지)"
            else:
                confidence = 0.8
                message = f"임신으로 추정됩니다 ({line_count}개 선 감지, 색상 약함)"
                
        elif line_count == 1:
            # 1개의 선
            is_pregnant = True
            if colored_ratio > 0.01:
                confidence = min(0.85, 0.7 + colored_ratio * 12)
                message = f"임신 가능성이 높습니다 ({line_count}개 선 + 색상)"
            elif colored_ratio > 0.005:
                confidence = min(0.75, 0.6 + colored_ratio * 10)
                message = f"임신 가능성이 있습니다 ({line_count}개 선 + 약한 색상)"
            else:
                confidence = 0.65
                message = f"임신 가능성이 있습니다 ({line_count}개 선 감지)"
                
        else:
            # 선이 감지되지 않음 - 색상으로만 판정
            if colored_ratio > 0.015:
                is_pregnant = True
                confidence = min(0.75, 0.5 + colored_ratio * 8)
                message = "임신 가능성이 있습니다 (강한 색상 신호, 선 감지 실패)"
            elif colored_ratio > 0.008:
                is_pregnant = True
                confidence = min(0.65, 0.4 + colored_ratio * 8)
                message = "매우 약한 임신 신호 감지 (재검사 권장)"
            else:
                is_pregnant = False
                confidence = max(0.7, 0.9 - colored_ratio * 6)
                message = "비임신으로 추정됩니다"
        
        return {
            'is_pregnant': is_pregnant,
            'message': message,
            'confidence': confidence,
            'method': '개선된 선 감지 + 색상 분석',
            'details': f'감지된 선: {line_count}개, 색상 비율: {colored_ratio:.3%}',
            'disclaimer': '개선된 선 감지와 색상 분석을 결합한 결과입니다. 정확한 진단은 의료진에게 문의하세요.'
        }
        
    except Exception as e:
        # OpenCV 분석 실패 시 색상 분석으로 대체
        return balanced_color_analysis(image)

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
                        result = balanced_color_analysis(image)
                    
                    st.markdown("---")
                    st.subheader("📊 분석 결과")
                    
                    # 결과 표시
                    if result['is_pregnant']:
                        if result['confidence'] > 0.8:
                            st.success(f"✅ {result['message']}")
                            st.balloons()
                        elif result['confidence'] > 0.65:
                            st.warning(f"⚠️ {result['message']}")
                        else:
                            st.info(f"🔍 {result['message']}")
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
                    if result['is_pregnant']:
                        if result['confidence'] < 0.7:
                            st.info("🔍 매우 약한 신호입니다. 며칠 후 재검사하거나 의료진에게 문의하세요.")
                        elif result['confidence'] < 0.8:
                            st.info("🔍 약한 신호입니다. 재검사하거나 의료진에게 문의하세요.")
                    
                    # 주의사항
                    st.warning("⚠️ " + result['disclaimer'])
                    
                except Exception as e:
                    st.error(f"❌ 분석 중 오류가 발생했습니다: {str(e)}")
                    st.info("다른 이미지로 다시 시도해주세요.")

# 판정 기준 설명 (업데이트된 기준)
st.markdown("---")
st.subheader("📋 개선된 AI 판정 기준")

# 판정 기준 탭
tab1, tab2, tab3 = st.tabs(["�� 선 감지 우선 기준", "🎨 색상 분석 기준", "📊 신뢰도 해석"])

with tab1:
    st.markdown("""
    ### 🔬 개선된 선 감지 분석 판정 기준 (우선 적용)
    
    #### ✅ **선 감지 결과에 따른 판정**
    | 선 개수 | 색상 비율 | 신뢰도 | 결과 메시지 |
    |---------|-----------|--------|-------------|
    | **2개 이상** | 0.8% 이상 | 85-95% | "임신으로 추정됩니다 (X개의 명확한 선 감지)" |
    | **2개 이상** | 0.8% 미만 | 80% | "임신으로 추정됩니다 (X개 선 감지, 색상 약함)" |
    | **1개** | 1.0% 이상 | 70-85% | "임신 가능성이 높습니다 (1개 선 + 색상)" |
    | **1개** | 0.5% 이상 | 60-75% | "임신 가능성이 있습니다 (1개 선 + 약한 색상)" |
    | **1개** | 0.5% 미만 | 65% | "임신 가능성이 있습니다 (1개 선 감지)" |
    | **0개** | 1.5% 이상 | 50-75% | "임신 가능성이 있습니다 (강한 색상 신호, 선 감지 실패)" |
    
    #### 🔍 **개선된 선 감지 방법**
    - **3가지 방법 동시 적용**: 기본 이진화 + 적응적 이진화 + 부드러운 블러
    - **완화된 기준**: 길이 10% 이상, 각도 70-90도, 위치 10-90% 범위
    - **중복 제거**: 비슷한 위치의 선들은 하나로 통합
    """)

with tab2:
    st.markdown("""
    ### 🎨 색상 분석 기준 (선 감지 실패시 적용)
    
    #### ✅ **임신 양성으로 판정**
    | 신호 강도 | 색상 비율 | 집중도 | 결과 | 신뢰도 |
    |-----------|-----------|--------|------|--------|
    | **강한 신호** | 1.2% 이상 | 0.3% 이상 | 임신으로 추정 | 70-85% |
    | **중간 신호** | 0.8% 이상 | 0.2% 이상 | 임신 가능성 있음 | 60-75% |
    | **약한 신호** | 0.5% 이상 | - | 매우 약한 신호 | 50-65% |
    
    #### 🔍 **감지하는 색상**
    - **빨간색**: 진한 빨강 (R > 120, G < 80, B < 80)
    - **분홍색**: 연한 분홍 (R > 140, 70 < G < 160, 70 < B < 160)
    - **보라색**: 자주/보라 (일부 테스트기에서 나타남)
    """)

with tab3:
    st.markdown("""
    ### 📊 신뢰도 해석 가이드
    
    #### 🟢 **높은 신뢰도 (80% 이상)**
    - **의미**: 2개 이상 선 감지 또는 매우 명확한 신호
    - **권장 행동**: 의료진 상담 권장
    
    #### 🟡 **중간 신뢰도 (65-79%)**
    - **의미**: 1개 선 + 색상 또는 강한 색상만
    - **권장 행동**: 며칠 후 재검사 또는 의료진 상담
    
    #### 🟠 **낮은 신뢰도 (50-64%)**
    - **의미**: 매우 약한 신호, 불확실
    - **권장 행동**: 며칠 후 재검사 필수
    
    #### ⚪ **비임신 신뢰도 (65-85%)**
    - **의미**: 양성 신호가 없음
    - **권장 행동**: 의심스러우면 며칠 후 재검사
    """)

# 면책 조항
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #666; font-size: 12px; padding: 20px; background-color: #f0f0f0; border-radius: 10px;'>
    <strong>⚠️ 의료 면책 조항</strong><br>
    본 애플리케이션은 보조 도구일 뿐이며, 의료진의 정확한 진단을 대체할 수 없습니다.<br>
    선 감지 실패는 이미지 품질이나 조명 등 다양한 요인에 의해 발생할 수 있습니다.<br>
    <strong>임신 여부는 반드시 의료진의 정확한 검사를 통해 확인하세요.</strong>
    </div>
    """, 
    unsafe_allow_html=True
)
