import streamlit as st
import pandas as pd
import os
from datetime import datetime

# ==========================================
# 파일 경로 및 상수 설정
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
ANNUAL_LEAVE_FILE = "annual_leave_records.csv"   # 파트타이머 연차 기록
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
RM_HAZARD_FILE   = "rm_hazard_analysis.csv"  # 원부자재 위해요소분석
RM_FILE          = "raw_materials.csv"        # 원·부자재 등록
RM_SPEC_DIR      = "rm_specs"                 # 원·부자재 규격서 디렉토리
OUTBOUND_FILE    = "outbound_records.csv"     # 출고 기록 데이터
INVENTORY_ADJ_FILE = "inventory_adj.csv"      # 재고 임의 조정 로그
HISTORY_LOG_FILE = "history_log.csv"          # 시스템 작업 히스토리 로그
SEVERITY_FILE    = "severity_settings.csv"    # 위해요소 심각성 설정
DESTINATION_FILE = "destinations.csv"         # 출하처 마스터 데이터
PALLET_MASTER_FILE = "pallet_master.csv"      # 파렛트 마스터 데이터
PALLET_LOG_FILE = "pallet_logs.csv"            # 파렛트 입출입 로그

# 원부자재 컬럼 정의
RM_COLS = [
    "원자재코드", "원자재명", "유형", "규격", "원산지", "제조원", "판매원", 
    "검사주기", "비고", "최소_수분", "최대_수분", "최소_밀도", "최대_밀도", "관능_기준"
]

# 세척소독 대분류 11종
CLEAN_CATEGORIES = [
    "1. 종업원", "2. 위생복장", "3. 작업장 주변", "4. 작업장 내부(공통)", 
    "5. 식품 제조시설", "6. 보관시설", "7. 운반도구 및 용기", 
    "8. 모니터링 및 검사장비", "9. 환기시설", "10. 폐기물처리용기", "11. 세척 소독 도구"
]

# ==========================================
# 히스토리 기록 함수
# ==========================================
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

@st.cache_data
def load_history_log(mtime=None):
    if os.path.exists(HISTORY_LOG_FILE):
        try:
            return pd.read_csv(HISTORY_LOG_FILE, dtype=str).fillna("-")
        except: pass
    return pd.DataFrame(columns=["일시", "작업자", "대상", "작업내용", "상세"])

def get_history_log():
    mtime = os.path.getmtime(HISTORY_LOG_FILE) if os.path.exists(HISTORY_LOG_FILE) else 0
    return load_history_log(mtime)

# ==========================================
# 데이터 로드 및 저장 함수 (HACCP 관련)
# ==========================================
@st.cache_data
def load_ccp_decision(cat_id: str, mtime=None):
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

def get_ccp_decision(cat_id: str):
    os.makedirs(CCP_DECISION_DIR, exist_ok=True)
    safe_id = str(cat_id).replace("/","_").replace("\\","_").replace(" ","_")
    fpath = os.path.join(CCP_DECISION_DIR, f"ccp_decision_{safe_id}.csv")
    mt = os.path.getmtime(fpath) if os.path.exists(fpath) else 0
    return load_ccp_decision(cat_id, mtime=mt)

def save_ccp_decision(cat_id: str, df):
    os.makedirs(CCP_DECISION_DIR, exist_ok=True)
    safe_id = str(cat_id).replace("/","_").replace("\\","_").replace(" ","_")
    fpath = os.path.join(CCP_DECISION_DIR, f"ccp_decision_{safe_id}.csv")
    df.to_csv(fpath, index=False, encoding="utf-8-sig")
    log_history("CCP 결정도 업데이트", f"공정: {cat_id}", f"데이터 {len(df)}건 저장")

# ── 원부자재 CCP 결정도 ────────────────────────────────────────────
@st.cache_data
def load_rm_ccp_decision(rm_code: str, mtime=None):
    os.makedirs(CCP_DECISION_DIR, exist_ok=True)
    safe_code = str(rm_code).replace("/","_").replace("\\","_").replace(" ","_")
    fpath = os.path.join(CCP_DECISION_DIR, f"rm_ccp_decision_{safe_code}.csv")
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

def get_rm_ccp_decision(rm_code: str):
    os.makedirs(CCP_DECISION_DIR, exist_ok=True)
    safe_code = str(rm_code).replace("/","_").replace("\\","_").replace(" ","_")
    fpath = os.path.join(CCP_DECISION_DIR, f"rm_ccp_decision_{safe_code}.csv")
    mt = os.path.getmtime(fpath) if os.path.exists(fpath) else 0
    return load_rm_ccp_decision(rm_code, mtime=mt)

def save_rm_ccp_decision(rm_code: str, df):
    os.makedirs(CCP_DECISION_DIR, exist_ok=True)
    safe_code = str(rm_code).replace("/","_").replace("\\","_").replace(" ","_")
    fpath = os.path.join(CCP_DECISION_DIR, f"rm_ccp_decision_{safe_code}.csv")
    df.to_csv(fpath, index=False, encoding="utf-8-sig")
    log_history("원부자재 CCP 결정도 업데이트", f"원부자재: {rm_code}", f"데이터 {len(df)}건 저장")

@st.cache_data
def load_haccp_revisions(mtime=None):
    if os.path.exists(HACCP_REVISION_FILE):
        try: 
            return pd.read_csv(HACCP_REVISION_FILE, dtype=str)
        except Exception: pass
    df_rev = pd.DataFrame(columns=["개정일자", "분류", "문서명", "개정번호", "개정사유"])
    if not os.path.exists(HACCP_REVISION_FILE):
        df_rev.to_csv(HACCP_REVISION_FILE, index=False, encoding='utf-8-sig')
    return df_rev

