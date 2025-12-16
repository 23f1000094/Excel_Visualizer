import streamlit as st
import pandas as pd
import pygwalker as pyg
from pygwalker.api.streamlit import StreamlitRenderer

# --- Page Configuration ---
st.set_page_config(
    page_title="Excel Insight Wizard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Session State Initialization ---
# This acts as the memory for the 'Wizard' steps
if 'step' not in st.session_state:
    st.session_state.step = 1
if 'dataframes' not in st.session_state:
    st.session_state.dataframes = {}
if 'final_df' not in st.session_state:
    st.session_state.final_df = None

# --- Helper Functions ---
def move_to_step(step_number):
    st.session_state.step = step_number
    st.rerun()

def load_excel_file(uploaded_file):
    """Loads all sheets from the Excel file into session state."""
    try:
        xls = pd.ExcelFile(uploaded_file)
        # Load all sheets into a dictionary
        st.session_state.dataframes = {
            sheet: xls.parse(sheet) for sheet in xls.sheet_names
        }
        st.success(f"Successfully loaded {len(st.session_state.dataframes)} sheets!")
    except Exception as e:
        st.error(f"Error loading file: {e}")

# --- Step 1: Upload & Extract ---
def render_step1_upload():
    st.header("Step 1: Upload Your Data 📂")
    st.write("Upload an Excel file containing multiple sheets.")
    
    uploaded_file = st.file_uploader("Choose an Excel file", type=['xlsx', 'xls'])
    
    if uploaded_file:
        if not st.session_state.dataframes:
            load_excel_file(uploaded_file)
            
        if st.session_state.dataframes:
            st.write("### Preview Loaded Sheets:")
            tabs = st.tabs(list(st.session_state.dataframes.keys()))
            for i, (sheet_name, df) in enumerate(st.session_state.dataframes.items()):
                with tabs[i]:
                    st.dataframe(df.head(), use_container_width=True)
            
            st.button("Next: Build Relationships ➡️", on_click=move_to_step, args=(2,))

# --- Step 2: Relational Builder ---
def render_step2_relations():
    st.header("Step 2: Build Relational Tables 🔗")
    
    # 2a. Select Base Table
    sheet_names = list(st.session_state.dataframes.keys())
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Left Table (Base)")
        left_sheet = st.selectbox("Select Left Sheet", sheet_names, key='left_sheet')
        left_df = st.session_state.dataframes[left_sheet]
        st.write(f"Columns: {list(left_df.columns)}")

    with col2:
        st.subheader("Right Table (To Join)")
        right_sheet = st.selectbox("Select Right Sheet", [s for s in sheet_names if s != left_sheet], key='right_sheet')
        right_df = st.session_state.dataframes[right_sheet]
        st.write(f"Columns: {list(right_df.columns)}")

    # 2b. Join Configuration
    st.divider()
    c1, c2, c3 = st.columns(3)
    with c1:
        left_on = st.selectbox("Join Key (Left)", left_df.columns)
    with c2:
        right_on = st.selectbox("Join Key (Right)", right_df.columns)
    with c3:
        how = st.selectbox("Join Type", ["inner", "left", "right", "outer"])

    # 2c. Perform Merge
    if st.button("Merge Sheets"):
        try:
            merged_df = pd.merge(left_df, right_df, left_on=left_on, right_on=right_on, how=how)
            st.session_state.final_df = merged_df
            st.success("Tables merged successfully!")
            st.dataframe(merged_df.head(), use_container_width=True)
        except Exception as e:
            st.error(f"Merge failed: {e}")

    # Navigation
    st.divider()
    col_back, col_next = st.columns([1, 5])
    with col_back:
        st.button("⬅️ Back", on_click=move_to_step, args=(1,))
    with col_next:
        # Allow skipping merge if they just want to visualize one sheet
        if st.session_state.final_df is None:
            if st.button("Skip Merge & Use Base Sheet"):
                st.session_state.final_df = left_df
                move_to_step(3)
        else:
            st.button("Next: Visualize 📊", on_click=move_to_step, args=(3,))

# --- Step 3: Visualizer (PyGWalker) ---
def render_step3_visualize():
    st.header("Step 3: Visualizer Dashboard 🎨")
    st.info("Drag fields from the left sidebar to the X/Y axes to build charts.")
    
    if st.session_state.final_df is not None:
        # Calculate width dynamically or use full container
        renderer = StreamlitRenderer(st.session_state.final_df, spec="./gw_config.json", spec_io_mode="RW")
        renderer.explorer()
    else:
        st.warning("No data found. Please go back and select data.")

    st.divider()
    if st.button("⬅️ Start Over"):
        st.session_state.dataframes = {}
        st.session_state.final_df = None
        move_to_step(1)

# --- Main App Router ---
def main():
    st.title("Excel Sheet Visualizer Wizard 🧙‍♂️")
    
    # Progress Bar
    progress_map = {1: 33, 2: 66, 3: 100}
    st.progress(progress_map[st.session_state.step])

    if st.session_state.step == 1:
        render_step1_upload()
    elif st.session_state.step == 2:
        render_step2_relations()
    elif st.session_state.step == 3:
        render_step3_visualize()

if __name__ == "__main__":
    main()

