import streamlit as st
import pandas as pd

# 1. 웹앱 기본 설정
st.set_page_config(page_title="2026 정보 설문지", page_icon="🏖️", layout="centered")

# 눈이 아프지 않은 여름 감성 커스텀 CSS
st.markdown("""
    <style>
    .main { background-color: #f4f9f9; }
    h1 { color: #1e5163; }
    h3 { color: #2d768d; }
    .stButton>button { background-color: #4ca1a3; color: white; border-radius: 8px; border: none; }
    .stButton>button:hover { background-color: #3b8284; color: white; }
    </style>
    """, unsafe_allow_html=True)

# 2. 구글 시트 데이터 로드 함수
# 본인의 구글 시트 URL에서 d/ 와 /edit 사이의 문자열(ID)을 입력하세요.
SHEET_ID = "1W-IiwnreVtr9VnoCH725yddS6EQYSxRGO9CrZ_YY8cM"

@st.cache_data(ttl=60)  # 60초 동안 데이터를 캐싱하여 자주 불러오지 않도록 설정
def load_data_from_sheets():
    # 탭 이름을 지정하여 데이터프레임으로 변환
    students_url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=students"
    activities_url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=activities"
    
    df_students = pd.read_csv(students_url)
    df_activities = pd.read_csv(activities_url)
    
    # 학번(id) 컬럼을 매칭하기 쉽도록 문자열로 변환 및 공백 제거
    df_students['id'] = df_students['id'].astype(str).str.strip()
    df_activities['id'] = df_activities['id'].astype(str).str.strip()
    
    return df_students, df_activities

try:
    df_students, df_activities = load_data_from_sheets()
except Exception as e:
    st.error("구글 시트 데이터를 불러오는 데 실패했습니다. 링크 공유 설정 및 SHEET_ID를 확인해주세요.")
    st.stop()

# 제출 결과를 저장할 세션 상태 초기화 (실제 운영 시에는 결과용 시트에 append하는 것이 좋습니다)
if 'survey_results' not in st.session_state:
    st.session_state['survey_results'] = {}

# 3. 사이드바 - 모드 전환
st.sidebar.title("🏖️ 세특 설문 시스템")
mode = st.sidebar.radio("모드를 선택하세요", ["학생 설문 참여", "교사 결과 확인"])

# --- 교사 결과 확인 페이지 ---
if mode == "교사 결과 확인":
    st.title("👩‍🏫 교사 결과 확인")
    teacher_pw = st.text_input("교사 인증 비밀번호를 입력하세요.", type="password")
    if teacher_pw == "admin1234":
        st.success("인증되었습니다.")
        st.markdown("### 📥 학생 제출 결과")
        if st.session_state['survey_results']:
            st.write(st.session_state['survey_results'])
        else:
            st.write("아직 제출한 학생이 없습니다.")
    elif teacher_pw:
        st.error("비밀번호가 일치하지 않습니다.")

# --- 학생 설문 참여 페이지 ---
else:
    st.title("정보 세특 설문지")
    st.caption("구글 시트에 등록된 본인의 활동을 확인하고 설문을 진행하세요.")
    st.write("---")
    
    if 'logged_in_student' not in st.session_state:
        st.subheader("🔑 학생 로그인")
        input_id = st.text_input("학번을 입력하세요 (예: 30101)").strip()
        input_pw = st.text_input("비밀번호를 입력하세요", type="password").strip()
        
        if st.button("입장하기"):
            # 시트에서 해당 학번 학생 정보 조회
            student_row = df_students[df_students['id'] == input_id]
            
            if not student_row.empty:
                correct_pw = str(student_row.iloc[0]['password']).strip()
                if input_pw == correct_pw:
                    st.session_state['logged_in_student'] = input_id
                    st.session_state['logged_in_name'] = student_row.iloc[0]['name']
                    st.success(f"{st.session_state['logged_in_name']}님 환영합니다!")
                    st.rerun()
                else:
                    st.error("비밀번호가 틀렸습니다.")
            else:
                st.error("등록되지 않은 학번입니다. 선생님께 문의하세요.")
                
    else:
        student_id = st.session_state['logged_in_student']
        student_name = st.session_state['logged_in_name']
        
        st.markdown(f"### 🧑‍🎓 접속 학생: **{student_id} {student_name}**")
        if st.button("로그아웃"):
            del st.session_state['logged_in_student']
            del st.session_state['logged_in_name']
            st.rerun()
            
        st.write("---")
        
        # 🌟 핵심: 로그인한 학생의 학번과 일치하는 활동만 필터링 (학생별 개수가 달라도 자동 처리됨)
        my_activities = df_activities[df_activities['id'] == student_id]
        
        if my_activities.empty:
            st.warning("조회된 활동 데이터가 없습니다. 선생님께 확인 요청을 하세요.")
        else:
            with st.form(key='survey_form'):
                answers = {}
                st.subheader("💡 나의 활동별 느낀점 작성")
                
                # 학생에게 할당된 활동 개수만큼 반복문 실행
                for index, row in my_activities.iterrows():
                    act_title = row['title']
                    act_desc = row['desc']
                    act_img = row['img'] if pd.notna(row['img']) else "✨"
                    
                    st.markdown(f"#### {act_img} {act_title}")
                    st.write(act_desc)
                    
                    include = st.checkbox("이 활동을 생활기록부에 기록하는 것에 동의합니다.", value=True, key=f"inc_{index}")
                    
                    if include:
                        reflection = st.text_area(
                            "이 활동에서 본인이 노력한 점이나 배우고 느낀 점을 구체적으로 적어주세요.", 
                            key=f"ref_{index}"
                        )
                        answers[act_title] = {"상태": "반영 요청", "내용": reflection}
                    else:
                        st.warning("⚠️ 이 활동은 생기부 작성에서 제외됩니다.")
                        answers[act_title] = {"상태": "제외 요청", "내용": ""}
                    st.write("---")
                
                st.subheader("✉️ 선생님께 하고 싶은 말")
                teacher_msg = st.text_area("그 외에 추가하고 싶거나 선생님께 드리고 싶은 말씀을 적어주세요.")
                answers["선생님께 드리는 메시지"] = teacher_msg
                
                submit_button = st.form_submit_button(label="🌊 설문지 제출하기")
                
                if submit_button:
                    st.session_state['survey_results'][student_id] = answers
                    st.balloons()
                    st.success("설문이 성공적으로 제출되었습니다! 알찬 생기부로 보답할게요. ☀️")
