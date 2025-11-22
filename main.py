import streamlit as st
import google.generativeai as genai
import json
import pandas as pd
from datetime import datetime, timedelta
import random
import io


# Page config
st.set_page_config(
    page_title="Task & Workflow Automation Agent",
    page_icon="🤖",
    layout="wide"
)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "workflows" not in st.session_state:
    st.session_state.workflows = []
if "task_history" not in st.session_state:
    st.session_state.task_history = []
if "uploaded_df" not in st.session_state:
    st.session_state.uploaded_df = None
if "uploaded_filename" not in st.session_state:
    st.session_state.uploaded_filename = None


# Configure Gemini
def configure_gemini(api_key):
    genai.configure(api_key=api_key)
    return genai.GenerativeModel('gemini-1.5-flash')


# File reading function
def read_uploaded_file(uploaded_file):
    try:
        file_name = uploaded_file.name.lower()

        if file_name.endswith('.csv'):
            try:
                df = pd.read_csv(uploaded_file)
            except UnicodeDecodeError:
                uploaded_file.seek(0)
                df = pd.read_csv(uploaded_file, encoding='latin-1')

        elif file_name.endswith('.xlsx'):
            df = pd.read_excel(uploaded_file, engine='openpyxl')

        elif file_name.endswith('.xls'):
            df = pd.read_excel(uploaded_file, engine='xlrd')

        else:
            return None, "Unsupported file format. Please upload CSV, XLSX, or XLS."

        return df, None

    except Exception as e:
        return None, f"Error reading file: {str(e)}"


