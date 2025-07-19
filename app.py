import streamlit as st
from PIL import Image
import numpy as np
from datetime import datetime, timedelta

# 페이지 설정
st.set_page_config(
    page_title="임신 테스트 확인",
    page_icon="🤱",
    layout="centered"
)

# 제목
st.title("임신 테스트 확인 🤱")
st.markdown("---")

# 메인 탭 추가
main_tab1, main_tab2 = st.tabs(["📷 임신테스트기 분석", "📅 배란일 & 테스트 시기 계산"])

with main_tab1:
    st.markdown("### 임신테스트기 사진을 업로드하여 결과를 확인해보세요")

    # OpenCV 사용 가능 여부 확인
    try:
        import cv2
        OPENCV_AVAILABLE = True
    except ImportError:
        OPENCV_AVAILABLE = False

    # 분석 방법 선택 (개선된 디자인)
    with st.container():
        st.markdown("""
        <div style='background: linear-gradient(90deg, #ff9a9e 0%, #fecfef 50%, #fecfef 100%); 
                    padding: 20px; border-radius: 15px; margin: 10px 0;'>
            <h3 style='color: #333; margin: 0; text-align: center;'>🔍 분석 방법 선택</h3>
        </div>
        """, unsafe_allow_html=True)
        
        if OPENCV_AVAILABLE:
            analysis_method = st.radio(
                "원하는 분석 방법을 선택해주세요:",
                ["🎨 간단한 색상 분석 (빠름)", "🔬 정밀한 선 감지 분석 (정확함)"],
                help="색상 분석은 빠르지만 기본적이고, 선 감지 분석은 더 정확하지만 시간이 조금 더 걸립니다.",
                key="analysis_method"
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
            
            # 유효한 수직선 찾기
            if all_lines:
                for line in all_lines:
                    x1, y1, x2, y2 = line[0]
                    
                    line_length = np.sqrt((x2-x1)**2 + (y2-y1)**2)
                    
                    if line_length < height * 0.1:
                        continue
                    
                    if abs(x2 - x1) < 0.1:
                        angle = 90
                    else:
                        angle = np.arctan2(abs(y2 - y1), abs(x2 - x1)) * 180 / np.pi
                    
                    if 70 <= angle <= 90:
                        center_x = (x1 + x2) / 2
                        if width * 0.1 < center_x < width * 0.9:
                            is_duplicate = False
                            for existing_line in valid_vertical_lines:
                                ex1, ey1, ex2, ey2 = existing_line[0]
                                existing_center_x = (ex1 + ex2) / 2
                                if abs(center_x - existing_center_x) < width * 0.05:
                                    is_duplicate = True
                                    break
                            
                            if not is_duplicate:
                                valid_vertical_lines.append(line)
            
            # 색상 분석도 함께 수행
            color_result = balanced_color_analysis(image)
            colored_ratio = float(color_result['details'].split('색상 비율: ')[1].split('%')[0].replace(',', '')) / 100
            
            # 종합 판정
            line_count = len(valid_vertical_lines)
            
            is_pregnant = False
            confidence = 0.6
            message = ""
            
            if line_count >= 2:
                is_pregnant = True
                if colored_ratio > 0.008:
                    confidence = min(0.95, 0.85 + colored_ratio * 10)
                    message = f"임신으로 추정됩니다 ({line_count}개의 명확한 선 감지)"
                else:
                    confidence = 0.8
                    message = f"임신으로 추정됩니다 ({line_count}개 선 감지, 색상 약함)"
                    
            elif line_count == 1:
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
            return balanced_color_analysis(image)

    # 파일 업로더
    uploaded_file = st.file_uploader(
        "임신테스트기 사진을 업로드해주세요",
        type=['png', 'jpg', 'jpeg'],
        help="지원 형식: PNG, JPG, JPEG (최대 10MB)"
    )

    if uploaded_file is not None:
        if uploaded_file.size > 10 * 1024 * 1024:
            st.error("❌ 파일 크기가 10MB를 초과합니다.")
        else:
            image = Image.open(uploaded_file)
            
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                st.image(image, caption="업로드된 임신테스트기", use_container_width=True)
            
            st.markdown("---")
            
            analyze_button_text = "🔍 임신 여부 분석하기"
            if use_opencv:
                analyze_button_text += " (정밀 분석)"
            else:
                analyze_button_text += " (빠른 분석)"
                
            if st.button(analyze_button_text, type="primary", use_container_width=True):
                with st.spinner("이미지를 분석 중입니다..."):
                    try:
                        if use_opencv and OPENCV_AVAILABLE:
                            result = improved_opencv_analysis(image)
                        else:
                            result = balanced_color_analysis(image)
                        
                        st.markdown("---")
                        st.subheader("📊 분석 결과")
                        
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
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            confidence_percent = int(result['confidence'] * 100)
                            st.metric("신뢰도", f"{confidence_percent}%")
                            st.progress(result['confidence'])
                        
                        with col2:
                            st.metric("분석 방법", result['method'])
                            st.caption(result['details'])
                        
                        if result['is_pregnant']:
                            if result['confidence'] < 0.7:
                                st.info("🔍 매우 약한 신호입니다. 며칠 후 재검사하거나 의료진에게 문의하세요.")
                            elif result['confidence'] < 0.8:
                                st.info("🔍 약한 신호입니다. 재검사하거나 의료진에게 문의하세요.")
                        
                        st.warning("⚠️ " + result['disclaimer'])
                        
                        # 임신 가능성이 있을 때 추가 정보 제공
                        if result['is_pregnant']:
                            st.markdown("---")
                            st.subheader("🤱 임신 관련 추가 정보")
                            
                            # 마지막 생리일 입력받기 (자동 계산)
                            st.markdown("#### 📅 임신 주수 및 출산예정일 계산")
                            st.markdown("마지막 생리 시작일을 선택하면 자동으로 계산됩니다!")
                            
                            last_period_input = st.date_input(
                                "마지막 생리 시작일",
                                value=datetime.now().date() - timedelta(days=28),
                                help="마지막 생리가 시작된 날짜를 선택하면 주수와 출산예정일이 자동으로 계산됩니다",
                                key="pregnancy_lmp"
                            )
                            
                            # 자동으로 계산 (날짜가 입력되면 바로 계산)
                            if last_period_input:
                                    # 임신 주수 계산 (마지막 생리일로부터)
                                    today = datetime.now().date()
                                    days_since_lmp = (today - last_period_input).days
                                    weeks = days_since_lmp // 7
                                    days = days_since_lmp % 7
                                    
                                    # 출산예정일 계산 (LMP + 280일)
                                    due_date = last_period_input + timedelta(days=280)
                                    
                                    # 병원 방문 권장 시기
                                    first_visit_start = last_period_input + timedelta(weeks=6)
                                    first_visit_end = last_period_input + timedelta(weeks=8)
                                    
                                    col1, col2, col3 = st.columns(3)
                                    
                                    with col1:
                                        st.metric(
                                            "현재 임신 주수",
                                            f"{weeks}주 {days}일",
                                            help="마지막 생리일 기준 계산"
                                        )
                                    
                                    with col2:
                                        st.metric(
                                            "출산 예정일",
                                            due_date.strftime("%Y년 %m월 %d일"),
                                            help="40주 기준 계산"
                                        )
                                    
                                    with col3:
                                        remaining_days = (due_date - today).days
                                        if remaining_days > 0:
                                            st.metric(
                                                "출산까지",
                                                f"{remaining_days}일",
                                                help="대략적인 남은 기간"
                                            )
                                        else:
                                            st.metric(
                                                "예정일 지남",
                                                f"{abs(remaining_days)}일",
                                                help="예정일을 지났습니다"
                                            )
                                    
                                    # 병원 방문 안내
                                    st.markdown("### 🏥 병원 방문 안내")
                                    if weeks < 6:
                                        st.info(f"""
                                        **첫 병원 방문 권장 시기**
                                        
                                        🗓️ **{first_visit_start.strftime('%Y년 %m월 %d일')} ~ {first_visit_end.strftime('%Y년 %m월 %d일')}** (임신 6-8주)
                                        
                                        **현재는 조금 이른 시기입니다.** 
                                        임신 6주 이후에 방문하시면 태아 심장박동을 확인할 수 있습니다.
                                        """)
                                    elif 6 <= weeks <= 8:
                                        st.success(f"""
                                        **지금이 첫 병원 방문에 적절한 시기입니다! 🎉**
                                        
                                        ✅ 태아 심장박동 확인 가능
                                        ✅ 정확한 임신 주수 확인
                                        ✅ 산전 관리 시작
                                        """)
                                    else:
                                        st.warning(f"""
                                        **빠른 병원 방문을 권장합니다**
                                        
                                        임신 {weeks}주로 첫 방문 권장 시기를 지났습니다.
                                        가능한 빨리 산부인과에 방문하세요.
                                        """)
                            
                            # 일반적인 임신 관리 팁
                            st.markdown("### 💡 임신 초기 관리 팁")
                            
                            tip_col1, tip_col2 = st.columns(2)
                            
                            with tip_col1:
                                st.markdown("""
                                **🍎 영양 관리**
                                - 엽산 보충제 복용 (하루 400-800㎍)
                                - 충분한 수분 섭취
                                - 금주, 금연
                                - 카페인 제한 (하루 1-2잔)
                                """)
                            
                            with tip_col2:
                                st.markdown("""
                                **⚠️ 주의사항**
                                - 생선회, 날고기 피하기
                                - 과도한 운동 피하기
                                - 스트레스 관리
                                - 정기적인 병원 방문
                                """)
                        
                    except Exception as e:
                        st.error(f"❌ 분석 중 오류가 발생했습니다: {str(e)}")
                        st.info("다른 이미지로 다시 시도해주세요.")
    
    # 판정 기준 설명 (임신테스트기 분석 탭 내에서만)
    st.markdown("---")
    st.subheader("📋 AI 판정 기준")

    tab1, tab2, tab3 = st.tabs(["🔬 선 감지 우선 기준", "🎨 색상 분석 기준", "📊 신뢰도 해석"])

    with tab1:
        st.markdown("""
        ### 🔬 개선된 선 감지 분석 판정 기준
        
        #### ✅ **선 감지 결과에 따른 판정**
        | 선 개수 | 색상 비율 | 신뢰도 | 결과 메시지 |
        |---------|-----------|--------|-------------|
        | **2개 이상** | 0.8% 이상 | 85-95% | "임신으로 추정됩니다 (X개의 명확한 선 감지)" |
        | **2개 이상** | 0.8% 미만 | 80% | "임신으로 추정됩니다 (X개 선 감지, 색상 약함)" |
        | **1개** | 1.0% 이상 | 70-85% | "임신 가능성이 높습니다 (1개 선 + 색상)" |
        | **1개** | 0.5% 이상 | 60-75% | "임신 가능성이 있습니다 (1개 선 + 약한 색상)" |
        | **1개** | 0.5% 미만 | 65% | "임신 가능성이 있습니다 (1개 선 감지)" |
        | **0개** | 1.5% 이상 | 50-75% | "임신 가능성이 있습니다 (강한 색상 신호, 선 감지 실패)" |
        """)

    with tab2:
        st.markdown("""
        ### 🎨 색상 분석 기준
        
        #### ✅ **임신 양성으로 판정**
        | 신호 강도 | 색상 비율 | 집중도 | 결과 | 신뢰도 |
        |-----------|-----------|--------|------|--------|
        | **강한 신호** | 1.2% 이상 | 0.3% 이상 | 임신으로 추정 | 70-85% |
        | **중간 신호** | 0.8% 이상 | 0.2% 이상 | 임신 가능성 있음 | 60-75% |
        | **약한 신호** | 0.5% 이상 | - | 매우 약한 신호 | 50-65% |
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
        """)

with main_tab2:
    st.markdown("### 배란일과 임신테스트 최적 시기를 계산해보세요")
    
    # 배란일 계산 함수
    def calculate_ovulation_and_test_dates(last_period_date, cycle_length, relationship_date=None):
        """배란일과 테스트 시기 계산"""
        
        # 다음 생리 예정일 계산
        next_period_date = last_period_date + timedelta(days=cycle_length)
        
        # 배란일 계산 (다음 생리 예정일로부터 14일 전)
        ovulation_date = next_period_date - timedelta(days=14)
        
        # 임신 가능 기간 (배란일 ± 3일)
        fertile_start = ovulation_date - timedelta(days=3)
        fertile_end = ovulation_date + timedelta(days=3)
        
        # 임신테스트 가능 시기
        earliest_test_date = next_period_date + timedelta(days=1)  # 생리 예정일 다음날부터
        best_test_date = next_period_date + timedelta(days=3)     # 더 정확한 결과를 위해
        
        # 관계일이 제공된 경우 관계일 기준 테스트 시기도 계산
        relation_based_test = None
        if relationship_date:
            relation_based_test = relationship_date + timedelta(days=14)  # 관계 후 14일
        
        return {
            'ovulation_date': ovulation_date,
            'fertile_start': fertile_start,
            'fertile_end': fertile_end,
            'next_period_date': next_period_date,
            'earliest_test_date': earliest_test_date,
            'best_test_date': best_test_date,
            'relation_based_test': relation_based_test
        }
    
    # 입력 폼
    st.subheader("📅 생리 주기 정보 입력")
    
    col1, col2 = st.columns(2)
    
    with col1:
        last_period = st.date_input(
            "마지막 생리 시작일",
            value=datetime.now().date() - timedelta(days=14),
            help="마지막 생리가 시작된 날짜를 선택하세요"
        )
        
        cycle_length = st.slider(
            "생리주기 (일)",
            min_value=21,
            max_value=35,
            value=28,
            help="평소 생리주기를 선택하세요 (일반적으로 21-35일)"
        )
    
    with col2:
        relationship_date = st.date_input(
            "관계일 (선택사항)",
            value=None,
            help="관계를 가진 날짜를 선택하면 더 정확한 테스트 시기를 안내해드립니다"
        )
    
    if st.button("🔮 배란일 & 테스트 시기 계산하기", type="primary", use_container_width=True):
        
        # 계산 실행
        results = calculate_ovulation_and_test_dates(last_period, cycle_length, relationship_date)
        
        st.markdown("---")
        st.subheader("🎯 계산 결과")
        
        # 배란일 하이라이트
        st.markdown("### 🌟 바로 이날이야! 🌟")
        st.success(f"**가장 임신 가능성이 높은 날: {results['ovulation_date'].strftime('%Y년 %m월 %d일')} (배란일)**")
        
        # 임신 가능 기간
        st.markdown("### 📅 임신 가능 기간")
        st.info(f"""
        **{results['fertile_start'].strftime('%Y년 %m월 %d일')} ~ {results['fertile_end'].strftime('%Y년 %m월 %d일')}**
        
        이 기간 중 관계를 가지면 임신 가능성이 높습니다! 🤗
        """)
        
        # 임신테스트 시기
        st.markdown("### 🧪 임신테스트기 사용 시기")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### �� 생리 기준")
            st.warning(f"""
            **가장 빠른 검사일:** {results['earliest_test_date'].strftime('%Y년 %m월 %d일')}
            (생리 예정일 다음날)
            
            **권장 검사일:** {results['best_test_date'].strftime('%Y년 %m월 %d일')}
            (더 정확한 결과)
            """)
        
        with col2:
            if relationship_date and results['relation_based_test']:
                st.markdown("#### 💕 관계일 기준")
                st.success(f"""
                **검사 가능일:** {results['relation_based_test'].strftime('%Y년 %m월 %d일')}
                (관계 후 14일)
                
                이날부터 테스트 가능! 🎉
                """)
            else:
                st.info("관계일을 입력하시면 더 정확한 테스트 시기를 알려드려요!")
        
        # 추가 정보
        st.markdown("### 📋 유용한 정보")
        
        info_tab1, info_tab2, info_tab3 = st.tabs(["🕐 타이밍 가이드", "🔬 테스트 팁", "⚠️ 주의사항"])
        
        with info_tab1:
            st.markdown("""
            #### 🎯 최적의 타이밍
            - **배란일 3일 전 ~ 배란일**: 임신 확률 가장 높음
            - **배란일 당일**: 임신 확률 최고점! 🌟
            - **배란일 1일 후**: 여전히 임신 가능
            
            #### 📈 임신 확률
            - 배란일 3일 전: 약 8%
            - 배란일 2일 전: 약 13%
            - 배란일 1일 전: 약 21%
            - **배란일 당일: 약 33%** ⭐
            """)
        
        with info_tab2:
            st.markdown("""
            #### 🧪 정확한 테스트를 위한 팁
            - **아침 첫 소변** 사용 (hCG 농도 가장 높음)
            - **생리 예정일 이후** 검사 권장
            - **너무 이른 검사는 위음성** 가능
            - **약한 선도 양성**으로 간주
            
            #### 🔄 재검사 시기
            - 음성이지만 생리가 늦어지면: 3-5일 후 재검사
            - 양성이지만 확신이 안 서면: 혈액검사 권장
            """)
        
        with info_tab3:
            st.markdown("""
            #### ⚠️ 중요한 주의사항
            - 본 계산은 **일반적인 28일 주기** 기준입니다
            - **개인차**가 있을 수 있으므로 참고용으로만 사용하세요
            - **불규칙한 생리주기**인 경우 정확도가 떨어질 수 있습니다
            - **임신 계획**이 있다면 의료진 상담을 권장합니다
            
            #### 🏥 병원 방문이 필요한 경우
            - 6개월 이상 시도해도 임신이 안 되는 경우
            - 생리주기가 매우 불규칙한 경우
            - 임신 준비를 위한 건강검진
            """)

# 면책 조항
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #666; font-size: 12px; padding: 20px; background-color: #f0f0f0; border-radius: 10px;'>
    <strong>⚠️ 의료 면책 조항</strong><br>
    본 애플리케이션은 보조 도구일 뿐이며, 의료진의 정확한 진단을 대체할 수 없습니다.<br>
    배란일 계산은 일반적인 28일 주기를 기준으로 하며 개인차가 있을 수 있습니다.<br>
    <strong>임신 여부와 임신 계획은 반드시 의료진과 상담하세요.</strong>
    </div>
    """, 
    unsafe_allow_html=True
)

# 개발자 정보
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #888; font-size: 11px; padding: 15px; margin-top: 20px;'>
    <p>💻 <strong>Developed by BNK</strong></p>
    <p>📧 Contact: <a href="mailto:ppojung2@naver.com" style="color: #ff6b9d; text-decoration: none;">ppojung2@naver.com</a></p>
    <p style="margin-top: 10px; color: #aaa;">임신 기록 어시스턴트 v2.0 🤱</p>
    </div>
    """, 
    unsafe_allow_html=True
)
