import streamlit as st
import pandas as pd
import os
from datetime import datetime

# ==========================================
# 데이터 파일 경로 정의
# ==========================================
DATA_FILE = "qc_data.csv"
SPEC_FILE = "qc_specs.csv"
CLEAN_FILE = "cleaning_specs.csv"
VERIFY_FILE = "verify_plan.csv"
OTHER_SCHED_FILE = "other_schedule.csv"
HEALTH_CERT_FILE = "health_cert.csv" 
EMPLOYEE_FILE = "employees.csv"
FACILITY_FILE = "facilities.csv"
REPAIR_FILE = "repairs.csv"
ANNUAL_LEAVE_FILE = "annual_leave_records.csv"   
CALIB_LIST_FILE = "calib_list.csv"
CALIB_REPORT_FILE = "calib_report.csv"
FILTER_PLAN_FILE = "filter_plan.csv"
NOTICE_BOARD_FILE = "notice_board.csv" 
POLL_BOARD_FILE = "poll_board.csv" 
HACCP_REVISION_FILE = "haccp_revision.csv"
FLOW_FILE = "haccp_flowchart.csv"
FLOW_CATEGORY_FILE = "haccp_flow_categories.csv"
CCP_DECISION_DIR = "ccp_decisions"
HAZARD_FILE      = "hazard_analysis.csv"
RM_HAZARD_FILE   = "rm_hazard_analysis.csv"  
RM_FILE          = "raw_materials.csv"        
RM_SPEC_DIR      = "rm_specs"                 
OUTBOUND_FILE    = "outbound_records.csv"     
INVENTORY_ADJ_FILE = "inventory_adj.csv"      
HISTORY_LOG_FILE = "history_log.csv"          

# ==========================================
# 캐시 관리 유틸리티
# ==========================================
def clear_all_cache():
    st.cache_data.clear()
    st.cache_resource.clear()