# TASK EXECUTION FUNCTIONS
class AutomationAgent:
    def __init__(self, model):
        self.model = model

    def parse_intent(self, user_input):
        prompt = f"""Analyze this automation request and extract structured information.
Request: "{user_input}"

Return a JSON object with:
- task_type: one of [sheet_update, report_generation, presentation_creation, hr_workflow, sales_task, finance_task]
- action: specific action to perform
- parameters: dict of relevant parameters
- description: brief description of what will be done
"""

        response = self.model.generate_content(prompt)

        try:
            clean = response.text.strip().replace("```json", "").replace("```", "")
            return json.loads(clean)
        except:
            return {
                "task_type": "general",
                "action": "process",
                "parameters": {},
                "description": user_input
            }

    def execute_sheet_update(self, params, uploaded_df=None):
        if uploaded_df is not None:
            df = uploaded_df.copy()
            df["Last_Updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            return df, f"Processed uploaded sheet: {len(df)} rows, {len(df.columns)} columns"

        rows = params.get("rows", random.randint(10, 100))
        cols = params.get("columns", ["Name", "Value", "Status", "Date"])

        data = {
            col: [
                f"Data_{i}" if col != "Date" else datetime.now().strftime("%Y-%m-%d")
                for i in range(rows)
            ]
            for col in cols
        }

        df = pd.DataFrame(data)
        return df, f"Generated {rows} rows across {len(cols)} columns"

    def generate_report(self, params):
        report_type = params.get("type", "summary")
        prompt = f"""Generate a professional {report_type} report with sections:
1. Executive Summary
2. Key Metrics (with sample numbers)
3. Analysis
4. Recommendations
5. Next Steps

Format in markdown.
"""

        response = self.model.generate_content(prompt)
        return response.text

    def create_presentation_outline(self, params):
        topic = params.get("topic", "Business Review")
        slides = params.get("slides", 10)

        prompt = f"""Create a {slides}-slide presentation outline on: {topic}
For each slide include:
- Slide title
- 3–4 bullet points
- Speaker notes (1–2 sentences)
"""

        response = self.model.generate_content(prompt)
        return response.text

    def hr_workflow(self, params):
        workflow_type = params.get("workflow", "onboarding")

        workflows = {
            "onboarding": [
                "Create employee profile",
                "Generate welcome email",
                "Setup system accounts",
                "Schedule orientation",
                "Assign mentor",
                "Create training plan"
            ],
            "offboarding": [
                "Initiate exit process",
                "Schedule exit interview",
                "Revoke system access",
                "Process final payroll",
                "Transfer knowledge docs",
                "Update org chart"
            ],
            "leave_request": [
                "Validate leave balance",
                "Check team coverage",
                "Notify manager",
                "Update calendar",
                "Adjust workload"
            ]
        }

        return workflows.get(workflow_type, workflows["onboarding"])

    def sales_automation(self, params):
        data = pd.DataFrame({
            "Lead": [f"Company_{i}" for i in range(1, 11)],
            "Stage": random.choices(["Prospect", "Qualified", "Proposal", "Negotiation", "Closed"], k=10),
            "Value": [random.randint(10000, 100000) for _ in range(10)],
            "Probability": [random.randint(10, 90) for _ in range(10)],
            "Expected Close": [
                (datetime.now() + timedelta(days=random.randint(7, 90))).strftime("%Y-%m-%d")
                for _ in range(10)
            ]
        })
        return data

    def finance_task(self, params):
        df = pd.DataFrame({
            "Category": ["Travel", "Software", "Marketing", "Office", "Utilities"],
            "Budget": [50000, 30000, 75000, 20000, 15000],
            "Actual": [
                random.randint(40000, 55000),
                random.randint(25000, 35000),
                random.randint(60000, 80000),
                random.randint(15000, 25000),
                random.randint(12000, 18000)
            ]
        })

        df["Variance"] = df["Budget"] - df["Actual"]
        return df


# ---- SIDEBAR ----
with st.sidebar:
    st.title("⚙️ Configuration")
    api_key = st.text_input("Google Gemini API Key", type="password")

    st.divider()
    st.subheader("📋 Recent Tasks")
    if st.session_state.task_history:
        for t in st.session_state.task_history[-5:]:
            st.caption(f"✔ {t['name']} — {t['time']}")
    else:
        st.caption("No tasks yet")


# ---- MAIN UI ----
st.title("🤖 Task & Workflow Automation Agent")
st.caption("Automate HR • Sales • Finance • Reporting • Sheets")


# ---------- FILE UPLOADER ----------
st.subheader("📁 Upload Spreadsheet")

uploaded_file = st.file_uploader(
    "Upload CSV or Excel",
    type=["csv", "xlsx", "xls"]
)

if uploaded_file:
    if st.session_state.uploaded_filename != uploaded_file.name:
        df, error = read_uploaded_file(uploaded_file)
        if error:
            st.error(error)
        else:
            st.session_state.uploaded_df = df
            st.session_state.uploaded_filename = uploaded_file.name
            st.success(f"Loaded: {uploaded_file.name}")

    if st.session_state.uploaded_df is not None:
        df = st.session_state.uploaded_df

        st.dataframe(df.head(), use_container_width=True)


# ---------- CHAT INTERFACE ----------
st.subheader("💬 Automation Chat")

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

user_input = st.chat_input("Describe a task...")

if user_input:
    if not api_key:
        st.error("Enter Gemini API Key first!")
    else:
        st.session_state.messages.append({"role": "user", "content": user_input})

        with st.chat_message("assistant"):
            with st.spinner("Processing..."):
                model = configure_gemini(api_key)
                agent = AutomationAgent(model)

                intent = agent.parse_intent(user_input)

                st.markdown(f"**Task:** {intent['task_type']}")
                st.markdown(f"**Action:** {intent['description']}")

                result = ""
                data = None

                if intent["task_type"] == "sheet_update":
                    df, msg = agent.execute_sheet_update(intent["parameters"], st.session_state.uploaded_df)
                    st.dataframe(df)
                    result = msg

                elif intent["task_type"] == "report_generation":
                    result = agent.generate_report(intent["parameters"])
                    st.markdown(result)

                elif intent["task_type"] == "presentation_creation":
                    result = agent.create_presentation_outline(intent["parameters"])
                    st.markdown(result)

                elif intent["task_type"] == "hr_workflow":
                    steps = agent.hr_workflow(intent["parameters"])
                    result = "\n".join([f"✔ {s}" for s in steps])
                    st.markdown(result)

                elif intent["task_type"] == "sales_task":
                    df = agent.sales_automation(intent["parameters"])
                    st.dataframe(df)
                    result = "Generated Sales Pipeline"

                elif intent["task_type"] == "finance_task":
                    df = agent.finance_task(intent["parameters"])
                    st.dataframe(df)
                    result = "Generated Finance Report"

                else:
                    resp = model.generate_content(user_input)
                    result = resp.text
                    st.markdown(result)

                st.session_state.messages.append({"role": "assistant", "content": result})
                st.session_state.task_history.append({
                    "name": intent["task_type"],
                    "time": datetime.now().strftime("%H:%M")
                })


# FOOTER
st.divider()
st.caption("🤖 Powered by Google Gemini + Streamlit")

