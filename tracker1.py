import streamlit as st
from datetime import datetime, timedelta
import pandas as pd
import os
import plotly.graph_objects as go
import plotly.express as px
import numpy as np

# File to store data
DATA_FILE = "tracker_data.csv"
HISTORY_FILE = "progress_history.csv"

# Initialize session state
if 'data' not in st.session_state:
    if os.path.exists(DATA_FILE):
        st.session_state.data = pd.read_csv(DATA_FILE)
        st.session_state.data['DueDate'] = pd.to_datetime(st.session_state.data['DueDate']).dt.date
        st.session_state.data['DateAdded'] = pd.to_datetime(st.session_state.data['DateAdded']).dt.date
        # Drop 'Completed' if it exists from old data
        if 'Completed' in st.session_state.data.columns:
            st.session_state.data = st.session_state.data.drop(columns=['Completed'])
    else:
        st.session_state.data = pd.DataFrame(columns=[
            'GoalID', 'GoalName', 'DueDate', 'Frequency', 'Progress', 'DateAdded', 'Week'
        ])
if 'history' not in st.session_state:
    if os.path.exists(HISTORY_FILE):
        st.session_state.history = pd.read_csv(HISTORY_FILE)
        # Fix: Convert 'Date' to datetime.date and ensure 'Change' column
        st.session_state.history['Date'] = pd.to_datetime(st.session_state.history['Date']).dt.date
        if 'Change' not in st.session_state.history.columns:
            st.session_state.history['Change'] = st.session_state.history['Percentage'].apply(
                lambda x: 0.01 if x == 100 else 0.005 if x == 50 else -0.01
            )
    else:
        st.session_state.history = pd.DataFrame(columns=['GoalID', 'GoalName', 'Date', 'Progress', 'Percentage', 'Change'])
if 'menu_open' not in st.session_state:
    st.session_state.menu_open = False
if 'selected_type' not in st.session_state:
    st.session_state.selected_type = None
if 'expanded_goal' not in st.session_state:
    st.session_state.expanded_goal = None

# Function to save data to CSV
def save_data():
    # Convert dates to strings for CSV storage
    data_to_save = st.session_state.data.copy()
    data_to_save['DueDate'] = data_to_save['DueDate'].astype(str)
    data_to_save['DateAdded'] = data_to_save['DateAdded'].astype(str)
    history_to_save = st.session_state.history.copy()
    history_to_save['Date'] = history_to_save['Date'].astype(str)
    data_to_save.to_csv(DATA_FILE, index=False)
    history_to_save.to_csv(HISTORY_FILE, index=False)

# Function to calculate the week number
def get_week_number(date):
    return date.isocalendar()[1]

# Function to calculate streak
def calculate_streak(history):
    if history.empty:
        return 0
    # Ensure 'Date' is datetime.date
    history = history.copy()
    history['Date'] = pd.to_datetime(history['Date']).dt.date
    history = history.sort_values('Date')
    streak = 0
    for change in history['Change'].iloc[::-1]:
        if change > 0:
            streak += 1
        else:
            break
    return streak

# Function to add a goal
def add_goal(goal_name, due_date, frequency):
    current_date = datetime.now().date()
    week = get_week_number(current_date)
    goal_id = f"G{len(st.session_state.data['GoalID'].unique()) + 1}" if not st.session_state.data.empty else "G1"
    new_item = {
        'GoalID': goal_id,
        'GoalName': goal_name,
        'DueDate': due_date,
        'Frequency': frequency,
        'Progress': 1.0,  # Start at 1 per Atomic Habits
        'DateAdded': current_date,
        'Week': week
    }
    st.session_state.data = pd.concat([st.session_state.data, pd.DataFrame([new_item])], ignore_index=True)
    # Initialize progress history
    st.session_state.history = pd.concat([st.session_state.history, pd.DataFrame({
        'GoalID': [goal_id],
        'GoalName': [goal_name],
        'Date': [current_date],
        'Progress': [1.0],
        'Percentage': [0.0],
        'Change': [0.0]
    })], ignore_index=True)
    save_data()

