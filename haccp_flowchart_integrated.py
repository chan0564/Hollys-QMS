"""
HACCP 공정 흐름도 통합 패치
별첨6(흐름도), 별첨7(가공방법), 별첨18(위해요소), 별첨19(CCP결정도) 연동
app.py 의 elif sub_menu == "공정 흐름도": 블록 전체를 아래로 교체하세요.
"""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import os

# ─────────────────────────────────────────────
# 파일 경로 상수 (app.py 상단 상수 블록에 추가)
# ─────────────────────────────────────────────
FLOWCHART_FILE   = "별첨6__제조공정흐름도_250822.xlsx"
PROCESS_FILE     = "별첨7__공정별가공방법.xlsx"
HAZARD_FILE_XLS  = "별첨18__공정별_위해요소목록표.xls"
CCP_FILE_XLS     = "별첨19__공정별_CCP_결정도.xls"
# xls → xlsx 변환본 (앱 첫 실행 시 자동 생성)
HAZARD_FILE      = "별첨18__공정별_위해요소목록표.xlsx"
CCP_FILE         = "별첨19__공정별_CCP_결정도.xlsx"

# ─────────────────────────────────────────────
# 헬퍼: xls 자동 변환
# ─────────────────────────────────────────────
def ensure_xlsx(xls_path, xlsx_path):
    if not os.path.exists(xlsx_path):
        import subprocess
        subprocess.run(
            ["libreoffice", "--headless", "--convert-to", "xlsx",
             xls_path, "--outdir", os.path.dirname(xlsx_path) or "."],
            capture_output=True
        )

# ─────────────────────────────────────────────
# 데이터 로더
# ─────────────────────────────────────────────
PRODUCT_SHEET_MAP = {
    "커피(소포장)":       ("커피(소포장)",         "공정별 가공방법(소포장)", "커피(소포장)",   "커피(소포장)"),
    "커피(대포장)":       ("커피(대포장)",         "공정별 가공방법(대포장)", "커피(대포장)",   "커피(대포장)"),
    "커피(소포장-분쇄)":  ("커피(소포장-분쇄)",    "공정별 가공방법(소포장)", "커피(소포장_분쇄)", "커피(소포장_분쇄)"),
    "스틱커피":           ("스틱커피",             "공정별 가공방법(소포장)", "커피(인스턴트 커피,조제커피)", "커피(스틱)"),
    "커피(캡슐)－향료":   ("커피(캡슐)－향료",     "공정별 가공방법(소포장)", "커피(캡슐)",     "커피(캡슐)"),
    "커피(캡슐)":         ("커피(캡슐)",           "공정별 가공방법(소포장)", "커피(캡슐)",     "커피(캡슐)"),
}

def _safe_str(v):
    if pd.isna(v): return ""
    return str(v).replace("\n", " ").strip()

