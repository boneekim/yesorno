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

# 간단한 분석 함수 (OpenCV 없이)
def simple_analyze(image):
    """간단한 이미지 분석 (OpenCV 없이)"""
    img_array = np.array(image.convert('RGB'))
    
    # 빨간색 픽셀 감지
    red_mask = (img_array[:,:,0] > 100) & (img_array[:,:,1] < 100) & (img_array[:,:,2] < 100)
    red_pixels = np.sum(red_mask)
    
    # 전체 픽셀 대비 빨간색 픽셀 비율
    total_pixels = img_array.shape[0] * img_array.shape[1]
    red_ratio = red_pixels / total_pixels
    
    # 간단한 판정
    if red_ratio > 0.01:  # 1% 이상
        return {
            'is_pregnant': True,
            'message': '임신으로 추정됩니다',
            'confidence': min(0.8, red_ratio * 50),
            'disclaimer': '이는 간단한 색상 분석 결과입니다. 정확한 진단은 의료진에게 문의하세요.'
        }
    else:
        return {
            'is_pregnant': False,
            'message': '비임신으로 추정됩니다',
            'confidence': 0.6,
            'disclaimer': '이는 간단한 색상 분석 결과입니다. 정확한 진단은 의료진에게 문의하세요.'
        }

# 파일 업로더
uploaded_file = st.file_uploader(
    "임신테스트기 사진을 업로드해주세요",
    type=['png', 'jpg', 'jpeg'],
    help="지원 형식: PNG, JPG, JPEG"
)

if uploaded_file is not None:
    # 이미지 표시
    image = Image.open(uploaded_file)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.image(image, caption="업로드된 임신테스트기", use_container_width=True)
    
    st.markdown("---")
    
    # 분석 버튼
    if st.button("🔍 임신 여부 분석하기", type="primary", use_container_width=True):
        with st.spinner("이미지를 분석 중입니다..."):
            try:
                result = simple_analyze(image)
                
                st.markdown("---")
                st.subheader("📊 분석 결과")
                
                # 결과 표시
                if result['is_pregnant']:
                    st.success(f"✅ {result['message']}")
                    st.balloons()
                else:
                    st.info(f"➖ {result['message']}")
                
                # 신뢰도 표시
                confidence_percent = int(result['confidence'] * 100)
                st.progress(result['confidence'])
                st.caption(f"분석 신뢰도: {confidence_percent}%")
                
                # 주의사항
                st.warning("⚠️ " + result['disclaimer'])
                
            except Exception as e:
                st.error(f"❌ 분석 중 오류가 발생했습니다: {str(e)}")

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
