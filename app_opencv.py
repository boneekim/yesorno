import streamlit as st
import os
from datetime import datetime
from PIL import Image
from modules.pregnancy_test_analyzer import PregnancyTestAnalyzer
from modules.utils import save_uploaded_file, validate_image

# 페이지 설정
st.set_page_config(
    page_title="임신 테스트 확인",
    page_icon="��",
    layout="centered"
)

# 제목
st.title("임신 테스트 확인 🤱")
st.markdown("---")
st.markdown("### 임신테스트기 사진을 업로드하여 결과를 확인해보세요")

# 파일 업로더
uploaded_file = st.file_uploader(
    "임신테스트기 사진을 업로드해주세요",
    type=['png', 'jpg', 'jpeg'],
    help="지원 형식: PNG, JPG, JPEG (최대 10MB)"
)

if uploaded_file is not None:
    # 이미지 유효성 검사
    is_valid, error_message = validate_image(uploaded_file)
    
    if not is_valid:
        st.error(f"❌ {error_message}")
    else:
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
                    # 파일 저장
                    saved_path = save_uploaded_file(uploaded_file, "uploads")
                    
                    # 임신테스트기 분석
                    analyzer = PregnancyTestAnalyzer()
                    result = analyzer.analyze(saved_path)
                    
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
                    
                    # 상세 정보 (접기 가능)
                    with st.expander("🔍 상세 분석 정보"):
                        st.write(f"**감지된 선 개수:** {result['line_count']}개")
                        st.write(f"**분석 신뢰도:** {confidence_percent}%")
                        st.write("**분석 방법:** OpenCV 이미지 처리 및 선 감지 알고리즘")
                    
                    # 파일 정리 (임시 저장된 파일 삭제)
                    if os.path.exists(saved_path):
                        os.remove(saved_path)
                        
                except Exception as e:
                    st.error(f"❌ 분석 중 오류가 발생했습니다: {str(e)}")
                    st.info("다른 이미지로 다시 시도해주세요.")

# 사용법 안내
st.markdown("---")
with st.expander("📋 사용법 및 팁"):
    st.markdown("""
    **좋은 분석을 위한 팁:**
    - 밝고 균일한 조명에서 촬영해주세요
    - 테스트기가 화면에 크게 나오도록 촬영해주세요
    - 흔들림 없이 선명하게 촬영해주세요
    - 배경은 단순하게 해주세요
    
    **지원 이미지 형식:**
    - PNG, JPG, JPEG
    - 최대 파일 크기: 10MB
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