def load_process_steps(product_key):
    """별첨6에서 공정 순서 파악 → 별첨7에서 작업내용/설비/담당 매핑"""
    sheet6, sheet7, _, _ = PRODUCT_SHEET_MAP[product_key]

    # ── 별첨7 파싱 (공정명, 작업내용, 설비, 담당)
    try:
        raw7 = pd.read_excel(PROCESS_FILE, sheet_name=sheet7, header=None)
    except Exception:
        raw7 = None

    process_detail = {}  # {공정명: {작업내용, 설비, 담당}}
    if raw7 is not None:
        current_no = None
        current_name = None
        for _, row in raw7.iterrows():
            vals = [v for v in row if pd.notna(v) and str(v).strip()]
            if len(vals) >= 3 and vals[1] not in ("공정명", "문서번호"):
                no_v = _safe_str(vals[0])
                name_v = _safe_str(vals[1])
                content_v = _safe_str(vals[2])
                equip_v = _safe_str(vals[3]) if len(vals) > 3 else ""
                staff_v = _safe_str(vals[4]) if len(vals) > 4 else ""
                if no_v and name_v and content_v:
                    process_detail[name_v] = {
                        "번호": no_v,
                        "작업내용": content_v,
                        "설비": equip_v,
                        "담당": staff_v,
                    }

    # ── 별첨6에서 공정 순서 추출
    try:
        raw6 = pd.read_excel(FLOWCHART_FILE, sheet_name=sheet6, header=None)
    except Exception:
        return []

    steps = []
    seen = set()
    for _, row in raw6.iterrows():
        for v in row:
            if pd.notna(v):
                s = str(v).strip().replace("\n", " ")
                # 공정명 패턴: 숫자+공정명이 아니라 순수 공정명 셀
                if (s and len(s) < 20 and s not in seen
                        and s not in ("원재료", "포장재", "부자재", "기타", "제조공정흐름도",
                                      "커피 제조공정도", "문서번호", "제정일자", "개정일자", "개정번호")
                        and not s.startswith("■")
                        and not s.startswith("HLSHS")
                        and not any(c.isdigit() and len(s) <= 4 for c in s[:2] if not s[0].isdigit())
                   ):
                    # 공정명스럽게 생긴 것만
                    if any(k in s for k in ["입고", "검수", "보관", "선별", "계량", "배합",
                                             "로스팅", "가열", "방냉", "분쇄", "포장", "내포장",
                                             "외포장", "이물", "검출", "출고", "충진", "멸균",
                                             "냉각", "쇳가루", "수분", "금속"]):
                        seen.add(s)
                        detail = process_detail.get(s, {})
                        steps.append({
                            "순서": len(steps) + 1,
                            "공정명": s,
                            "작업내용": detail.get("작업내용", ""),
                            "설비": detail.get("설비", ""),
                            "담당": detail.get("담당", ""),
                        })
    return steps


def load_hazards(product_key):
    """별첨18 파싱: 공정별 위해요소 목록"""
    ensure_xlsx(HAZARD_FILE_XLS, HAZARD_FILE)
    _, _, sheet18, _ = PRODUCT_SHEET_MAP[product_key]
    try:
        raw = pd.read_excel(HAZARD_FILE, sheet_name=sheet18, header=None)
    except Exception:
        return pd.DataFrame()

    records = []
    cur_no, cur_process = None, None
    cur_type = None

    for _, row in raw.iterrows():
        v0 = row.iloc[0] if pd.notna(row.iloc[0]) else None
        v1 = row.iloc[1] if pd.notna(row.iloc[1]) else None
        v2 = row.iloc[2] if pd.notna(row.iloc[2]) else None
        v3 = row.iloc[3] if pd.notna(row.iloc[3]) else None
        v4 = row.iloc[4] if pd.notna(row.iloc[4]) else None
        v5 = row.iloc[5] if pd.notna(row.iloc[5]) else None
        v6 = row.iloc[6] if pd.notna(row.iloc[6]) else None
        v7 = row.iloc[7] if pd.notna(row.iloc[7]) else None
        v9 = row.iloc[9] if len(row) > 9 and pd.notna(row.iloc[9]) else None

        if v0 is not None and str(v0).strip() not in ("구분", "심각성"):
            try:
                _ = float(str(v0).replace("-", ""))
                cur_no = str(v0).strip()
                cur_process = str(v1).strip().replace("\n", "/") if v1 else cur_process
            except:
                if str(v0).strip() in ("B", "C", "P"):
                    cur_type = str(v0).strip()

        if v2 in ("B", "C", "P"):
            cur_type = str(v2)

        if cur_process and cur_type and v3 and str(v3).strip() not in ("위해요소\n(생물학적:B 화학적:C 물리적:P)", "발생원인(유래)"):
            hazard_name = str(v3).strip()
            if hazard_name and len(hazard_name) < 50:
                records.append({
                    "공정번호": cur_no or "",
                    "공정명": cur_process,
                    "유형": cur_type,
                    "위해요소": hazard_name,
                    "발생원인": _safe_str(v4) if v4 else "",
                    "심각성": v5 if v5 else "",
                    "발생가능성": v6 if v6 else "",
                    "종합평가": v7 if v7 else "",
                    "예방조치": _safe_str(v9) if v9 else "",
                })

    return pd.DataFrame(records)


