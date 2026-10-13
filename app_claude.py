# Creative Role Studio (extended chatbot) - redesigned UI
# Same features as before:
#   1. Conversation memory (chat interface)
#   2. Streaming answers (text appears as it is written)
#   3. Two providers in one app: OpenAI and Claude
#   4. Settings: model, answer length, creativity, language, and your own custom role
#   5. Download the conversation
# New: a role "stage" banner whose illustration and colours change with the selected role.

import html
import re

import streamlit as st
import anthropic
from openai import OpenAI

st.set_page_config(page_title="🎭 Creative Role Studio", page_icon="🎭", layout="wide")

# -----------------------
# Roles (system prompts) - unchanged
# -----------------------
ROLES = {
    "🎥 Video Director":
    "You are a professional film director. Always analyze ideas in terms of visual storytelling: use camera movement, lighting, framing, and emotional tone. Describe concepts as if you are planning a film scene.",
    "💃 Dance Instructor":
    "You are a dance instructor. Always respond using movement and rhythm metaphors. Translate ideas into body motion, choreography, and stage presence.",
    "👗 Fashion Stylist":
    "You are a fashion stylist. Explain every idea using the language of color, texture, and silhouette. Think visually: how something would appear, feel, and harmonize.",
    "🎭 Acting Coach":
    "You are an acting coach. Speak as if guiding an actor through emotion and timing. Use scene examples, emotional layering, and body language descriptions.",
    "🎨 Art Curator":
    "You are an art curator. Reflect in an analytical yet poetic tone. Compare artistic elements, styles, and their emotional effects as if curating an exhibition.",
    "✍️ Custom role (write your own)": "",
}

MODELS = {
    "OpenAI": ["gpt-4o-mini"],
    "Claude": ["claude-haiku-5-5", "claude-sonnet-5-5"],
}
KEY_NAMES = {"OpenAI": "OPENAI_API_KEY", "Claude": "ANTHROPIC_API_KEY"}

# -----------------------
# Role artwork: one small inline SVG per role (200 x 200), drawn in the role's accent colour
# -----------------------
W = "#ffffff"


def art_director(a):
    return f"""
    <path d="M18 8 L76 64 L6 78 Z" fill="{a}" opacity=".28"/>
    <path d="M182 8 L124 64 L194 78 Z" fill="{a}" opacity=".18"/>
    <g transform="rotate(-14 42 84)">
      <rect x="42" y="58" width="116" height="26" rx="4" fill="{W}"/>
      <path d="M64 58l-12 26h16l12-26z M98 58l-12 26h16l12-26z M132 58l-12 26h16l12-26z" fill="{a}"/>
    </g>
    <rect x="42" y="88" width="116" height="22" rx="4" fill="{W}"/>
    <path d="M64 88l-12 22h16l12-22z M98 88l-12 22h16l12-22z M132 88l-12 22h16l12-22z" fill="{a}"/>
    <rect x="42" y="114" width="116" height="62" rx="6" fill="none" stroke="{W}" stroke-width="5"/>
    <path d="M58 138h58M58 156h84" stroke="{a}" stroke-width="5" stroke-linecap="round"/>
    """


def art_dance(a):
    return f"""
    <path d="M24 150 C60 190 140 190 176 150" fill="none" stroke="{a}" stroke-width="3" stroke-dasharray="2 8" stroke-linecap="round"/>
    <path d="M30 70 C40 40 66 24 96 20" fill="none" stroke="{a}" stroke-width="3" stroke-dasharray="2 8" stroke-linecap="round"/>
    <circle cx="104" cy="40" r="11" fill="{W}"/>
    <path d="M102 54 C100 80 98 96 100 112" stroke="{W}" stroke-width="8" fill="none" stroke-linecap="round"/>
    <path d="M101 68 C82 58 68 42 60 26" stroke="{W}" stroke-width="6" fill="none" stroke-linecap="round"/>
    <path d="M101 68 C126 72 146 64 162 52" stroke="{W}" stroke-width="6" fill="none" stroke-linecap="round"/>
    <path d="M100 108 C70 112 52 130 36 152 C70 144 90 144 100 142 C112 144 134 148 166 140 C152 126 128 110 100 108Z" fill="{a}"/>
    <path d="M96 142 C92 162 84 176 68 188" stroke="{W}" stroke-width="6" fill="none" stroke-linecap="round"/>
    <path d="M106 142 C116 158 130 168 150 172" stroke="{W}" stroke-width="6" fill="none" stroke-linecap="round"/>
    """