# Function to update progress using Atomic Habits
def update_goal(goal_id, goal_name, percentage):
    current_date = datetime.now().date()
    goal_data = st.session_state.data[st.session_state.data['GoalID'] == goal_id]
    current_progress = goal_data['Progress'].iloc[0]
    
    # Calculate new progress and change
    if percentage == 100:
        new_progress = current_progress * 1.01  # Full completion
        change = 0.01
    elif percentage == 50:
        new_progress = current_progress * 1.005  # Partial completion
        change = 0.005
    else:  # percentage == 0
        new_progress = current_progress / 1.01  # Skipped
        change = -0.01
    
    # Update data
    st.session_state.data.loc[st.session_state.data['GoalID'] == goal_id, 'Progress'] = new_progress
    
    # Update history
    history_entry = pd.DataFrame({
        'GoalID': [goal_id],
        'GoalName': [goal_name],
        'Date': [current_date],
        'Progress': [new_progress],
        'Percentage': [float(percentage)],
        'Change': [change]
    })
    st.session_state.history = pd.concat([st.session_state.history, history_entry], ignore_index=True)
    save_data()

# Custom CSS for simple, sleek UI with mountain background
st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%), url('https://www.transparenttextures.com/patterns/snow.png');
        background-blend-mode: overlay;
        color: #ffffff;
        font-family: 'Arial', sans-serif;
    }
    .hamburger {
        font-size: 28px;
        cursor: pointer;
        padding: 10px;
        background-color: #ff6b6b;
        color: white;
        border-radius: 50%;
        display: inline-block;
    }
    .card {
        background: rgba(255, 255, 255, 0.1);
        border-radius: 10px;
        padding: 15px;
        margin-bottom: 15px;
        backdrop-filter: blur(5px);
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }
    .stButton > button {
        background-color: #ff6b6b;
        color: white;
        border-radius: 10px;
        padding: 8px 16px;
        border: none;
    }
    h1, h2, h3 {
        color: #ffffff;
    }
    .motivation {
        font-style: italic;
        color: #4ecdc4;
        text-align: center;
        margin-top: 10px;
    }
    </style>
