import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import json
import os
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import datetime
import re
from pathlib import Path

# -------- GOOGLE SHEETS CONFIGURATION --------
SPREADSHEET_ID = "1g3XL1EllHoWV3jhmi7gT3at6MtCNTJBo8DQ1WyWhMEo"
SHEET_NAME = "Sheet1"

# -------- STYLING --------
def apply_custom_css():
    st.markdown("""
    <style>
    /* Main app styling */
    .stApp {
        background: linear-gradient(135deg, #0f0f23 0%, #1a1a2e 100%);
        color: #ffffff;
    }
    
    /* Header styling */
    .main-header {
        text-align: center;
        padding: 2rem 0;
        background: linear-gradient(135deg, #16213e 0%, #0f0f23 100%);
        border-radius: 15px;
        margin-bottom: 2rem;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    .main-title {
        font-size: 3rem;
        font-weight: 700;
        background: linear-gradient(45deg, #ffd700, #ffed4e);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }
    
    .subtitle {
        font-size: 1.2rem;
        color: #b0b0b0;
        margin-bottom: 1rem;
    }
    
    .accuracy-badge {
        background: linear-gradient(45deg, #ffd700, #ffed4e);
        color: #000;
        padding: 0.5rem 1rem;
        border-radius: 25px;
        font-weight: 600;
        display: inline-block;
        margin-top: 1rem;
    }
    
    /* Stats cards */
    .stats-container {
        display: flex;
        gap: 1.5rem;
        margin: 2rem 0;
        flex-wrap: wrap;
        justify-content: center;
    }
    
    .stat-card {
        background: linear-gradient(135deg, rgba(255, 255, 255, 0.1) 0%, rgba(255, 255, 255, 0.05) 100%);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.2);
        border-radius: 15px;
        padding: 1.5rem;
        text-align: center;
        min-width: 200px;
        flex: 1;
        max-width: 300px;
    }
    
    .stat-icon {
        font-size: 2rem;
        margin-bottom: 0.5rem;
    }
    
    .stat-value {
        font-size: 2.5rem;
        font-weight: 700;
        color: #ffd700;
        margin: 0.5rem 0;
    }
    
    .stat-label {
        font-size: 0.9rem;
        color: #b0b0b0;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    /* Chart containers */
    .chart-container {
        background: linear-gradient(135deg, rgba(255, 255, 255, 0.1) 0%, rgba(255, 255, 255, 0.05) 100%);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.2);
        border-radius: 15px;
        padding: 1.5rem;
        margin: 1rem 0;
    }
    
    /* Buttons */
    .stButton button {
        background: linear-gradient(45deg, #ffd700, #ffed4e);
        color: #000;
        border: none;
        border-radius: 25px;
        padding: 0.7rem 2rem;
        font-weight: 600;
        font-size: 1rem;
        transition: all 0.3s ease;
        width: 100%;
    }
    
    .stButton button:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 20px rgba(255, 215, 0, 0.3);
    }
    
    /* Radio buttons */
    .stRadio > div {
        background: rgba(255, 255, 255, 0.1);
        border-radius: 10px;
        padding: 1rem;
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.2);
    }
    
    /* Data table */
    .stDataFrame {
        background: rgba(255, 255, 255, 0.1);
        border-radius: 10px;
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.2);
    }
    
    /* Sidebar */
    .css-1d391kg {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
    }
    
    /* Success/Warning messages */
    .stSuccess {
        background: linear-gradient(45deg, #4caf50, #45a049);
        border-radius: 10px;
    }
    
    .stWarning {
        background: linear-gradient(45deg, #ff9800, #f57c00);
        border-radius: 10px;
    }
    
    .stError {
        background: linear-gradient(45deg, #f44336, #d32f2f);
        border-radius: 10px;
    }
    

    </style>
    """, unsafe_allow_html=True)