def log_history(action, target, detail=""):
    """작성 일시, 작업자(세션 정보), 대상 메뉴/기능, 작업 내용, 세부 사항을 CSV에 기록"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    worker = st.session_state.get("worker_name", "시스템/관리자")
    
    new_entry = pd.DataFrame([{
        "일시": now,
        "작업자": worker,
        "대상": target,
        "작업내용": action,
        "상세": detail
    }])
    
    if os.path.exists(HISTORY_LOG_FILE):
        try:
            new_entry.to_csv(HISTORY_LOG_FILE, mode='a', header=False, index=False, encoding='utf-8-sig')
        except:
            pass
    else:
        new_entry.to_csv(HISTORY_LOG_FILE, index=False, encoding='utf-8-sig')

# ==========================================
# 데이터 로드 함수 (캐싱 적용)
# ==========================================

@st.cache_data
def load_data():
    cols = ["생산일", "유형", "제품명", "생산량", "소비기한", "규격", "질소(%)", "수분(%)", "색도(Agtron)", "추출시간(sec)", "추출시간_상세", "날짜기록", "판정", "비고"]
    if os.path.exists(DATA_FILE): 
        try: 
            df = pd.read_csv(DATA_FILE)
            if "단위" in df.columns and "규격" not in df.columns:
                df = df.rename(columns={"단위": "규격"})
            for col in cols:
                if col not in df.columns:
                    if col == "생산량": df[col] = 0
                    else: df[col] = ""
            return df[cols]
        except Exception: pass
    return pd.DataFrame(columns=cols)

@st.cache_data
def load_specs():
    if os.path.exists(SPEC_FILE): 
        try:
            df = pd.read_csv(SPEC_FILE, dtype=str)
            if "제품코드" not in df.columns: df.insert(0, "제품코드", [f"P-{str(i+1).zfill(3)}" for i in range(len(df))])
            if "규격" not in df.columns:
                if "단위" in df.columns:
                    df = df.rename(columns={"단위": "규격"})
                else:
                    df.insert(3, "규격", "EA") 
            return df
        except Exception: pass
    return pd.DataFrame(columns=["제품코드", "제품명", "유형", "규격", "최소_질소", "최대_질소", "최소_수분", "최대_수분", "최소_색도", "최대_색도", "최소_추출", "최대_추출", "날짜유형", "날짜기록"])

@st.cache_data
def load_cleaning_specs():
    if os.path.exists(CLEAN_FILE): 
        try:
            df = pd.read_csv(CLEAN_FILE, dtype=str)
            req_cols = ['ID', '대분류', '구역', '설비명', '부위', '세척소독방법', '주기', '사용도구', '책임자', '사진파일']
            for col in req_cols:
                if col not in df.columns:
                    if col == 'ID': df['ID'] = [f"C-{str(i).zfill(4)}" for i in range(len(df))]
                    elif col == '대분류': df['대분류'] = "5. 식품 제조시설"  
                    elif col == '설비명': df['설비명'] = "기본대상"
                    elif col == '부위': df['부위'] = df.get('관리부위', "")
                    elif col == '세척소독방법': df['세척소독방법'] = df.get('작업방법', "")
                    elif col == '주기': df['주기'] = df.get('청소주기', "")
                    elif col == '사용도구': df['사용도구'] = df.get('세제_도구', "")
                    else: df[col] = ""
            return df[req_cols]
        except Exception: pass
    return pd.DataFrame(columns=['ID', '대분류', '구역', '설비명', '부위', '세척소독방법', '주기', '사용도구', '책임자', '사진파일'])

@st.cache_data
def load_filter_plan():
    if os.path.exists(FILTER_PLAN_FILE):
        try:
            df = pd.read_csv(FILTER_PLAN_FILE, dtype=str).fillna("")
            if '설비명_위치' in df.columns:
                df.rename(columns={'설비명_위치': '설치장소', '필터종류': '필터명', '최근점검일': '점검일자', '차기점검일': '차기점검일자'}, inplace=True)
                if '내용' not in df.columns: df['내용'] = '교체'
            if '설치장소' in df.columns: return df
        except Exception: pass
    return pd.DataFrame(columns=["설치장소", "필터명", "내용", "주기_개월", "점검일자", "차기점검일자", "상태", "비고"])

@st.cache_data
def load_verify():
    if os.path.exists(VERIFY_FILE): 
        try: 
            df = pd.read_csv(VERIFY_FILE)
            if '담당자' not in df.columns: df['담당자'] = ""
            if '계획일자' in df.columns: return df
        except Exception: pass
    return pd.DataFrame(columns=["계획일자", "검증종류", "검증항목", "세부내용", "검증방법", "상태", "담당자"])

@st.cache_data
def load_other_sched():
    if os.path.exists(OTHER_SCHED_FILE): 
        try:
            df = pd.read_csv(OTHER_SCHED_FILE)
            if '담당자' not in df.columns: df['담당자'] = ""
            if '일자' in df.columns: return df
        except Exception: pass
    return pd.DataFrame(columns=["일자", "일정명", "세부내용", "상태", "담당자"])

@st.cache_data
def load_health_cert():
    if os.path.exists(HEALTH_CERT_FILE):
        try:
            df = pd.read_csv(HEALTH_CERT_FILE)
            if '검진일자' in df.columns: return df
        except Exception: pass
    return pd.DataFrame(columns=["직급", "이름", "연락처", "검진일자"])

@st.cache_data
def load_employees():
    if os.path.exists(EMPLOYEE_FILE):
        try:
            df = pd.read_csv(EMPLOYEE_FILE, dtype=str)
            if 'HACCP 직책' not in df.columns: df['HACCP 직책'] = "해당없음"
            if '모니터링 CCP' not in df.columns: df['모니터링 CCP'] = ""
            if '기타' not in df.columns: df['기타'] = ""
            if '사번' in df.columns: return df
        except Exception: pass
    return pd.DataFrame(columns=["사번", "직급", "이름", "연락처", "입사일", "재직상태", "HACCP 직책", "모니터링 CCP", "기타"])

@st.cache_data
def load_facilities():
    if os.path.exists(FACILITY_FILE):
        try: return pd.read_csv(FACILITY_FILE, dtype=str)
        except Exception: pass
    return pd.DataFrame(columns=["설비번호", "설비명", "사용용도", "전압", "구입년월", "제조회사명", "설치장소", "관리부서", "관리자_정", "관리자_부", "특이사항"])

@st.cache_data
def load_repairs():
    if os.path.exists(REPAIR_FILE):
        try: return pd.read_csv(REPAIR_FILE, dtype=str)
        except Exception: pass
    return pd.DataFrame(columns=["설비번호", "수리일자", "수리사항", "수리처", "비고"])

@st.cache_data
def load_annual_leave():
    if os.path.exists(ANNUAL_LEAVE_FILE):
        try:
            df = pd.read_csv(ANNUAL_LEAVE_FILE, dtype=str).fillna("")
            for c in ["사번","이름","날짜","유형","비고"]:
                if c not in df.columns: df[c] = ""
            return df[["사번","이름","날짜","유형","비고"]]
        except Exception: pass
    return pd.DataFrame(columns=["사번","이름","날짜","유형","비고"])

@st.cache_data
def load_calib_list():
    if os.path.exists(CALIB_LIST_FILE):
        try:
            df = pd.read_csv(CALIB_LIST_FILE, dtype=str)
            if "차기_검교정일자" not in df.columns: df["차기_검교정일자"] = ""
            return df
        except Exception: pass
    return pd.DataFrame(columns=["관리번호", "검사_설비명", "측정범위", "주기", "구분", "검교정일자", "차기_검교정일자", "비고"])

@st.cache_data
def load_calib_reports():
    if os.path.exists(CALIB_REPORT_FILE):
        try: return pd.read_csv(CALIB_REPORT_FILE, dtype=str)
        except Exception: pass
    return pd.DataFrame(columns=["설비명", "교정일자", "작성자", "검교정방법", "판정기준", "표준값", "측정값", "보정율/오차", "개선조치", "판정결과"])

@st.cache_data
def load_notices():
    if os.path.exists(NOTICE_BOARD_FILE):
        try: return pd.read_csv(NOTICE_BOARD_FILE)
        except Exception: pass
    return pd.DataFrame(columns=["작성일", "작성자", "제목", "내용", "중요공지"])

@st.cache_data
def load_polls():
    if os.path.exists(POLL_BOARD_FILE):
        try: return pd.read_csv(POLL_BOARD_FILE)
        except Exception: pass
    return pd.DataFrame(columns=["ID", "작성일", "제목", "선택지", "투표현황", "참여자"])

@st.cache_data
def load_outbound_records():
    cols = ["출고일", "출고시간", "차량번호", "기사명", "출하처", "유형", "제품명", "규격", "제조일자", "소비기한", "수량", "비고"]
    if os.path.exists(OUTBOUND_FILE):
        try:
            df = pd.read_csv(OUTBOUND_FILE, dtype=str)
            for c in cols:
                if c not in df.columns: df[c] = ""
            return df[cols]
        except Exception: pass
    return pd.DataFrame(columns=cols)

@st.cache_data
def load_inventory_adj():
    cols = ["조정일시", "유형", "제품명", "규격", "생산일", "소비기한", "기존재고", "변경재고", "방향", "차이", "사유"]
    if os.path.exists(INVENTORY_ADJ_FILE):
        try: 
            df = pd.read_csv(INVENTORY_ADJ_FILE, dtype=str)
            for c in cols:
                if c not in df.columns: df[c] = ""
            return df[cols]
        except Exception: pass
    return pd.DataFrame(columns=cols)

@st.cache_data
def load_haccp_revisions():
    if os.path.exists(HACCP_REVISION_FILE):
        try: 
            return pd.read_csv(HACCP_REVISION_FILE, dtype=str)
        except Exception: pass
    return pd.DataFrame(columns=["개정일자", "분류", "문서명", "개정번호", "개정사유"])

@st.cache_data
def load_flowchart():
    if os.path.exists(FLOW_FILE):
        try: return pd.read_csv(FLOW_FILE, dtype=str)
        except Exception: pass
    return pd.DataFrame(columns=["순서", "단계명", "설명", "유형", "CCP여부", "CCP번호"])

@st.cache_data
def load_flow_categories():
    if os.path.exists(FLOW_CATEGORY_FILE):
        try: return pd.read_csv(FLOW_CATEGORY_FILE, dtype=str)
        except Exception: pass
    return pd.DataFrame([{"cat_id": "main", "cat_name": "메인 공정 (커피 원두)", "description": "핵심 제조 공정 흐름"}])

@st.cache_data
def load_flowchart_by_cat(cat_id: str):
    safe_id = str(cat_id).replace("/", "_").replace("\\", "_").replace(" ", "_")
    fpath = f"haccp_flowchart_{safe_id}.csv"
    if os.path.exists(fpath):
        try: return pd.read_csv(fpath, dtype=str)
        except Exception: pass
    return pd.DataFrame(columns=["순서", "단계명", "설명", "유형", "CCP여부", "CCP번호", "lane", "merge_from", "merge_label", "merge_from_2", "merge_label_2", "merge_from_3", "merge_label_3"])

@st.cache_data
def load_ccp_decision(cat_id: str):
    os.makedirs(CCP_DECISION_DIR, exist_ok=True)
    safe_id = str(cat_id).replace("/","_").replace("\\","_").replace(" ","_")
    fpath = os.path.join(CCP_DECISION_DIR, f"ccp_decision_{safe_id}.csv")
    cols = ["단계명","위해유형","위해요소",
            "Q1_답변","Q1_비고","Q2_답변","Q2_비고","Q21_답변","Q21_비고",
            "Q3_답변","Q3_비고","Q4_답변","Q4_비고","Q5_답변","Q5_비고",
            "CCP결정","CCP번호","비고"]
    if os.path.exists(fpath):
        try:
            df = pd.read_csv(fpath, dtype=str).fillna("")
            for c in cols:
                if c not in df.columns: df[c] = ""
            return df[cols]
        except Exception: pass
    return pd.DataFrame(columns=cols)

@st.cache_data
def load_raw_materials():
    if os.path.exists(RM_FILE):
        try: return pd.read_csv(RM_FILE, dtype=str)
        except Exception: pass
    return pd.DataFrame(columns=["분류", "품목명", "규격", "제조업체", "단위"])

@st.cache_data
def load_hazard_analysis():
    if os.path.exists(HAZARD_FILE):
        try: return pd.read_csv(HAZARD_FILE, dtype=str)
        except Exception: pass
    return pd.DataFrame(columns=["공정명", "위해요소", "발생원인", "심각성", "발생가능성", "위해평가", "예방조치", "비고"])

@st.cache_data
def load_rm_hazard_analysis():
    if os.path.exists(RM_HAZARD_FILE):
        try: return pd.read_csv(RM_HAZARD_FILE, dtype=str)
        except Exception: pass
    return pd.DataFrame(columns=["구분", "품목명", "위해요소", "평가결과", "조치사항"])

# ==========================================
# 데이터 저장 함수 (저장 후 캐시 초기화)
# ==========================================

def save_data(df, file_path):
    df.to_csv(file_path, index=False, encoding='utf-8-sig')
    st.cache_data.clear()

def save_ccp_decision(cat_id: str, df):
    os.makedirs(CCP_DECISION_DIR, exist_ok=True)
    safe_id = str(cat_id).replace("/","_").replace("\\","_").replace(" ","_")
    fpath = os.path.join(CCP_DECISION_DIR, f"ccp_decision_{safe_id}.csv")
    df.to_csv(fpath, index=False, encoding="utf-8-sig")
    log_history("CCP 결정도 업데이트", f"공정: {cat_id}", f"데이터 {len(df)}건 저장")
    st.cache_data.clear()

def save_annual_leave(df):
    df.to_csv(ANNUAL_LEAVE_FILE, index=False, encoding="utf-8-sig")
    st.cache_data.clear()