def get_haccp_revisions():
    mtime = os.path.getmtime(HACCP_REVISION_FILE) if os.path.exists(HACCP_REVISION_FILE) else 0
    return load_haccp_revisions(mtime)

def save_haccp_revisions(df):
    df.to_csv(HACCP_REVISION_FILE, index=False, encoding="utf-8-sig")
    log_history("HACCP 문서 개정 업데이트", "HACCP 관리", f"데이터 {len(df)}건 저장")

@st.cache_data
def load_flowchart(mtime=None):
    """공정 흐름도 단계 데이터 로드. 없으면 기본 커피 제조 공정 샘플 생성."""
    if os.path.exists(FLOW_FILE):
        try:
            return pd.read_csv(FLOW_FILE, dtype=str)
        except Exception: pass
    default_steps = [
        {"순서": "1",  "단계명": "원료 입고",        "설명": "생두, 부자재 입고 및 수량 확인",        "유형": "공정",  "CCP여부": "N", "CCP번호": ""},
        {"순서": "2",  "단계명": "원료 검사",        "설명": "관능검사, 이물 확인, 서류 검토",         "유형": "검사",  "CCP여부": "N", "CCP번호": ""},
        {"순서": "3",  "단계명": "원료 보관",        "설명": "온·습도 관리 창고 보관 (15℃ 이하)",     "유형": "공정",  "CCP여부": "N", "CCP번호": ""},
        {"순서": "4",  "단계명": "로스팅",           "설명": "로스터기 가열 처리 (열처리 CCP)",        "유형": "공정",  "CCP여부": "Y", "CCP번호": "CCP-1"},
        {"순서": "5",  "단계명": "냉각",             "설명": "로스팅 후 신속 냉각",                   "유형": "공정",  "CCP여부": "N", "CCP번호": ""},
        {"순서": "6",  "단계명": "분쇄",             "설명": "제품 규격에 맞는 입도 분쇄",             "유형": "공정",  "CCP여부": "N", "CCP번호": ""},
        {"순서": "7",  "단계명": "품질 검사",        "설명": "색도·수분·질소 측정 및 합불 판정",      "유형": "검사",  "CCP여부": "Y", "CCP번호": "CCP-2"},
        {"순서": "8",  "단계명": "충전/포장",        "설명": "캡슐 충전, 질소 치환, 밀봉",            "유형": "공정",  "CCP여부": "N", "CCP번호": ""},
        {"순서": "9",  "단계명": "금속 검출",        "설명": "금속 검출기 통과 (이물 CCP)",           "유형": "검사",  "CCP여부": "Y", "CCP번호": "CCP-3"},
        {"순서": "10", "단계명": "완제품 검사",      "설명": "외관, 중량, 표시사항 최종 확인",         "유형": "검사",  "CCP여부": "N", "CCP번호": ""},
        {"순서": "11", "단계명": "완제품 보관",      "설명": "온·습도 관리 창고 보관",                "유형": "공정",  "CCP여부": "N", "CCP번호": ""},
        {"순서": "12", "단계명": "출하/납품",        "설명": "주문 확인 및 배송 출고",                "유형": "공정",  "CCP여부": "N", "CCP번호": ""},
    ]
    df_flow = pd.DataFrame(default_steps)
    if not os.path.exists(FLOW_FILE):
        df_flow.to_csv(FLOW_FILE, index=False, encoding="utf-8-sig")
    return df_flow

def get_flowchart():
    mtime = os.path.getmtime(FLOW_FILE) if os.path.exists(FLOW_FILE) else 0
    return load_flowchart(mtime)

@st.cache_data
def load_flow_categories(mtime=None):
    """공정 흐름도 카테고리(제품군/라인) 목록 로드"""
    if os.path.exists(FLOW_CATEGORY_FILE):
        try:
            return pd.read_csv(FLOW_CATEGORY_FILE, dtype=str)
        except Exception: pass
    default_cats = pd.DataFrame([
        {"cat_id": "main", "cat_name": "메인 공정 (커피 원두)", "description": "핵심 제조 공정 흐름"},
    ])
    if not os.path.exists(FLOW_CATEGORY_FILE):
        default_cats.to_csv(FLOW_CATEGORY_FILE, index=False, encoding="utf-8-sig")
    return default_cats

def get_flow_categories():
    mtime = os.path.getmtime(FLOW_CATEGORY_FILE) if os.path.exists(FLOW_CATEGORY_FILE) else 0
    return load_flow_categories(mtime)

def save_flow_categories(df):
    df.to_csv(FLOW_CATEGORY_FILE, index=False, encoding="utf-8-sig")
    log_history("항목 카테고리 업데이트", "HACCP 관리", f"데이터 {len(df)}건 저장")