def art_fashion(a):
    return f"""
    <path d="M100 46 C100 34 114 34 114 24 C114 14 98 12 94 24" fill="none" stroke="{W}" stroke-width="5" stroke-linecap="round"/>
    <path d="M100 46 L30 88 H170 Z" fill="none" stroke="{W}" stroke-width="5" stroke-linejoin="round"/>
    <path d="M74 96 H126 L120 126 H80 Z" fill="{W}"/>
    <path d="M80 126 L48 184 H152 L120 126 Z" fill="{a}"/>
    <path d="M80 126 H120" stroke="#00000055" stroke-width="5"/>
    <path d="M78 150 L66 184 M100 132 V184 M122 150 L134 184" stroke="#00000033" stroke-width="3" fill="none"/>
    """


def art_acting(a):
    return f"""
    <g transform="translate(-6 8)">
      <path d="M28 52 H108 V108 C108 138 90 158 68 158 C46 158 28 138 28 108 Z" fill="{W}"/>
      <path d="M44 88 Q55 78 64 88 M74 88 Q85 78 94 88" stroke="#000000aa" stroke-width="5" fill="none" stroke-linecap="round"/>
      <path d="M46 118 Q68 140 90 118" stroke="#000000aa" stroke-width="5" fill="none" stroke-linecap="round"/>
    </g>
    <g transform="rotate(14 138 104)">
      <path d="M98 44 H178 V100 C178 130 160 150 138 150 C116 150 98 130 98 100 Z" fill="{a}"/>
      <path d="M114 82 Q125 92 134 82 M144 82 Q155 92 164 82" stroke="#000000aa" stroke-width="5" fill="none" stroke-linecap="round"/>
      <path d="M116 124 Q138 106 160 124" stroke="#000000aa" stroke-width="5" fill="none" stroke-linecap="round"/>
    </g>
    """


def art_curator(a):
    return f"""
    <path d="M70 12 H130 L116 28 H84 Z" fill="{a}" opacity=".6"/>
    <path d="M84 28 L40 40 H160 L116 28 Z" fill="{a}" opacity=".18"/>
    <rect x="30" y="44" width="140" height="108" rx="4" fill="none" stroke="{a}" stroke-width="8"/>
    <rect x="38" y="52" width="124" height="92" fill="#ffffff22"/>
    <circle cx="132" cy="78" r="12" fill="{W}"/>
    <path d="M38 144 L78 92 L104 124 L124 104 L162 144 Z" fill="{W}"/>
    <rect x="76" y="164" width="48" height="14" rx="3" fill="{W}"/>
    <path d="M84 171 H116" stroke="{a}" stroke-width="3" stroke-linecap="round"/>
    """


def art_custom(a):
    star = lambda x, y, s: f'<path d="M{x} {y-s} L{x+s*0.3} {y-s*0.3} L{x+s} {y} L{x+s*0.3} {y+s*0.3} L{x} {y+s} L{x-s*0.3} {y+s*0.3} L{x-s} {y} L{x-s*0.3} {y-s*0.3} Z" fill="{a}"/>'
    return f"""
    <path d="M156 26 C96 34 62 84 56 146 C102 138 144 98 156 26 Z" fill="{W}"/>
    <path d="M156 26 L48 172" stroke="{a}" stroke-width="5" stroke-linecap="round"/>
    <path d="M70 120 L100 112 M84 92 L112 90 M104 70 L128 70" stroke="{a}" stroke-width="3" stroke-linecap="round" opacity=".7"/>
    <path d="M48 172 L40 186 L56 180 Z" fill="{W}"/>
    {star(40, 50, 14)}{star(166, 128, 10)}{star(120, 168, 7)}
    """


# name -> (title, tagline, gradient start, gradient end, accent, artwork function)
THEMES = {
    "🎥 Video Director": ("Video Director", "Thinks in camera angles, light, and pacing.", "#1d2b44", "#0a1222", "#f2b134", art_director),
    "💃 Dance Instructor": ("Dance Instructor", "Turns every idea into movement and rhythm.", "#5a1b4b", "#240a26", "#ff80b5", art_dance),
    "👗 Fashion Stylist": ("Fashion Stylist", "Sees ideas as colour, texture, and silhouette.", "#0f3f3b", "#06201e", "#6fe0c3", art_fashion),
    "🎭 Acting Coach": ("Acting Coach", "Guides emotion, timing, and presence.", "#4b1224", "#1e0710", "#ff9d66", art_acting),
    "🎨 Art Curator": ("Art Curator", "Compares styles like an exhibition wall.", "#2a2e6b", "#13153a", "#a3b6ff", art_curator),
    "✍️ Custom role (write your own)": ("Custom role", "", "#2f3d2a", "#131c11", "#c8e45f", art_custom),
}


