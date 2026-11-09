"""AI Content Generator (Streamlit) - single file.
Works with NO key (Offline) or Gemini / OpenAI."""
import requests
import streamlit as st

OFFLINE = "Offline (no key needed)"
GEMINI = "Google Gemini (free key)"
OPENAI = "OpenAI"

# ---- Prompt templates (used by Gemini / OpenAI) ----
TEMPLATES = {
    "Blog Post": ("Write a well-structured blog post (about 300 words) on '{topic}' in a {tone} tone. "
                  "Include a catchy title, a short intro, 3 sections with subheadings and a conclusion."),
    "Social Media Caption": ("Write 3 engaging social media captions about '{topic}' in a {tone} tone. "
                             "Keep each under 30 words and add 2-3 relevant hashtags."),
    "Summary": "Summarize the following text in a {tone} tone in 5 bullet points:\n{topic}",
}
TONES = ["Professional", "Casual", "Humorous", "Inspirational", "Formal"]

OPENERS = {
    "Professional": "In today's landscape, {t} has become a key area of focus.",
    "Casual": "Let's talk about {t} - it's more interesting than you'd think!",
    "Humorous": "Nobody asked, but here's everything about {t} anyway.",
    "Inspirational": "Every great journey begins with a single step, and {t} is yours.",
    "Formal": "This document presents a considered overview of {t}.",
}


def offline(ctype, tone, topic):
    """Template-based generation, works with no API key."""
    t = topic.strip()
    op = OPENERS[tone].format(t=t)
    if ctype == "Blog Post":
        return (f"# {t.title()}: What You Need to Know\n\n{op}\n\n"
                f"## Why {t} Matters\n{t.capitalize()} affects how people work, learn and make decisions every day.\n\n"
                f"## Key Ideas\nStart with the basics, build skills step by step, and apply what you learn to real problems.\n\n"
                f"## Getting Started\nPick one small goal related to {t}, set a timeline, and track your progress.\n\n"
                f"## Conclusion\nWith consistent effort, {t} can deliver real, lasting value.")
    if ctype == "Social Media Caption":
        tag = "#" + "".join(w.capitalize() for w in t.split()[:3])
        return "\n".join([f"1. {op} {tag} #Trending",
                          f"2. Big things start with {t}. Are you in? {tag} #Growth",
                          f"3. {t.capitalize()} - save this for later! {tag} #Learn"])
    sents = [s.strip() for s in t.replace("\n", " ").split(".") if s.strip()]
    return "\n".join(f"- {s}." for s in sents[:5]) or f"- {t}"


def refine_offline(text, instr):
    if "short" in instr.lower():
        lines = text.split("\n")
        return "\n".join(lines[: max(2, len(lines) // 2)])
    return text + f"\n\n(Refined: {instr})"


def gemini(prompt, key, model):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    r = requests.post(url, params={"key": key}, timeout=60,
                      json={"contents": [{"parts": [{"text": prompt}]}]})
    r.raise_for_status()
    return r.json()["candidates"][0]["content"]["parts"][0]["text"].strip()


def openai_chat(prompt, key, model):
    from openai import OpenAI
    r = OpenAI(api_key=key).chat.completions.create(
        model=model, messages=[{"role": "user", "content": prompt}], temperature=0.8)
    return r.choices[0].message.content.strip()


# ---------------- UI ----------------
st.set_page_config(page_title="AI Content Generator", page_icon="✍️")
st.title("✍️ AI Content Generator")

with st.sidebar:
    backend = st.selectbox("AI backend", [OFFLINE, GEMINI, OPENAI])
    key, model = "", ""
    if backend != OFFLINE:
        key = st.text_input("API key", type="password")
        model = st.text_input("Model", "gemini-2.0-flash" if backend == GEMINI else "gpt-4o-mini")

ctype = st.selectbox("Content type", list(TEMPLATES))
tone = st.selectbox("Tone", TONES)
topic = st.text_area("Topic / text", height=100)
refine = st.text_input("Refine instruction (optional, e.g. 'make it shorter')")


def run(use_refine=False):
    if not topic.strip():
        st.error("Please enter a topic.")
        return
    if backend != OFFLINE and not key.strip():
        st.error("Enter an API key in the sidebar, or choose Offline.")
        return
    prev = st.session_state.get("out")
    try:
        with st.spinner("Generating..."):
            if backend == OFFLINE:
                if use_refine and prev:
                    st.session_state["out"] = refine_offline(prev, refine)
                else:
                    st.session_state["out"] = offline(ctype, tone, topic)
                return
            prompt = TEMPLATES[ctype].format(topic=topic.strip(), tone=tone.lower())
            if use_refine and prev:
                prompt += f"\n\nPrevious draft:\n{prev}\n\nRefine it: {refine}"
            fn = gemini if backend == GEMINI else openai_chat
            st.session_state["out"] = fn(prompt, key.strip(), model.strip())
    except Exception as e:
        st.error(f"API error: {e}")


c1, c2 = st.columns(2)
if c1.button("Generate / Regenerate", type="primary"):
    run()
if c2.button("Refine last output"):
    run(use_refine=True)

if "out" in st.session_state:
    out = st.session_state["out"]
    st.markdown("### Output")
    st.write(out)
    st.caption(f"Words: {len(out.split())} | Characters: {len(out)}")
    st.code(out, language=None)  # copy icon at top-right