@st.cache_data
def load_flowchart_by_cat(cat_id: str, mtime: float = 0):
    """카테고리 ID에 해당하는 공정 단계 CSV 로드. 없으면 기본값 생성."""
    safe_id = str(cat_id).replace("/", "_").replace("\\", "_").replace(" ", "_")
    fpath = f"haccp_flowchart_{safe_id}.csv"
    if os.path.exists(fpath):
        try:
            return pd.read_csv(fpath, dtype=str)
        except Exception: pass
    if cat_id == "main":
        default_steps = [
            {"순서": "1",  "단계명": "원료 입고",    "설명": "생두 입고 및 수량 확인",             "유형": "공정", "CCP여부": "N", "CCP번호": "", "lane": "원재료", "merge_from": "", "merge_label": "", "merge_from_2": "", "merge_label_2": "", "merge_from_3": "", "merge_label_3": ""},
            {"순서": "2",  "단계명": "원료 검사",    "설명": "관능검사, 이물 확인",                "유형": "검사", "CCP여부": "N", "CCP번호": "", "lane": "원재료", "merge_from": "", "merge_label": "", "merge_from_2": "", "merge_label_2": "", "merge_from_3": "", "merge_label_3": ""},
            {"순서": "3",  "단계명": "원료 보관",    "설명": "온·습도 관리 창고 (15℃ 이하)",      "유형": "공정", "CCP여부": "N", "CCP번호": "", "lane": "원재료", "merge_from": "", "merge_label": "", "merge_from_2": "", "merge_label_2": "", "merge_from_3": "", "merge_label_3": ""},
            {"순서": "4",  "단계명": "선 별",        "설명": "이물·불량두 제거",                   "유형": "공정", "CCP여부": "N", "CCP번호": "", "lane": "원재료", "merge_from": "", "merge_label": "", "merge_from_2": "", "merge_label_2": "", "merge_from_3": "", "merge_label_3": ""},
            {"순서": "5",  "단계명": "계량/배합",    "설명": "블렌딩 배합비 계량",                 "유형": "공정", "CCP여부": "N", "CCP번호": "", "lane": "원재료", "merge_from": "", "merge_label": "", "merge_from_2": "", "merge_label_2": "", "merge_from_3": "", "merge_label_3": ""},
            {"순서": "6",  "단계명": "가열(로스팅)", "설명": "로스터기 가열 처리 (열처리 CCP)",    "유형": "공정", "CCP여부": "Y", "CCP번호": "CCP-1", "lane": "원재료", "merge_from": "", "merge_label": "", "merge_from_2": "", "merge_label_2": "", "merge_from_3": "", "merge_label_3": ""},
            {"순서": "7",  "단계명": "방 냉",        "설명": "로스팅 후 신속 냉각",                "유형": "공정", "CCP여부": "N", "CCP번호": "", "lane": "원재료", "merge_from": "", "merge_label": "", "merge_from_2": "", "merge_label_2": "", "merge_from_3": "", "merge_label_3": ""},
            {"순서": "8",  "단계명": "내포장",       "설명": "내포장재(PE) 충전 및 밀봉",          "유형": "공정", "CCP여부": "N", "CCP번호": "", "lane": "원재료", "merge_from": "포장재", "merge_label": "내포장재(PE)", "merge_from_2": "기타", "merge_label_2": "질소", "merge_from_3": "", "merge_label_3": ""},
            {"순서": "9",  "단계명": "X-ray이물검출","설명": "이물 검출기 통과 (이물 CCP)",        "유형": "검사", "CCP여부": "Y", "CCP번호": "CCP-2", "lane": "원재료", "merge_from": "", "merge_label": "", "merge_from_2": "", "merge_label_2": "", "merge_from_3": "", "merge_label_3": ""},
            {"순서": "10", "단계명": "외포장",       "설명": "외포장재(박스) 포장",                "유형": "공정", "CCP여부": "N", "CCP번호": "", "lane": "원재료", "merge_from": "포장재", "merge_label": "외포장재(박스)", "merge_from_2": "", "merge_label_2": "", "merge_from_3": "", "merge_label_3": ""},
            {"순서": "11", "단계명": "보 관",        "설명": "완제품 창고 온·습도 관리",           "유형": "공정", "CCP여부": "N", "CCP번호": "", "lane": "원재료", "merge_from": "", "merge_label": "", "merge_from_2": "", "merge_label_2": "", "merge_from_3": "", "merge_label_3": ""},
            {"순서": "12", "단계명": "출 고",        "설명": "주문 확인 및 배송 출고",             "유형": "공정", "CCP여부": "N", "CCP번호": "", "lane": "원재료", "merge_from": "", "merge_label": "", "merge_from_2": "", "merge_label_2": "", "merge_from_3": "", "merge_label_3": ""},
            {"순서": "1",  "단계명": "포장재 입고",  "설명": "내·외포장재 입고 및 검수",           "유형": "공정", "CCP여부": "N", "CCP번호": "", "lane": "포장재", "merge_from": "", "merge_label": "", "merge_from_2": "", "merge_label_2": "", "merge_from_3": "", "merge_label_3": ""},
            {"순서": "2",  "단계명": "포장재 보관",  "설명": "청결구역 보관 (온·습도 관리)",       "유형": "공정", "CCP여부": "N", "CCP번호": "", "lane": "포장재", "merge_from": "", "merge_label": "", "merge_from_2": "", "merge_label_2": "", "merge_from_3": "", "merge_label_3": ""},
            {"순서": "1",  "단계명": "질소 입고",    "설명": "식품용 질소 가스 입고·검수",         "유형": "공정", "CCP여부": "N", "CCP번호": "", "lane": "기타",   "merge_from": "", "merge_label": "", "merge_from_2": "", "merge_label_2": "", "merge_from_3": "", "merge_label_3": ""},
        ]
        df_f = pd.DataFrame(default_steps)
        df_f.to_csv(fpath, index=False, encoding="utf-8-sig")
        return df_f
    return pd.DataFrame(columns=["순서", "단계명", "설명", "유형", "CCP여부", "CCP번호", "lane", "merge_from", "merge_label", "merge_from_2", "merge_label_2", "merge_from_3", "merge_label_3"])

def get_flowchart_by_cat(cat_id: str):
    """mtime 기반 캐시 우회 로더"""
    safe_id = str(cat_id).replace("/", "_").replace("\\", "_").replace(" ", "_")
    fpath = f"haccp_flowchart_{safe_id}.csv"
    mt = os.path.getmtime(fpath) if os.path.exists(fpath) else 0
    return load_flowchart_by_cat(cat_id, mtime=mt)