def get_key(provider):
    """Use a key typed in the sidebar; otherwise look in Streamlit secrets."""
    typed = st.session_state.get("typed_key", "").strip()
    if typed:
        return typed
    try:
        return st.secrets[KEY_NAMES[provider]]
    except Exception:
        return ""


# -----------------------
# One streaming function per provider (each yields pieces of text)
# -----------------------
def stream_openai(api_key, model, system, history, max_tokens, temperature):
    client = OpenAI(api_key=api_key)
    kwargs = dict(
        model=model,
        messages=[{"role": "system", "content": system}] + history,
        max_completion_tokens=max_tokens,
        stream=True,
    )
    if temperature is not None:
        kwargs["temperature"] = temperature
    for chunk in client.chat.completions.create(**kwargs):
        if chunk.choices and chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content


def stream_claude(api_key, model, system, history, max_tokens, temperature):
    client = anthropic.Anthropic(api_key=api_key)
    kwargs = dict(model=model, max_tokens=max_tokens, system=system, messages=history)
    if temperature is not None:
        kwargs["temperature"] = temperature
    with client.messages.stream(**kwargs) as stream:
        for text in stream.text_stream:
            yield text


STREAMERS = {"OpenAI": stream_openai, "Claude": stream_claude}

# -----------------------
# Sidebar (same settings as before)
# -----------------------
st.sidebar.header("⚙️ Settings")
provider = st.sidebar.radio("AI provider", ["Claude", "OpenAI"])
st.sidebar.text_input(
    f"{provider} API key",
    type="password",
    key="typed_key",
    placeholder="sk-ant-..." if provider == "Claude" else "sk-...",
)
model = st.sidebar.selectbox("Model", MODELS[provider])

role_name = st.sidebar.selectbox("Role", list(ROLES.keys()))
if role_name.startswith("✍️"):
    role_text = st.sidebar.text_area(
        "Write your role (who is the AI, how does it think and speak?)",
        "You are a poet who explains everything through the seasons.",
        height=120,
    )
else:
    role_text = ROLES[role_name]
    st.sidebar.info(role_text)

language = st.sidebar.selectbox("Answer language", ["Same as my question", "English", "한국어"])
max_tokens = st.sidebar.slider("Answer length (max tokens)", 200, 1500, 600, step=100)
use_creativity = st.sidebar.checkbox("Set creativity (temperature) myself")
temperature = st.sidebar.slider("Creativity", 0.0, 1.0, 0.7, step=0.1) if use_creativity else None

if st.sidebar.button("🗑️ Clear conversation"):
    st.session_state.messages = []

# -----------------------
# Look and feel: colours follow the selected role
# -----------------------
title, tagline, c1, c2, accent, art = THEMES[role_name]
role_emoji = role_name.split(" ", 1)[0]
if role_name.startswith("✍️"):
    tagline = role_text.strip()[:140] + ("…" if len(role_text.strip()) > 140 else "")

