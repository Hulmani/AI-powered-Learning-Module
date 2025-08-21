import os
import streamlit as st
from openai import OpenAI


# ---------- Secrets & Client Setup ----------
XAI_API_KEY = st.secrets.get("XAI_API_KEY", os.getenv("XAI_API_KEY", ""))
if not XAI_API_KEY:
    st.warning("Add your Grok API key in Settings → Secrets (key: XAI_API_KEY) or set the environment variable XAI_API_KEY.\nApp will run in demo mode without making API calls.")

BASE_URL = "https://api.groq.com/openai/v1"
client = None
if XAI_API_KEY:
    client = OpenAI(api_key=XAI_API_KEY, base_url=BASE_URL)
    
SCENARIOS = {
    "Collections — Late Fee Dispute": {
        "customer_seed": (
            "You are an upset customer who received a late payment fee on a small loan. "
            "You believe the charge is unfair and you are worried about your credit. "
            "Your goal is to push back firmly but realistically. Provide short, natural replies."
        ),
        "context": "Context: customer is 18 days past due on a $600 loan; fee is $25; store is Cash 4 You."
    },
    "Retail — Refund Request": {
        "customer_seed": (
            "You are a frustrated retail customer who wants a refund for a defective item. "
            "You feel you've already explained this too many times. "
            "Your goal is to get a clear resolution quickly."
        ),
        "context": "Context: product failed within 10 days; receipt on file; standard 14-day return policy."
    },
    "Lending — Concern About Terms": {
        "customer_seed": (
            "You are a nervous loan applicant uncertain about interest rates and repayment terms. "
            "Your goal is to understand costs and avoid hidden fees."
        ),
        "context": "Context: small installment loan; rate and term must be explained in plain language."
    },
}

# ---------- Config ----------
st.set_page_config(page_title="AI Roleplay Trainer (Cash 4 You)", page_icon="🎯", layout="centered")
st.title("🎯 AI Roleplay Trainer")
st.caption("Practice real conversations. Get adaptive coaching. (Powered by Grok via OpenAI-compatible API)")
st.sidebar.title("🎛️ Scenario & Settings")
scenario_key = st.sidebar.selectbox("Choose a scenario", list(SCENARIOS.keys()))
turn_limit = st.sidebar.slider("Number of assistant replies before feedback", min_value=3, max_value=8, value=5, step=1)
model_name = st.sidebar.selectbox("Model", ["llama-3.1-8b-instant", "llama-3.3-70b-versatile", "openai/gpt-oss-120b"], index=0)
st.markdown("---")
st.markdown(
    "Built for the Cash 4 You Agentic Learning Engineer application. "
    "This demo constrains the model to stay in character and produce coaching feedback aligned to KPIs."
)

if "messages" not in st.session_state:
    st.session_state.messages = []
if "assistant_count" not in st.session_state:
    st.session_state.assistant_count = 0
if "feedback_given" not in st.session_state:
    st.session_state.feedback_given = False

    



def build_system_prompt(scenario_key: str, turns_limit: int) -> str:
    s = SCENARIOS[scenario_key]
    return f"""
You are a training simulator for Cash 4 You. Act ONLY as the CUSTOMER in the roleplay.
- Stay strictly in character; do NOT provide general knowledge or step out of role.
- Keep responses brief and conversational (1–3 sentences).
- Mirror the user's tone within professional limits.
- After exactly {turns_limit} assistant messages have been sent in this session, STOP the roleplay and provide a COACHING SUMMARY.
- In the summary, evaluate the employee's performance with a numeric score (0–10) on:
  1) Empathy, 2) Professionalism, 3) Problem-Solving/Resolution.
- Provide 3 specific, actionable improvement tips tailored to what happened.
- IfSCENARIOS the user asks out-of-scope questions, politely redirect back to the scenario.
Scenario: {scenario_key}
Customer background: {s["customer_seed"]}
{ s["context"] }
    """.strip()

def call_grok(messages, model="llama-3.1-8b-instant"):
    if client is None:
        return {"role": "assistant", "content": "([Demo mode] Please add your XAI_API_KEY to enable real conversations.)"}
    resp = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0.6,
        max_tokens=350,
    )
    return resp.choices[0].message


if st.sidebar.button("🔄 Reset Conversation"):
    st.session_state.messages = []
    st.session_state.assistant_count = 0
    st.session_state.feedback_given = False
    st.experimental_rerun()


if not any(m for m in st.session_state.messages if m["role"] == "system"):
    st.session_state.messages.insert(0, {"role": "system", "content": build_system_prompt(scenario_key, turn_limit)})

chat_container = st.container()
with chat_container:
    for m in st.session_state.messages:
        if m["role"] == "user":
            with st.chat_message("user"):
                st.markdown(m["content"])
        elif m["role"] == "assistant":
            with st.chat_message("assistant"):
                st.markdown(m["content"])

# Display all messages in the chat

user_input = st.chat_input("Type your response to the customer...")
if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    if st.session_state.assistant_count >= turn_limit and not st.session_state.feedback_given:
        st.session_state.messages.append(
            {"role": "user",
             "content": "Please provide the coaching summary now based on the conversation so far."}
        )
        with st.spinner("AI is typing..."):
            msg = call_grok(st.session_state.messages, model=model_name)
        print("Message: ",msg)
        st.session_state.messages.append({"role": "assistant", "content": msg.content})
        st.session_state.feedback_given = True
    else:
        with st.spinner("AI is typing..."):
            msg = call_grok(st.session_state.messages, model=model_name)
        print("Message: ",msg)
        st.session_state.messages.append({"role": "assistant", "content": msg.content})
        st.session_state.assistant_count += 1
        print("Assistant count: ",st.session_state.assistant_count)
st.rerun()

if not st.session_state.feedback_given and st.session_state.assistant_count >= 2:
    if st.button("🧠 Give Feedback Now"):
        st.session_state.messages.append(
            {"role": "user",
             "content": "Stop the roleplay and provide the coaching summary now."}
        )
        msg = call_grok(st.session_state.messages, model=model_name)
        st.session_state.messages.append({"role": "assistant", "content": msg.content})
        st.session_state.feedback_given = True
        st.experimental_rerun()