def save_flowchart_by_cat(cat_id: str, df):
    safe_id = str(cat_id).replace("/", "_").replace("\\", "_").replace(" ", "_")
    fpath = f"haccp_flowchart_{safe_id}.csv"
    df.to_csv(fpath, index=False, encoding="utf-8-sig")
    log_history("공정 흐름도 업데이트", f"카테고리: {cat_id}", f"데이터 {len(df)}건 저장")

# ==========================================
# 데이터 로드 및 저장 함수 (일반 제품 및 관리)
# ==========================================
@st.cache_data
def load_data(mtime=None):
    cols = ["생산일", "유형", "제품명", "생산량", "소비기한", "규격", "규격코드", "질소(%)", "수분(%)", "색도(Agtron)", "추출시간(sec)", "추출시간_상세", "날짜기록", "판정", "비고"]
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
        except Exception: 
            pass
    return pd.DataFrame(columns=cols)

def get_qc_data():
    """파일 수정 시간을 감지하여 최신 QC 데이터를 불러옵니다."""
    mtime = os.path.getmtime(DATA_FILE) if os.path.exists(DATA_FILE) else 0
    return load_data(mtime)

def save_qc_data(df):
    df.to_csv(DATA_FILE, index=False, encoding="utf-8-sig")
    log_history("품질 기록 업데이트", "품질 관리", f"데이터 {len(df)}건 저장")

@st.cache_data
def load_outbound_records(mtime=None):
    """출고 기록 로드 (mtime이 변경되면 캐시 갱신)"""
    cols = ["출고일", "출고시간", "차량번호", "기기명", "출하처", "유형", "제품명", "규격", "규격코드", "제조일자", "소비기한", "수량", "비고"]
    if os.path.exists(OUTBOUND_FILE):
        try:
            df = pd.read_csv(OUTBOUND_FILE, dtype=str)
            for c in cols:
                if c not in df.columns: df[c] = ""
            return df[cols]
        except Exception: 
            pass
    return pd.DataFrame(columns=cols)

def get_outbound_records():
    """파일 수정 시간을 감지하여 최신 데이터를 불러옵니다."""
    mtime = os.path.getmtime(OUTBOUND_FILE) if os.path.exists(OUTBOUND_FILE) else 0
    return load_outbound_records(mtime)

def save_outbound_records(df):
    df.to_csv(OUTBOUND_FILE, index=False, encoding="utf-8-sig")
    log_history("출고 기록 업데이트", "출고 관리", f"데이터 {len(df)}건 저장")

@st.cache_data
def load_destinations(mtime=None):
    """출하처 목록 로드 (mtime 변경 시 캐시 갱신)"""
    new_cols = ["업체명", "담당자", "연락처", "주소", "비고"]
    if os.path.exists(DESTINATION_FILE):
        try:
            df = pd.read_csv(DESTINATION_FILE, dtype=str)
            # 하위 호환성: 기존 '출하처명'이 있으면 '업체명'으로 변경
            if "출하처명" in df.columns:
                df = df.rename(columns={"출하처명": "업체명"})
            # 누락된 컬럼 추가
            for c in new_cols:
                if c not in df.columns: df[c] = ""
            return df[new_cols]
        except Exception: 
            pass
    return pd.DataFrame(columns=new_cols)

def get_destinations():
    """출하처 최신 데이터를 불러옵니다."""
    mtime = os.path.getmtime(DESTINATION_FILE) if os.path.exists(DESTINATION_FILE) else 0
    return load_destinations(mtime)

def save_destinations(df):
    df.to_csv(DESTINATION_FILE, index=False, encoding="utf-8-sig")
    log_history("출하처 마스터 업데이트", "출고 관리", f"데이터 {len(df)}건 저장")

@st.cache_data
def load_pallet_master(mtime=None):
    """파렛트 마스터 로드"""
    if os.path.exists(PALLET_MASTER_FILE):
        try: return pd.read_csv(PALLET_MASTER_FILE, dtype=str)
        except: pass
    return pd.DataFrame(columns=["파렛트명", "색상"])

def get_pallet_master():
    mtime = os.path.getmtime(PALLET_MASTER_FILE) if os.path.exists(PALLET_MASTER_FILE) else 0
    return load_pallet_master(mtime)

def save_pallet_master(df):
    df.to_csv(PALLET_MASTER_FILE, index=False, encoding="utf-8-sig")
    log_history("파렛트 마스터 업데이트", "시설 관리", f"데이터 {len(df)}건 저장")

@st.cache_data
def load_pallet_logs(mtime=None):
    """파렛트 입출고 로그 로드"""
    cols = ["날짜", "유형", "파렛트명", "수량", "비고"]
    if os.path.exists(PALLET_LOG_FILE):
        try:
            df = pd.read_csv(PALLET_LOG_FILE, dtype=str)
            for c in cols:
                if c not in df.columns: df[c] = ""
            return df[cols]
        except: pass
    return pd.DataFrame(columns=cols)

def get_pallet_logs():
    mtime = os.path.getmtime(PALLET_LOG_FILE) if os.path.exists(PALLET_LOG_FILE) else 0
    return load_pallet_logs(mtime)

def save_pallet_logs(df):
    df.to_csv(PALLET_LOG_FILE, index=False, encoding="utf-8-sig")
    log_history("파렛트 입출고 로그 업데이트", "시설 관리", f"데이터 {len(df)}건 저장")