st.markdown(
    f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,500;12..96,700&family=Figtree:wght@400;500;600&display=swap');
:root {{ --accent: {accent}; --c1: {c1}; --c2: {c2}; }}
html, body, [class*="st-"], .stMarkdown {{ font-family: 'Figtree', system-ui, sans-serif; }}
.block-container {{ padding-top: 2.2rem; max-width: 980px; }}

.app-head {{ margin: 0 0 1.1rem 0; }}
.app-head h1 {{ font-family: 'Bricolage Grotesque', sans-serif; font-weight: 700; font-size: 1.9rem;
  letter-spacing: -0.02em; margin: 0; padding: 0; }}
.app-head p {{ margin: .25rem 0 0 0; opacity: .65; font-size: .95rem; }}

.stage {{ display: grid; grid-template-columns: 190px 1fr; gap: 1.6rem; align-items: center;
  padding: 1.4rem 1.8rem 1.4rem 1.4rem; border-radius: 28px; color: #fff;
  background: radial-gradient(120% 140% at 0% 0%, var(--c1) 0%, var(--c2) 70%);
  border: 1px solid color-mix(in srgb, var(--accent) 35%, transparent); margin-bottom: 1.4rem; }}
.stage .art {{ width: 190px; height: 190px; border-radius: 22px; padding: 10px;
  background: color-mix(in srgb, var(--accent) 14%, transparent);
  box-shadow: inset 0 0 0 2px color-mix(in srgb, var(--accent) 45%, transparent); }}
.stage .art svg {{ width: 100%; height: 100%; display: block; }}
.stage .now {{ font-size: .9rem; opacity: .75; margin: 0; }}
.stage h2 {{ font-family: 'Bricolage Grotesque', sans-serif; font-weight: 700; font-size: 2.3rem;
  line-height: 1.05; letter-spacing: -0.02em; margin: .2rem 0 .5rem 0; padding: 0; color: #fff; }}
.stage .tag {{ font-size: 1.05rem; margin: 0 0 1rem 0; max-width: 46ch; color: #ffffffdd; }}
.stage .chip {{ display: inline-block; padding: .25rem .75rem; border-radius: 999px; font-size: .85rem; font-weight: 600;
  color: var(--c2); background: var(--accent); }}
@media (max-width: 640px) {{
  .stage {{ grid-template-columns: 1fr; justify-items: start; padding: 1.2rem; }}
  .stage .art {{ width: 140px; height: 140px; }}
  .stage h2 {{ font-size: 1.8rem; }}
}}

[data-testid="stChatMessage"] {{ border-radius: 18px; padding: .9rem 1.1rem; }}
[data-testid="stChatInput"] {{ border-radius: 18px; }}
[data-testid="stChatInput"]:focus-within {{ box-shadow: 0 0 0 2px var(--accent); }}
[data-testid="stSidebar"] [data-testid="stSidebarHeader"] {{ padding-bottom: 0; }}
[data-testid="stSidebar"] h2 {{ font-family: 'Bricolage Grotesque', sans-serif; letter-spacing: -0.01em; }}
.stButton > button, .stDownloadButton > button {{ border-radius: 12px; }}
.stButton > button:hover, .stDownloadButton > button:hover {{ border-color: var(--accent); color: inherit; }}
.foot {{ opacity: .6; font-size: .85rem; }}
</style>
""",
    unsafe_allow_html=True,
)

st.markdown(
    """
<div class="app-head">
<h1>🎭 Creative Role Studio</h1>
<p>Arts and Advanced Big Data | Chat with a creative role, powered by OpenAI or Claude</p>
</div>
""",
    unsafe_allow_html=True,
)

# Role banner: the illustration, name and colours change with the selected role
stage_html = f"""
<div class="stage">
<div class="art"><svg viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="{html.escape(title)} illustration">{art(accent)}</svg></div>
<div>
<p class="now">You are talking to</p>
<h2>{role_emoji} {html.escape(title)}</h2>
<p class="tag">{html.escape(tagline)}</p>
<span class="chip">{provider} · {html.escape(model)}</span>
</div>
</div>
"""
# collapse whitespace so Markdown never treats indented lines or blank lines as code
st.markdown(re.sub(r"\s+", " ", stage_html), unsafe_allow_html=True)

# -----------------------
# Conversation memory
# -----------------------
if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"], avatar="🧑" if msg["role"] == "user" else role_emoji):
        st.markdown(msg["content"])

if not st.session_state.messages:
    st.info(f"Ask {role_name} anything, for example: How can I express sadness in movement?")

# -----------------------
# New question
# -----------------------
question = st.chat_input("Type your question or idea...")
if question:
    api_key = get_key(provider)
    if not api_key:
        st.warning(f"Please enter your {provider} API key in the sidebar.")
        st.stop()

    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user", avatar="🧑"):
        st.markdown(question)

    system = role_text
    if language != "Same as my question":
        system += f" Always answer in {'English' if language == 'English' else 'Korean'}."

    with st.chat_message("assistant", avatar=role_emoji):
        try:
            stream = STREAMERS[provider](
                api_key, model, system, st.session_state.messages, max_tokens, temperature
            )
            answer = st.write_stream(stream)
            st.session_state.messages.append({"role": "assistant", "content": answer})
        except Exception as e:
            st.session_state.messages.pop()   # remove the question that got no answer
            st.error(f"Error: {e}")

# -----------------------
# Download the conversation
# -----------------------
if st.session_state.messages:
    transcript = "\n\n".join(
        f"{'You' if m['role'] == 'user' else role_name}: {m['content']}"
        for m in st.session_state.messages
    )
    st.sidebar.download_button("💾 Download conversation", transcript, file_name="conversation.txt")

st.markdown("---")
st.markdown(
    "<p class='foot'>Built for 'Art &amp; Advanced Big Data' • Prof. Jahwan Koo (SKKU)</p>",
    unsafe_allow_html=True,
)