# -------- GOOGLE SHEETS CONNECTION --------
@st.cache_resource
def connect_to_gsheet():
    try:
        if "gcp_service_account" in st.secrets:
            credentials_info = st.secrets["gcp_service_account"]
        elif "credentials_json" in st.secrets:
            if isinstance(st.secrets["credentials_json"], dict):
                credentials_info = st.secrets["credentials_json"]
            else:
                credentials_info = json.loads(st.secrets["credentials_json"])
        else:
            credentials_json_str = os.environ.get("CREDENTIALS_JSON")
            if credentials_json_str:
                credentials_info = json.loads(credentials_json_str)
            else:
                raise ValueError("Google Sheets credentials not found. Make sure 'gcp_service_account' or 'credentials_json' secret is configured.")
        
        credentials = Credentials.from_service_account_info(
            credentials_info,
            scopes=[
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive",
            ]
        )
        client = gspread.authorize(credentials)
        sheet = client.open_by_key(SPREADSHEET_ID).worksheet(SHEET_NAME)
        return sheet
    except Exception as e:
        st.error(f"Google Sheets connection error: {str(e)}")
        raise e

# -------- DATA PROCESSING FUNCTIONS --------
def get_sheet_data():
    """Get all data from Google Sheets and convert to DataFrame"""
    sheet = connect_to_gsheet()
    
    all_values = sheet.get_all_values()
    header_row = all_values[0]
    data_rows = all_values[1:]
    
    last_index = 0
    for i, row in enumerate(data_rows):
        if any(row[:6]):
            last_index = i
    
    valid_data_rows = data_rows[:last_index + 1] if data_rows else []
    
    if valid_data_rows:
        df = pd.DataFrame(valid_data_rows, columns=header_row)
        df = df[df.iloc[:, :6].any(axis=1)]
        
        if df.empty:
            return None
        
        df.columns = df.columns.str.strip()
        
        # Column mapping
        column_mapping = {}
        for col in df.columns:
            col_lower = col.lower().strip()
            if any(keyword in col_lower for keyword in ['date', 'tanggal', 'tgl']):
                column_mapping['Date'] = col
            elif any(keyword in col_lower for keyword in ['total', 'signal']):
                column_mapping['Total_Signal'] = col
            elif 'finish' in col_lower:
                column_mapping['Finished'] = col
            elif col_lower == 'tp':
                column_mapping['TP'] = col
            elif col_lower == 'sl':
                column_mapping['SL'] = col
            elif any(keyword in col_lower for keyword in ['winrate', 'win_rate', 'win rate']):
                column_mapping['Winrate_pct'] = col
        
        df = df.rename(columns=column_mapping)
        
        # Process numeric columns
        numeric_columns = ['Total_Signal', 'Finished', 'TP', 'SL']
        for col in numeric_columns:
            if col in df.columns:
                df[col] = df[col].astype(str).str.replace(r'[^\d]', '', regex=True)
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)
        
        # Process winrate column
        if 'Winrate_pct' in df.columns:
            df['Winrate_num'] = df['Winrate_pct'].astype(str).str.replace('%', '').str.strip()
            df['Winrate_num'] = pd.to_numeric(df['Winrate_num'], errors='coerce').fillna(0)
        
        # Process date column
        if 'Date' in df.columns:
            df['Date_parsed'] = None
            df['Date_display'] = df['Date'].astype(str)
            
            for idx, date_str in enumerate(df['Date']):
                if pd.isna(date_str) or date_str == '' or str(date_str).strip() == '':
                    continue
                
                date_str = str(date_str).strip()
                
                # Handle date ranges
                range_pattern = re.search(r'(\d{2})/(\d{2})-(\d{2})/(\d{2})', date_str)
                if range_pattern:
                    start_month, start_day, end_month, end_day = range_pattern.groups()
                    try:
                        current_year = datetime.datetime.now().year
                        end_date = pd.to_datetime(f"{current_year}-{end_month}-{end_day}", format='%Y-%m-%d')
                        df.at[idx, 'Date_parsed'] = end_date
                        df.at[idx, 'Date_display'] = f"2025-{end_month}-{end_day}"
                        continue
                    except:
                        pass
                
                # Handle simple date formats
                date_patterns = [
                    r'(\d{4})-(\d{1,2})-(\d{1,2})',
                    r'(\d{1,2})/(\d{1,2})/(\d{4})',
                    r'(\d{1,2})-(\d{1,2})-(\d{4})',
                ]
                
                parsed = False
                for pattern in date_patterns:
                    match = re.search(pattern, date_str)
                    if match:
                        try:
                            if pattern == date_patterns[0]:
                                year, month, day = match.groups()
                            else:
                                month, day, year = match.groups()
                            
                            parsed_date = pd.to_datetime(f"{year}-{month}-{day}", format='%Y-%m-%d')
                            df.at[idx, 'Date_parsed'] = parsed_date
                            df.at[idx, 'Date_display'] = parsed_date.strftime('%Y-%m-%d')
                            parsed = True
                            break
                        except:
                            continue
                
                if not parsed:
                    try:
                        parsed_date = pd.to_datetime(date_str, errors='coerce')
                        if not pd.isna(parsed_date):
                            df.at[idx, 'Date_parsed'] = parsed_date
                            df.at[idx, 'Date_display'] = parsed_date.strftime('%Y-%m-%d')
                    except:
                        base_date = datetime.datetime.now() - pd.Timedelta(days=len(df)-idx-1)
                        df.at[idx, 'Date_parsed'] = base_date
                        df.at[idx, 'Date_display'] = base_date.strftime('%Y-%m-%d')
        
        if 'Date_parsed' in df.columns and not df['Date_parsed'].isna().all():
            df['Date_parsed'] = pd.to_datetime(df['Date_parsed'], errors='coerce')
            df = df.sort_values('Date_parsed')
        
        return df
    else:
        return None

