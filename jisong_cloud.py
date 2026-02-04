import streamlit as st
import os
import datetime
import json
import time
import zipfile
import io

# --- 설정 ---
MEMO_FILE = "memos.json"
ACCESS_LOG_FILE = "access_log.json"
UPLOAD_DIR = "files"
now = datetime.datetime.now()

# --- 초기화 및 데이터 관리 ---
def init_app():
    """앱 실행 시 필요한 디렉토리 생성"""
    if not os.path.exists(UPLOAD_DIR):
        os.makedirs(UPLOAD_DIR)

def load_memos():
    if not os.path.exists(MEMO_FILE):
        return {}
    with open(MEMO_FILE, "r") as f:
        memos = json.load(f)
        for title, data in memos.items():
            if isinstance(data, str):
                memos[title] = {"content": data, "timestamp": now.strftime("%Y-%m-%d %H:%M")}
        return memos

def save_memos(memos):
    with open(MEMO_FILE, "w") as f:
        json.dump(memos, f, ensure_ascii=False, indent=4)

def save_uploaded_file(uploaded_file):
    """업로드된 파일을 서버(files 폴더)에 저장"""
    try:
        file_path = os.path.join(UPLOAD_DIR, uploaded_file.name)
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        return True
    except Exception as e:
        return False

def create_zip_of_files():
    """UPLOAD_DIR 내의 모든 파일을 압축하여 bytes로 반환"""
    if not os.path.exists(UPLOAD_DIR):
        return None
    
    files = os.listdir(UPLOAD_DIR)
    if not files:
        return None
        
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for file_name in files:
            file_path = os.path.join(UPLOAD_DIR, file_name)
            zf.write(file_path, arcname=file_name)
    
    zip_buffer.seek(0)
    return zip_buffer

# --- 접속 기록 관리 함수 ---
def handle_access_log():
    if "last_access_display" not in st.session_state:
        if os.path.exists(ACCESS_LOG_FILE):
            with open(ACCESS_LOG_FILE, "r") as f:
                try:
                    data = json.load(f)
                    st.session_state.last_access_display = data.get("last_access", "기록 없음")
                except:
                    st.session_state.last_access_display = "기록 오류"
        else:
            st.session_state.last_access_display = "최초 접속"

        with open(ACCESS_LOG_FILE, "w") as f:
            json.dump({"last_access": now.strftime("%Y-%m-%d %H:%M:%S")}, f)

