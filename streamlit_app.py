import os
import json
import streamlit as st
from google import genai
from dotenv import load_dotenv
from app.database import init_db, fetch_all_opportunities
from app.scraper import sync_feeds

load_dotenv()

st.set_page_config(page_title="Digest | Tech Student Scout", page_icon="⚡", layout="wide")
init_db()

@st.cache_resource
def get_client():
    key = os.getenv("GEMINI_API_KEY")
    return genai.Client(api_key=key) if key else None

client = get_client()

CHAT_SYSTEM_PROMPT = """
You are Digest AI, an expert tech scout and career mentor for engineering and computer science students.
Base primary recommendations strictly on the provided live opportunities database context.
When highlighting an opportunity, always include:
- Program / Role Title and Company or Organization
- Target Batch / Eligibility
- Application Deadline / Status
- Direct Application Link as a clickable Markdown link, using the exact apply_url from the database
For general career questions with no matching active records, recommend only verified avenues such as
Google Summer of Code, MLSA, LFX Mentorship, Outreachy, or MLH Fellowship. Do not fabricate deadlines,
availability, eligibility, or links. Say when the database has no matching record. Keep answers encouraging,
concise, structured, and student-friendly with bold text and bullets.
"""

with st.sidebar:
    st.title("⚡ Digest")
    selected_category = st.selectbox("Category", ["All", "Internship", "Student Program", "Fellowship", "Tech Update", "Hackathon"])
    search_query = st.text_input("🔍 Search")
    if st.button("🔄 Sync Live Feeds", use_container_width=True, type="primary"):
        with st.spinner("Syncing feeds..."):
            inserted = sync_feeds()
            st.success(f"Added {inserted} new item(s).")
            st.rerun()

tab_cards, tab_chat = st.tabs(["📋 Opportunities Hub", "💬 Ask Digest AI"])

with tab_cards:
    cat_filter = None if selected_category == "All" else selected_category
    data = fetch_all_opportunities(category=cat_filter)
    if search_query and data:
        query = search_query.casefold()
        data = [d for d in data if query in " ".join(str(value) for value in d.values()).casefold()]
    
    if not data:
        st.info("No records yet. Click 'Sync Live Feeds' in the sidebar.")
    else:
        cols = st.columns(2)
        for idx, item in enumerate(data):
            with cols[idx % 2]:
                with st.container(border=True):
                    st.caption(f"{item.get('organization')} • {item.get('category')}")
                    st.markdown(f"### {item.get('title')}")
                    st.write(item.get("summary"))
                    st.caption(f"🎯 **Target:** {item.get('eligibility')} | ⏳ **Deadline:** {item.get('deadline')}")
                    url = item.get("apply_url") or "#"
                    st.link_button("View & Apply ↗", url=url, use_container_width=True)

with tab_chat:
    st.subheader("🤖 Ask Digest AI")
    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "assistant", "content": "Ask me anything about current opportunities or updates!"}]
    
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
    
    if query := st.chat_input("Ask a question..."):
        st.session_state.messages.append({"role": "user", "content": query})
        with st.chat_message("user"):
            st.markdown(query)
        
        with st.chat_message("assistant"):
            if not client:
                st.error("GEMINI_API_KEY missing.")
            else:
                opps = json.dumps(fetch_all_opportunities(), indent=2)
                prompt = f"{CHAT_SYSTEM_PROMPT}\n\nLIVE OPPORTUNITIES DATABASE:\n{opps}\n\nUSER QUESTION:\n{query}"
                try:
                    res = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
                    answer = res.text or "I couldn't generate an answer from the current opportunities."
                except Exception as error:
                    answer = f"I couldn't reach Gemini right now: {error}"
                st.markdown(answer)
                st.session_state.messages.append({"role": "assistant", "content": answer})