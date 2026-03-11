# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 앱 실행

```bash
# 일반 실행 (브라우저 자동 오픈)
python -m streamlit run app.py --server.headless false

# 또는 배치파일 실행 (Windows)
QMS실행.bat
```

패키지 설치:
```bash
pip install -r requirements.txt
# requirements: streamlit, pandas, plotly, openpyxl, pillow, xlsxwriter
```

## 아키텍처 개요

**단일 파일 구조** (`app.py`, 6,461줄). 모듈 분리 없이 전체 앱이 하나의 파일에 구현되어 있음.

### 실행 흐름

```
앱 시작
  → check_login()  # st.secrets["PASSWORD"] 인증
  → 전역 CSS 주입
  → 스플래시 화면 (3초, session_state.welcomed로 1회만 표시)
  → 로고 렌더링 (image_1ab965.png → base64 인라인)
  → 데이터 로드 (load_data, load_specs, load_cleaning_specs)
  → 사이드바 메뉴 선택
  → if/elif 분기로 각 메뉴 렌더링 (라인 686~6461)
```

### 메뉴 → 코드 위치 구조

사이드바 `menu_selection` 값에 따라 `if menu_selection == "..."` 블록으로 분기:

| 메뉴 | 하위 메뉴 (`sub_menu`) |
|------|----------------------|
| 대시보드 (메인) | 없음 |
| 게시판 | 없음 |
| 캘린더 | 📅 달력 보기 / 검증 계획표 / 기타 일정 |
| 제품 관리 | 제품 등록 / 제품 규격 마스터 / 데이터 히스토리 / 제품별 데이터 관리 |
| 원·부자재 관리 | 원·부자재 등록 / 원·부자재 규격서 마스터 |
| 직원 관리 | 조직도 및 인원 관리 / 보건증 현황관리 / 파트타이머 연차 관리 |
| 설비 관리 | 제조위생설비이력관리 / 필터 점검관리 / 세척소독 기준 / 계측기기 검교정 |
| HACCP | HACCP 일지 / HACCP 기준서 / 개정이력 / 공정 흐름도 / 공정별 CCP 결정도 / 심각성 설정 / 공정 위해요소분석 / 원부자재 위해요소분석 |

### 데이터 레이어

모든 데이터는 CSV 파일로 저장/로드. DB 없음. 각 파일에 대응하는 `load_*()` 함수가 있으며, 파일이 없으면 기본 데이터로 자동 생성함.

| 상수명 | 파일 | 용도 |
|--------|------|------|
| `DATA_FILE` | `qc_data.csv` | QC 검사 실적 |
| `SPEC_FILE` | `qc_specs.csv` | 완제품 규격 마스터 |
| `CLEAN_FILE` | `cleaning_specs.csv` | SSOP 세척소독 기준 (11개 대분류) |
| `VERIFY_FILE` | `verify_plan.csv` | 검증 계획 |
| `EMPLOYEE_FILE` | `employees.csv` | 직원 정보 |
| `FACILITY_FILE` | `facilities.csv` | 설비 목록 |
| `REPAIR_FILE` | `repairs.csv` | 설비 수리 이력 |
| `ANNUAL_LEAVE_FILE` | `annual_leave_records.csv` | 파트타이머 연차 기록 |
| `CALIB_LIST_FILE` | `calib_list.csv` | 검교정 설비 목록 |
| `CALIB_REPORT_FILE` | `calib_report.csv` | 검교정 보고서 |
| `NOTICE_BOARD_FILE` | `notice_board.csv` | 공지사항/게시판 |
| `POLL_BOARD_FILE` | `poll_board.csv` | 익명 투표 |
| `HACCP_REVISION_FILE` | `haccp_revision.csv` | HACCP 개정이력 |
| `HAZARD_FILE` | `hazard_analysis.csv` | 공정 위해요소분석 |
| `RM_HAZARD_FILE` | `rm_hazard_analysis.csv` | 원부자재 위해요소분석 |
| `RM_FILE` | `raw_materials.csv` | 원·부자재 등록 |

**카테고리별 독립 파일** (디렉토리):
- `ccp_decisions/ccp_decision_{cat_id}.csv` — 공정별 CCP 결정도 (Q1~Q5 의사결정 나무)
- `rm_specs/rm_basic_{rm_code}.csv` — 원·부자재 규격서
- `haccp_flowchart_{cat_id}.csv` — 카테고리별 공정 흐름도 단계
- `haccp_docs/`, `haccp_standards/` — HACCP 문서/기준서 파일 저장

### 엑셀 출력 함수

`openpyxl` / `xlsxwriter` 둘 다 사용. 함수 이름이 `export_*`:

- `export_full_excel()` — 완제품 규격서 (사진 포함)
- `export_rm_excel()` — 원·부자재 규격서
- `export_health_excel()` — 보건증 현황 관리표
- `export_facility_list()` — 설비 목록표
- `export_cleaning_excel()` — SSOP 세척소독 기준표 (사진 삽입)
- `export_flowchart_excel()` — 공정 흐름도 (다중 레인)
- `export_org_excel()` — HACCP 조직도
- `export_rm_hazard_excel()` — 원부자재 위해요소분석표

### 핵심 비즈니스 로직

- **연차 계산** (`calc_annual_leave()`): 입사 1년 미만 → 월 1일 발생, 1년 이상 → 연 15일, 무급휴가는 잔여 연차에서 차감
- **CCP 결정** (`calc_ccp()`): HACCP 의사결정 나무 Q1~Q5 답변으로 CCP 자동 판정
- **공정 흐름도 시각화**: Plotly Scatter를 직접 구성 (다중 레인, CCP 강조 표시)

## 주요 개발 패턴

### CSV 로드 패턴
모든 load 함수는 파일 없으면 기본 DataFrame 반환, 컬럼 누락 시 자동 추가:
```python
def load_xxx():
    if os.path.exists(FILE):
        try:
            df = pd.read_csv(FILE, dtype=str)
            for col in required_cols:
                if col not in df.columns: df[col] = ""
            return df
        except: pass
    return pd.DataFrame(columns=required_cols)
```

### 로그인
`st.secrets["PASSWORD"]` 값으로 인증. 로컬 개발 시 `.streamlit/secrets.toml`에 `PASSWORD = "..."` 설정 필요.

### 라이트 모드 고정
앱 시작 시 `.streamlit/config.toml`을 `base="light"`로 자동 생성. 테마 변경 불가.

### 이미지 처리
로컬 이미지 파일을 base64로 인코딩해 HTML `<img src="data:...">` 태그로 인라인 삽입. `get_base64_of_local_file()` 함수 사용.

## 파일 구조 (주요 항목)

```
Hollys_QMS/
├── app.py                    # 메인 앱 (전체 코드)
├── requirements.txt
├── QMS실행.bat               # Windows 실행 스크립트
├── .streamlit/
│   ├── config.toml           # 라이트 모드 고정
│   └── secrets.toml          # PASSWORD (git 제외, 로컬 생성)
├── image_1ab965.png          # 헤더 로고
├── ccp_decisions/            # 공정별 CCP 결정도 CSV
├── rm_specs/                 # 원·부자재 규격서 CSV
├── haccp_docs/               # HACCP 문서 (1~8 분류)
├── haccp_standards/          # HACCP 기준서 파일
└── *.csv                     # 모든 데이터 파일 (루트)
```
