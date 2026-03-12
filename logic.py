import pandas as pd
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta
import os

# ==========================================
# 연차 계산 로직
# ==========================================
def calc_annual_leave(hire_date_str, leave_records_df, emp_id, today=None):
    """
    발생 규칙:
      - 입사 후 1년 미만: 매월(입사일 기준) 1개 발생, 단 해당 월에 무급휴가 사용 시 그 달은 1개 미발생
      - 입사 후 1년 도달 시점에 15개 일괄 발생 (그 이후는 매년 15개)
    반환: (발생, 사용, 잔여, 상세dict)
    """
    if today is None:
        today = date.today()

    try:
        hire = pd.to_datetime(hire_date_str).date()
    except Exception:
        return 0, 0, 0, {}

    # 이 직원의 무급휴가/연차 사용 기록
    emp_df = leave_records_df[leave_records_df["사번"] == emp_id].copy()
    emp_df["날짜_dt"] = pd.to_datetime(emp_df["날짜"], errors="coerce")
    emp_df = emp_df.dropna(subset=["날짜_dt"])

    # ── 발생 연차 계산 ──────────────────────────────────────────
    months_worked = relativedelta(today, hire).months + relativedelta(today, hire).years * 12
    years_worked  = relativedelta(today, hire).years

    accrued = 0
    detail  = {}   # {기간설명: 발생수}

    if years_worked >= 1:
        # 1년 미만 구간: 최대 11개월 (무급 제외)
        year1_accrued = 0
        for m in range(1, 12):           # 1개월차 ~ 11개월차
            month_point = hire + relativedelta(months=m)
            if month_point > today: break
            
            window_start = hire + relativedelta(months=m-1)
            window_end   = hire + relativedelta(months=m) - timedelta(days=1)
            has_unpaid = any(
                window_start <= r["날짜_dt"].date() <= window_end
                for _, r in emp_df[emp_df["유형"] == "무급휴가"].iterrows()
            )
            if not has_unpaid:
                year1_accrued += 1
        accrued += year1_accrued
        detail["입사 1년 미만 (월 발생)"] = year1_accrued

        # 1년 단위: 1년째, 2년째, ...
        for yr in range(1, years_worked + 1):
            anniversary = hire + relativedelta(years=yr)
            if anniversary <= today:
                accrued += 15
                detail[f"입사 {yr}년 (연간 15개)"] = 15
    else:
        # 1년 미만
        year1_accrued = 0
        for m in range(1, months_worked + 1):
            month_point = hire + relativedelta(months=m)
            if month_point > today: break
            window_start = hire + relativedelta(months=m-1)
            window_end   = hire + relativedelta(months=m) - timedelta(days=1)
            has_unpaid = any(
                window_start <= r["날짜_dt"].date() <= window_end
                for _, r in emp_df[emp_df["유형"] == "무급휴가"].iterrows()
            )
            if not has_unpaid:
                year1_accrued += 1
        accrued = year1_accrued
        detail[f"입사 {months_worked}개월 (월 발생)"] = year1_accrued

    # ── 사용 연차 (유형=='연차'인 레코드 수) ──────────────────────
    used = len(emp_df[emp_df["유형"] == "연차"])
    remaining = accrued - used

    return accrued, used, remaining, detail

# ==========================================
# 일정 상태 토글 로직
# ==========================================
def toggle_task_status(file_path, idx):
    try:
        temp_df = pd.read_csv(file_path)
        current_status = temp_df.loc[idx, '상태']
        temp_df.loc[idx, '상태'] = '예정' if current_status == '완료' else '완료'
        temp_df.to_csv(file_path, index=False, encoding='utf-8-sig')
        return True
    except Exception: 
        return False

# ==========================================
# 위해요소 판정 및 기타 비즈니스 로직
# ==========================================
def calculate_hazard_level(severity, probability):
    """
    심각성과 발생가능성을 바탕으로 위해평가 점수 계산
    예: Score = Severity * Probability
    """
    try:
        s = int(severity)
        p = int(probability)
        return s * p
    except:
        return 0

def judge_qc_data(value, min_val, max_val):
    """
    QC 데이터 합불 판정
    """
    if str(value) == "N/A" or str(min_val) in ["", "N/A", "nan"]:
        return "PASS"
    try:
        v = float(value)
        mn = float(min_val)
        mx = float(max_val)
        if mn <= v <= mx:
            return "PASS"
        else:
            return "FAIL"
    except:
        return "UNKNOWN"
