"""
CropCare AI — Farmer-Friendly Crop Disease Detection Website
==============================================================

A single-file Streamlit application that gives farmers a warm, jargon-free
way to check Corn and Grape crops for disease: a friendly landing section,
two crop-model cards, an inline upload-and-diagnose flow, and a simple
"How it works" strip.

Run with:
    streamlit run crop_disease_app.py

Dependencies: streamlit, numpy, pandas, Pillow. No external network calls
are required at runtime — every illustration is a self-contained SVG, so
the site renders identically with or without internet access.

Implementation note (read this before editing layout):
    Every visual "card" on this page uses `st.container(border=True)`,
    a real Streamlit component that truly nests its contents. Do NOT
    replace these with manually written `<div>...</div>` wrapper tags —
    Streamlit renders each widget/markdown call as its own sibling
    element, so hand-written opening/closing div tags never actually
    contain what's between them. Real containers are the only way to
    make an upload widget, a preview image, and result text visually
    live inside one bordered card.
"""

from __future__ import annotations

#import textwrap
#import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

#import numpy as np
import streamlit as st
from PIL import Image

#from dup_app import _build_corn_diseases, _build_grape_diseases
from utilis import predict_corn
from utilis import predict_grape
from rag_utilis import retrieve_solution
# ============================================================
# 1. PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="CropCare AI — Crop Disease Detector",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# ============================================================
# 2. THEME CONSTANTS
# ============================================================

class Theme:
    """Central place for the green agricultural design system."""

    BG: str = "#FAFDF9"
    BG_SOFT: str = "#F2F8F1"
    CARD_BG: str = "#FFFFFF"
    CARD_BORDER: str = "#E4F0E2"

    PRIMARY: str = "#2E7D32"
    PRIMARY_DARK: str = "#1B5E20"
    PRIMARY_LIGHT: str = "#66BB6A"
    GRAPE: str = "#6A3D9A"
    GRAPE_LIGHT: str = "#9C6FD4"
    DANGER: str = "#E53935"
    WARNING: str = "#F57C00"
    SUCCESS: str = "#2E7D32"

    TEXT: str = "#1B2B1E"
    MUTED: str = "#5F6F63"

    RADIUS_LG: str = "20px"
    RADIUS_MD: str = "14px"


def md(html: str) -> None:
    """Render a block of HTML safely.

    Strips leading/trailing whitespace from every individual line
    before handing the result to st.markdown. This is stronger than
    textwrap.dedent(): dedent only removes the *common minimum*
    indentation across all lines, which still fails once strings built
    by different functions (each with their own internal indentation)
    get concatenated together — some lines end up under-stripped,
    still start with 4+ spaces, and Markdown renders them as a literal
    code block instead of live HTML. Stripping every line individually
    sidesteps that regardless of how the string was assembled.
    """
    normalized = "\n".join(line.strip() for line in html.strip("\n").splitlines())
    st.markdown(normalized, unsafe_allow_html=True)


# ============================================================
# 3. DATA MODELS
# ============================================================

@dataclass
class CropConfig:
    """Everything a single crop card needs to render itself."""

    key: str
    label: str
    emoji: str
    accent: str
    #diseases: dict[str, DiseaseInfo]


# ============================================================
# 4. KNOWLEDGE BASE
# ============================================================


CROPS: dict[str, CropConfig] = {
    "corn": CropConfig(
        key="corn",
        label="Corn",
        emoji="🌽",
        accent=Theme.PRIMARY,
        #diseases=_build_corn_diseases(),
    ),
    "grape": CropConfig(
        key="grape",
        label="Grape",
        emoji="🍇",
        accent=Theme.GRAPE,
        #diseases=_build_grape_diseases(),
    ),
}


# ============================================================
# 5. SESSION STATE
# ============================================================