@st.cache_data
def load_inventory_adj(mtime=None):
    cols = ["조정일시", "유형", "제품명", "규격", "생산일", "소비기한", "기존재고", "변경재고", "방향", "차이", "사유"]
    if os.path.exists(INVENTORY_ADJ_FILE):
        try: 
            df = pd.read_csv(INVENTORY_ADJ_FILE, dtype=str)
            for c in cols:
                if c not in df.columns: df[c] = ""
            return df[cols]
        except Exception: pass
    return pd.DataFrame(columns=cols)

def get_inventory_adj():
    mtime = os.path.getmtime(INVENTORY_ADJ_FILE) if os.path.exists(INVENTORY_ADJ_FILE) else 0
    return load_inventory_adj(mtime)

def save_inventory_adj(df):
    df.to_csv(INVENTORY_ADJ_FILE, index=False, encoding="utf-8-sig")
    log_history("재고 임의 조정 업데이트", "재고 관리", f"데이터 {len(df)}건 저장")

@st.cache_data
def load_specs(mtime=None):
    if os.path.exists(SPEC_FILE): 
        try:
            df = pd.read_csv(SPEC_FILE, dtype=str)
            if "제품코드" not in df.columns: df.insert(0, "제품코드", [f"P-{str(i+1).zfill(3)}" for i in range(len(df))])
            if "규격" not in df.columns:
                if "단위" in df.columns:
                    df = df.rename(columns={"단위": "규격"})
                else:
                    df.insert(3, "규격", "EA")
            if "규격코드" not in df.columns:
                df.insert(4, "규격코드", "")
            return df
        except Exception: 
            pass
    return pd.DataFrame(columns=["제품코드", "제품명", "유형", "규격", "규격코드", "최소_질소", "최대_질소", "최소_수분", "최대_수분", "최소_색도", "최대_색도", "최소_추출", "최대_추출", "날짜유형", "날짜기록"])

def get_specs():
    """파일 수정 시간을 감지하여 최신 제품 규격 데이터를 불러옵니다."""
    mtime = os.path.getmtime(SPEC_FILE) if os.path.exists(SPEC_FILE) else 0
    return load_specs(mtime)

def save_specs(df):
    df.to_csv(SPEC_FILE, index=False, encoding="utf-8-sig")
    log_history("제품 규격 업데이트", "제품 관리", f"데이터 {len(df)}건 저장")

@st.cache_data
def load_cleaning_specs(mtime=None):
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
    df_clean = pd.DataFrame(columns=['ID', '대분류', '구역', '설비명', '부위', '세척소독방법', '주기', '사용도구', '책임자', '사진파일'])
    if not os.path.exists(CLEAN_FILE):
        df_clean.to_csv(CLEAN_FILE, index=False, encoding='utf-8-sig')
    return df_clean

def get_cleaning_specs():
    mtime = os.path.getmtime(CLEAN_FILE) if os.path.exists(CLEAN_FILE) else 0
    return load_cleaning_specs(mtime)

def save_cleaning_specs(df):
    df.to_csv(CLEAN_FILE, index=False, encoding="utf-8-sig")
    log_history("세척소독 기준 업데이트", "위생 관리", f"데이터 {len(df)}건 저장")

@st.cache_data
def load_filter_plan(mtime=None):
    if os.path.exists(FILTER_PLAN_FILE):
        try:
            df = pd.read_csv(FILTER_PLAN_FILE, dtype=str).fillna("")
            if '설비명_위치' in df.columns:
                df.rename(columns={'설비명_위치': '설치장소', '필터종류': '필터명', '최근점검일': '점검일자', '차기점검일': '차기점검일자'}, inplace=True)
                if '내용' not in df.columns: df['내용'] = '교체'
            if '설치장소' in df.columns: return df
        except Exception: pass
    df_f = pd.DataFrame(columns=["설치장소", "필터명", "내용", "주기_개월", "점검일자", "차기점검일자", "상태", "비고"])
    if not os.path.exists(FILTER_PLAN_FILE):
        df_f.to_csv(FILTER_PLAN_FILE, index=False, encoding='utf-8-sig')
    return df_f

def get_filter_plan():
    mtime = os.path.getmtime(FILTER_PLAN_FILE) if os.path.exists(FILTER_PLAN_FILE) else 0
    return load_filter_plan(mtime)

def save_filter_plan(df):
    df.to_csv(FILTER_PLAN_FILE, index=False, encoding="utf-8-sig")
    log_history("필터 관리 계획 업데이트", "시설 관리", f"데이터 {len(df)}건 저장")

@st.cache_data
def load_verify(mtime=None):
    if os.path.exists(VERIFY_FILE): 
        try: 
            df = pd.read_csv(VERIFY_FILE)
            if '담당자' not in df.columns: df['담당자'] = ""
            if '계획일자' in df.columns: return df
        except Exception: pass
    df_v = pd.DataFrame(columns=["계획일자", "검증종류", "검증항목", "세부내용", "검증방법", "상태", "담당자"])
    if not os.path.exists(VERIFY_FILE):
        df_v.to_csv(VERIFY_FILE, index=False, encoding='utf-8-sig')
    return df_v

def get_verify():
    mtime = os.path.getmtime(VERIFY_FILE) if os.path.exists(VERIFY_FILE) else 0
    return load_verify(mtime)

def save_verify(df):
    df.to_csv(VERIFY_FILE, index=False, encoding="utf-8-sig")
    log_history("검증 계획 업데이트", "일정/기록 관리", f"데이터 {len(df)}건 저장")

