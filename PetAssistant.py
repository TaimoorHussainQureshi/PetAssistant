import os
import streamlit as st
from agents import Agent, Runner, function_tool, set_tracing_disabled
import nest_asyncio

nest_asyncio.apply()
set_tracing_disabled(True)

# Load API key securely
os.environ["OPENAI_API_KEY"] = "openai api key"

# Dummy tool
@function_tool
def noop() -> None:
    return None

# Core questions
CORE_QS = [
    "What's your cat’s name?",
    "How would you describe your cat’s personality at home?",
    "Tell me about their feeding routine—any changes lately?",
    "Have you noticed any litter box issues or concerns?",
    "How does your cat behave around people—family or visitors?",
    "Do you have other pets? How do they get along?",
    "Are there situations that tend to stress your cat?",
    "Have there been changes in your cat’s energy or activity levels?",
    "Walk me through a typical day for your cat.",
    "Is there anything else you’d like me to share with the vet about your cat?"
]

instructions = (
    "You are a warm, conversational veterinary behavior assistant. "
    "If the user asks what you are or seems confused, explain that you're here to collect behavioral details about their cat for a veterinary visit. "
    "If they say something unrelated like 'I'm bored' or 'What is this?', gently let them know your role before starting the interview.\n\n"
    "When the user first says anything relevant—whether it's a greeting or a concern—start the structured interview naturally. "
    "Begin with this first core question (wording must be exact): "
    f"“{CORE_QS[0]}”\n\n"
    "When the user first says anything—whether it's a greeting or a concern—start the conversation naturally. "
    "You have 10 specific core questions to ask, shown below. You must ask each of these questions "
    "**in the exact order and with the exact wording provided**. Do not rephrase, shorten, or alter any of them. "
    "However, to sound natural, you may include a soft, friendly transition that leads into the question, based on the user’s prior response. "
    "Example: If the user shares their cat's name is Jamie, you could say, 'That’s a lovely name—Jamie! Now, how would you describe her personality at home?'. This is just for example its not you exactly resonse with these wordinds every time. "
    "After the user answers each core question, you *must* have to ask one intelligent, empathetic *follow-up question* related to what they said.(Don't forget this instruction.)"
    "Even in response if user respond core question with yes or no or don't know, still you asked exactly one follow-up question to extract usefull information. You must have to do this in order to become more interactive and sounds natural."
    "Please do not ask core questions along with follow-up question as one core question then follow-up question then in again core question not together."
    "Ask only **one** follow-up per core question. Then, smoothly continue to the next core question with a natural transition. "
    "Never mention or label a question as a core question or follow-up. Never number the questions. "
    "After all 10 core questions and their follow-ups are completed, provide a concise, one-paragraph clinical summary."
    "After providing summary ask gently anything else i can do or you want to share etc."
    "Then stay available to continue chatting naturally based on the previous conversation.\n\n"

    "Here are the 10 core questions (you must ask each one exactly as written with friendly tone, you may include a soft, friendly transition that leads into the question, based on the user’s prior response.):\n"
    "After the user answers each core question, you *must* have to ask one intelligent, empathetic *follow-up question* related to what they said like after asking cat name ask about age or anything else as follow up question.(Don't forget this instruction.)"
    f"Core Questions: “{CORE_QS}” Then follow this pattern:\n"

    "Important Note: *Please do not ask core questions along with follow-up question as one core question then follow-up question then in again core question not together.*"
)
# Agent initialization
agent = Agent(
    name="CatBehaviorInterviewer",
    instructions=instructions,
    tools=[noop],
    model="gpt-4.1"
)

# Session state setup
if "history" not in st.session_state:
    st.session_state.history = []
if "summary_given" not in st.session_state:
    st.session_state.summary_given = False

# Streamlit UI config
st.set_page_config(page_title="Pets Assistant", layout="centered")
st.title("🐾 Pets Assistant")

# Custom CSS
st.markdown("""
    <style>
.user-container {
    display: flex;
    justify-content: flex-end;
    align-items: center;
    margin: 0.3em 0;
}
.user-bubble {
    background-color: #262730;
    padding: 0.6em 1em;
    border-radius: 12px;
    max-width: 80%;
    color: white;
}
.user-avatar-emoji {
    background-color: #ff4b4b;
    color: black;
    width: 36px;
    height: 36px;
    font-size: 20px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 8px;  /* square with rounded corners */
    margin-left: 0.5em;
    font-weight: bold;
}
</style>
""", unsafe_allow_html=True)

# Display message history
for msg in st.session_state.history:
    if msg["role"] == "user":
        with st.container():
            st.markdown(
                f"""
                <div class="user-container">
                    <div class="user-bubble">{msg['content']}</div>
                    <div class="user-avatar-emoji">👤</div>
                </div>
                """,
                unsafe_allow_html=True
            )
    else:
        with st.chat_message("assistant"):
            st.markdown(msg["content"])

# Input
user_input = st.chat_input("Type your message...")

if user_input:
    st.session_state.history.append({"role": "user", "content": user_input})
    with st.container():
        st.markdown(
            f"""
            <div class="user-container">
                <div class="user-bubble">{user_input}</div>
                <div class="user-avatar-emoji">👤</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    # Get assistant reply
    res = Runner.run_sync(agent, st.session_state.history)
    reply = res.final_output.strip()
    st.session_state.history.append({"role": "assistant", "content": reply})

    with st.chat_message("assistant"):
        st.markdown(reply)

    # Trigger summary
    assistant_text = "".join(h["content"] for h in st.session_state.history if h["role"] == "assistant")
    if not st.session_state.summary_given and all(q in assistant_text for q in CORE_QS):
        st.session_state.history.append({"role": "user", "content": "Please provide a one-paragraph clinical summary."})
        summary = Runner.run_sync(agent, st.session_state.history).final_output.strip()
        st.session_state.history.append({"role": "assistant", "content": summary})
        with st.chat_message("assistant"):
            st.markdown(f"📋 **Clinical Summary:**\n\n{summary}")
        st.session_state.summary_given = True
