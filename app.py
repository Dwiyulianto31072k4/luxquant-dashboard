import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import json
import os
import pandas as pd
import altair as alt
import datetime

# -------- GOOGLE SHEETS CONFIGURATION --------
SPREADSHEET_ID = "1g3XL1EllHoWV3jhmi7gT3at6MtCNTJBo8DQ1WyWhMEo"  # You can replace this with your sheet ID
SHEET_NAME = "Sheet1"

# -------- LANGUAGE SETTINGS --------
# Dictionary with text in multiple languages (Indonesian and English)
LANGUAGES = {
    "id": {
        "page_title": "Trading Statistics | LuxQuant VIP | 智汇尊享会",
        "main_title": "📊 Statistik Trading LuxQuant VIP | 智汇尊享会",
        "app_description": "Visualisasi performa trading Anda berdasarkan periode yang dipilih.",
        "language_selector": "Pilih Bahasa:",
        "period_selector": "Pilih Periode:",
        "period_week": "Seminggu Terakhir",
        "period_month": "Sebulan Terakhir",
        "period_all": "Semua Data",
        "load_stats_button": "🔄 Muat Statistik",
        "error_message": "❌ Error: ",
        "no_data_message": "Tidak ada data yang tersedia untuk periode ini.",
        "winrate_chart_title": "### Winrate Berdasarkan Periode",
        "tpsl_chart_title": "### Perbandingan TP vs SL",
        "stats_summary_title": "### Ringkasan Statistik",
        "avg_winrate": "Rata-rata Winrate",
        "total_tp": "Total TP",
        "total_sl": "Total SL",
        "total_signals": "Total Signals",
        "overall_winrate": "Overall Winrate",
        "completion_rate": "Completion Rate",
        "data_table_title": "### Data Detail",
        "footer": "<div style='text-align: center'>Made with ❤️ by LuxQuant VIP | 智汇尊享会</div>",
        "date": "Tanggal",
        "signals": "Sinyal",
        "finished": "Finished",
        "tp": "TP",
        "sl": "SL",
        "winrate": "Winrate",
        "comment": "Komentar",
        "loading_message": "Memuat data...",
        "data_loaded": "Data berhasil dimuat!",
        "config_header": "🔧 Konfigurasi",
        "config_text": """
        ### Konfigurasi Google Service Account
        
        Untuk konfigurasi yang benar, tambahkan secret berikut ke Streamlit Cloud:
        
        `gcp_service_account` - untuk akses Google Sheets
        
        Format TOML yang benar:
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
        """
    },
    "en": {
        "page_title": "Trading Statistics | LuxQuant VIP | 智汇尊享会",
        "main_title": "📊 LuxQuant VIP | 智汇尊享会 Trading Statistics",
        "app_description": "Visualize your trading performance based on selected period.",
        "language_selector": "Select Language:",
        "period_selector": "Select Period:",
        "period_week": "Last Week",
        "period_month": "Last Month",
        "period_all": "All Data",
        "load_stats_button": "🔄 Load Statistics",
        "error_message": "❌ Error: ",
        "no_data_message": "No data available for this period.",
        "winrate_chart_title": "### Winrate by Period",
        "tpsl_chart_title": "### TP vs SL Comparison",
        "stats_summary_title": "### Statistical Summary",
        "avg_winrate": "Average Winrate",
        "total_tp": "Total TP",
        "total_sl": "Total SL", 
        "total_signals": "Total Signals",
        "overall_winrate": "Overall Winrate",
        "completion_rate": "Completion Rate",
        "data_table_title": "### Detailed Data",
        "footer": "<div style='text-align: center'>Made with ❤️ by Lian Capital</div>",
        "date": "Date",
        "signals": "Signals",
        "finished": "Finished",
        "tp": "TP",
        "sl": "SL",
        "winrate": "Winrate",
        "comment": "Comment",
        "loading_message": "Loading data...",
        "data_loaded": "Data loaded successfully!",
        "config_header": "🔧 Configuration",
        "config_text": """
        ### Google Service Account Configuration
        
        For correct configuration, add the following secret to Streamlit Cloud:
        
        `gcp_service_account` - for Google Sheets access
        
        Correct TOML format:
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
        """
    }
}