""", unsafe_allow_html=True)

# Streamlit app
st.title("🏋️‍♂️ Goal Tracker")

# Hamburger menu button
if st.button("☰", key="hamburger"):
    st.session_state.menu_open = not st.session_state.menu_open
    st.session_state.expanded_goal = None

# Sidebar for menu
if st.session_state.menu_open:
    with st.sidebar:
        st.header("Menu")
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        if st.session_state.data.empty:
            st.write("No goals added yet.")
            if st.button("Create New Goals"):
                st.session_state.menu_open = False
                st.session_state.selected_type = 'create'
        else:
            if st.button("View Goals"):
                st.session_state.menu_open = False
                st.session_state.selected_type = 'goals'
            if st.button("Create New Goals"):
                st.session_state.menu_open = False
                st.session_state.selected_type = 'create'
        st.markdown("</div>", unsafe_allow_html=True)

# Initial state
if st.session_state.data.empty and st.session_state.selected_type is None:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.write("Create Your Goals")
    if st.button("Create Goals"):
        st.session_state.menu_open = True
        st.session_state.selected_type = 'create'
    st.markdown("</div>", unsafe_allow_html=True)

# Create new goals
if st.session_state.selected_type == 'create':
    st.header("✨ Create New Goal")
    with st.container():
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        goal_name = st.text_input("Goal Name")
        due_date = st.date_input("Due Date")
        frequency = st.selectbox("Frequency", ["Daily", "Weekly", "Monthly"])
        if st.button("Add Goal"):
            if goal_name.strip():
                add_goal(goal_name, due_date, frequency)
                st.success(f"Goal '{goal_name}' added!")
                st.session_state.selected_type = 'goals'
            else:
                st.error("Please enter a goal name.")
        st.subheader("Import from CSV")
        st.write("CSV format: GoalID,GoalName,DueDate,Frequency")
        uploaded_file = st.file_uploader("Choose a CSV file", type="csv")
        if uploaded_file:
            try:
                csv_data = pd.read_csv(uploaded_file)
                required_cols = ['GoalID', 'GoalName', 'DueDate', 'Frequency']
                if all(col in csv_data.columns for col in required_cols):
                    csv_data['DueDate'] = pd.to_datetime(csv_data['DueDate']).dt.date
                    csv_data['Progress'] = 1.0
                    csv_data['DateAdded'] = datetime.now().date()
                    csv_data['Week'] = get_week_number(datetime.now().date())
                    # Drop 'Completed' if present in CSV
                    if 'Completed' in csv_data.columns:
                        csv_data = csv_data.drop(columns=['Completed'])
                    for _, row in csv_data.iterrows():
                        history_entry = pd.DataFrame({
                            'GoalID': [row['GoalID']],
                            'GoalName': [row['GoalName']],
                            'Date': [datetime.now().date()],
                            'Progress': [1.0],
                            'Percentage': [0.0],
                            'Change': [0.0]
                        })
                        st.session_state.history = pd.concat([st.session_state.history, history_entry], ignore_index=True)
                    st.session_state.data = pd.concat([st.session_state.data, csv_data], ignore_index=True)
                    save_data()
                    st.success("Goals imported successfully!")
                    st.session_state.selected_type = 'goals'
                else:
                    st.error("CSV must contain GoalID,GoalName,DueDate,Frequency columns.")
            except Exception as e:
                st.error(f"Error importing CSV: {str(e)}")
        st.markdown("</div>", unsafe_allow_html=True)

# Display goals
if st.session_state.selected_type == 'goals':
    st.header("🎯 Goals")
    if not st.session_state.data.empty:
        goal_ids = st.session_state.data['GoalID'].unique()
        for goal_id in goal_ids:
            goal_data = st.session_state.data[st.session_state.data['GoalID'] == goal_id]
            goal_name = goal_data['GoalName'].iloc[0]
            due_date = goal_data['DueDate'].iloc[0]
            frequency = goal_data['Frequency'].iloc[0]
            with st.container():
                st.markdown("<div class='card'>", unsafe_allow_html=True)
                is_expanded = (goal_id == goal_ids[0] and st.session_state.expanded_goal is None) or st.session_state.expanded_goal == goal_id
                with st.expander(f"Goal: {goal_name} (Due: {due_date}, Freq: {frequency})", expanded=is_expanded):
                    if st.button("Show Details", key=f"show_{goal_id}"):
                        st.session_state.expanded_goal = goal_id
                    tab1, tab2 = st.tabs(["Progress", "Graph"])
                    
                    with tab1:
                        percentage = st.selectbox(
                            f"Progress for {goal_name}",
                            [0, 50, 100],
                            format_func=lambda x: f"{x}%",
                            key=f"prog_{goal_id}"
                        )
                        if st.button("Update", key=f"update_{goal_id}"):
                            update_goal(goal_id, goal_name, percentage)
                            st.success(f"Updated {goal_name}")
                    
                    with tab2:
                        history = st.session_state.history[st.session_state.history['GoalID'] == goal_id]
                        # Fix: Compute 'Change' if missing
                        if 'Change' not in history.columns:
                            history['Change'] = history['Percentage'].apply(
                                lambda x: 0.01 if x == 100 else 0.005 if x == 50 else -0.01
                            )
                        if not history.empty:
                            # Ensure 'Date' is datetime.date
                            history = history.copy()
                            history['Date'] = pd.to_datetime(history['Date']).dt.date
                            history = history.sort_values('Date')
                            # Calculate streak
                            streak = calculate_streak(history)
                            # Create mountain climb plot
                            current_progress = history['Progress'].iloc[-1]
                            max_progress = max(history['Progress'].max(), 2.0)
                            fig = go.Figure()
                            # Mountain path
                            fig.add_trace(
                                go.Scatter(
                                    x=history['Date'],
                                    y=history['Progress'],
                                    mode='lines+markers',
                                    name='Progress',
                                    line=dict(color='green', width=3, shape='spline'),
                                    marker=dict(size=10, symbol='circle')
                                )
                            )
                            # Add climber at current progress
                            fig.add_trace(
                                go.Scatter(
                                    x=[history['Date'].iloc[-1]],
                                    y=[current_progress],
                                    mode='markers+text',
                                    text=['🏂'],
                                    textposition='top center',
                                    marker=dict(size=20, color='blue'),
                                    showlegend=False
                                )
                            )
                            # Add milestones
                            milestones = [1.5, 2.0]
                            for milestone in milestones:
                                if current_progress >= milestone:
                                    fig.add_hline(
                                        y=milestone,
                                        line_dash='dash',
                                        line_color='yellow',
                                        annotation_text=f"Peak {milestone} 🏁",
                                        annotation_position="top left",
                                        annotation_font_color='white'
                                    )
                            # Add daily change badges
                            changes = history['Change']
                            badge_texts = changes.apply(
                                lambda x: '✅ +1%' if x == 0.01 else '✔️ +0.5%' if x == 0.005 else '⚠️ -1%'
                            )
                            badge_colors = changes.apply(
                                lambda x: 'green' if x == 0.01 else 'lightgreen' if x == 0.005 else 'red'
                            )
                            fig.add_trace(
                                go.Scatter(
                                    x=history['Date'],
                                    y=[0.85] * len(history),
                                    mode='markers+text',
                                    text=badge_texts,
                                    textposition='bottom center',
                                    marker=dict(size=30, color=badge_colors, symbol='circle'),
                                    showlegend=False
                                )
                            )
                            # Update layout
                            fig.update_layout(
                                title=f"Climb to Success: {goal_name}",
                                height=600,
                                plot_bgcolor='rgba(0,0,0,0)',
                                paper_bgcolor='rgba(0,0,0,0)',
                                font_color='white',
                                xaxis_title="Date",
                                yaxis_title="Progress",
                                yaxis_range=[0.8, max_progress],
                                showlegend=True
                            )
                            st.plotly_chart(fig)
                            # Motivational message
                            message = (
                                f"{streak}-day climb! Keep ascending! 🔥" if streak >= 3 else
                                f"{streak}-day climb! You're gaining ground! 💪" if streak > 0 else
                                "Start your climb today! 🎯"
                            )
                            if current_progress >= 1.5:
                                message += " Reached Peak 1.5! You're a legend! 🎉"
                            st.markdown(f"<p class='motivation'>{message}</p>", unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.write("No goals added yet.")

# Weekly progress (shown when not viewing goals)
if st.session_state.selected_type is None and not st.session_state.data.empty:
    st.header("📊 Weekly Progress")
    current_week = get_week_number(datetime.now().date())
    weekly_data = st.session_state.data[st.session_state.data['Week'] == current_week]
    if not weekly_data.empty:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.write("Progress for this week:")
        for index, row in weekly_data.iterrows():
            st.write(f"Goal: {row['GoalName']}: {row['Progress']:.2f}")
        fig = px.bar(
            weekly_data,
            x='GoalName',
            y='Progress',
            title="Weekly Progress Overview",
            text='Progress',
            color_discrete_sequence=['#4ecdc4']
        )
        fig.update_traces(texttemplate='%{text:.2f}', textposition='outside')
        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font_color='white',
            title_font_color='white',
            xaxis_title="Goal",
            yaxis_title="Progress",
            yaxis_range=[0.9, max(weekly_data['Progress'].max(), 1.5)]
        )
        st.plotly_chart(fig)
        st.markdown(
            "<p class='motivation'>You're building habits that last! 🚀</p>",
            unsafe_allow_html=True
        )
        st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.write("No progress tracked for this week.")
        st.markdown("</div>", unsafe_allow_html=True)