@st.cache_data
def load_other_sched(mtime=None):
    if os.path.exists(OTHER_SCHED_FILE): 
        try:
            df = pd.read_csv(OTHER_SCHED_FILE)
            if '담당자' not in df.columns: df['담당자'] = ""
            if '일자' in df.columns: return df
        except Exception: pass
    df_o = pd.DataFrame(columns=["일자", "일정명", "세부내용", "상태", "담당자"])
    if not os.path.exists(OTHER_SCHED_FILE):
        df_o.to_csv(OTHER_SCHED_FILE, index=False, encoding='utf-8-sig')
    return df_o

def get_other_sched():
    mtime = os.path.getmtime(OTHER_SCHED_FILE) if os.path.exists(OTHER_SCHED_FILE) else 0
    return load_other_sched(mtime)

def save_other_sched(df):
    df.to_csv(OTHER_SCHED_FILE, index=False, encoding="utf-8-sig")
    log_history("기타 일정 업데이트", "일정/기록 관리", f"데이터 {len(df)}건 저장")

@st.cache_data
def load_health_cert(mtime=None):
    if os.path.exists(HEALTH_CERT_FILE):
        try:
            df = pd.read_csv(HEALTH_CERT_FILE)
            if '검진일자' in df.columns: return df
        except Exception: pass
    df_hc = pd.DataFrame(columns=["직급", "이름", "연락처", "검진일자"])
    if not os.path.exists(HEALTH_CERT_FILE):
        df_hc.to_csv(HEALTH_CERT_FILE, index=False, encoding='utf-8-sig')
    return df_hc

def get_health_cert():
    mtime = os.path.getmtime(HEALTH_CERT_FILE) if os.path.exists(HEALTH_CERT_FILE) else 0
    return load_health_cert(mtime)

def save_health_cert(df):
    df.to_csv(HEALTH_CERT_FILE, index=False, encoding="utf-8-sig")
    log_history("보건증 정보 업데이트", "직원 관리", f"데이터 {len(df)}건 저장")

@st.cache_data
def load_employees(mtime=None):
    if os.path.exists(EMPLOYEE_FILE):
        try:
            df = pd.read_csv(EMPLOYEE_FILE, dtype=str).fillna("")
            if 'HACCP 직책' not in df.columns: df['HACCP 직책'] = "해당없음"
            if '모니터링 CCP' not in df.columns: df['모니터링 CCP'] = ""
            if '기타' not in df.columns: df['기타'] = ""
            if '사번' in df.columns: return df
        except Exception: pass
    df_emp = pd.DataFrame(columns=["사번", "직급", "이름", "연락처", "입사일", "재직상태", "HACCP 직책", "모니터링 CCP", "기타"])
    if not os.path.exists(EMPLOYEE_FILE):
        df_emp.to_csv(EMPLOYEE_FILE, index=False, encoding='utf-8-sig')
    return df_emp

def get_employees():
    mtime = os.path.getmtime(EMPLOYEE_FILE) if os.path.exists(EMPLOYEE_FILE) else 0
    return load_employees(mtime)

def save_employees(df):
    df.to_csv(EMPLOYEE_FILE, index=False, encoding="utf-8-sig")
    log_history("직원 정보 업데이트", "직원 관리", f"데이터 {len(df)}건 저장")

@st.cache_data
def load_facilities(mtime=None):
    if os.path.exists(FACILITY_FILE):
        try: return pd.read_csv(FACILITY_FILE, dtype=str)
        except Exception: pass
    df = pd.DataFrame(columns=["설비번호", "설비명", "사용용도", "전압", "구입년월", "제조회사명", "설치장소", "관리부서", "관리자_정", "관리자_부", "특이사항"])
    if not os.path.exists(FACILITY_FILE):
        df.to_csv(FACILITY_FILE, index=False, encoding='utf-8-sig')
    return df

def get_facilities():
    mtime = os.path.getmtime(FACILITY_FILE) if os.path.exists(FACILITY_FILE) else 0
    return load_facilities(mtime)

def save_facilities(df):
    df.to_csv(FACILITY_FILE, index=False, encoding="utf-8-sig")
    log_history("설비 마스터 업데이트", "시설 관리", f"데이터 {len(df)}건 저장")

@st.cache_data
def load_repairs(mtime=None):
    if os.path.exists(REPAIR_FILE):
        try: return pd.read_csv(REPAIR_FILE, dtype=str)
        except Exception: pass
    df = pd.DataFrame(columns=["설비번호", "수리일자", "수리사항", "수리처", "비고"])
    if not os.path.exists(REPAIR_FILE):
        df.to_csv(REPAIR_FILE, index=False, encoding='utf-8-sig')
    return df

def get_repairs():
    mtime = os.path.getmtime(REPAIR_FILE) if os.path.exists(REPAIR_FILE) else 0
    return load_repairs(mtime)

def save_repairs(df):
    df.to_csv(REPAIR_FILE, index=False, encoding="utf-8-sig")
    log_history("수리 이력 업데이트", "시설 관리", f"데이터 {len(df)}건 저장")

@st.cache_data
def load_annual_leave(mtime=None):
    if os.path.exists(ANNUAL_LEAVE_FILE):
        try:
            df = pd.read_csv(ANNUAL_LEAVE_FILE, dtype=str).fillna("")
            for c in ["사번","이름","날짜","유형","비고"]:
                if c not in df.columns: df[c] = ""
            return df[["사번","이름","날짜","유형","비고"]]
        except Exception: pass
    df = pd.DataFrame(columns=["사번","이름","날짜","유형","비고"])
    if not os.path.exists(ANNUAL_LEAVE_FILE):
        df.to_csv(ANNUAL_LEAVE_FILE, index=False, encoding="utf-8-sig")
    return df