# -------- GOOGLE SHEETS CONNECTION --------
@st.cache_resource
def connect_to_gsheet():
    try:
        # Get credentials from Streamlit secrets
        if "gcp_service_account" in st.secrets:
            credentials_info = st.secrets["gcp_service_account"]
        elif "credentials_json" in st.secrets:
            if isinstance(st.secrets["credentials_json"], dict):
                credentials_info = st.secrets["credentials_json"]
            else:
                credentials_info = json.loads(st.secrets["credentials_json"])
        else:
            # Try to read from environment for local development
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
    data = sheet.get_all_records()
    
    if not data:
        return None
    
    df = pd.DataFrame(data)
    
    # Process columns
    numeric_columns = ['Total_Signal', 'Finished', 'TP', 'SL']
    for col in numeric_columns:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)
    
    # Find winrate column and convert to numeric
    winrate_col = None
    for col in df.columns:
        if 'winrate' in col.lower() or 'win rate' in col.lower() or 'win_rate' in col.lower():
            winrate_col = col
            break
    
    if winrate_col:
        df['Winrate_num'] = pd.to_numeric(
            df[winrate_col].astype(str).str.rstrip('%').replace('', '0'), 
            errors='coerce'
        ).fillna(0)
    
    # Try to convert date column to datetime
    date_col = None
    for col in df.columns:
        if 'date' in col.lower() or 'tanggal' in col.lower():
            date_col = col
            break
    
    if date_col:
        # Try multiple date formats
        try:
            df['Date_parsed'] = pd.to_datetime(df[date_col], errors='coerce')
        except:
            # If that didn't work, the date might be in a different format or language
            # We'll keep the original for display purposes
            df['Date_parsed'] = pd.to_datetime('today')
    
    return df

def filter_data_by_period(df, period):
    """Filter DataFrame by selected time period"""
    if df is None or df.empty:
        return None
    
    today = datetime.datetime.now()
    
    # Check if we have a date column to filter on
    if 'Date_parsed' not in df.columns:
        return df  # Return all data if we can't filter by date
    
    if period == 'week':
        # Last 7 days
        start_date = today - datetime.timedelta(days=7)
        filtered_df = df[df['Date_parsed'] >= start_date]
    elif period == 'month':
        # Last 30 days
        start_date = today - datetime.timedelta(days=30)
        filtered_df = df[df['Date_parsed'] >= start_date]
    else:
        # All data
        filtered_df = df
    
    return filtered_df

def calculate_statistics(df):
    """Calculate trading statistics from DataFrame"""
    if df is None or df.empty:
        return None
    
    # Make sure we have the required columns
    required_cols = ['TP', 'SL', 'Total_Signal', 'Finished', 'Winrate_num']
    missing_cols = [col for col in required_cols if col not in df.columns]
    
    if missing_cols:
        st.warning(f"Missing columns: {', '.join(missing_cols)}")
        return None
    
    stats = {
        'avg_winrate': df['Winrate_num'].mean(),
        'total_tp': df['TP'].sum(),
        'total_sl': df['SL'].sum(),
        'total_signals': df['Total_Signal'].sum(),
    }
    
    # Calculate overall winrate from totals
    if stats['total_tp'] + stats['total_sl'] > 0:
        stats['overall_winrate'] = (stats['total_tp'] / (stats['total_tp'] + stats['total_sl'])) * 100
    else:
        stats['overall_winrate'] = 0
    
    # Calculate completion rate
    if stats['total_signals'] > 0:
        stats['completion_rate'] = ((stats['total_tp'] + stats['total_sl']) / stats['total_signals']) * 100
    else:
        stats['completion_rate'] = 0
    
    return stats

# -------- VISUALIZATION FUNCTIONS --------
def create_winrate_chart(df, lang):
    """Create a line chart for winrate trend"""
    # Need date and winrate columns
    if df is None or df.empty or 'Winrate_num' not in df.columns:
        return None
    
    # Sort by date if available
    if 'Date_parsed' in df.columns:
        df = df.sort_values('Date_parsed')
    
    # Use either parsed date or original date for display
    date_col = 'Date_parsed' if 'Date_parsed' in df.columns else 'Date'
    
    # Create a display column for the x-axis
    if date_col == 'Date_parsed':
        df['Date_display'] = df['Date_parsed'].dt.strftime('%Y-%m-%d')
    else:
        df['Date_display'] = df[date_col]
    
    chart = alt.Chart(df).mark_line(point=True).encode(
        x=alt.X('Date_display:N', title=lang['date'], sort=None),
        y=alt.Y('Winrate_num:Q', title=lang['winrate'] + ' (%)', scale=alt.Scale(domain=[0, 100])),
        tooltip=['Date_display', 'Winrate_num', 'Total_Signal', 'TP', 'SL']
    ).properties(height=300)
    
    return chart

def create_tpsl_chart(df, lang):
    """Create a bar chart comparing TP vs SL by date"""
    if df is None or df.empty or 'TP' not in df.columns or 'SL' not in df.columns:
        return None
    
    # Sort by date if available
    if 'Date_parsed' in df.columns:
        df = df.sort_values('Date_parsed')
    
    # Use either parsed date or original date for display
    date_col = 'Date_parsed' if 'Date_parsed' in df.columns else 'Date'
    
    # Create a display column for the x-axis
    if date_col == 'Date_parsed':
        df['Date_display'] = df['Date_parsed'].dt.strftime('%Y-%m-%d')
    else:
        df['Date_display'] = df[date_col]
    
    # Melt the dataframe for the stacked bar chart
    df_melted = pd.melt(
        df, 
        id_vars=['Date_display'], 
        value_vars=['TP', 'SL'],
        var_name='Type', 
        value_name='Count'
    )
    
    chart = alt.Chart(df_melted).mark_bar().encode(
        x=alt.X('Date_display:N', title=lang['date']),
        y=alt.Y('Count:Q', title='Count'),
        color=alt.Color('Type:N', scale=alt.Scale(
            domain=['TP', 'SL'],
            range=['#36b37e', '#ff5630']
        )),
        tooltip=['Date_display', 'Type', 'Count']
    ).properties(height=300)
    
    return chart

