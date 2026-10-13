# Creative Role Studio (extended chatbot)
# Extensions on top of the Step 3 and Step 5 apps:
#   1. Conversation memory (chat interface)
#   2. Streaming answers (text appears as it is written)
#   3. Two providers in one app: OpenAI and Claude
#   4. Settings: model, answer length, creativity, language, and your own custom role
#   5. Download the conversation

import streamlit as st
import anthropic
from openai import OpenAI

st.set_page_config(page_title="🎭 Creative Role Studio", layout="wide")
st.title("🎭 Creative Role Studio")
st.caption("Arts and Advanced Big Data | Chat with a creative role, powered by OpenAI or Claude")

# -----------------------
# Roles (system prompts)
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
# Sidebar
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
# Conversation memory
# -----------------------
if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
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
    with st.chat_message("user"):
        st.markdown(question)

    system = role_text
    if language != "Same as my question":
        system += f" Always answer in {'English' if language == 'English' else 'Korean'}."

    with st.chat_message("assistant"):
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
st.caption("Built for 'Art & Advanced Big Data' • Prof. Jahwan Koo (SKKU)")