# --- 메인 함수 ---
def main():
    init_app()
    handle_access_log()
    
    st.set_page_config(page_title="Jisong Cloud", layout="wide") 

    memos = load_memos()

    # --- [사이드바 메뉴] ---
    st.sidebar.title("Jisong Cloud")
    
    if "menu" not in st.session_state:
        st.session_state.menu = "files"

    if st.session_state.menu == "files":
        btn_files_type = "primary"
        btn_memos_type = "secondary"
    else:
        btn_files_type = "secondary"
        btn_memos_type = "primary"

    if st.sidebar.button("📂 웹하드", type=btn_files_type, use_container_width=True):
        st.session_state.menu = "files"
        st.rerun()
        
    if st.sidebar.button("📝 메모장", type=btn_memos_type, use_container_width=True):
        st.session_state.menu = "memos"
        st.rerun()
    
    st.sidebar.markdown("---")
    st.sidebar.caption(f"🕒 현재 시간: {now.strftime('%H:%M')}")
    st.sidebar.caption(f"🔒 마지막 접속: {st.session_state.last_access_display}")
    st.sidebar.markdown("---")
    st.sidebar.caption("@Jisong Bang 2026") 

    # --- [메뉴 1] 파일 전송 기능 ---
    if st.session_state.menu == "files":
        st.title("📂 웹하드")
        
        uploaded_files = st.file_uploader("파일 선택 (PPT, PDF 등)", accept_multiple_files=True)
        
        if uploaded_files:
            if st.button("서버로 전송", use_container_width=True, type="primary"):
                success_count = 0
                for u_file in uploaded_files:
                    if save_uploaded_file(u_file):
                        success_count += 1
                
                if success_count > 0:
                    st.toast(f"✅ {success_count}개 파일 업로드 완료!")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("업로드 실패")

        st.markdown("---")
        st.subheader("💾 저장된 파일")
        
        if os.path.exists(UPLOAD_DIR):
            files = os.listdir(UPLOAD_DIR)
            
            # [수정됨] 파일을 수정 시간(mtime) 기준 내림차순 정렬 (최신순)
            # os.path.join으로 전체 경로를 만든 뒤 getmtime으로 시간 추출 -> 역순 정렬
            files.sort(key=lambda f: os.path.getmtime(os.path.join(UPLOAD_DIR, f)), reverse=True)
            
            if files:
                for file_name in files:
                    file_path = os.path.join(UPLOAD_DIR, file_name)
                    
                    # 파일 날짜 확인용 (옵션)
                    file_time = datetime.datetime.fromtimestamp(os.path.getmtime(file_path)).strftime('%Y-%m-%d %H:%M')
                    
                    col_d1, col_d2 = st.columns([4, 1])
                    
                    with col_d1:
                        with open(file_path, "rb") as f:
                            # 버튼 라벨에 시간 정보도 살짝 추가해주면 더 직관적입니다.
                            st.download_button(
                                label=f"{file_name} ({file_time})", 
                                data=f,
                                file_name=file_name,
                                mime="application/octet-stream",
                                use_container_width=True
                            )
                    
                    with col_d2:
                        if st.button("🗑️", key=f"del_{file_name}", use_container_width=True):
                            try:
                                os.remove(file_path)
                                st.toast(f"🗑️ '{file_name}' 삭제됨")
                                time.sleep(0.5)
                                st.rerun()
                            except Exception as e:
                                st.error(f"삭제 오류: {e}")
                
                st.markdown("---")
                st.markdown("📦 일괄 처리")
                zip_data = create_zip_of_files()
                if zip_data:
                    st.download_button(
                        label="📥 모든 파일 ZIP으로 다운로드",
                        data=zip_data,
                        file_name=f"files_{now.strftime('%Y%m%d_%H%M')}.zip",
                        mime="application/zip",
                        use_container_width=True
                    )

                st.markdown("---")
                st.markdown("🧹 보안 관리")
                if st.button("🔥 모든 파일 삭제", type="primary", use_container_width=True):
                    try:
                        files_to_delete = os.listdir(UPLOAD_DIR)
                        for f in files_to_delete:
                            os.remove(os.path.join(UPLOAD_DIR, f))
                        st.toast("✅ 모든 파일이 삭제되었습니다.")
                        time.sleep(1)
                        st.rerun()
                    except Exception as e:
                        st.error(f"삭제 중 오류 발생: {e}")
                        
            else:
                st.write("📂 현재 저장된 파일이 없습니다.")
        else:
            st.write("📂 저장소 폴더가 생성되지 않았습니다.")

    # --- [메뉴 2] 메모장 기능 ---
    elif st.session_state.menu == "memos":
        st.title("📝 메모장")
        
        with st.container():
            st.subheader("새 메모 작성")
            col_new1, col_new2 = st.columns([3, 1], vertical_alignment="bottom")
            with col_new1:
                new_title = st.text_input("제목", placeholder="제목을 입력하세요")
            with col_new2:
                save_btn = st.button("저장하기", type="primary", use_container_width=True)

            new_content = st.text_area("내용", height=150, placeholder="여기에 내용을 입력하세요")
            
            if save_btn:
                if new_title:
                    memos[new_title] = {"content": new_content, "timestamp": now.strftime("%Y-%m-%d %H:%M")}
                    save_memos(memos)
                    st.toast("✅ 메모 저장 완료!")
                    time.sleep(0.5)
                    st.rerun()
                else:
                    st.warning("제목을 입력해주세요.")

        st.markdown("---")
        st.subheader("💾 저장된 메모")

        if not memos:
            st.info("저장된 메모가 없습니다.")
        
        for t, d in reversed(list(memos.items())):
            with st.expander(f"{t} ({d['timestamp']})"):
                line_count = d['content'].count('\n') + 1
                dynamic_height = 40 + (line_count * 25)

                edited_content = st.text_area(
                    label="내용 수정",
                    value=d['content'],
                    height=dynamic_height,
                    key=f"content_{t}"
                )

                col_m1, col_m2 = st.columns([4, 1])
                with col_m1:
                    if st.button("수정 내용 저장", key=f"save_{t}", use_container_width=True):
                        memos[t] = {"content": edited_content, "timestamp": now.strftime("%Y-%m-%d %H:%M")}
                        save_memos(memos)
                        st.toast("✅ 수정되었습니다.")
                        time.sleep(0.5)
                        st.rerun()
                with col_m2:
                    if st.button("삭제", key=f"del_memo_{t}", type="secondary", use_container_width=True):
                        del memos[t]
                        save_memos(memos)
                        st.toast("🗑️ 삭제되었습니다.")
                        time.sleep(0.5)
                        st.rerun()

if __name__ == "__main__":
    main()