def filter_data_by_period(df, period):
    """Filter DataFrame by selected time period"""
    if df is None or df.empty:
        return None
    
    today = datetime.datetime.now()
    
    if 'Date_parsed' not in df.columns or df['Date_parsed'].isna().all():
        total_rows = len(df)
        
        if period == 'week':
            rows_to_keep = min(7, total_rows)
            return df.iloc[-rows_to_keep:]
        elif period == 'month':
            rows_to_keep = min(30, total_rows)
            return df.iloc[-rows_to_keep:]
        else:
            return df
    
    if period == 'week':
        start_date = today - datetime.timedelta(days=7)
        filtered_df = df[df['Date_parsed'] >= start_date]
        if filtered_df.empty:
            return df.tail(7)
        return filtered_df
    elif period == 'month':
        start_date = today - datetime.timedelta(days=30)
        filtered_df = df[df['Date_parsed'] >= start_date]
        if filtered_df.empty:
            return df.tail(30)
        return filtered_df
    else:
        return df

def calculate_statistics(df):
    """Calculate trading statistics from DataFrame"""
    if df is None or df.empty:
        return None
    
    tp_col = 'TP' if 'TP' in df.columns else None
    sl_col = 'SL' if 'SL' in df.columns else None
    total_signal_col = 'Total_Signal' if 'Total_Signal' in df.columns else None
    finished_col = 'Finished' if 'Finished' in df.columns else None
    
    if not tp_col or not sl_col:
        return None
    
    tp_data = pd.to_numeric(df[tp_col], errors='coerce').fillna(0)
    sl_data = pd.to_numeric(df[sl_col], errors='coerce').fillna(0)
    
    stats = {
        'total_tp': int(tp_data.sum()),
        'total_sl': int(sl_data.sum()),
    }
    
    if stats['total_tp'] + stats['total_sl'] > 0:
        stats['overall_winrate'] = 100 * stats['total_tp'] / (stats['total_tp'] + stats['total_sl'])
    else:
        stats['overall_winrate'] = 0
    
    if total_signal_col:
        total_signals = pd.to_numeric(df[total_signal_col], errors='coerce').fillna(0).sum()
        stats['total_signals'] = int(total_signals)
        
        if total_signals > 0:
            finished_total = stats['total_tp'] + stats['total_sl']
            stats['completion_rate'] = 100 * finished_total / total_signals
        else:
            stats['completion_rate'] = 0
    elif finished_col:
        finished = pd.to_numeric(df[finished_col], errors='coerce').fillna(0).sum()
        stats['total_signals'] = int(finished)
        stats['completion_rate'] = 100
    else:
        stats['total_signals'] = int(stats['total_tp'] + stats['total_sl'])
        stats['completion_rate'] = 100
    
    return stats