# -------- STREAMLIT APP --------
def main():
    # Initialize session state for language preference
    if 'language' not in st.session_state:
        st.session_state.language = "id"  # Default to Indonesian
    
    # Get current language text dictionary
    lang = LANGUAGES[st.session_state.language]
    
    st.set_page_config(
        page_title=lang["page_title"],
        page_icon="📊",
        layout="centered",
        initial_sidebar_state="expanded",
    )
    
    # Language selector in sidebar
    with st.sidebar:
        selected_lang = st.selectbox(
            lang["language_selector"],
            options=["id", "en"],
            format_func=lambda x: "Bahasa Indonesia" if x == "id" else "English",
            index=0 if st.session_state.language == "id" else 1
        )
        
        # Update language if changed
        if selected_lang != st.session_state.language:
            st.session_state.language = selected_lang
            # Update the lang variable
            lang = LANGUAGES[st.session_state.language]
            st.experimental_rerun()
    
    st.title(lang["main_title"])
    st.markdown(lang["app_description"])
    
    # Period selector
    period = st.radio(
        lang["period_selector"],
        options=["week", "month", "all"],
        format_func=lambda x: lang["period_week"] if x == "week" else (
            lang["period_month"] if x == "month" else lang["period_all"]
        ),
        horizontal=True
    )
    
    # Load data button
    if st.button(lang["load_stats_button"], use_container_width=True):
        with st.spinner(lang["loading_message"]):
            try:
                # Get all data from Google Sheets
                df = get_sheet_data()
                
                if df is None or df.empty:
                    st.warning(lang["no_data_message"])
                else:
                    # Filter data by selected period
                    filtered_df = filter_data_by_period(df, period)
                    
                    if filtered_df is None or filtered_df.empty:
                        st.warning(lang["no_data_message"])
                    else:
                        st.success(lang["data_loaded"])
                        
                        # Calculate statistics
                        stats = calculate_statistics(filtered_df)
                        
                        # Display statistics summary
                        if stats:
                            st.markdown(lang["stats_summary_title"])
                            
                            col1, col2, col3 = st.columns(3)
                            col1.metric(lang["avg_winrate"], f"{stats['avg_winrate']:.1f}%")
                            col2.metric(lang["total_tp"], int(stats['total_tp']))
                            col3.metric(lang["total_sl"], int(stats['total_sl']))
                            
                            col4, col5, col6 = st.columns(3)
                            col4.metric(lang["total_signals"], int(stats['total_signals']))
                            col5.metric(lang["overall_winrate"], f"{stats['overall_winrate']:.1f}%")
                            col6.metric(lang["completion_rate"], f"{stats['completion_rate']:.1f}%")
                        
                        # Create and display charts
                        st.markdown(lang["winrate_chart_title"])
                        winrate_chart = create_winrate_chart(filtered_df, lang)
                        if winrate_chart:
                            st.altair_chart(winrate_chart, use_container_width=True)
                        
                        st.markdown(lang["tpsl_chart_title"])
                        tpsl_chart = create_tpsl_chart(filtered_df, lang)
                        if tpsl_chart:
                            st.altair_chart(tpsl_chart, use_container_width=True)
                        
                        # Display detailed data table
                        st.markdown(lang["data_table_title"])
                        
                        # Select columns for display
                        display_cols = []
                        
                        # Find date column
                        date_col = None
                        for col in filtered_df.columns:
                            if 'date' in col.lower() and not col.startswith('Date_'):
                                date_col = col
                                display_cols.append(col)
                                break
                        
                        # Add other important columns
                        important_cols = ['Total_Signal', 'TP', 'SL', 'Finished']
                        for col in important_cols:
                            if col in filtered_df.columns:
                                display_cols.append(col)
                        
                        # Add winrate column
                        winrate_col = None
                        for col in filtered_df.columns:
                            if 'winrate' in col.lower() and not col == 'Winrate_num':
                                winrate_col = col
                                display_cols.append(col)
                                break
                        
                        # Add comment column if it exists
                        comment_col = None
                        for col in filtered_df.columns:
                            if 'comment' in col.lower() or 'komentar' in col.lower():
                                comment_col = col
                                display_cols.append(col)
                                break
                        
                        # Display the data table
                        st.dataframe(
                            filtered_df[display_cols] if display_cols else filtered_df,
                            use_container_width=True
                        )
            
            except Exception as e:
                st.error(f"{lang['error_message']}{str(e)}")
    
    # Configuration information
    with st.expander(lang["config_header"]):
        st.markdown(lang["config_text"])
    
    # Footer
    st.markdown("---")
    st.markdown(lang["footer"], unsafe_allow_html=True)

if __name__ == "__main__":
    main()
