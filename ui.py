"""Research Radar frontend. Calls the FastAPI backend and renders the digest in
the style of Great Question's AI Repository: a summary, tagged highlights, and
linked quotes that expand to the source study.

    streamlit run ui.py
"""

import os

import requests
import streamlit as st

API_URL = os.environ.get("RADAR_API", "http://localhost:8000")

STANCE_BADGE = {
    "supports": "🟢 Supports your assumption",
    "contradicts": "🔴 Contradicts your assumption",
    "neutral": "⚪ Neutral / adds nuance",
}

st.set_page_config(page_title="Research Radar", layout="centered")
st.title("Research Surface Tool")
st.caption("Push-based companion that surfaces relevant past research while you draft — "
           "even when it's filed under different terminology.")

page = st.text_input("Notion page URL or id",
                     placeholder="https://www.notion.so/your-draft-page")
st.caption("First use opens a one-time Notion sign-in in your browser.")

if st.button("🔍 Scan my draft", type="primary", use_container_width=True):
    with st.spinner("Reading the draft and scanning past research…"):
        resp = requests.post(f"{API_URL}/scan", json={"notion_page": page}, timeout=300)
        if not resp.ok:
            st.error(f"API error {resp.status_code}: {resp.text}")
            st.stop()
        digest = resp.json()

    intent = digest["intent"]
    st.divider()
    st.subheader("What you're drafting")
    st.write("**Topics:** " + ", ".join(intent["topics"]))
    st.write("**Proposed feature:** " + intent["proposed_feature"])
    st.write("**Assumptions:** " + "; ".join(intent["assumptions"]))

    st.divider()
    if digest["gap"]:
        st.subheader("🕳️ Research gap")
        st.warning("No past research clears the relevance bar for this draft.")
        st.write(digest["suggestion"])
    else:
        st.subheader("Related research")
        for m in digest["matches"]:
            st.markdown(f"### [{m['title']}]({m['url']})")
            st.caption(f"{m['team']} · {m['date']} · relevance {m['relevance']}/10")
            st.write(m["relevance_summary"])
            st.write(STANCE_BADGE[m["stance"]] + " — " + m["stance_note"])
            for flag in m["flags"]:
                st.warning("⚠️ " + flag)
            quote = m["quote"]
            with st.expander(f"Source quote — {quote['speaker']}, {quote['timestamp_or_section']}"):
                st.markdown(f"> {quote['text']}")
                st.markdown(f"[Open source study ↗]({m['url']})")
            st.divider()