def get_annual_leave():
    """파일 수정 시간을 감지하여 최신 연차 기록 데이터를 불러옵니다."""
    mtime = os.path.getmtime(ANNUAL_LEAVE_FILE) if os.path.exists(ANNUAL_LEAVE_FILE) else 0
    return load_annual_leave(mtime)

def save_annual_leave(df):
    df.to_csv(ANNUAL_LEAVE_FILE, index=False, encoding="utf-8-sig")
    log_history("연차 기록 업데이트", "파트타이머 연차 관리", f"데이터 {len(df)}건 저장")

@st.cache_data
def load_calib_list(mtime=None):
    if os.path.exists(CALIB_LIST_FILE):
        try:
            df = pd.read_csv(CALIB_LIST_FILE, dtype=str)
            if "차기_검교정일자" not in df.columns: df["차기_검교정일자"] = ""
            return df
        except Exception: pass
    return pd.DataFrame(columns=["관리번호", "검사_설비명", "측정범위", "주기", "구분", "검교정일자", "차기_검교정일자", "비고"])

def get_calib_list():
    mtime = os.path.getmtime(CALIB_LIST_FILE) if os.path.exists(CALIB_LIST_FILE) else 0
    return load_calib_list(mtime)

def save_calib_list(df):
    df.to_csv(CALIB_LIST_FILE, index=False, encoding="utf-8-sig")
    log_history("검교정 목록 업데이트", "시설 관리", f"데이터 {len(df)}건 저장")

@st.cache_data
def load_calib_reports(mtime=None):
    if os.path.exists(CALIB_REPORT_FILE):
        try: return pd.read_csv(CALIB_REPORT_FILE, dtype=str)
        except Exception: pass
    df = pd.DataFrame(columns=["설비명", "교정일자", "작성자", "검교정방법", "판정기준", "표준값", "측정값", "보정율/오차", "개선조치", "판정결과"])
    if not os.path.exists(CALIB_REPORT_FILE):
        df.to_csv(CALIB_REPORT_FILE, index=False, encoding='utf-8-sig')
    return df

def get_calib_reports():
    mtime = os.path.getmtime(CALIB_REPORT_FILE) if os.path.exists(CALIB_REPORT_FILE) else 0
    return load_calib_reports(mtime)

def save_calib_reports(df):
    df.to_csv(CALIB_REPORT_FILE, index=False, encoding="utf-8-sig")
    log_history("검교정 성적서 업데이트", "시설 관리", f"데이터 {len(df)}건 저장")

@st.cache_data
def load_notices(mtime=None):
    if os.path.exists(NOTICE_BOARD_FILE):
        try: return pd.read_csv(NOTICE_BOARD_FILE)
        except Exception: pass
    df_n = pd.DataFrame(columns=["작성일", "작성자", "제목", "내용", "중요공지"])
    if not os.path.exists(NOTICE_BOARD_FILE):
        df_n.to_csv(NOTICE_BOARD_FILE, index=False, encoding='utf-8-sig')
    return df_n

def get_notices():
    mtime = os.path.getmtime(NOTICE_BOARD_FILE) if os.path.exists(NOTICE_BOARD_FILE) else 0
    return load_notices(mtime)

def save_notices(df):
    df.to_csv(NOTICE_BOARD_FILE, index=False, encoding="utf-8-sig")
    log_history("게시판 업데이트", "사내 게시판", f"데이터 {len(df)}건 저장")

@st.cache_data
def load_polls(mtime=None):
    if os.path.exists(POLL_BOARD_FILE):
        try: return pd.read_csv(POLL_BOARD_FILE)
        except Exception: pass
    df_p = pd.DataFrame(columns=["ID", "작성일", "제목", "선택지", "투표현황", "참여자"])
    if not os.path.exists(POLL_BOARD_FILE):
        df_p.to_csv(POLL_BOARD_FILE, index=False, encoding='utf-8-sig')
    return df_p

def get_polls():
    mtime = os.path.getmtime(POLL_BOARD_FILE) if os.path.exists(POLL_BOARD_FILE) else 0
    return load_polls(mtime)

def save_polls(df):
    df.to_csv(POLL_BOARD_FILE, index=False, encoding="utf-8-sig")
    log_history("투표 게시판 업데이트", "사내 게시판", f"데이터 {len(df)}건 저장")

def toggle_task_status(file_path, idx):
    try:
        temp_df = pd.read_csv(file_path)
        current_status = temp_df.loc[idx, '상태']
        temp_df.loc[idx, '상태'] = '예정' if current_status == '완료' else '완료'
        temp_df.to_csv(file_path, index=False, encoding='utf-8-sig')
    except Exception: pass

# ==========================================
# 추가된 로드 함수들 (원부자재 및 위해요소)
# ==========================================
@st.cache_data
def load_rm(mtime=None):
    if os.path.exists(RM_FILE):
        try:
            df = pd.read_csv(RM_FILE, dtype=str)
            if "포장단위" in df.columns and "규격" not in df.columns:
                df = df.rename(columns={"포장단위": "규격"})
            for c in RM_COLS:
                if c not in df.columns: df[c] = ""
            return df[RM_COLS]
        except Exception: pass
    return pd.DataFrame(columns=RM_COLS)

def get_rm():
    mtime = os.path.getmtime(RM_FILE) if os.path.exists(RM_FILE) else 0
    return load_rm(mtime)

def save_rm(df):
    df.to_csv(RM_FILE, index=False, encoding="utf-8-sig")
    log_history("원부자재 목록 업데이트", "원부자재 관리", f"데이터 {len(df)}건 저장")

@st.cache_data
def load_rm_csv(fpath, cols, mtime=None):
    if os.path.exists(fpath):
        try: return pd.read_csv(fpath, dtype=str)
        except Exception: pass
    return pd.DataFrame(columns=cols)