def load_ccp(product_key):
    """별첨19 파싱: CCP 결정도"""
    ensure_xlsx(CCP_FILE_XLS, CCP_FILE)
    _, _, _, sheet19 = PRODUCT_SHEET_MAP[product_key]
    try:
        raw = pd.read_excel(CCP_FILE, sheet_name=sheet19, header=None)
    except Exception:
        return pd.DataFrame()

    records = []
    cur_no, cur_process = None, None

    for _, row in raw.iterrows():
        v0 = row.iloc[0] if pd.notna(row.iloc[0]) else None
        v1 = row.iloc[1] if pd.notna(row.iloc[1]) else None
        v2 = row.iloc[2] if pd.notna(row.iloc[2]) else None
        v3 = row.iloc[3] if pd.notna(row.iloc[3]) else None
        # 질문1~5 + 결과
        cols = [row.iloc[i] if len(row) > i and pd.notna(row.iloc[i]) else "" for i in range(4, 17)]

        if v0 is not None:
            try:
                _ = float(str(v0).replace("-", ""))
                cur_no = str(v0).strip()
                cur_process = str(v1).strip().replace("\n", "/") if v1 else cur_process
            except:
                pass

        if v2 in ("B", "C", "P") and v3 and cur_process:
            result = ""
            for c in reversed(cols):
                cs = str(c).strip()
                if cs.startswith("CCP") or cs == "CP":
                    result = cs
                    break

            records.append({
                "공정번호": cur_no or "",
                "공정명": cur_process,
                "유형": str(v2),
                "위해요소": _safe_str(v3),
                "결정": result,
                "Q1": _safe_str(cols[0]),
                "Q2": _safe_str(cols[2]),
                "Q3": _safe_str(cols[6]),
                "Q4": _safe_str(cols[8]),
                "Q5": _safe_str(cols[10]),
            })

    return pd.DataFrame(records)


