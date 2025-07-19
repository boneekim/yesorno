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

# 간단한 색상 분석 함수
def simple_color_analysis(image):
    """간단한 색상 기반 분석"""
    img_array = np.array(image.convert('RGB'))
    
    # 빨간색/분홍색 픽셀 감지 (개선된 버전)
    red_mask = (img_array[:,:,0] > 120) & (img_array[:,:,1] < 80) & (img_array[:,:,2] < 80)
    pink_mask = (img_array[:,:,0] > 150) & (img_array[:,:,1] > 100) & (img_array[:,:,1] < 180) & (img_array[:,:,2] > 100) & (img_array[:,:,2] < 180)
    
    colored_pixels = np.sum(red_mask) + np.sum(pink_mask)
    total_pixels = img_array.shape[0] * img_array.shape[1]
    colored_ratio = colored_pixels / total_pixels
    
    if colored_ratio > 0.008:  # 0.8% 이상
        confidence = min(0.75, colored_ratio * 80)
        return {
            'is_pregnant': True,
            'message': '임신으로 추정됩니다',
            'confidence': confidence,
            'method': '색상 분석',
            'details': f'색상 픽셀 비율: {colored_ratio:.3%}',
            'disclaimer': '간단한 색상 분석 결과입니다. 정확한 진단은 의료진에게 문의하세요.'
        }
    else:
        return {
            'is_pregnant': False,
            'message': '비임신으로 추정됩니다',
            'confidence': 0.65,
            'method': '색상 분석',
            'details': f'색상 픽셀 비율: {colored_ratio:.3%}',
            'disclaimer': '간단한 색상 분석 결과입니다. 정확한 진단은 의료진에게 문의하세요.'
        }

# OpenCV 기반 선 감지 분석 함수
def opencv_line_analysis(image):
    """OpenCV를 사용한 정밀한 선 감지 분석"""
    try:
        import cv2
        
        # PIL을 OpenCV 형식으로 변환
        img_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        
        # 그레이스케일 변환
        gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
        
        # 가우시안 블러 적용
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # 이진화
        _, binary = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # 엣지 감지
        edges = cv2.Canny(binary, 50, 150, apertureSize=3)
        
        # Hough Line Transform으로 선 감지
        lines = cv2.HoughLinesP(edges, 1, np.pi/180, threshold=80, minLineLength=30, maxLineGap=10)
        
        # 수직선과 수평선 분류
        vertical_lines = []
        horizontal_lines = []
        
        if lines is not None:
            for line in lines:
                x1, y1, x2, y2 = line[0]
                
                # 선의 각도 계산
                if x2 - x1 != 0:
                    angle = np.arctan2(y2 - y1, x2 - x1) * 180 / np.pi
                    angle = abs(angle)
                    
                    # 수직선 (70-110도)
                    if 70 <= angle <= 110:
                        vertical_lines.append(line)
                    # 수평선 (0-20도 또는 160-180도)
                    elif angle <= 20 or angle >= 160:
                        horizontal_lines.append(line)
        
        # 색상 분석도 함께 수행
        img_array = np.array(image.convert('RGB'))
        red_mask = (img_array[:,:,0] > 120) & (img_array[:,:,1] < 80) & (img_array[:,:,2] < 80)
        pink_mask = (img_array[:,:,0] > 150) & (img_array[:,:,1] > 100) & (img_array[:,:,1] < 180) & (img_array[:,:,2] > 100) & (img_array[:,:,2] < 180)
        colored_pixels = np.sum(red_mask) + np.sum(pink_mask)
        total_pixels = img_array.shape[0] * img_array.shape[1]
        colored_ratio = colored_pixels / total_pixels
        
        # 종합 판정
        line_count = len(vertical_lines)
        
        # 판정 로직 개선
        is_pregnant = False
        confidence = 0.5
        
        if line_count >= 2 and colored_ratio > 0.005:
            is_pregnant = True
            confidence = min(0.9, 0.7 + colored_ratio * 20)
            message = f"임신으로 추정됩니다 ({line_count}개 선 감지)"
        elif line_count >= 1 and colored_ratio > 0.01:
            is_pregnant = True
            confidence = min(0.8, 0.6 + colored_ratio * 15)
            message = f"임신 가능성이 있습니다 ({line_count}개 선 감지)"
        elif colored_ratio > 0.015:
            is_pregnant = True
            confidence = min(0.75, 0.5 + colored_ratio * 10)
            message = "임신 가능성이 있습니다 (색상 기반)"
        else:
            is_pregnant = False
            confidence = max(0.6, 0.8 - colored_ratio * 5)
            message = "비임신으로 추정됩니다"
        
        return {
            'is_pregnant': is_pregnant,
            'message': message,
            'confidence': confidence,
            'method': '선 감지 + 색상 분석',
            'details': f'감지된 선: {line_count}개, 색상 비율: {colored_ratio:.3%}',
            'disclaimer': 'OpenCV 선 감지와 색상 분석을 결합한 결과입니다. 정확한 진단은 의료진에게 문의하세요.'
        }
        
    except Exception as e:
        # OpenCV 분석 실패 시 색상 분석으로 대체
        return simple_color_analysis(image)

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
                        result = opencv_line_analysis(image)
                    else:
                        result = simple_color_analysis(image)
                    
                    st.markdown("---")
                    st.subheader("📊 분석 결과")
                    
                    # 결과 표시
                    if result['is_pregnant']:
                        st.success(f"✅ {result['message']}")
                        st.balloons()
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
                    
                    # 주의사항
                    st.warning("⚠️ " + result['disclaimer'])
                    
                except Exception as e:
                    st.error(f"❌ 분석 중 오류가 발생했습니다: {str(e)}")
                    st.info("다른 이미지로 다시 시도해주세요.")

# 사용법 안내
st.markdown("---")
with st.expander("📋 분석 방법 비교 및 사용 팁"):
    st.markdown("""
    ## 🔍 분석 방법 비교
    
    ### 🎨 간단한 색상 분석
    - **속도**: 매우 빠름 ⚡
    - **정확도**: 기본 수준 📊
    - **특징**: 빨간색/분홍색 픽셀 비율 분석
    - **장점**: 빠르고 안정적, 클라우드 환경에서 잘 작동
    
    ### 🔬 정밀한 선 감지 분석  
    - **속도**: 조금 느림 🐌
    - **정확도**: 높음 🎯
    - **특징**: OpenCV 선 감지 + 색상 분석 결합
    - **장점**: 더 정확한 결과, 선의 개수까지 고려
    
    ## 📸 좋은 분석을 위한 팁
    - 밝고 균일한 조명에서 촬영
    - 테스트기가 화면에 크게 나오도록 촬영
    - 흔들림 없이 선명하게 촬영
    - 배경은 단순하고 밝게
    - 테스트기가 수평이 되도록 촬영
    """)

# 면책 조항
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #666; font-size: 12px; padding: 20px; background-color: #f0f0f0; border-radius: 10px;'>
    <strong>⚠️ 의료 면책 조항</strong><br>
    본 애플리케이션은 보조 도구일 뿐이며, 의료진의 정확한 진단을 대체할 수 없습니다.<br>
    정확한 진단과 상담은 반드시 의료진에게 문의하시기 바랍니다.
    </div>
    """, 
    unsafe_allow_html=True
)