def init_session_state() -> None:
    """Ensure every key this app depends on exists in session state."""
    defaults = {
        "corn_show_uploader": False,
        "corn_uploaded_bytes": None,
        "corn_prediction": None,
        "grape_show_uploader": False,
        "grape_uploaded_bytes": None,
        "grape_prediction": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


# ============================================================
# 6. MOCK INFERENCE
# ============================================================

def run_prediction(crop: CropConfig, image: Image.Image):

    if crop.key == "corn":
        try:
            disease,confidence = predict_corn(image)
        except Exception as e:
            st.error(e)
            return None, None, None

    else:
        try:
            disease,confidence = predict_grape(image)
        except Exception as e:
            st.error(e)
            return None, None, None

    rag_data = retrieve_solution(disease)
    if rag_data is None:
        rag_data = {
            "summary":"No information found.",
            "symptoms":[],
            "immediate_action":[],
            "prevention":[],
            "treatment":[],
            "fungicides":[]
        }

    return disease, confidence, rag_data

'''
def severity_color(severity: str) -> str:
    """Map a disease severity label to a theme color."""
    return {
        "Healthy": Theme.SUCCESS,
        "Mild": Theme.PRIMARY_LIGHT,
        "Moderate": Theme.WARNING,
        "Severe": Theme.DANGER,
    }.get(severity, Theme.MUTED)
'''

# ============================================================
# 7. GLOBAL CSS
# ============================================================

def inject_global_css() -> None:
    """Inject the green agri-tech design system as custom CSS.

    Cards are real `st.container(border=True)` blocks, so this styles
    Streamlit's own bordered-container wrapper rather than any
    hand-written div — that's what keeps content genuinely inside
    the rounded card instead of leaking out as separate elements.
    """
    md(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&family=Inter:wght@400;500;600&display=swap');

        html, body, [class*="css"] {{
            font-family: 'Inter', sans-serif;
            color: {Theme.TEXT};
        }}

        .stApp {{
            background: linear-gradient(180deg, {Theme.BG} 0%, {Theme.BG_SOFT} 100%);
        }}

        h1, h2, h3 {{ font-family: 'Poppins', sans-serif; }}

        #MainMenu, footer, header {{ visibility: hidden; }}

        .block-container {{
            padding-top: 1.5rem;
            padding-bottom: 3rem;
            max-width: 1100px;
        }}

        /* Real bordered containers = our cards */
        div[data-testid="stVerticalBlockBorderWrapper"] {{
            background: {Theme.CARD_BG};
            border: 1px solid {Theme.CARD_BORDER} !important;
            border-radius: {Theme.RADIUS_LG} !important;
            box-shadow: 0 8px 24px rgba(27, 94, 32, 0.07);
            padding: 6px 6px;
            margin-bottom: 22px;
        }}

        /* ---------- Text helpers ---------- */
        .brand-name {{
            font-family: 'Poppins', sans-serif;
            font-size: 1.7rem;
            font-weight: 700;
            color: {Theme.PRIMARY_DARK};
            margin: 0;
            line-height: 1.2;
        }}
        .brand-subtitle {{ color: {Theme.MUTED}; font-size: 0.9rem; margin: 2px 0 0 0; }}

        .hero-title {{
            font-family: 'Poppins', sans-serif;
            font-size: 2.1rem;
            font-weight: 700;
            color: {Theme.TEXT};
            text-align: center;
            margin: 4px 0 2px 0;
        }}
        .hero-title .accent {{ color: {Theme.PRIMARY}; }}
        .hero-subtitle {{
            text-align: center;
            color: {Theme.MUTED};
            font-size: 1rem;
            max-width: 640px;
            margin: 0 auto 6px auto;
        }}

        .section-title {{
            text-align: center;
            font-family: 'Poppins', sans-serif;
            font-weight: 700;
            font-size: 1.3rem;
            color: {Theme.TEXT};
            margin: 6px 0 18px 0;
        }}

        /* ---------- Illustration row ---------- */
        .scene-row {{
            display: flex;
            align-items: flex-end;
            justify-content: center;
            gap: 18px;
            padding: 10px 0 4px 0;
            flex-wrap: wrap;
        }}
        .scene-row svg {{ flex-shrink: 0; }}

        .farmer-avatar {{ animation: bob 3s ease-in-out infinite; }}
        @keyframes bob {{
            0%, 100% {{ transform: translateY(0px); }}
            50% {{ transform: translateY(-8px); }}
        }}
        .farmer-hand {{
            transform-origin: 76px 58px;
            animation: wave 1.6s ease-in-out infinite;
        }}
        @keyframes wave {{
            0%, 100% {{ transform: rotate(0deg); }}
            25% {{ transform: rotate(-18deg); }}
            50% {{ transform: rotate(0deg); }}
            75% {{ transform: rotate(-10deg); }}
        }}
        .heart-bubble {{ animation: pulse 1.8s ease-in-out infinite; transform-origin: center; }}
        @keyframes pulse {{
            0%, 100% {{ transform: scale(1); }}
            50% {{ transform: scale(1.15); }}
        }}
        .sway {{ animation: sway 4s ease-in-out infinite; transform-origin: bottom center; }}
        @keyframes sway {{
            0%, 100% {{ transform: rotate(-2deg); }}
            50% {{ transform: rotate(2deg); }}
        }}

        /* ---------- Crop model card content ---------- */
        .crop-card-header {{ display: flex; align-items: center; gap: 12px; margin-bottom: 2px; padding: 10px 10px 0 10px; }}
        .crop-emoji-badge {{
            font-size: 1.7rem;
            border-radius: 50%;
            width: 54px; height: 54px;
            display: flex; align-items: center; justify-content: center;
        }}
        .crop-emoji-badge.corn {{ background: #FFF3D6; }}
        .crop-emoji-badge.grape {{ background: #F1E7FA; }}
        .crop-title {{ font-family: 'Poppins', sans-serif; font-size: 1.2rem; font-weight: 600; margin: 0; }}
        .crop-title.corn {{ color: {Theme.PRIMARY_DARK}; }}
        .crop-title.grape {{ color: {Theme.GRAPE}; }}
        .crop-subtitle {{ color: {Theme.MUTED}; font-size: 0.88rem; margin: 0; }}

        /* All buttons: shared base shape */
        div[data-testid="stVerticalBlockBorderWrapper"] .stButton > button {{
            border-radius: 999px;
            font-weight: 600;
            padding: 0.5rem 1.3rem;
        }}

        /* Corn action zone (Upload / Close) = green outline */
        .st-key-corn_action_zone .stButton > button {{
            background: {Theme.CARD_BG};
            color: {Theme.PRIMARY_DARK};
            border: 1.5px solid {Theme.PRIMARY};
        }}
        .st-key-corn_action_zone .stButton > button:hover {{
            background: {Theme.PRIMARY}; color: white;
        }}

        /* Grape action zone (Upload / Close) = purple outline */
        .st-key-grape_action_zone .stButton > button {{
            background: {Theme.CARD_BG};
            color: {Theme.GRAPE};
            border: 1.5px solid {Theme.GRAPE};
        }}
        .st-key-grape_action_zone .stButton > button:hover {{
            background: {Theme.GRAPE}; color: white;
        }}

        /* Analyze buttons = solid gradient, full width */
        .st-key-corn_analyze_zone .stButton > button {{
            background: linear-gradient(135deg, {Theme.PRIMARY} 0%, {Theme.PRIMARY_DARK} 100%);
            color: white; border: none; width: 100%;
        }}
        .st-key-grape_analyze_zone .stButton > button {{
            background: linear-gradient(135deg, {Theme.GRAPE_LIGHT} 0%, {Theme.GRAPE} 100%);
            color: white; border: none; width: 100%;
        }}

        /* ---------- Result badge ---------- */
        .result-badge {{
            display: inline-flex; align-items: center; gap: 8px;
            padding: 6px 16px; border-radius: 999px;
            font-weight: 600; font-size: 0.95rem; margin: 10px 0 4px 0;
        }}

        /* ---------- Speech bubble ---------- */
        .speech-bubble {{
            position: relative;
            background: {Theme.BG_SOFT};
            border: 1px solid {Theme.CARD_BORDER};
            border-radius: {Theme.RADIUS_MD};
            padding: 16px 18px;
            margin: 14px 0 18px 0;
            font-size: 0.98rem; line-height: 1.5; color: {Theme.TEXT};
        }}
        .speech-bubble::before {{
            content: "";
            position: absolute; top: -10px; left: 28px;
            border-width: 0 10px 10px 10px;
            border-style: solid;
            border-color: transparent transparent {Theme.BG_SOFT} transparent;
        }}
        .speech-bubble-label {{
            display: flex; align-items: center; gap: 8px;
            font-weight: 600; color: {Theme.PRIMARY_DARK};
            margin-bottom: 6px; font-size: 0.92rem;
        }}

        /* ---------- Info sections ---------- */
        .info-section-title {{
            font-weight: 600; font-size: 0.95rem; color: {Theme.PRIMARY_DARK};
            margin: 4px 0 6px 0; display: flex; align-items: center; gap: 6px;
        }}
        .info-list {{ margin: 0 0 4px 0; padding-left: 20px; }}
        .info-list li {{ margin-bottom: 4px; color: {Theme.TEXT}; font-size: 0.92rem; }}
        .fungicide-pill {{
            display: inline-block;
            background: {Theme.PRIMARY_LIGHT}22;
            color: {Theme.PRIMARY_DARK};
            border: 1px solid {Theme.PRIMARY_LIGHT}55;
            padding: 4px 12px; border-radius: 999px;
            font-size: 0.85rem; margin: 3px 4px 3px 0;
        }}

        .stImage img {{ border-radius: {Theme.RADIUS_MD}; }}

        [data-testid="stFileUploaderDropzone"] {{
            border-radius: {Theme.RADIUS_MD} !important;
            border: 1.5px dashed {Theme.PRIMARY_LIGHT} !important;
            background: {Theme.BG_SOFT} !important;
        }}

        /* ---------- How it works strip ---------- */
        .how-it-works-inner {{ padding: 10px 8px; }}
        .how-title {{
            display: flex; align-items: center; gap: 8px;
            font-weight: 700; color: {Theme.PRIMARY_DARK}; margin-bottom: 14px;
        }}
        .steps-row {{
            display: flex; align-items: center; justify-content: space-between;
            flex-wrap: wrap; gap: 10px;
        }}
        .step {{ display: flex; flex-direction: column; align-items: center; gap: 6px; min-width: 110px; }}
        .step-icon {{
            width: 44px; height: 44px; border-radius: 50%;
            background: {Theme.BG_SOFT}; border: 1px solid {Theme.CARD_BORDER};
            display: flex; align-items: center; justify-content: center; font-size: 1.2rem;
        }}
        .step-label {{ font-size: 0.82rem; color: {Theme.MUTED}; text-align: center; }}
        .step-arrow {{ color: {Theme.PRIMARY_LIGHT}; font-size: 1.3rem; }}

        .footer-note {{ text-align: center; color: {Theme.MUTED}; font-size: 0.85rem; margin-top: 10px; }}

        @media (max-width: 768px) {{
            .hero-title {{ font-size: 1.6rem; }}
            .steps-row {{ justify-content: center; }}
            .step-arrow {{ display: none; }}
        }}
        </style>
        """
    )


# ============================================================
# 8. SVG ILLUSTRATIONS (self-contained, no network calls)
# ============================================================

def svg_farmer() -> str:
    """Friendly waving farmer avatar."""
    return """
    <svg class="farmer-avatar" width="120" height="130" viewBox="0 0 120 130" xmlns="http://www.w3.org/2000/svg">
        <ellipse cx="60" cy="122" rx="34" ry="7" fill="#2E7D3222"/>
        <rect x="42" y="66" width="36" height="36" rx="14" fill="#2E7D32"/>
        <rect x="50" y="66" width="6" height="20" fill="#1B5E20"/>
        <rect x="64" y="66" width="6" height="20" fill="#1B5E20"/>
        <circle cx="60" cy="52" r="20" fill="#FFD9A6"/>
        <ellipse cx="60" cy="38" rx="26" ry="8" fill="#E4B34F"/>
        <ellipse cx="60" cy="33" rx="14" ry="9" fill="#F2C868"/>
        <circle cx="53" cy="52" r="2.4" fill="#3E2C1C"/>
        <circle cx="67" cy="52" r="2.4" fill="#3E2C1C"/>
        <path d="M52 59 Q60 66 68 59" stroke="#8A4B2A" stroke-width="2.4" fill="none" stroke-linecap="round"/>
        <circle cx="49" cy="57" r="3" fill="#FF9E80" opacity="0.5"/>
        <circle cx="71" cy="57" r="3" fill="#FF9E80" opacity="0.5"/>
        <g class="farmer-hand">
            <rect x="72" y="60" width="9" height="26" rx="4.5" fill="#FFD9A6"/>
            <circle cx="76" cy="58" r="6" fill="#FFD9A6"/>
        </g>
        <rect x="39" y="72" width="9" height="24" rx="4.5" fill="#FFD9A6"/>
        <rect x="46" y="100" width="12" height="20" rx="4" fill="#1B5E20"/>
        <rect x="62" y="100" width="12" height="20" rx="4" fill="#1B5E20"/>
    </svg>
    """


def svg_corn_stalk() -> str:
    """Simple flat-style corn stalk illustration."""
    return """
    <svg class="sway" width="70" height="130" viewBox="0 0 70 130" xmlns="http://www.w3.org/2000/svg">
        <ellipse cx="35" cy="122" rx="18" ry="6" fill="#2E7D3222"/>
        <rect x="32" y="40" width="6" height="82" rx="3" fill="#4CAF50"/>
        <path d="M35 55 C10 50 6 30 8 15 C24 22 35 38 35 55 Z" fill="#66BB6A"/>
        <path d="M35 70 C60 65 64 45 62 30 C46 37 35 53 35 70 Z" fill="#4CAF50"/>
        <path d="M35 90 C14 88 10 72 12 60 C26 66 35 77 35 90 Z" fill="#388E3C"/>
        <g>
            <ellipse cx="46" cy="55" rx="9" ry="24" fill="#F2C14E"/>
            <path d="M39 34 Q46 28 53 34" stroke="#4CAF50" stroke-width="3" fill="none" stroke-linecap="round"/>
            <line x1="41" y1="40" x2="41" y2="72" stroke="#E0A93C" stroke-width="1.4"/>
            <line x1="46" y1="38" x2="46" y2="76" stroke="#E0A93C" stroke-width="1.4"/>
            <line x1="51" y1="40" x2="51" y2="72" stroke="#E0A93C" stroke-width="1.4"/>
        </g>
    </svg>
    """


def svg_grape_vine() -> str:
    """Simple flat-style grape vine illustration."""
    return """
    <svg class="sway" width="80" height="130" viewBox="0 0 80 130" xmlns="http://www.w3.org/2000/svg">
        <ellipse cx="40" cy="122" rx="20" ry="6" fill="#6A3D9A22"/>
        <path d="M40 20 C36 45 44 70 38 122" stroke="#6D4C2C" stroke-width="5" fill="none" stroke-linecap="round"/>
        <ellipse cx="24" cy="34" rx="16" ry="13" fill="#66BB6A" transform="rotate(-15 24 34)"/>
        <ellipse cx="56" cy="46" rx="16" ry="13" fill="#4CAF50" transform="rotate(15 56 46)"/>
        <ellipse cx="26" cy="66" rx="15" ry="12" fill="#66BB6A" transform="rotate(-10 26 66)"/>
        <g fill="#7B4FA6">
            <circle cx="34" cy="76" r="6"/>
            <circle cx="42" cy="80" r="6"/>
            <circle cx="30" cy="86" r="6"/>
            <circle cx="40" cy="90" r="6"/>
            <circle cx="48" cy="88" r="6"/>
            <circle cx="36" cy="98" r="6"/>
            <circle cx="46" cy="100" r="6"/>
        </g>
    </svg>
    """


def svg_robot() -> str:
    """Friendly assistant robot with a heart speech bubble."""
    return """
    <svg width="90" height="130" viewBox="0 0 90 130" xmlns="http://www.w3.org/2000/svg">
        <ellipse cx="40" cy="122" rx="20" ry="6" fill="#2E7D3222"/>
        <g class="heart-bubble">
            <path d="M50 18 h28 a6 6 0 0 1 6 6 v14 a6 6 0 0 1 -6 6 h-10 l-6 8 v-8 h-12 a6 6 0 0 1 -6 -6 v-14 a6 6 0 0 1 6 -6 Z" fill="#FFFFFF" stroke="#EADCF7" stroke-width="1.5"/>
            <path d="M64 30 c-2 -3 -7 -2 -7 2 c0 3 4 5 7 8 c3 -3 7 -5 7 -8 c0 -4 -5 -5 -7 -2 Z" fill="#EF5350"/>
        </g>
        <rect x="10" y="10" width="8" height="10" rx="3" fill="#B0BEC5"/>
        <circle cx="14" cy="8" r="3" fill="#66BB6A"/>
        <rect x="4" y="24" width="52" height="46" rx="18" fill="#F5F5F7" stroke="#D8DEE3" stroke-width="1.5"/>
        <rect x="14" y="34" width="32" height="18" rx="9" fill="#1B2B1E"/>
        <circle cx="24" cy="43" r="3.4" fill="#66FFCB"/>
        <circle cx="36" cy="43" r="3.4" fill="#66FFCB"/>
        <rect x="10" y="74" width="40" height="30" rx="12" fill="#E3E7EA" stroke="#D8DEE3" stroke-width="1.5"/>
        <rect x="20" y="82" width="20" height="16" rx="3" fill="#66BB6A"/>
        <path d="M27 90 l3 3 l6 -7" stroke="white" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
        <rect x="-2" y="78" width="10" height="20" rx="5" fill="#CFD8DC"/>
        <rect x="52" y="78" width="10" height="20" rx="5" fill="#CFD8DC"/>
    </svg>
    """


# ============================================================
# 9. RENDER: HEADER + HERO
# ============================================================

def render_header() -> None:
    """Minimal top-left brand strip — no card box, just a clean navbar."""
    md(
        """
        <div style="display:flex; align-items:center; gap:10px; padding:4px 2px 0 2px; margin-bottom:18px;">
            <span style="font-size:1.7rem;">🌱</span>
            <div>
                <p class="brand-name">CropCare AI</p>
                <p class="brand-subtitle">Smart Crop Disease Assistant</p>
            </div>
        </div>
        """
    )


def render_hero() -> None:
    """Landing hero: greeting, short explanation, and the farm scene."""
    with st.container(border=True):
        md(
            """
            <div style="display:flex; flex-direction:column; align-items:center; text-align:center; width:100%;">
                <p class="hero-title">Hi Farmer! 👋</p>
                <p class="hero-title" style="font-size:1.5rem;">
                    I'm here to help your crops stay <span class="accent">healthy</span> 🌿
                </p>
                <p class="hero-subtitle">
                    Upload a leaf photo of Corn or Grape and get simple, friendly advice —
                    no farming jargon, just clear next steps for your crop.
                </p>
            </div>
            """
        )
        scene_html = f"""
        <div class="scene-row">
            {svg_corn_stalk()}
            {svg_farmer()}
            {svg_robot()}
            {svg_grape_vine()}
        </div>
        """
        md(scene_html)


# ============================================================
# 10. RENDER: CROP MODEL CARDS
# ============================================================

def render_prediction_details(disease,confidence,rag) -> None:
    """Render the full result: badge, speech bubble, and five sections."""
    #color = severity_color(disease.severity)
    color=Theme.PRIMARY
    #icon = "✅" if disease.severity == "Healthy" else "⚠️"
    icon = "⚠️"
    md(
        f"""
        <div class="result-badge" style="background:{color}1A; color:{color}; border:1px solid {color}55;">
            {icon} {disease.replace("_"," ")} • {confidence*100:.1f}% confidence
        </div>
        """
    )
    #st.progress(min(max(confidence, 0.0), 1.0))
    st.write(f"Confidence : {confidence*100:.2f}%")

    md(
        f"""
        <div class="speech-bubble">
            <div class="speech-bubble-label">👨‍🌾 Here's what I found:</div>
            {rag.get("summary","No information found.")}
        </div>
        """
    )

    tab_symptoms, tab_action, tab_prevent, tab_treat, tab_fungicide = st.tabs(
        ["🩺 Symptoms", "⚡ Immediate Action", "🛡️ Prevention", "💊 Treatment", "🧪 Fungicides"]
    )
    with tab_symptoms:
        items = "".join(f"<li>{i}</li>" for i in rag.get("symptoms",[]))
        md(f'<div class="info-section-title">🔍 What to look for</div><ul class="info-list">{items}</ul>')
    with tab_action:
        items = "".join(f"<li>{i}</li>" for i in rag.get("immediate_action",[]))
        md(f'<div class="info-section-title">⚡ Do this now</div><ul class="info-list">{items}</ul>')
    with tab_prevent:
        items = "".join(f"<li>{i}</li>" for i in rag.get("prevention",[]))
        md(f'<div class="info-section-title">🛡️ Avoid it next time</div><ul class="info-list">{items}</ul>')
    with tab_treat:
        items = "".join(f"<li>{i}</li>" for i in rag.get("treatment",[]))
        md(f'<div class="info-section-title">💊 How to treat it</div><ul class="info-list">{items}</ul>')
    with tab_fungicide:
        pills = "".join(f'<span class="fungicide-pill">{f}</span>' for f in rag.get("fungicides",[]))
        md(f'<div class="info-section-title">🧪 Recommended Fungicides</div>{pills}')


def render_crop_card(crop: CropConfig) -> None:
    """Render one crop-model card: icon, description, and toggleable uploader.

    Button color-scoping uses real `st.container(key=...)` blocks rather
    than hand-written wrapper divs. Streamlit gives a container created
    with `key=` an actual CSS class (`st-key-<key>`) on its real DOM
    node, so a button placed inside it is a genuine descendant — unlike
    a manually written `<div>...</div>` pair, which never truly wraps
    the widgets rendered between the two `st.markdown()` calls.
    """
    show_key = f"{crop.key}_show_uploader"
    bytes_key = f"{crop.key}_uploaded_bytes"
    pred_key = f"{crop.key}_prediction"

    with st.container(border=True):
        md(
            f"""
            <div class="crop-card-header">
                <div class="crop-emoji-badge {crop.key}">{crop.emoji}</div>
                <div>
                    <p class="crop-title {crop.key}">{crop.label} Model</p>
                    <p class="crop-subtitle">Detect diseases in {crop.label} leaves</p>
                </div>
            </div>
            """
        )

        with st.container(key=f"{crop.key}_action_zone"):
            if not st.session_state[show_key]:
                if st.button(f"⬆ Upload {crop.label} Leaf", key=f"{crop.key}_open_btn"):
                    st.session_state[show_key] = True
                    st.rerun()
            else:
                uploaded_file = st.file_uploader(
                    f"Upload a {crop.label.lower()} leaf photo",
                    type=["jpg", "jpeg", "png"],
                    key=f"{crop.key}_uploader",
                    label_visibility="collapsed",
                )

                if uploaded_file is not None:
                    image_bytes = uploaded_file.getvalue()
                    st.session_state[bytes_key] = image_bytes
                    image = Image.open(uploaded_file).convert("RGB")
                    st.image(image, caption="Your uploaded photo", use_container_width=True)

                    with st.container(key=f"{crop.key}_analyze_zone"):
                        if st.button(
                            f"🔎 Analyze {crop.label} Leaf",
                            key=f"{crop.key}_analyze_btn",
                            use_container_width=True,
                        ):
                            with st.spinner("Analyzing image..."):
                                disease, confidence, rag_data = run_prediction(crop, image)
                            st.session_state[pred_key] = {
                                        "disease": disease,
                                        "confidence": confidence,
                                        "rag": rag_data}

                if st.button("← Close", key=f"{crop.key}_close_btn"):
                    st.session_state[show_key] = False
                    st.rerun()

                prediction = st.session_state.get(pred_key)
                if prediction is not None:
                    st.divider()
                    render_prediction_details(prediction["disease"],prediction["confidence"],prediction["rag"])
                elif uploaded_file is None:
                    st.caption("👆 Choose a photo to check your plant's health.")


# ============================================================
# 11. RENDER: HOW IT WORKS + FOOTER
# ============================================================

def render_how_it_works() -> None:
    """Simple 4-step explainer strip, farmer-friendly wording only."""
    with st.container(border=True):
        md(
            """
            <div class="how-it-works-inner">
                <div class="how-title">🧠 How it works</div>
                <div class="steps-row">
                    <div class="step">
                        <div class="step-icon">📷</div>
                        <div class="step-label">Upload a leaf photo</div>
                    </div>
                    <div class="step-arrow">→</div>
                    <div class="step">
                        <div class="step-icon">🔍</div>
                        <div class="step-label">We check for disease</div>
                    </div>
                    <div class="step-arrow">→</div>
                    <div class="step">
                        <div class="step-icon">📖</div>
                        <div class="step-label">Get simple advice</div>
                    </div>
                    <div class="step-arrow">→</div>
                    <div class="step">
                        <div class="step-icon">🌱</div>
                        <div class="step-label">Protect your crop</div>
                    </div>
                </div>
            </div>
            """
        )


def render_footer() -> None:
    md(
        """
        <div class="footer-note">
            🌱 CropCare AI gives general guidance — for severe or unclear cases,
            please consult your local agricultural extension office.
        </div>
        """
    )


# ============================================================
# 12. ORCHESTRATOR
# ============================================================

def main() -> None:
    """Application entry point: wires together state, styling, and layout."""
    init_session_state()
    inject_global_css()

    render_header()
    render_hero()

    md('<p class="section-title">🌾 Choose a Crop Model</p>')
    col_corn, col_grape = st.columns(2, gap="large")
    with col_corn:
        render_crop_card(CROPS["corn"])
    with col_grape:
        render_crop_card(CROPS["grape"])

    render_how_it_works()
    render_footer()


if __name__ == "__main__":
    main()