# ─────────────────────────────────────────────
# Plotly 흐름도 생성
# ─────────────────────────────────────────────
def build_flowchart(steps, ccp_df):
    """공정 단계 리스트로 Plotly 흐름도 그리기"""
    if not steps:
        return go.Figure()

    # CCP 공정명 집합
    ccp_processes = set()
    ccp_labels = {}
    if not ccp_df.empty:
        for _, r in ccp_df[ccp_df["결정"].str.startswith("CCP", na=False)].iterrows():
            p = r["공정명"]
            ccp_processes.add(p)
            ccp_labels[p] = r["결정"]

    HOLLYS_RED  = "#D11031"
    NORMAL_COL  = "#4A90D9"
    BOX_W, BOX_H = 0.3, 0.06
    X_CENTER = 0.5
    Y_START, Y_STEP = 0.95, 0.085

    shapes, annotations = [], []

    for i, step in enumerate(steps):
        name = step["공정명"]
        y_center = Y_START - i * Y_STEP
        is_ccp = name in ccp_processes
        color = HOLLYS_RED if is_ccp else NORMAL_COL
        label = f"{'⚠ ' + ccp_labels.get(name,'CCP') + '  ' if is_ccp else ''}{name}"

        # 박스
        shapes.append(dict(
            type="rect",
            x0=X_CENTER - BOX_W, x1=X_CENTER + BOX_W,
            y0=y_center - BOX_H/2, y1=y_center + BOX_H/2,
            line=dict(color=color, width=2.5 if is_ccp else 1.5),
            fillcolor="#FFE5E5" if is_ccp else "#EAF3FB",
        ))

        # 공정명
        annotations.append(dict(
            x=X_CENTER, y=y_center,
            text=f"<b>{label}</b>",
            showarrow=False,
            font=dict(size=12, color=color if is_ccp else "#1a1a2e"),
            xanchor="center", yanchor="middle",
        ))

        # 순서 번호
        annotations.append(dict(
            x=X_CENTER - BOX_W - 0.02, y=y_center,
            text=f"<b>{i+1}</b>",
            showarrow=False,
            font=dict(size=10, color="#888"),
            xanchor="right", yanchor="middle",
        ))

        # 화살표 (마지막 제외)
        if i < len(steps) - 1:
            arrow_y_start = y_center - BOX_H/2
            arrow_y_end   = y_center - Y_STEP + BOX_H/2
            shapes.append(dict(
                type="line",
                x0=X_CENTER, x1=X_CENTER,
                y0=arrow_y_start, y1=arrow_y_end + 0.005,
                line=dict(color="#aaa", width=1.5),
            ))
            # 화살촉
            annotations.append(dict(
                x=X_CENTER, y=arrow_y_end,
                ax=X_CENTER, ay=arrow_y_end + 0.015,
                axref="x", ayref="y",
                xref="x", yref="y",
                showarrow=True, arrowhead=2, arrowsize=1,
                arrowcolor="#aaa", arrowwidth=1.5,
                text="",
            ))

    total_h = max(600, len(steps) * 80 + 80)
    fig = go.Figure()
    fig.update_layout(
        shapes=shapes, annotations=annotations,
        xaxis=dict(visible=False, range=[0, 1]),
        yaxis=dict(visible=False, range=[Y_START - len(steps)*Y_STEP - 0.05, Y_START + 0.05]),
        margin=dict(l=20, r=20, t=30, b=20),
        height=total_h,
        plot_bgcolor="white", paper_bgcolor="white",
    )
    return fig