def get_rm_csv(fpath, cols):
    mt = os.path.getmtime(fpath) if os.path.exists(fpath) else 0
    return load_rm_csv(fpath, cols, mtime=mt)

@st.cache_data
def load_severity(mtime=None):
    if os.path.exists(SEVERITY_FILE):
        try:
            df = pd.read_csv(SEVERITY_FILE, encoding='utf-8-sig')
            for c in ["유형","위해요소","심각성"]:
                if c not in df.columns: df[c] = ""
            return df
        except Exception: 
            pass
    d = pd.DataFrame(columns=["유형","위해요소","심각성"])
    d.to_csv(SEVERITY_FILE, index=False, encoding='utf-8-sig')
    return d

def get_severity():
    mtime = os.path.getmtime(SEVERITY_FILE) if os.path.exists(SEVERITY_FILE) else 0
    return load_severity(mtime)

def save_severity(df):
    df.to_csv(SEVERITY_FILE, index=False, encoding="utf-8-sig")
    log_history("위해요소 심각성 설정 업데이트", "HACCP 관리", f"데이터 {len(df)}건 저장")

@st.cache_data
def load_hazard(mtime=None):
    if os.path.exists(HAZARD_FILE):
        try:
            df = pd.read_csv(HAZARD_FILE, encoding='utf-8-sig')
            for c in ["카테고리","No","공정명","유형","위해요소","발생원인","심각성","발생가능성","종합평가","최종위해요소","예방조치및관리방법"]:
                if c not in df.columns: df[c] = ""
            return df
        except Exception: pass
    d = pd.DataFrame(columns=["카테고리","No","공정명","유형","위해요소","발생원인","심각성","발생가능성","종합평가","최종위해요소","예방조치및관리방법"])
    if not os.path.exists(HAZARD_FILE):
        d.to_csv(HAZARD_FILE, index=False, encoding='utf-8-sig')
    return d

def get_hazard():
    mtime = os.path.getmtime(HAZARD_FILE) if os.path.exists(HAZARD_FILE) else 0
    return load_hazard(mtime)

def save_hazard(df):
    df.to_csv(HAZARD_FILE, index=False, encoding="utf-8-sig")
    log_history("위해요소 분석 업데이트", "HACCP 관리", f"데이터 {len(df)}건 저장")

@st.cache_data
def load_sev2(mtime=None):
    return load_severity(mtime)

@st.cache_data
def load_rm_hazard(mtime=None):
    cols = ["원자재명","원자재코드","유형코드","No","유형","위해요소","발생원인",
            "심각성","발생가능성","종합평가","최종위해요소","예방조치및관리방법"]
    if os.path.exists(RM_HAZARD_FILE):
        try:
            df = pd.read_csv(RM_HAZARD_FILE, encoding='utf-8-sig')
            for c in cols:
                if c not in df.columns: df[c] = ""
            return df
        except Exception: pass
    d = pd.DataFrame(columns=cols)
    if not os.path.exists(RM_HAZARD_FILE):
        d.to_csv(RM_HAZARD_FILE, index=False, encoding='utf-8-sig')
    return d

def get_rm_hazard():
    mtime = os.path.getmtime(RM_HAZARD_FILE) if os.path.exists(RM_HAZARD_FILE) else 0
    return load_rm_hazard(mtime)

def save_rm_hazard(df):
    df.to_csv(RM_HAZARD_FILE, index=False, encoding="utf-8-sig")
    log_history("원부자재 위해요소 분석 업데이트", "원부자재 관리", f"데이터 {len(df)}건 저장")

@st.cache_data
def load_rm_list(mtime=None):
    if os.path.exists(RM_FILE):
        try:
            df = pd.read_csv(RM_FILE, dtype=str)
            for c in RM_COLS:
                if c not in df.columns: df[c] = ""
            return df[RM_COLS]
        except Exception: 
            pass
    return pd.DataFrame(columns=RM_COLS)

def get_rm_list():
    """파일 수정 시간을 감지하여 최신 원부자재 데이터를 불러옵니다."""
    mtime = os.path.getmtime(RM_FILE) if os.path.exists(RM_FILE) else 0
    return load_rm_list(mtime)

@st.cache_data
def load_sev_rm(mtime=None):
    return load_severity(mtime)

def get_sev_rm():
    return get_severity()
def rm_spec_path(code, kind):
    os.makedirs(RM_SPEC_DIR, exist_ok=True)
    safe = str(code).replace("/","_").replace("\\","_")
    return os.path.join(RM_SPEC_DIR, f"rm_{kind}_{safe}.csv")

def save_rm_spec(code, kind, df):
    fpath = rm_spec_path(code, kind)
    df.to_csv(fpath, index=False, encoding="utf-8-sig")
    log_history(f"원부자재 규격 업데이트 ({kind})", "원부자재 관리", f"코드: {code}, 데이터 {len(df)}건")

def save_history_log(df):
    df.to_csv(HISTORY_LOG_FILE, index=False, encoding="utf-8-sig")
    # 히스토리 로그 자체를 저장할 때는 별도 로그를 남기지 않거나 필요시 추가

def prod_spec_path(code, kind):
    safe = str(code).replace("/","_").replace("\\","_")
    return f"spec_{kind}_{safe}.csv"

def save_prod_spec(name, code, kind, df):
    fpath = prod_spec_path(code, kind)
    df.to_csv(fpath, index=False, encoding="utf-8-sig")
    log_history(f"제품 규격 업데이트 ({kind})", "제품 관리", f"제품: {name} ({code})")