# -------- VISUALIZATION FUNCTIONS --------
def create_winrate_chart(df):
    """Create an enhanced winrate chart with Plotly"""
    if df is None or df.empty or 'Winrate_num' not in df.columns:
        return None
    
    if 'Date_parsed' in df.columns and not df['Date_parsed'].isna().all():
        df = df.copy()
        df['Date_parsed'] = pd.to_datetime(df['Date_parsed'], errors='coerce')
        df = df.sort_values('Date_parsed')
    
    fig = go.Figure()
    
    # Add winrate line
    fig.add_trace(go.Scatter(
        x=df['Date_display'],
        y=df['Winrate_num'],
        mode='lines+markers',
        name='Winrate',
        line=dict(color='#FFD700', width=3),
        marker=dict(size=8, color='#FFD700', line=dict(width=2, color='#FFF')),
        hovertemplate='<b>Date:</b> %{x}<br><b>Winrate:</b> %{y}%<extra></extra>'
    ))
    
    # Add average line
    avg_winrate = df['Winrate_num'].mean()
    fig.add_hline(y=avg_winrate, line_dash="dash", line_color="#FF6B6B", 
                  annotation_text=f"Average: {avg_winrate:.1f}%")
    
    fig.update_layout(
        title="Historical Winrate Trend",
        title_font=dict(size=20, color='#FFD700'),
        xaxis_title="Date",
        yaxis_title="Winrate (%)",
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white'),
        height=400,
        showlegend=False,
        yaxis=dict(range=[0, 100], gridcolor='rgba(255,255,255,0.2)'),
        xaxis=dict(gridcolor='rgba(255,255,255,0.2)')
    )
    
    return fig

def create_tpsl_chart(df):
    """Create an enhanced TP/SL comparison chart"""
    if df is None or df.empty or 'TP' not in df.columns or 'SL' not in df.columns:
        return None
    
    if 'Date_parsed' in df.columns and not df['Date_parsed'].isna().all():
        df = df.copy()
        df['Date_parsed'] = pd.to_datetime(df['Date_parsed'], errors='coerce')
        df = df.sort_values('Date_parsed')
    
    fig = go.Figure()
    
    # Add TP bars
    fig.add_trace(go.Bar(
        x=df['Date_display'],
        y=df['TP'],
        name='Take Profit',
        marker_color='#4CAF50',
        hovertemplate='<b>Date:</b> %{x}<br><b>TP:</b> %{y}<extra></extra>'
    ))
    
    # Add SL bars
    fig.add_trace(go.Bar(
        x=df['Date_display'],
        y=df['SL'],
        name='Stop Loss',
        marker_color='#F44336',
        hovertemplate='<b>Date:</b> %{x}<br><b>SL:</b> %{y}<extra></extra>'
    ))
    
    fig.update_layout(
        title="Take Profit vs Stop Loss Distribution",
        title_font=dict(size=20, color='#FFD700'),
        xaxis_title="Date",
        yaxis_title="Count",
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white'),
        height=400,
        barmode='group',
        legend=dict(x=0, y=1),
        yaxis=dict(gridcolor='rgba(255,255,255,0.2)'),
        xaxis=dict(gridcolor='rgba(255,255,255,0.2)')
    )
    
    return fig

