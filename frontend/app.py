import streamlit as st
import requests

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
    suspicious_points = item.get("suspicious_points", [])
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

    st.markdown(f"**🧠 Authenticity Score: {confidence_score}%**")
    st.progress(confidence_score / 100)
    if confidence_reason:
        st.caption(f"💬 {confidence_reason}")

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

    if suspicious_points:
        st.markdown("**🚨 Risk Signals:**")
        for point in suspicious_points:
            st.markdown(f"• {point}")

    improvements = item.get("improvements", [])
    if improvements:
        st.markdown("**🛠️ How to Improve:**")
        for suggestion in improvements:
            st.markdown(f"• {suggestion}")

    st.markdown("---")
    st.markdown("**🎯 Verification Questions:**")

    for i, q in enumerate(questions, 1):
        question_text = q.get("question", "")
        expected = q.get("expected_signals", "")
        red_flags = q.get("red_flags", "")
        question_id = q.get("question_id")

        st.markdown(f"""
        <div class="question-item">
            <strong style="color:#f59e0b; font-size:1rem;">{i}. {question_text}</strong>
            <div class="expected-box">
                <span style="color:#34d399; font-weight:700;">🎯 Expected Signals:</span><br>
                <span style="color:#ecfdf5;">{expected}</span>
            </div>
            <div class="risk-box">
                <span style="color:#f87171; font-weight:700;">🚩 Red Flags:</span><br>
                <span style="color:#fef2f2;">{red_flags}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.code(question_text, language="text")

        if question_id:
            existing = None
            try:
                fb_res = requests.get(f"http://localhost:8000/feedback/{question_id}")
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
                                    "http://localhost:8000/feedback",
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
        projects = requests.get(f"http://localhost:8000/resumes/{rid}/projects", timeout=5).json()
        for idx, proj in enumerate(projects):
            questions = requests.get(f"http://localhost:8000/projects/{proj['id']}/questions", timeout=5).json()
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
                "http://localhost:8000/analyze-stream",
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
                    avg = summary.get("average_score", 0)
                    risk_count = summary.get("high_risk_projects", 0)
                    verdict = summary.get("verdict", "")
                    st.markdown("---")
                    st.markdown("## 📊 Resume Summary")
                    st.markdown(f"**🧠 Overall Authenticity Score: {avg}%**")
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

        except Exception as e:
            st.error(f"⚠️ Connection Failed: {str(e)}")

    st.markdown('</div>', unsafe_allow_html=True)

# ---- FOOTER ----
st.markdown("<div style='margin-top:80px;'></div>", unsafe_allow_html=True)
st.markdown(
    "<p style='text-align:center; color:#484f58; font-size:0.8rem;'>NoBluff AI™ • Stone Aged Ecosystem • Ranchi, India</p>",
    unsafe_allow_html=True
)
