"""
Multimodal Construction Intelligence Platform
Skill Wallet Capstone Project 1

Run:
  pip install -r requirements.txt
  streamlit run app.py

Safety note: AI outputs are preliminary decision support, not a substitute for
competent-person inspections, licensed engineering review, or applicable codes.
"""
from __future__ import annotations

import json
import math
import os
import re
from datetime import datetime
from typing import Any

import streamlit as st
from PIL import Image

try:
    from google import genai
    from google.genai import types
except ImportError:
    genai = None
    types = None

APP_NAME = "Multimodal Construction Intelligence Platform"
MODEL_NAME = "gemini-2.5-flash"

st.set_page_config(page_title=APP_NAME, page_icon="🏗️", layout="wide")

# ---------- Styling ----------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap');
html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
h1,h2,h3 { font-family:'Space Grotesk',sans-serif; letter-spacing:-.03em; }
.stApp { background: linear-gradient(145deg,#f5f7fa 0%,#edf2f7 100%); }
.block-container { padding-top: 1.5rem; max-width: 1440px; }
.hero { padding:1.35rem 1.6rem; border-radius:20px; color:#fff;
 background:linear-gradient(120deg,#14283f,#23566a 65%,#2b7a78); margin-bottom:1.2rem; }
.hero p { color:#d9e8ed; margin-bottom:0; }
.panel { background:white; border:1px solid #e4eaf0; padding:1rem 1.2rem; border-radius:16px; }
.metric { background:white; border:1px solid #e4eaf0; border-radius:15px; padding:1rem; }
.pill { display:inline-block; padding:.28rem .7rem; border-radius:999px; font-weight:700; font-size:.82rem; }
.good { background:#d8f5e8;color:#126344; } .warn {background:#fff0c2;color:#825500;}
.bad {background:#ffe0dc;color:#9a2b20;} .neutral {background:#e6edf5;color:#29435c;}
.small-muted { color:#62758a; font-size:.88rem; }
div[data-testid="stMetric"] { background:#fff; border:1px solid #e4eaf0; padding:12px 15px; border-radius:14px; }
.stButton>button { border-radius:11px; font-weight:700; }
section[data-testid="stSidebar"] { background:#12263a; }
section[data-testid="stSidebar"] * { color:#edf4f8; }
</style>
""", unsafe_allow_html=True)

# ---------- Utilities ----------
def safe_json(text: str) -> dict[str, Any]:
    """Parse model JSON defensively, including fenced output."""
    cleaned = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.I | re.M).strip()
    try:
        obj = json.loads(cleaned)
        return obj if isinstance(obj, dict) else {"result": obj}
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", cleaned, flags=re.S)
        if match:
            try:
                obj = json.loads(match.group(0))
                return obj if isinstance(obj, dict) else {"result": obj}
            except json.JSONDecodeError:
                pass
    raise ValueError("The model response was not valid JSON. Please retry.")

def get_client(api_key: str | None):
    if not api_key or not genai:
        return None
    try:
        return genai.Client(api_key=api_key)
    except Exception as exc:
        st.warning(f"Could not initialize Gemini client: {exc}")
        return None

def gemini_json(client, prompt: str, image: Image.Image | None = None) -> dict[str, Any]:
    if client is None:
        raise RuntimeError("Gemini is not configured. Add an API key in the sidebar.")
    contents = [prompt]
    if image is not None:
        contents.append(image)
    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=contents,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0.2,
        ),
    )
    if not getattr(response, "text", None):
        raise ValueError("Gemini returned an empty response.")
    return safe_json(response.text)

def demo_safety() -> dict[str, Any]:
    return {
        "safety_score": 82,
        "overall_status": "Needs Improvement",
        "ppe_detection": {
            "helmet": {"compliant": True, "notes": "Hard hats appear present in visible areas."},
            "high_visibility_vest": {"compliant": True, "notes": "High-visibility clothing appears present."},
            "steel_toe_boots": {"compliant": False, "notes": "Footwear protection cannot be verified visually."},
            "safety_harness": {"compliant": False, "notes": "Harness use cannot be confirmed for elevated work."}
        },
        "site_hazards": [
            {"hazard": "Unprotected edge / fall exposure", "severity": "High",
             "remedy": "Install compliant guardrails or certified fall-arrest systems; restrict access until protected."},
            {"hazard": "Foot protection not verifiable", "severity": "Medium",
             "remedy": "Verify approved safety footwear for all workers before entering the work zone."}
        ],
        "disclaimer": "Demonstration data only; no image analysis was performed."
    }

def demo_crack() -> dict[str, Any]:
    return {
        "defect_type": "Hairline",
        "estimated_width_mm": 0.25,
        "root_causes": ["Drying shrinkage", "Minor thermal movement"],
        "recommended_repairs": ["Map and monitor crack progression", "Seal suitable non-structural cracks with an approved flexible sealant"],
        "urgency": "Routine",
        "engineering_review": "Have a qualified engineer confirm classification and suitability of repair.",
        "disclaimer": "Demonstration data only; no image analysis was performed."
    }

def json_download(data: dict[str, Any], filename: str):
    st.download_button("⬇ Download JSON report", json.dumps(data, indent=2), filename,
                       "application/json", use_container_width=False)

def status_pill(label: str):
    key = str(label).lower()
    cls = "good" if any(x in key for x in ["compliant", "safe", "routine", "low"]) else (
        "bad" if any(x in key for x in ["critical", "high", "unsafe", "fail"]) else "warn")
    st.markdown(f'<span class="pill {cls}">{label}</span>', unsafe_allow_html=True)

def image_from_upload(upload) -> Image.Image | None:
    if upload is None:
        return None
    try:
        img = Image.open(upload)
        img.verify()
        upload.seek(0)
        return Image.open(upload).convert("RGB")
    except Exception:
        st.error("This file is not a valid image. Please upload a JPG or PNG.")
        return None

# ---------- Sidebar ----------
with st.sidebar:
    st.markdown("## 🏗️ Construction IQ")
    st.caption("Multimodal field intelligence")
    api_key = st.text_input("Google Gemini API key", type="password",
                            help="Used only for this session. Avoid sharing keys or committing them.")
    client = get_client(api_key.strip() if api_key else None)
    if client:
        st.success("Gemini connected")
    else:
        st.info("Demo mode active — sample results are clearly labeled.")
    st.divider()
    st.markdown("### Architecture")
    st.markdown("""
    **Streamlit UI** → **Gemini multimodal**

    Image uploads → structured JSON → validation/rendering

    Session state → assistant conversation

    Local calculations → budget & material estimates
    """)
    st.divider()
    st.markdown("### Navigate")
    module = st.radio("Feature modules", [
        "Site Safety & PPE Audit", "Crack Diagnostics",
        "Planning & Real Estate", "Daily Site Assistant"
    ], label_visibility="collapsed")
    st.caption("No external database. Session data is ephemeral.")

st.markdown(f"""
<div class="hero">
  <h1>🏗️ {APP_NAME}</h1>
  <p>Practical AI-assisted safety, defect diagnostics, project planning, and daily site guidance.</p>
</div>
""", unsafe_allow_html=True)
st.warning("Decision-support prototype. Image-based assessments can miss hazards and cannot establish code compliance. Confirm findings with qualified site safety and structural professionals; apply current local regulations and project specifications.")

# ---------- Module 1 ----------
if module == "Site Safety & PPE Audit":
    st.header("🦺 Site Safety & PPE Audit")
    st.write("Upload a site photo to evaluate visible PPE and potential hazards.")
    uploaded = st.file_uploader("Construction site photo", type=["jpg", "jpeg", "png"], key="safety_img")
    img = image_from_upload(uploaded)
    if img:
        left, right = st.columns([1, 1.15], gap="large")
        with left:
            st.image(img, caption="Uploaded site image", use_container_width=True)
        with right:
            if st.button("Run PPE & hazard audit", type="primary", use_container_width=True):
                prompt = """You are a careful construction safety image-review assistant. Analyze only what is visible; use unknown/not_verifiable rather than guessing. Consider applicable OSHA construction PPE principles and Indian project context/IS 456 only as contextual references (IS 456 is a concrete design code, not a PPE checklist). Do not claim legal compliance. Return JSON exactly with:
{"safety_score": integer 0-100, "overall_status": string, "ppe_detection":{"helmet":{"compliant":boolean|null,"notes":string},"high_visibility_vest":{"compliant":boolean|null,"notes":string},"steel_toe_boots":{"compliant":boolean|null,"notes":string},"safety_harness":{"compliant":boolean|null,"notes":string}}, "site_hazards":[{"hazard":string,"severity":"Low|Medium|High|Critical","remedy":string}], "limitations":string}
Include only observable details, and mention obscured/uncertain evidence."""
                with st.spinner("Reviewing image with Gemini…" if client else "Preparing demonstration audit…"):
                    try:
                        result = gemini_json(client, prompt, img) if client else demo_safety()
                        st.session_state["safety_result"] = result
                        st.session_state["safety_demo"] = not bool(client)
                    except Exception as exc:
                        st.error(f"Audit failed: {exc}")
            result = st.session_state.get("safety_result")
            if result:
                if st.session_state.get("safety_demo"):
                    st.caption("🧪 Demonstration result — generated without image analysis.")
                score = result.get("safety_score", "—")
                status = result.get("overall_status", "Not assessed")
                m1, m2 = st.columns(2)
                m1.metric("Safety score", f"{score}/100" if isinstance(score, (int,float)) else score)
                m2.metric("Overall status", status)
                status_pill(status)
                st.subheader("PPE checklist")
                ppe = result.get("ppe_detection", {})
                for label, key in [("Helmet", "helmet"), ("High-visibility vest", "high_visibility_vest"),
                                   ("Steel-toe boots", "steel_toe_boots"), ("Safety harness", "safety_harness")]:
                    item = ppe.get(key, {})
                    compliant = item.get("compliant")
                    icon = "✅" if compliant is True else "❌" if compliant is False else "❔"
                    st.markdown(f"**{icon} {label}** — {item.get('notes', 'Not assessed')}")
                st.subheader("Identified hazards")
                hazards = result.get("site_hazards", [])
                if not hazards:
                    st.success("No hazards identified in the visible image; this is not proof of a hazard-free site.")
                for h in hazards:
                    with st.expander(f"{h.get('severity','Unrated')} · {h.get('hazard','Hazard')}"):
                        st.write(h.get("remedy", "No remedy provided."))
                json_download(result, "site_safety_audit.json")

# ---------- Module 2 ----------
elif module == "Crack Diagnostics":
    st.header("🧱 Crack Diagnostics & Structural Integrity")
    st.write("Upload a concrete or wall surface image for preliminary defect characterization.")
    uploaded = st.file_uploader("Concrete / wall image", type=["jpg", "jpeg", "png"], key="crack_img")
    img = image_from_upload(uploaded)
    if img:
        st.image(img, caption="Uploaded surface image", width=620)
        if st.button("Analyze surface defect", type="primary"):
            prompt = """Act as a cautious visual concrete defect triage assistant. Analyze the supplied surface photo, explicitly state uncertainty and do not infer structural safety from an image. Return valid JSON:
{"defect_type":"Hairline|Settlement|Structural Shear|Thermal Expansion|Spalling|Uncertain","estimated_width_mm":number|null,"root_causes":[string],"recommended_repairs":[string],"urgency":"Routine|Soon|Urgent|Immediate","engineering_review":string,"limitations":string}
Estimate crack width only if scale/reference supports it; otherwise null. Mention potential options such as epoxy injection or structural re-grouting only when suitable, and require an engineer's diagnosis before repair selection."""
            try:
                with st.spinner("Analyzing defect…"):
                    result = gemini_json(client, prompt, img) if client else demo_crack()
                st.session_state["crack_result"] = result
                st.session_state["crack_demo"] = not bool(client)
            except Exception as exc:
                st.error(f"Diagnostics failed: {exc}")
        result = st.session_state.get("crack_result")
        if result:
            if st.session_state.get("crack_demo"):
                st.caption("🧪 Demonstration result — generated without image analysis.")
            a,b,c = st.columns(3)
            a.metric("Defect classification", result.get("defect_type","Uncertain"))
            width = result.get("estimated_width_mm")
            b.metric("Estimated width", f"{width} mm" if width is not None else "Not estimable")
            c.metric("Urgency", result.get("urgency","Unrated"))
            status_pill(result.get("urgency","Unrated"))
            st.subheader("Potential root causes")
            for cause in result.get("root_causes", []): st.markdown(f"- {cause}")
            st.subheader("Recommended engineering actions")
            for repair in result.get("recommended_repairs", []): st.markdown(f"- {repair}")
            st.info(result.get("engineering_review", "Obtain a qualified engineering review."))
            json_download(result, "crack_diagnostics.json")

# ---------- Module 3 ----------
elif module == "Planning & Real Estate":
    st.header("📐 Planning & Real Estate Valuation")
    st.write("Indicative planning estimates; tune the assumptions to your project and local rates.")
    c1,c2 = st.columns(2)
    with c1:
        structure = st.selectbox("Structure type", ["Residential apartment", "Independent house", "Commercial building", "Industrial shed"])
        sqft = st.number_input("Built-up area (sq ft)", min_value=100, max_value=2_000_000, value=2400, step=100)
        tier = st.selectbox("Location tier", ["Tier 1", "Tier 2", "Tier 3"])
    with c2:
        completion = st.slider("Completion percentage", 0, 100, 35, 5)
        contingency_pct = st.slider("Contingency (%)", 0, 20, 8)
        market_multiplier = st.slider("Market valuation multiplier", 0.8, 2.5, 1.35, 0.05)
    rates = {"Tier 1": 2800, "Tier 2": 2200, "Tier 3": 1750}
    type_factor = {"Residential apartment":1.0, "Independent house":1.08, "Commercial building":1.25, "Industrial shed":0.78}
    rate = rates[tier] * type_factor[structure]
    base_budget = sqft * rate
    total_budget = base_budget * (1 + contingency_pct/100)
    incurred = total_budget * completion/100
    asset_value = sqft * rate * market_multiplier
    # Rule-of-thumb planning quantities; validate with structural design and BOQ.
    steel_kg = sqft * (3.5 if structure == "Industrial shed" else 4.0 if structure == "Commercial building" else 4.2)
    cement_bags = sqft * (0.32 if structure == "Industrial shed" else 0.40)
    def inr(value):
        if value >= 10_000_000: return f"₹{value/10_000_000:,.2f} Cr"
        return f"₹{value/100_000:,.2f} Lakhs"
    st.markdown("### Financial snapshot")
    k1,k2,k3 = st.columns(3)
    k1.metric("Estimated total budget", inr(total_budget))
    k2.metric("CapEx incurred to date", inr(incurred), f"{completion}% complete")
    k3.metric("Indicative market asset value", inr(asset_value))
    st.progress(completion/100, text=f"Milestone progress · {completion}%")
    st.markdown("### Material planning indicators")
    x,y,z = st.columns(3)
    x.metric("Steel requirement", f"{steel_kg:,.0f} kg", f"{steel_kg/1000:,.2f} tonnes")
    y.metric("Cement requirement", f"{cement_bags:,.0f} bags", "50 kg bags (rule of thumb)")
    z.metric("Indicative base rate", f"₹{rate:,.0f}/sq ft")
    st.caption("Budget and material quantities are high-level planning heuristics, not a bill of quantities or engineering design. Obtain local quotations and engineer-approved quantities.")
    st.divider()
    st.subheader("Conceptual 3D architectural rendering prompt")
    style = st.selectbox("Design direction", ["Contemporary Indian", "Tropical modern", "Minimalist", "Traditional courtyard"])
    floors = st.selectbox("Storeys", ["G+1", "G+2", "G+3", "G+4 or more"])
    render_prompt = (f"Photorealistic conceptual architectural visualization of a {style.lower()} {structure.lower()}, "
                     f"{floors}, {sqft:,} sq ft built-up, located in an Indian {tier.lower()} city. "
                     "Show realistic local materials, daylight, landscaped frontage, human scale, professional architectural render. "
                     "Concept only, not construction documentation.")
    st.text_area("Prompt for Pollinations AI", render_prompt, height=110)
    pollinations_url = "https://image.pollinations.ai/prompt/" + __import__("urllib.parse", fromlist=["quote"]).quote(render_prompt)
    st.markdown(f"[Open conceptual render in Pollinations AI]({pollinations_url})")
    st.caption("Rendering service is external. Do not treat generated visuals as approved plans.")

# ---------- Module 4 ----------
else:
    st.header("🌦️ Daily Site Assistant & Weather-Aware Advisory")
    weather = st.selectbox("Current / forecast condition", ["Normal", "High Wind", "Heavy Rain", "Extreme Heat"])
    alerts = {
        "Normal": ("Routine site controls", "Continue toolbox talks, housekeeping, PPE checks, lifting plans, and daily equipment inspections."),
        "High Wind": ("Wind alert · lifting operations", "Pause crane and hoisting operations when wind exceeds equipment/manufacturer or lift-plan limits. Secure loose materials, inspect scaffolds, and restrict exposed elevated work."),
        "Heavy Rain": ("Rain alert · water and electrical hazards", "Suspend unsafe excavation and work at height; inspect trench stability and drainage. Isolate damaged/wet electrical equipment, use GFCI/RCD protection, and reassess access routes."),
        "Extreme Heat": ("Heat stress alert", "Schedule strenuous work for cooler hours, provide shade and potable water/electrolytes, enforce acclimatization and work-rest cycles, and monitor workers for heat illness.")
    }
    heading, advice = alerts[weather]
    st.markdown(f'<div class="panel"><h3>{heading}</h3><p>{advice}</p></div>', unsafe_allow_html=True)
    if weather == "Heavy Rain":
        st.info("Concrete: protect fresh pours from washout; reassess placement conditions and follow the approved curing/mix procedure. Do not add water to the mix on site without authorization.")
    st.divider()
    st.subheader("Construction engineering assistant")
    st.caption("Ask about planning, site controls, concrete, materials, or construction workflows. For project-specific engineering, consult the responsible professional.")
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    for item in st.session_state.chat_history:
        with st.chat_message(item["role"]):
            st.markdown(item["content"])
    user_prompt = st.chat_input("Ask your site engineering question…")
    if user_prompt:
        st.session_state.chat_history.append({"role":"user","content":user_prompt})
        with st.chat_message("user"): st.markdown(user_prompt)
        with st.chat_message("assistant"):
            if client:
                try:
                    history = "\n".join(f'{x["role"]}: {x["content"]}' for x in st.session_state.chat_history[-12:])
                    answer = client.models.generate_content(
                        model=MODEL_NAME,
                        contents=("You are a helpful construction engineering site assistant. Give practical, "
                                  "cautious guidance, flag assumptions, and avoid claiming to certify safety. "
                                  f"Weather context: {weather}. Conversation:\n{history}")
                    ).text or "I couldn't generate a response. Please retry."
                except Exception as exc:
                    answer = f"Assistant error: {exc}"
            else:
                answer = ("Demo mode is active, so I can't generate a personalized AI response. "
                          "Add a Gemini API key in the sidebar to enable the assistant. "
                          "For this condition, remember: " + advice)
            st.markdown(answer)
        st.session_state.chat_history.append({"role":"assistant","content":answer})
    if st.button("Clear conversation"):
        st.session_state.chat_history = []
        st.rerun()

st.markdown("---")
st.markdown('<p class="small-muted">Multimodal Construction Intelligence Platform · Skill Wallet Capstone Project 1 · Prototype for educational and operational support.</p>', unsafe_allow_html=True)