# ─────────────────────────────────────────────
# ★ 메인 렌더링 블록 (sub_menu == "공정 흐름도")
# ─────────────────────────────────────────────
def render_haccp_flowchart():
    st.subheader("📊 HACCP 공정 흐름도")

    product_list = list(PRODUCT_SHEET_MAP.keys())
    selected = st.selectbox("제품 유형 선택", product_list)

    tab1, tab2, tab3, tab4 = st.tabs(["🔷 공정 흐름도", "📋 공정별 가공방법", "⚠️ 위해요소 분석", "✅ CCP 결정도"])

    with st.spinner("데이터 불러오는 중..."):
        steps   = load_process_steps(selected)
        hazards = load_hazards(selected)
        ccp_df  = load_ccp(selected)

    # ── TAB 1: 흐름도 ──────────────────────────────
    with tab1:
        if not steps:
            st.warning("공정 데이터를 불러올 수 없습니다.")
        else:
            col_legend1, col_legend2, col_legend3 = st.columns(3)
            with col_legend1:
                st.markdown("🔵 **일반 공정**")
            with col_legend2:
                st.markdown("🔴 **CCP (중요관리점)**")
            with col_legend3:
                ccp_count = len(ccp_df[ccp_df["결정"].str.startswith("CCP", na=False)]) if not ccp_df.empty else 0
                st.markdown(f"총 CCP 수: **{ccp_count}**개")

            fig = build_flowchart(steps, ccp_df)
            st.plotly_chart(fig, use_container_width=True)

            # CCP 요약
            if not ccp_df.empty:
                ccp_only = ccp_df[ccp_df["결정"].str.startswith("CCP", na=False)][["공정명", "유형", "위해요소", "결정"]].drop_duplicates()
                if not ccp_only.empty:
                    st.markdown("#### 🚨 CCP 지점 요약")
                    st.dataframe(ccp_only.reset_index(drop=True), use_container_width=True)

    # ── TAB 2: 공정별 가공방법 ────────────────────────
    with tab2:
        if not steps:
            st.info("공정 데이터 없음")
        else:
            st.markdown(f"**총 {len(steps)}개 공정**")
            for s in steps:
                with st.expander(f"**{s['순서']}. {s['공정명']}**"):
                    c1, c2 = st.columns([3, 1])
                    with c1:
                        st.markdown(f"**📝 작업내용:**\n\n{s['작업내용'] or '(내용 없음)'}")
                    with c2:
                        st.markdown(f"**🔧 설비:** {s['설비'] or '-'}")
                        st.markdown(f"**👤 담당:** {s['담당'] or '-'}")

    # ── TAB 3: 위해요소 분석 ──────────────────────────
    with tab3:
        if hazards.empty:
            st.info("위해요소 데이터를 불러올 수 없습니다.")
        else:
            TYPE_LABEL = {"B": "🦠 생물학적", "C": "⚗️ 화학적", "P": "🔩 물리적"}

            # 공정 필터
            process_list = ["전체"] + sorted(hazards["공정명"].dropna().unique().tolist())
            sel_process = st.selectbox("공정 선택", process_list, key="hz_process")

            filtered = hazards if sel_process == "전체" else hazards[hazards["공정명"] == sel_process]

            # 유형 탭
            h_b = filtered[filtered["유형"] == "B"]
            h_c = filtered[filtered["유형"] == "C"]
            h_p = filtered[filtered["유형"] == "P"]

            ht1, ht2, ht3 = st.tabs([f"🦠 생물학적 ({len(h_b)})", f"⚗️ 화학적 ({len(h_c)})", f"🔩 물리적 ({len(h_p)})"])

            for tab_h, df_h in [(ht1, h_b), (ht2, h_c), (ht3, h_p)]:
                with tab_h:
                    if df_h.empty:
                        st.info("해당 유형의 위해요소 없음")
                    else:
                        show_cols = ["공정명", "위해요소", "심각성", "발생가능성", "종합평가", "예방조치"]
                        show_df = df_h[show_cols].copy()

                        # 종합평가 색상 강조
                        def color_score(val):
                            try:
                                v = int(val)
                                if v >= 4: return "background-color: #ffcccc"
                                if v >= 2: return "background-color: #fff3cc"
                                return "background-color: #e8f5e9"
                            except:
                                return ""

                        styled = show_df.style.applymap(color_score, subset=["종합평가"])
                        st.dataframe(styled, use_container_width=True)

    # ── TAB 4: CCP 결정도 ────────────────────────────
    with tab4:
        if ccp_df.empty:
            st.info("CCP 결정도 데이터를 불러올 수 없습니다.")
        else:
            st.markdown("**질문 판단 흐름:** 질문1 → 질문2 → 질문3 → 질문4 → 질문5 → CCP/CP 결정")

            # 결정 필터
            result_filter = st.radio("필터", ["전체", "CCP만", "CP만"], horizontal=True, key="ccp_filter")
            if result_filter == "CCP만":
                view_df = ccp_df[ccp_df["결정"].str.startswith("CCP", na=False)]
            elif result_filter == "CP만":
                view_df = ccp_df[ccp_df["결정"] == "CP"]
            else:
                view_df = ccp_df

            def highlight_result(val):
                if str(val).startswith("CCP"): return "background-color: #ffcccc; font-weight: bold; color: #D11031"
                if str(val) == "CP": return "background-color: #e8f5e9; color: #27AE60"
                return ""

            show_cols = ["공정번호", "공정명", "유형", "위해요소", "Q1", "Q2", "Q3", "Q4", "Q5", "결정"]
            st.dataframe(
                view_df[show_cols].reset_index(drop=True).style.applymap(highlight_result, subset=["결정"]),
                use_container_width=True, height=500,
            )


# ─────────────────────────────────────────────
# app.py 에 붙여넣을 실행 구조
# ─────────────────────────────────────────────
if __name__ == "__main__":
    # 테스트용 단독 실행
    st.set_page_config(page_title="HACCP 공정 흐름도 테스트", layout="wide")
    render_haccp_flowchart()