def create_combined_dashboard_chart(df):
    """Create a combined chart with multiple metrics"""
    if df is None or df.empty:
        return None
    
    # Create subplots
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=('Winrate Trend', 'TP vs SL', 'Cumulative Performance', 'Daily Signals'),
        specs=[[{"secondary_y": False}, {"secondary_y": False}],
               [{"secondary_y": False}, {"secondary_y": False}]]
    )
    
    if 'Winrate_num' in df.columns:
        # Winrate trend
        fig.add_trace(
            go.Scatter(x=df['Date_display'], y=df['Winrate_num'], 
                      mode='lines+markers', name='Winrate',
                      line=dict(color='#FFD700')),
            row=1, col=1
        )
    
    if 'TP' in df.columns and 'SL' in df.columns:
        # TP vs SL
        fig.add_trace(
            go.Bar(x=df['Date_display'], y=df['TP'], name='TP', 
                   marker_color='#4CAF50'),
            row=1, col=2
        )
        fig.add_trace(
            go.Bar(x=df['Date_display'], y=df['SL'], name='SL',
                   marker_color='#F44336'),
            row=1, col=2
        )
        
        # Cumulative performance
        cumulative_tp = df['TP'].cumsum()
        cumulative_sl = df['SL'].cumsum()
        fig.add_trace(
            go.Scatter(x=df['Date_display'], y=cumulative_tp, 
                      mode='lines', name='Cumulative TP',
                      line=dict(color='#4CAF50')),
            row=2, col=1
        )
        fig.add_trace(
            go.Scatter(x=df['Date_display'], y=cumulative_sl,
                      mode='lines', name='Cumulative SL',
                      line=dict(color='#F44336')),
            row=2, col=1
        )
    
    if 'Total_Signal' in df.columns:
        # Daily signals
        fig.add_trace(
            go.Bar(x=df['Date_display'], y=df['Total_Signal'], 
                   name='Daily Signals', marker_color='#2196F3'),
            row=2, col=2
        )
    
    fig.update_layout(
        height=800,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white'),
        title_text="LuxQuant VIP Trading Dashboard",
        title_font=dict(size=24, color='#FFD700'),
        showlegend=True
    )
    
    return fig

