import os
import streamlit as st
import requests

API_BASE_URL = os.getenv("API_URL", "http://localhost:8000")

# ---- CONFIG ----
st.set_page_config(
    page_title="NoBluff AI",
    page_icon="frontend/assets/favicon.png",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ---- OG / SEO META TAGS ----
st.markdown("""
<head>
<meta property="og:title" content="NoBluff AI – Technical Interview Validator">
<meta property="og:description" content="Detect bluffing in projects and prepare for technical interviews.">
<meta property="og:image" content="https://nobluffai.com/preview.png">
<meta property="og:url" content="https://nobluffai.com">
<meta name="twitter:card" content="summary_large_image">
</head>
""", unsafe_allow_html=True)

# ---- STYLING ----
st.markdown("""
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
.stDeployButton {display:none;}

html, body, [class*="css"] {
    background: radial-gradient(circle at top, #0f172a, #020617);
    color: white;
    font-family: 'Inter', sans-serif;
    scroll-behavior: smooth;
}

.block-container {
    max-width: 800px;
    margin: auto;
    padding-top: 2rem;
}

.glass-card {
    background: rgba(255,255,255,0.05);
    backdrop-filter: blur(14px);
    -webkit-backdrop-filter: blur(14px);
    border-radius: 18px;
    padding: 30px;
    border: 1px solid rgba(255,255,255,0.08);
    box-shadow: 0 10px 40px rgba(0,0,0,0.4);
    transition: 0.3s;
    margin-bottom: 24px;
}
.glass-card:hover { transform: translateY(-4px); }

.stButton > button {
    background: linear-gradient(135deg, #6366f1, #8b5cf6);
    color: white;
    height: 52px;
    border-radius: 12px;
    font-weight: 600;
    border: none;
    transition: all 0.3s ease;
}
.stButton > button:hover {
    transform: scale(1.04);
    box-shadow: 0 0 25px rgba(139,92,246,0.6);
}

div[data-testid="stFileUploadDropzone"] {
    background: rgba(139,92,246,0.05);
    border: 2px dashed rgba(255,255,255,0.15);
    border-radius: 16px;
}

.project-card {
    background: rgba(255,255,255,0.05);
    backdrop-filter: blur(14px);
    border-radius: 18px; padding: 25px;
    margin-bottom: 30px;
    border: 1px solid rgba(255,255,255,0.08);
}
.question-item {
    background-color: #0f172a; padding: 20px; border-radius: 12px;
    border-left: 4px solid #f59e0b; margin-bottom: 16px;
    border-top: 1px solid #334155; border-right: 1px solid #334155; border-bottom: 1px solid #334155;
}
.risk-box {
    background:#450a0a; padding:12px; border-radius:8px;
    border: 1px solid #dc2626; margin-top:8px;
}
.expected-box {
    background:#064e3b; padding:12px; border-radius:8px;
    border: 1px solid #059669; margin-top:8px;
}

@keyframes fadeIn {
    from { opacity: 0; transform: translateY(20px); }
    to   { opacity: 1; transform: translateY(0); }
}
.fade-in { animation: fadeIn 0.8s ease forwards; }

.progress-bar {
    height: 8px;
    border-radius: 10px;
    background: linear-gradient(90deg, #6366f1, #8b5cf6);
    animation: loading 2s infinite;
}
@keyframes loading {
    0%   { width: 0%; }
    50%  { width: 70%; }
    100% { width: 100%; }
}
</style>
""", unsafe_allow_html=True)

# ---- HERO ----
st.markdown("""
<div class="fade-in" style="text-align:center; margin-bottom:30px;">
    <h1>🧠 NoBluff AI</h1>
    <h3 style="opacity:0.8;">Stop Bluffing. Start Proving.</h3>
    <p style="opacity:0.6;">Analyze your projects like a real interviewer would.</p>
</div>
""", unsafe_allow_html=True)
st.divider()

# ---- HISTORY SIDEBAR ----
if "user_resumes" not in st.session_state:
    st.session_state.user_resumes = []
if "practice_mode" not in st.session_state:
    st.session_state.practice_mode = False
if "practice_question" not in st.session_state:
    st.session_state.practice_question = ""

with st.sidebar:
    st.markdown("### 📜 Past Resumes")
    if st.session_state.user_resumes:
        st.caption("This session:")
        for name in st.session_state.user_resumes:
            st.markdown(f"• 📄 {name}")
    else:
        st.caption("No resumes yet this session.")

    st.markdown("---")
    st.markdown("## ⚖️ Legal")
    if st.button("Privacy Policy", use_container_width=True):
        st.session_state["show_privacy"] = not st.session_state.get("show_privacy", False)


st.info("⚡ First load may take a few seconds (server waking up)")
st.markdown('<div class="glass-card fade-in">', unsafe_allow_html=True)
st.markdown("### 📄 Upload Your Resume")
uploaded_file = st.file_uploader("Drag & drop or click to upload", type=["pdf"])

# ---- PRIVACY POLICY ----
if st.session_state.get("show_privacy"):
    import os
    policy_path = os.path.join(os.path.dirname(__file__), "privacy_policy.md")
    st.markdown(open(policy_path).read())
    st.stop()

col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    analyze = st.button("🚀 Analyze Resume", use_container_width=True, disabled=not uploaded_file)
st.markdown('</div>', unsafe_allow_html=True)

if not uploaded_file:
    st.markdown("""
<div style="text-align:center; opacity:0.6; margin-top:30px;">
    <p>Upload your resume to get:</p>
    <p>🔍 Bluff detection &nbsp;•&nbsp; ❓ Interview questions &nbsp;•&nbsp; 🧠 Confidence score</p>
</div>
""", unsafe_allow_html=True)


# ---- RENDER FUNCTION ----
def render_project(idx, item):
    confidence = item.get("confidence", 0)
    confidence_score = confidence["score"] if isinstance(confidence, dict) else confidence
    confidence_reason = confidence.get("reason", "") if isinstance(confidence, dict) else ""
    project_name = item.get("project_name", f"Project {idx + 1}")
    tech_stack = item.get("tech_stack", [])
    weak_spots = item.get("weak_spots", item.get("suspicious_points", []))  # backwards compat
    questions = item.get("interview_questions", [])
    verdict = item.get("verdict", "")

    tech_html = f"<p style='color:#94a3b8; font-size:0.85rem;'>🛠 {' &nbsp;•&nbsp; '.join(tech_stack)}</p>" if tech_stack else ""
    st.markdown(f"""
    <div class="project-card">
        <span style="color:#f59e0b; font-weight:700; font-size:0.75rem; letter-spacing:1px;">PROJECT {idx + 1}</span>
        <h3 style="margin:8px 0 4px 0; color:#f1f5f9;">📁 {project_name}</h3>
        {tech_html}
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"**🧠 Interview Readiness Score: {confidence_score}%**")
    st.progress(confidence_score / 100)
    # confidence label + reason
    label = confidence.get("label", "") if isinstance(confidence, dict) else ""
    label_color = {"Strong": "#34d399", "Needs polish": "#f59e0b", "At risk": "#f87171"}.get(label, "#94a3b8")
    label_html = f'<span style="color:{label_color}; font-weight:700; font-size:0.85rem;">● {label}</span>' if label else ""
    if confidence_reason or label:
        st.markdown(f"{label_html} {confidence_reason}", unsafe_allow_html=True)
    # score breakdown
    if isinstance(confidence, dict) and confidence.get("base_score") is not None:
        base = confidence.get("base_score", confidence_score)
        penalty = confidence.get("penalty", 0)
        st.caption(f"📊 Score breakdown: Base {base} − Weak spot penalty {penalty} = **{confidence_score}**")

    if confidence_score >= 75:
        badge = "🟢 Likely Genuine"
    elif confidence_score >= 50:
        badge = "🟡 Moderate Risk"
    else:
        badge = "🔴 High Bluff Risk"
    st.markdown(f"### {badge}")

    if verdict:
        if confidence_score < 40:
            st.error(f"⚖️ {verdict}")
        elif confidence_score < 70:
            st.warning(f"⚖️ {verdict}")
        else:
            st.success(f"⚖️ {verdict}")

    if weak_spots:
        st.markdown("**⚠️ Top Weak Spots Interviewer Will Target:**")
        severity_icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}
        for i, w in enumerate(weak_spots):
            if isinstance(w, dict):
                icon = severity_icon.get(w.get("severity", "medium"), "🟡")
                st.markdown(f"{icon} {w['point']}")
                # show fix_strategy only for the top (highest severity) weak spot
                if i == 0 and w.get("fix_strategy"):
                    with st.expander("🛠 How to fix this", expanded=False):
                        for step in w["fix_strategy"]:
                            st.markdown(f"→ {step}")
            else:
                st.markdown(f"🟡 {w}")

    trap_questions = item.get("trap_questions", [])
    if trap_questions:
        with st.expander("🪤 Trap Questions — If They Want to Catch You", expanded=False):
            for i, t in enumerate(trap_questions, 1):
                sev = t.get("severity", "medium")
                sev_color = {"high": "#f87171", "medium": "#f59e0b", "low": "#34d399"}.get(sev, "#f59e0b")
                label = "Most dangerous" if i == 1 else f"#{i}"
                st.markdown(f"""
<div style="background:#1e1b4b; border:1px solid #4f46e5; border-radius:10px; padding:14px; margin-bottom:10px;">
    <div style="display:flex; justify-content:space-between; margin-bottom:6px;">
        <span style="color:#a5b4fc; font-size:0.8rem;">Targets: <em>{t.get('weak_spot','')}</em></span>
        <span style="color:{sev_color}; font-size:0.75rem; font-weight:700; text-transform:uppercase;">⚡ {label} · {sev}</span>
    </div>
    <p style="color:#f1f5f9; font-weight:600; margin:0 0 6px 0;">❓ {t.get('trap_question','')}</p>
    <p style="color:#f87171; font-size:0.85rem; margin:0;">💥 {t.get('why_it_exposes_you','')}</p>
</div>
""", unsafe_allow_html=True)

    improvements = item.get("improvements", [])
    if improvements:
        st.markdown("**🛠️ How to Improve:**")
        for suggestion in improvements:
            st.markdown(f"• {suggestion}")

    st.markdown("---")
    st.markdown("**🎯 Interview Questions:**")

    for i, q in enumerate(questions, 1):
        question_text = q.get("question", "")
        answer = q.get("answer", "")
        difficulty = q.get("difficulty", "")
        why_asked = q.get("why_asked", "")
        expected = q.get("expected_signals", "")
        red_flags = q.get("red_flags", "")
        question_id = q.get("question_id")

        difficulty_color = {"easy": "#34d399", "medium": "#f59e0b", "hard": "#f87171"}.get(difficulty, "#94a3b8")

        st.markdown(f"""
        <div class="question-item">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
                <strong style="color:#f59e0b; font-size:1rem;">{i}. {question_text}</strong>
                {f'<span style="color:{difficulty_color}; font-size:0.75rem; font-weight:700; text-transform:uppercase;">{difficulty}</span>' if difficulty else ''}
            </div>
            {f'<p style="color:#94a3b8; font-size:0.8rem; margin:4px 0 8px 0;">🧠 Tests: {why_asked}</p>' if why_asked else ''}
            {f'''<div class="expected-box">
                <span style="color:#34d399; font-weight:700;">✅ Strong Answer:</span><br>
                <span style="color:#ecfdf5;">{answer}</span>
            </div>''' if answer else ''}
            {f'''<div class="expected-box" style="margin-top:8px;">
                <span style="color:#34d399; font-weight:700;">🎯 Expected Signals:</span><br>
                <span style="color:#ecfdf5;">{expected}</span>
            </div>''' if expected else ''}
            {f'''<div class="risk-box">
                <span style="color:#f87171; font-weight:700;">🚩 Red Flags:</span><br>
                <span style="color:#fef2f2;">{red_flags}</span>
            </div>''' if red_flags else ''}
        </div>
        """, unsafe_allow_html=True)

        if question_id:
            existing = None
            try:
                fb_res = requests.get(f"{API_BASE_URL}/feedback/{question_id}")
                if fb_res.status_code == 200 and fb_res.json():
                    existing = fb_res.json()
            except Exception:
                pass

            if st.session_state.get(f"saved_{question_id}") or existing:
                st.success("✅ Feedback saved")
                if existing:
                    st.caption(f"Rating: {existing.get('rating')}/5 | Useful: {'Yes' if existing.get('useful') else 'No'}" + (f" | {existing.get('notes')}" if existing.get('notes') else ""))
            else:
                with st.expander("📝 Rate this question", expanded=False):
                    col1, col2 = st.columns(2)
                    with col1:
                        useful = st.checkbox("👍 Useful", key=f"useful_{question_id}")
                    with col2:
                        rating = st.slider("Candidate Answer Quality", 1, 5, 3, key=f"rating_{question_id}")
                    notes = st.text_input("Notes (optional)", key=f"notes_{question_id}")
                    if st.button("💾 Save Feedback", key=f"save_{question_id}"):
                        if not (rating or notes or useful):
                            st.warning("Add some feedback before saving.")
                        else:
                            try:
                                fb_res = requests.post(
                                    f"{API_BASE_URL}/feedback",
                                    json={"question_id": question_id, "rating": rating, "notes": notes, "useful": useful}
                                )
                                if fb_res.status_code == 200:
                                    st.session_state[f"saved_{question_id}"] = True
                                    st.rerun()
                                else:
                                    st.error("Failed to save.")
                            except Exception as e:
                                st.error(f"Error: {e}")

    st.divider()


# ---- HISTORY VIEW ----
if "history_resume_id" in st.session_state and not (uploaded_file and analyze):
    rid = st.session_state["history_resume_id"]
    st.markdown(f"## 📜 {st.session_state.get('history_resume_name', 'Past Resume')}")
    try:
        projects = requests.get(f"{API_BASE_URL}/resumes/{rid}/projects", timeout=5).json()
        for idx, proj in enumerate(projects):
            questions = requests.get(f"{API_BASE_URL}/projects/{proj['id']}/questions", timeout=5).json()
            item = {
                "project_name": proj["name"],
                "confidence": proj["confidence"],
                "tech_stack": [],
                "suspicious_points": [],
                "interview_questions": [{"question": q["question_text"], "question_id": q["id"], "expected_signals": "", "red_flags": ""} for q in questions]
            }
            render_project(idx, item)
    except Exception as e:
        st.error(f"Could not load history: {e}")
    st.stop()


# ---- ANALYSIS ----
if uploaded_file and analyze:
    import json as _json
    import time

    st.markdown('<div class="glass-card fade-in">', unsafe_allow_html=True)
    st.markdown("## 🔍 Technical Interview Guide")

    # animated step loader
    progress_ph = st.empty()
    text_ph = st.empty()
    steps = [
        "📄 Parsing resume...",
        "🧠 Extracting projects...",
        "🔍 Detecting bluff signals...",
        "❓ Generating interview questions...",
        "📊 Calculating confidence score...",
    ]
    for step in steps:
        progress_ph.markdown('<div class="glass-card"><div class="progress-bar"></div></div>', unsafe_allow_html=True)
        text_ph.markdown(f"<p style='text-align:center; opacity:0.7;'>{step}</p>", unsafe_allow_html=True)
        time.sleep(1.0)
    progress_ph.empty()
    text_ph.empty()

    status_placeholder = st.empty()
    with st.spinner("Analyzing your resume..."):
        try:
            with requests.post(
                f"{API_BASE_URL}/analyze-stream",
                files={"file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")},
                stream=True,
                timeout=120
            ) as res:
                if res.status_code == 429:
                    st.warning("⚠️ Free limit reached. Please wait a minute 🚀")
                    st.stop()
                if res.status_code != 200:
                    st.error(f"⚠️ Backend Error: {res.status_code}")
                    st.stop()

                idx = 0
                summary = {}
                for line in res.iter_lines():
                    if not line:
                        continue
                    item = _json.loads(line)

                    if "error" in item:
                        st.error(item["error"])
                        break

                    if "summary" in item and "project_name" not in item:
                        summary = item["summary"]
                        continue

                    status_placeholder.info(f"⏳ Analyzing project {idx + 1}...")
                    render_project(idx, item)
                    idx += 1

                status_placeholder.success(f"✅ Done — {idx} project(s) analyzed")
                if uploaded_file.name not in st.session_state.user_resumes:
                    st.session_state.user_resumes.append(uploaded_file.name)

                if summary:
                    ap = summary.get("attack_plan", {})
                    if ap:
                        st.markdown("---")
                        st.markdown("## 🚀 Your Interview Attack Plan")
                        ttf = ap.get("time_to_fix", {})
                        time_html = ""
                        if ttf:
                            time_html = f"""
<div style="margin-top:10px; padding-top:10px; border-top:1px solid rgba(255,255,255,0.08); color:#94a3b8; font-size:0.85rem;">
    ⏱ Estimated effort: &nbsp;
    Weak spot fix: <strong style="color:#f1f5f9;">{ttf.get('weak_spot_fix','')}</strong> &nbsp;·&nbsp;
    Question prep: <strong style="color:#f1f5f9;">{ttf.get('question_prep','')}</strong>
</div>"""
                        st.markdown(f"""
<div class="glass-card fade-in">
    {'<div style="margin-bottom:14px;"><span style="color:#f87171; font-weight:700;">1. Fix this first:</span><br><span style="color:#f1f5f9; padding-left:12px;">⚠️ ' + ap['fix_first'] + '</span></div>' if ap.get('fix_first') else ''}
    {'<div style="margin-bottom:14px;"><span style="color:#f59e0b; font-weight:700;">2. Prepare this question:</span><br><span style="color:#f1f5f9; padding-left:12px;">❓ ' + ap['prepare_question'] + '</span></div>' if ap.get('prepare_question') else ''}
    {'<div style="margin-bottom:14px;"><span style="color:#a5b4fc; font-weight:700;">3. Biggest cross-resume risk:</span><br><span style="color:#f1f5f9; padding-left:12px;">🔥 ' + ap['biggest_risk'] + '</span></div>' if ap.get('biggest_risk') else ''}
    {'<div style="margin-top:10px; padding-top:10px; border-top:1px solid rgba(255,255,255,0.08);"><span style="color:#34d399; font-weight:700;">📈 Estimated readiness after fixing: ' + str(ap['estimated_readiness_after_fix']) + '%</span></div>' if ap.get('estimated_readiness_after_fix') else ''}
    {time_html}
</div>
""", unsafe_allow_html=True)
                        # Practice Mode
                        if ap.get("prepare_question"):
                            if st.button("🎯 Start Mock Interview", use_container_width=False):
                                st.session_state["practice_question"] = ap["prepare_question"]
                                st.session_state["practice_mode"] = True

                    # Practice Mode UI
                    if st.session_state.get("practice_mode") and st.session_state.get("practice_question"):
                        st.markdown("---")
                        st.markdown("## 🎯 Mock Interview")
                        st.markdown(f"**Q: {st.session_state['practice_question']}**")
                        user_answer = st.text_area("Your answer:", key="mock_answer", height=120)
                        if st.button("Submit Answer"):
                            if user_answer.strip():
                                st.session_state["practice_mode"] = False
                                st.info("✅ Answer recorded. Review the expected signals and red flags above for self-evaluation.")
                            else:
                                st.warning("Write your answer first.")
                    avg = summary.get("average_score", 0)
                    risk_count = summary.get("high_risk_projects", 0)
                    verdict = summary.get("verdict", "")
                    ga = summary.get("global_analysis", {})

                    st.markdown("---")
                    st.markdown("## 📊 Resume Summary")
                    st.markdown(f"**🧠 Overall Interview Readiness Score: {avg}%**")
                    st.progress(avg / 100)
                    st.markdown(f"**📊 Projects at Risk: {risk_count}**")
                    most_q = summary.get("most_questionable", {})
                    if most_q.get("name"):
                        st.markdown(f"**🔥 Most Questionable Project: {most_q['name']} (Score: {most_q['score']}%)**")
                    if verdict:
                        if avg >= 75:
                            st.success(f"⚖️ {verdict}")
                        elif avg >= 50:
                            st.warning(f"⚖️ {verdict}")
                        else:
                            st.error(f"⚖️ {verdict}")

                    if ga:
                        st.markdown("---")
                        st.markdown("## 🧠 Cross-Resume Intelligence")
                        if ga.get("verdict"):
                            overall = ga.get("overall_readiness", avg)
                            if overall >= 75:
                                st.success(f"**{ga['verdict']}**")
                            elif overall >= 50:
                                st.warning(f"**{ga['verdict']}**")
                            else:
                                st.error(f"**{ga['verdict']}**")

                        col_a, col_b = st.columns(2)
                        with col_a:
                            if ga.get("biggest_risks"):
                                st.markdown("**🚨 Biggest Risks Across Resume:**")
                                for r in ga["biggest_risks"]:
                                    st.markdown(f"• {r}")
                            if ga.get("likely_interview_focus"):
                                st.markdown("**🎯 Interviewer Will Focus On:**")
                                for f in ga["likely_interview_focus"]:
                                    st.markdown(f"• {f}")
                        with col_b:
                            if ga.get("strongest_areas"):
                                st.markdown("**✅ Genuine Strengths:**")
                                for s in ga["strongest_areas"]:
                                    st.markdown(f"• {s}")

        except Exception as e:
            st.error(f"⚠️ Connection Failed: {str(e)}")

    st.markdown('</div>', unsafe_allow_html=True)

# ---- FOOTER ----
st.markdown("<div style='margin-top:80px;'></div>", unsafe_allow_html=True)
st.markdown(
    "<p style='text-align:center; color:#484f58; font-size:0.8rem;'>NoBluff AI™ • Stone Aged Ecosystem • Ranchi, India</p>",
    unsafe_allow_html=True
)
