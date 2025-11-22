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
    """Read uploaded file and return DataFrame"""
    try:
        file_name = uploaded_file.name.lower()
        
        if file_name.endswith('.csv'):
            # Try different encodings
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

# Task execution functions
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
        
       
        
        response = self.model.generate_content(prompt)
        try:
            clean_text = response.text.strip().replace("```json", "").replace("```", "")
            return json.loads(clean_text)
        except:
            return {"task_type": "general", "action": "process", "parameters": {}, "description": user_input}
    
    def execute_sheet_update(self, params, uploaded_df=None):
        if uploaded_df is not None:
            df = uploaded_df.copy()
            df['Last_Updated'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            return df, f"Processed uploaded sheet: {len(df)} rows, {len(df.columns)} columns"
        
        rows = params.get("rows", random.randint(10, 100))
        cols = params.get("columns", ["Name", "Value", "Status", "Date"])
        
        data = {
            col: [f"Data_{i}" if col != "Date" else datetime.now().strftime("%Y-%m-%d") 
                  for i in range(rows)] for col in cols
        }
        df = pd.DataFrame(data)
        return df, f"Generated {rows} rows across {len(cols)} columns"
    
    def generate_report(self, params):
        report_type = params.get("type", "summary")
        prompt = f"""Generate a professional {report_type} report with the following sections:
        1. Executive Summary
        2. Key Metrics (with sample numbers)
        3. Analysis
        4. Recommendations
        5. Next Steps
        
        Make it realistic and professional. Use markdown formatting."""
        
        response = self.model.generate_content(prompt)
        return response.text
    
    def create_presentation_outline(self, params):
        topic = params.get("topic", "Business Review")
        slides = params.get("slides", 10)
        
        prompt = f"""Create a {slides}-slide presentation outline for: {topic}
        
        For each slide provide:
        - Slide title
        - 3-4 bullet points
        - Speaker notes (1-2 sentences)
        
        Format as a structured outline with clear slide numbers."""
        
        response = self.model.generate_content(prompt)
        return response.text
    
    def hr_workflow(self, params):
        workflow_type = params.get("workflow", "onboarding")
        
        workflows = {
            "onboarding": [
                "✅ Create employee profile",
                "✅ Generate welcome email",
                "✅ Setup system accounts",
                "✅ Schedule orientation",
                "✅ Assign mentor",
                "✅ Create training plan"
            ],
            "offboarding": [
                "✅ Initiate exit process",
                "✅ Schedule exit interview",
                "✅ Revoke system access",
                "✅ Process final payroll",
                "✅ Transfer knowledge docs",
                "✅ Update org chart"
            ],
            "leave_request": [
                "✅ Validate leave balance",
                "✅ Check team coverage",
                "✅ Notify manager",
                "✅ Update calendar",
                "✅ Adjust workload"
            ]
        }
        
        return workflows.get(workflow_type, workflows["onboarding"])
    
    def sales_automation(self, params):
        pipeline_data = pd.DataFrame({
            "Lead": [f"Company_{i}" for i in range(1, 11)],
            "Stage": random.choices(["Prospect", "Qualified", "Proposal", "Negotiation", "Closed"], k=10),
            "Value": [random.randint(10000, 100000) for _ in range(10)],
            "Probability": [random.randint(10, 90) for _ in range(10)],
            "Expected Close": [(datetime.now() + timedelta(days=random.randint(7, 90))).strftime("%Y-%m-%d") for _ in range(10)]
        })
        return pipeline_data
    
    def finance_task(self, params):
        expense_data = pd.DataFrame({
            "Category": ["Travel", "Software", "Marketing", "Office", "Utilities"],
            "Budget": [50000, 30000, 75000, 20000, 15000],
            "Actual": [random.randint(40000, 55000), random.randint(25000, 35000), 
                      random.randint(60000, 80000), random.randint(15000, 25000),
                      random.randint(12000, 18000)],
            "Variance": [0, 0, 0, 0, 0]
        })
        expense_data["Variance"] = expense_data["Budget"] - expense_data["Actual"]
        return expense_data

# Sidebar
with st.sidebar:
    st.title("⚙️ Configuration")
    api_key = st.text_input("Google Gemini API Key", type="password", key="api_key_input")
    
    st.divider()
    st.subheader("🔧 Automation Modules")
    
    modules = {
        "📊 Sheets & Data": st.checkbox("Sheets & Data", value=True),
        "📈 Reports": st.checkbox("Reports", value=True),
        "📑 Presentations": st.checkbox("Presentations", value=True),
        "👥 HR Workflows": st.checkbox("HR Workflows", value=True),
        "💰 Sales Automation": st.checkbox("Sales Automation", value=True),
        "💵 Finance Tasks": st.checkbox("Finance Tasks", value=True),
    }
    
    st.divider()
    st.subheader("📋 Recent Tasks")
    if st.session_state.task_history:
        for task in st.session_state.task_history[-5:]:
            st.caption(f"✅ {task['name']} - {task['time']}")
    else:
        st.caption("No tasks yet")

# Main UI
st.title("🤖 Task & Workflow Automation Agent")
st.caption("Automate repetitive tasks across HR, Sales, Finance, and more")

# ============ FILE UPLOAD SECTION ============
st.subheader("📁 Upload Spreadsheet")

uploaded_file = st.file_uploader(
    "Choose a file (CSV, XLSX, XLS)",
    type=["csv", "xlsx", "xls"],
    key="file_uploader",
    help="Upload your spreadsheet to process, analyze, or update"
)

# Process uploaded file
if uploaded_file is not None:
    # Check if it's a new file
    if st.session_state.uploaded_filename != uploaded_file.name:
        with st.spinner("Reading file..."):
            df, error = read_uploaded_file(uploaded_file)
            
            if error:
                st.error(error)
            elif df is not None:
                st.session_state.uploaded_df = df
                st.session_state.uploaded_filename = uploaded_file.name
                st.success(f"✅ File loaded: **{uploaded_file.name}**")
    
    # Display uploaded data
    if st.session_state.uploaded_df is not None:
        df = st.session_state.uploaded_df
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Rows", len(df))
        col2.metric("Columns", len(df.columns))
        col3.metric("File", st.session_state.uploaded_filename)
        
        with st.expander("📊 Preview Data (First 10 Rows)", expanded=True):
            st.dataframe(df.head(10), use_container_width=True)
        
        with st.expander("📋 Column Information"):
            col_info = pd.DataFrame({
                'Column': df.columns,
                'Data Type': df.dtypes.astype(str).values,
                'Non-Null Count': df.count().values,
                'Null Count': df.isnull().sum().values
            })
            st.dataframe(col_info, use_container_width=True)
        
        # Sheet Operations
        st.markdown("### 🔧 Quick Sheet Operations")
        op_col1, op_col2, op_col3 = st.columns(3)
        
        with op_col1:
            if st.button("📥 Download as CSV", use_container_width=True):
                csv = df.to_csv(index=False)
                st.download_button(
                    "Click to Download CSV",
                    csv,
                    f"processed_{st.session_state.uploaded_filename.rsplit('.', 1)[0]}.csv",
                    "text/csv",
                    key="download_csv"
                )
        
        with op_col2:
            if st.button("📥 Download as Excel", use_container_width=True):
                buffer = io.BytesIO()
                with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                    df.to_excel(writer, index=False)
                st.download_button(
                    "Click to Download Excel",
                    buffer.getvalue(),
                    f"processed_{st.session_state.uploaded_filename.rsplit('.', 1)[0]}.xlsx",
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key="download_excel"
                )
        
        with op_col3:
            if st.button("🗑️ Clear Uploaded File", use_container_width=True):
                st.session_state.uploaded_df = None
                st.session_state.uploaded_filename = None
                st.rerun()

st.divider()

# ============ QUICK ACTIONS ============
st.subheader("⚡ Quick Actions")
col1, col2, col3, col4 = st.columns(4)

quick_action = None
with col1:
    if st.button("📊 Update Sheet", use_container_width=True):
        quick_action = "Update my spreadsheet with latest data and add timestamp"
with col2:
    if st.button("📈 Generate Report", use_container_width=True):
        quick_action = "Generate a weekly performance report"
with col3:
    if st.button("👥 HR Onboarding", use_container_width=True):
        quick_action = "Start onboarding workflow for new employee"
with col4:
    if st.button("💰 Expense Report", use_container_width=True):
        quick_action = "Generate monthly expense report"

st.divider()

# ============ CHAT INTERFACE ============
st.subheader("💬 Automation Chat")

# Display chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if "data" in msg and msg["data"] is not None:
            st.dataframe(msg["data"], use_container_width=True)

# Get input
user_input = st.chat_input("Describe the task you want to automate...")

# Use quick action if clicked
if quick_action:
    user_input = quick_action

# Process input
if user_input:
    if not api_key:
        st.error("⚠️ Please enter your Google Gemini API Key in the sidebar")
    else:
        st.session_state.messages.append({"role": "user", "content": user_input})
        
        with st.chat_message("user"):
            st.markdown(user_input)
        
        with st.chat_message("assistant"):
            with st.spinner("🔄 Processing your request..."):
                try:
                    model = configure_gemini(api_key)
                    agent = AutomationAgent(model)
                    
                    intent = agent.parse_intent(user_input)
                    
                    st.markdown(f"**🎯 Detected Task:** {intent['task_type'].replace('_', ' ').title()}")
                    st.markdown(f"**📝 Action:** {intent['description']}")
                    st.markdown("---")
                    
                    response_content = ""
                    response_data = None
                    
                    if intent['task_type'] == 'sheet_update':
                        uploaded_df = st.session_state.uploaded_df
                        df, msg = agent.execute_sheet_update(intent['parameters'], uploaded_df)
                        response_content = f"✅ Sheet Update Complete!\n\n{msg}"
                        response_data = df
                        st.success(msg)
                        st.dataframe(df, use_container_width=True)
                        
                        # Download options
                        dl_col1, dl_col2 = st.columns(2)
                        with dl_col1:
                            csv = df.to_csv(index=False)
                            st.download_button("📥 Download CSV", csv, "updated_sheet.csv", "text/csv")
                        with dl_col2:
                            buffer = io.BytesIO()
                            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                                df.to_excel(writer, index=False)
                            st.download_button("📥 Download Excel", buffer.getvalue(), "updated_sheet.xlsx",
                                             "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
                        
                    elif intent['task_type'] == 'report_generation':
                        report = agent.generate_report(intent['parameters'])
                        response_content = f"✅ Report Generated!\n\n{report}"
                        st.markdown(report)
                        
                    elif intent['task_type'] == 'presentation_creation':
                        outline = agent.create_presentation_outline(intent['parameters'])
                        response_content = f"✅ Presentation Outline Created!\n\n{outline}"
                        st.markdown(outline)
                        
                    elif intent['task_type'] == 'hr_workflow':
                        steps = agent.hr_workflow(intent['parameters'])
                        response_content = "✅ HR Workflow Initiated!\n\n" + "\n".join(steps)
                        for step in steps:
                            st.markdown(step)
                            
                    elif intent['task_type'] == 'sales_task':
                        df = agent.sales_automation(intent['parameters'])
                        response_content = "✅ Sales Pipeline Updated!"
                        response_data = df
                        st.success(response_content)
                        st.dataframe(df, use_container_width=True)
                        
                    elif intent['task_type'] == 'finance_task':
                        df = agent.finance_task(intent['parameters'])
                        response_content = "✅ Finance Report Generated!"
                        response_data = df
                        st.success(response_content)
                        st.dataframe(df, use_container_width=True)
                        
                        total_variance = df["Variance"].sum()
                        status = "under budget ✅" if total_variance > 0 else "over budget ⚠️"
                        st.info(f"**Total Variance:** ${abs(total_variance):,.2f} {status}")
                        
                    else:
                        general_prompt = f"Help with this automation task: {user_input}"
                        response = model.generate_content(general_prompt)
                        response_content = response.text
                        st.markdown(response_content)
                    
                    msg_data = {"role": "assistant", "content": response_content}
                    if response_data is not None:
                        msg_data["data"] = response_data
                    st.session_state.messages.append(msg_data)
                    
                    st.session_state.task_history.append({
                        "name": intent['task_type'].replace('_', ' ').title(),
                        "time": datetime.now().strftime("%H:%M")
                    })
                    
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
                    st.info("Please check your API key and try again.")

# ============ WORKFLOW BUILDER ============
st.divider()
st.subheader("🔧 Workflow Builder")

with st.expander("Create Custom Workflow"):
    workflow_name = st.text_input("Workflow Name", key="wf_name")
    
    col1, col2 = st.columns(2)
    with col1:
        trigger = st.selectbox("Trigger", [
            "Manual",
            "Schedule (Daily)",
            "Schedule (Weekly)",
            "On Event",
            "API Webhook"
        ], key="wf_trigger")
    with col2:
        category = st.selectbox("Category", [
            "HR", "Sales", "Finance", "Operations", "Custom"
        ], key="wf_category")
    
    steps = st.text_area("Workflow Steps (one per line)", 
                         placeholder="Step 1: Fetch data from CRM\nStep 2: Process and validate\nStep 3: Update spreadsheet",
                         key="wf_steps")
    
    if st.button("💾 Save Workflow", key="save_wf"):
        if workflow_name and steps:
            workflow = {
                "name": workflow_name,
                "trigger": trigger,
                "category": category,
                "steps": steps.split("\n"),
                "created": datetime.now().strftime("%Y-%m-%d %H:%M")
            }
            st.session_state.workflows.append(workflow)
            st.success(f"✅ Workflow '{workflow_name}' saved!")
        else:
            st.warning("Please enter workflow name and steps")

# Display saved workflows
if st.session_state.workflows:
    st.subheader("📚 Saved Workflows")
    for i, wf in enumerate(st.session_state.workflows):
        with st.expander(f"🔄 {wf['name']} ({wf['category']})"):
            st.markdown(f"**Trigger:** {wf['trigger']}")
            st.markdown("**Steps:**")
            for step in wf['steps']:
                if step.strip():
                    st.markdown(f"  • {step}")
            if st.button(f"▶️ Run Workflow", key=f"run_wf_{i}"):
                st.info(f"Executing workflow: {wf['name']}...")

# Footer
st.divider()
st.caption("🤖 Powered by Google Gemini AI | Built with Streamlit")