# -------- MAIN APP --------
def main():
    st.set_page_config(
        page_title="LuxQuant VIP | Trading Dashboard",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    
    # Apply custom styling
    apply_custom_css()
    
    # Main header
    st.markdown("""
    <div class="main-header">
        <div class="main-title">LuxQuant VIP | 智汇尊享会</div>
        <div class="subtitle">Tools for Automated Crypto Trading Setup 24/7</div>
        <div class="subtitle">Help traders identify market opportunities without having to monitor charts continuously.</div>
        <div class="accuracy-badge">Historical Accuracy of 87.9% (No Future Guarantee)</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Period selector
    st.markdown("### 📊 Trading Performance Analysis")
    
    col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
    
    with col2:
        period = st.radio(
            "Select Time Period:",
            options=["week", "month", "all"],
            format_func=lambda x: {"week": "📅 Last Week", "month": "📆 Last Month", "all": "📈 All Time"}[x],
            horizontal=False
        )
    
    with col3:
        load_button = st.button("🚀 Load Trading Statistics", use_container_width=True)
    
    if load_button:
        with st.spinner("🔄 Loading trading data..."):
            try:
                # Get data
                df = get_sheet_data()
                
                if df is None or df.empty:
                    st.warning("⚠️ No trading data available for the selected period.")
                else:
                    # Filter data
                    filtered_df = filter_data_by_period(df, period)
                    
                    if filtered_df is None or filtered_df.empty:
                        st.warning("⚠️ No data available for the selected period.")
                    else:
                        st.success("✅ Trading data loaded successfully!")
                        
                        # Calculate statistics
                        stats = calculate_statistics(filtered_df)
                        
                        if stats:
                            # Display main statistics
                            st.markdown("### 📈 Key Performance Metrics")
                            
                            # Create stats cards
                            col1, col2, col3, col4 = st.columns(4)
                            
                            with col1:
                                st.markdown(f"""
                                <div class="stat-card">
                                    <div class="stat-icon">📊</div>
                                    <div class="stat-value">{stats['overall_winrate']:.1f}%</div>
                                    <div class="stat-label">Historical System<br>Accuracy (Win-Rate)</div>
                                </div>
                                """, unsafe_allow_html=True)
                            
                            with col2:
                                st.markdown(f"""
                                <div class="stat-card">
                                    <div class="stat-icon">⚡</div>
                                    <div class="stat-value">{stats['total_signals']:,}</div>
                                    <div class="stat-label">Total System<br>Output</div>
                                </div>
                                """, unsafe_allow_html=True)
                            
                            with col3:
                                st.markdown(f"""
                                <div class="stat-card">
                                    <div class="stat-icon">🎯</div>
                                    <div class="stat-value">{stats['total_tp']:,}</div>
                                    <div class="stat-label">Take Profit<br>Signals</div>
                                </div>
                                """, unsafe_allow_html=True)
                            
                            with col4:
                                st.markdown(f"""
                                <div class="stat-card">
                                    <div class="stat-icon">👥</div>
                                    <div class="stat-value">8,562</div>
                                    <div class="stat-label">Global<br>Users</div>
                                </div>
                                """, unsafe_allow_html=True)
                        
                        # Charts section
                        st.markdown("### 📊 Performance Analytics")
                        
                        # Combined dashboard
                        combined_chart = create_combined_dashboard_chart(filtered_df)
                        if combined_chart:
                            st.markdown('<div class="chart-container">', unsafe_allow_html=True)
                            st.plotly_chart(combined_chart, use_container_width=True)
                            st.markdown('</div>', unsafe_allow_html=True)
                        
                        # Individual charts
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            winrate_chart = create_winrate_chart(filtered_df)
                            if winrate_chart:
                                st.markdown('<div class="chart-container">', unsafe_allow_html=True)
                                st.plotly_chart(winrate_chart, use_container_width=True)
                                st.markdown('</div>', unsafe_allow_html=True)
                        
                        with col2:
                            tpsl_chart = create_tpsl_chart(filtered_df)
                            if tpsl_chart:
                                st.markdown('<div class="chart-container">', unsafe_allow_html=True)
                                st.plotly_chart(tpsl_chart, use_container_width=True)
                                st.markdown('</div>', unsafe_allow_html=True)
                        
                        # Detailed data table
                        st.markdown("### 📋 Detailed Trading Records")
                        
                        # Prepare display columns
                        display_cols = []
                        available_cols = ['Date', 'Total_Signal', 'Finished', 'TP', 'SL', 'Winrate_pct']
                        for col in available_cols:
                            if col in filtered_df.columns:
                                display_cols.append(col)
                        
                        # Display the data table with styling
                        if display_cols:
                            st.markdown('<div class="chart-container">', unsafe_allow_html=True)
                            st.dataframe(
                                filtered_df[display_cols],
                                use_container_width=True,
                                height=300
                            )
                            st.markdown('</div>', unsafe_allow_html=True)
                        else:
                            st.markdown('<div class="chart-container">', unsafe_allow_html=True)
                            st.dataframe(filtered_df, use_container_width=True, height=300)
                            st.markdown('</div>', unsafe_allow_html=True)
                        
                        # Additional insights
                        st.markdown("### 💡 Trading Insights")
                        
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            if stats['overall_winrate'] >= 70:
                                insight_color = "#4CAF50"
                                insight_icon = "🟢"
                                insight_text = "Excellent Performance"
                            elif stats['overall_winrate'] >= 60:
                                insight_color = "#FF9800"
                                insight_icon = "🟡"
                                insight_text = "Good Performance"
                            else:
                                insight_color = "#F44336"
                                insight_icon = "🔴"
                                insight_text = "Needs Improvement"
                            
                            st.markdown(f"""
                            <div class="stat-card">
                                <div class="stat-icon">{insight_icon}</div>
                                <div class="stat-label" style="color: {insight_color};">{insight_text}</div>
                                <div style="font-size: 0.9rem; margin-top: 0.5rem;">
                                    Winrate: {stats['overall_winrate']:.1f}%
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                        
                        with col2:
                            # Calculate recent trend
                            if len(filtered_df) >= 3 and 'Winrate_num' in filtered_df.columns:
                                recent_avg = filtered_df['Winrate_num'].tail(3).mean()
                                overall_avg = filtered_df['Winrate_num'].mean()
                                
                                if recent_avg > overall_avg:
                                    trend_icon = "📈"
                                    trend_text = "Improving Trend"
                                    trend_color = "#4CAF50"
                                else:
                                    trend_icon = "📉"
                                    trend_text = "Declining Trend"
                                    trend_color = "#F44336"
                            else:
                                trend_icon = "📊"
                                trend_text = "Stable Performance"
                                trend_color = "#2196F3"
                            
                            st.markdown(f"""
                            <div class="stat-card">
                                <div class="stat-icon">{trend_icon}</div>
                                <div class="stat-label" style="color: {trend_color};">{trend_text}</div>
                                <div style="font-size: 0.9rem; margin-top: 0.5rem;">
                                    Recent Performance Analysis
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                        
                        with col3:
                            # Risk assessment
                            if stats['total_sl'] > 0:
                                risk_ratio = stats['total_tp'] / stats['total_sl']
                                if risk_ratio >= 2:
                                    risk_icon = "🟢"
                                    risk_text = "Low Risk"
                                    risk_color = "#4CAF50"
                                elif risk_ratio >= 1:
                                    risk_icon = "🟡"
                                    risk_text = "Medium Risk"
                                    risk_color = "#FF9800"
                                else:
                                    risk_icon = "🔴"
                                    risk_text = "High Risk"
                                    risk_color = "#F44336"
                            else:
                                risk_icon = "🟢"
                                risk_text = "Low Risk"
                                risk_color = "#4CAF50"
                            
                            st.markdown(f"""
                            <div class="stat-card">
                                <div class="stat-icon">{risk_icon}</div>
                                <div class="stat-label" style="color: {risk_color};">{risk_text}</div>
                                <div style="font-size: 0.9rem; margin-top: 0.5rem;">
                                    TP/SL Ratio: {stats['total_tp']}/{stats['total_sl']}
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
            
            except Exception as e:
                st.error(f"❌ Error loading data: {str(e)}")
                st.error(f"Debug info: {type(e).__name__}")
    
    # Action buttons
    st.markdown("### 🚀 Take Action")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📊 SUBSCRIBE NOW", use_container_width=True):
            st.success("🎉 Redirecting to subscription page...")
    
    with col2:
        if st.button("📦 VIEW PACKAGES", use_container_width=True):
            st.info("📋 Displaying available packages...")
    
    with col3:
        if st.button("📞 CONTACT SUPPORT", use_container_width=True):
            st.info("💬 Connecting to support team...")
    
    # Configuration section
    with st.expander("🔧 Google Sheets Configuration"):
        st.markdown("""
        ### Google Service Account Configuration
        
        For correct configuration, add the following secret to Streamlit Cloud:
        
        `gcp_service_account` - for Google Sheets access
        
        **Required TOML format:**
        ```toml
        [gcp_service_account]
        type = "service_account"
        project_id = "your-project-id"
        private_key_id = "your-key-id"
        private_key = "-----BEGIN PRIVATE KEY-----\\n...\\n-----END PRIVATE KEY-----\\n"
        client_email = "your-service-account@your-project.iam.gserviceaccount.com"
        client_id = "your-client-id"
        auth_uri = "https://accounts.google.com/o/oauth2/auth"
        token_uri = "https://oauth2.googleapis.com/token"
        auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
        client_x509_cert_url = "https://www.googleapis.com/robot/v1/metadata/x509/your-service-account"
        universe_domain = "googleapis.com"
        ```
        
        ### Spreadsheet Structure
        Expected columns in your Google Sheet:
        - **Date**: Trading date (YYYY-MM-DD format)
        - **Total_Signal**: Total signals generated
        - **Finished**: Completed trades
        - **TP**: Take Profit count
        - **SL**: Stop Loss count
        - **Winrate**: Win rate percentage
        """)
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; padding: 2rem; background: linear-gradient(135deg, rgba(255, 255, 255, 0.1) 0%, rgba(255, 255, 255, 0.05) 100%); backdrop-filter: blur(10px); border-radius: 15px; margin-top: 2rem;'>
        <h3 style='color: #FFD700; margin-bottom: 1rem;'>Ready to Start Automated Trading?</h3>
        <p style='color: #B0B0B0; margin-bottom: 1.5rem;'>Join thousands of traders using LuxQuant VIP for automated crypto trading signals.</p>
        <p style='color: #888; font-size: 0.9rem;'>Made with ❤️ by LuxQuant VIP | 智汇尊享会 | Historical accuracy does not guarantee future results</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
