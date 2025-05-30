import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import json
import os
import pandas as pd
import altair as alt
import datetime
import re
from pathlib import Path

# -------- GOOGLE SHEETS CONFIGURATION --------
SPREADSHEET_ID = "1g3XL1EllHoWV3jhmi7gT3at6MtCNTJBo8DQ1WyWhMEo"
SHEET_NAME = "Sheet1"

# -------- IMAGE PATH --------
IMAGE_PATH = "logo.png"

# -------- LANGUAGE SETTINGS --------
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
        "footer": "<div style='text-align: center'>Made with ❤️ by LuxQuant VIP | 智汇尊享会</div>",
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
    
    # Get all records including empty rows at the bottom
    all_values = sheet.get_all_values()
    
    # Find header row
    header_row = all_values[0]
    
    # Get data rows (skip header)
    data_rows = all_values[1:]
    
    # Find the last non-empty row (checking key columns)
    last_index = 0
    for i, row in enumerate(data_rows):
        # Consider a row non-empty if it has values in essential columns
        if any(row[:6]):  # Check first 6 columns
            last_index = i
    
    # Get only rows up to the last non-empty row
    valid_data_rows = data_rows[:last_index + 1] if data_rows else []
    
    # Convert to DataFrame
    if valid_data_rows:
        df = pd.DataFrame(valid_data_rows, columns=header_row)
        
        # Remove empty rows where all essential columns are empty
        df = df[df.iloc[:, :6].any(axis=1)]
        
        if df.empty:
            return None
        
        # Clean column names
        df.columns = df.columns.str.strip()
        
        # Process columns based on expected structure from the images
        # Expected columns: Date, Total_Signal, Finished, TP, SL, Winrate_pct
        
        # Find column mappings (case insensitive and flexible matching)
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
        
        # Rename columns to standard names
        df = df.rename(columns=column_mapping)
        
        # Process numeric columns
        numeric_columns = ['Total_Signal', 'Finished', 'TP', 'SL']
        for col in numeric_columns:
            if col in df.columns:
                # Clean the data first (remove any non-numeric characters except numbers)
                df[col] = df[col].astype(str).str.replace(r'[^\d]', '', regex=True)
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)
        
        # Process winrate column
        if 'Winrate_pct' in df.columns:
            # Handle percentage format (e.g., "85.5%" -> 85.5)
            df['Winrate_num'] = df['Winrate_pct'].astype(str).str.replace('%', '').str.strip()
            df['Winrate_num'] = pd.to_numeric(df['Winrate_num'], errors='coerce').fillna(0)
        
        # Process date column with improved parsing for range dates
        if 'Date' in df.columns:
            df['Date_parsed'] = None
            df['Date_display'] = df['Date'].astype(str)
            
            for idx, date_str in enumerate(df['Date']):
                if pd.isna(date_str) or date_str == '' or str(date_str).strip() == '':
                    continue
                
                date_str = str(date_str).strip()
                
                # Handle date ranges like "05/22-05/23", "05/26-05/27"
                range_pattern = re.search(r'(\d{2})/(\d{2})-(\d{2})/(\d{2})', date_str)
                if range_pattern:
                    start_month, start_day, end_month, end_day = range_pattern.groups()
                    # Use the end date for sorting (more recent)
                    try:
                        # Assume current year if not specified
                        current_year = datetime.datetime.now().year
                        end_date = pd.to_datetime(f"{current_year}-{end_month}-{end_day}", format='%Y-%m-%d')
                        df.at[idx, 'Date_parsed'] = end_date
                        # Create a better display format
                        df.at[idx, 'Date_display'] = f"2025-{end_month}-{end_day}"
                        continue
                    except:
                        pass
                
                # Handle simple date formats
                date_patterns = [
                    r'(\d{4})-(\d{1,2})-(\d{1,2})',  # YYYY-MM-DD
                    r'(\d{1,2})/(\d{1,2})/(\d{4})',  # MM/DD/YYYY
                    r'(\d{1,2})-(\d{1,2})-(\d{4})',  # MM-DD-YYYY
                ]
                
                parsed = False
                for pattern in date_patterns:
                    match = re.search(pattern, date_str)
                    if match:
                        try:
                            if pattern == date_patterns[0]:  # YYYY-MM-DD
                                year, month, day = match.groups()
                            else:  # MM/DD/YYYY or MM-DD-YYYY
                                month, day, year = match.groups()
                            
                            parsed_date = pd.to_datetime(f"{year}-{month}-{day}", format='%Y-%m-%d')
                            df.at[idx, 'Date_parsed'] = parsed_date
                            df.at[idx, 'Date_display'] = parsed_date.strftime('%Y-%m-%d')
                            parsed = True
                            break
                        except:
                            continue
                
                # If still not parsed, use a default approach
                if not parsed:
                    try:
                        # Try pandas built-in parsing as last resort
                        parsed_date = pd.to_datetime(date_str, errors='coerce')
                        if not pd.isna(parsed_date):
                            df.at[idx, 'Date_parsed'] = parsed_date
                            df.at[idx, 'Date_display'] = parsed_date.strftime('%Y-%m-%d')
                    except:
                        # Use index-based date if all parsing fails
                        base_date = datetime.datetime.now() - pd.Timedelta(days=len(df)-idx-1)
                        df.at[idx, 'Date_parsed'] = base_date
                        df.at[idx, 'Date_display'] = base_date.strftime('%Y-%m-%d')
        
        # Sort DataFrame by parsed date if available
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
    
    # Check if we have a date column to filter on
    if 'Date_parsed' not in df.columns or df['Date_parsed'].isna().all():
        # If we don't have parsed dates, use the index as a proxy for recency
        total_rows = len(df)
        
        if period == 'week':
            rows_to_keep = min(7, total_rows)
            return df.iloc[-rows_to_keep:]
        elif period == 'month':
            rows_to_keep = min(30, total_rows)
            return df.iloc[-rows_to_keep:]
        else:
            return df
    
    # We have parsed dates, so use them for filtering
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
    
    # Use the standardized column names
    tp_col = 'TP' if 'TP' in df.columns else None
    sl_col = 'SL' if 'SL' in df.columns else None
    total_signal_col = 'Total_Signal' if 'Total_Signal' in df.columns else None
    finished_col = 'Finished' if 'Finished' in df.columns else None
    
    if not tp_col or not sl_col:
        st.warning("Missing essential columns (TP or SL)")
        return None
    
    # Extract numeric data
    tp_data = pd.to_numeric(df[tp_col], errors='coerce').fillna(0)
    sl_data = pd.to_numeric(df[sl_col], errors='coerce').fillna(0)
    
    stats = {
        'total_tp': int(tp_data.sum()),
        'total_sl': int(sl_data.sum()),
    }
    
    # Calculate overall winrate from totals
    if stats['total_tp'] + stats['total_sl'] > 0:
        stats['overall_winrate'] = 100 * stats['total_tp'] / (stats['total_tp'] + stats['total_sl'])
    else:
        stats['overall_winrate'] = 0
    
    # Calculate total signals and completion rate
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
def create_winrate_chart(df, lang):
    """Create a line chart for winrate trend"""
    if df is None or df.empty or 'Winrate_num' not in df.columns:
        return None
    
    # Sort by date if available
    if 'Date_parsed' in df.columns and not df['Date_parsed'].isna().all():
        df = df.copy()
        df['Date_parsed'] = pd.to_datetime(df['Date_parsed'], errors='coerce')
        df = df.sort_values('Date_parsed')
    
    # Use Date_display for x-axis with proper sorting
    domain = df['Date_display'].tolist()
    
    chart = alt.Chart(df).mark_line(point=True).encode(
        x=alt.X('Date_display:O', title=lang['date'], sort=domain),
        y=alt.Y('Winrate_num:Q', title=lang['winrate'] + ' (%)', scale=alt.Scale(domain=[0, 100])),
        tooltip=[
            alt.Tooltip('Date_display:O', title=lang['date']),
            alt.Tooltip('Winrate_num:Q', title=lang['winrate'] + ' (%)'),
            alt.Tooltip('TP:Q', title='TP'),
            alt.Tooltip('SL:Q', title='SL')
        ]
    ).properties(height=300)
    
    return chart

def create_tpsl_chart(df, lang):
    """Create a bar chart comparing TP vs SL by date"""
    if df is None or df.empty or 'TP' not in df.columns or 'SL' not in df.columns:
        return None
    
    # Sort by date if available
    if 'Date_parsed' in df.columns and not df['Date_parsed'].isna().all():
        df = df.copy()
        df['Date_parsed'] = pd.to_datetime(df['Date_parsed'], errors='coerce')
        df = df.sort_values('Date_parsed')
    
    # Create a copy for melting
    chart_df = df[['Date_display', 'TP', 'SL']].copy()
    
    # Melt the dataframe for the stacked bar chart
    df_melted = pd.melt(
        chart_df, 
        id_vars=['Date_display'], 
        value_vars=['TP', 'SL'],
        var_name='Type', 
        value_name='Count'
    )
    
    # Use Date_display for x-axis with proper sorting
    domain = df['Date_display'].tolist()
    
    chart = alt.Chart(df_melted).mark_bar().encode(
        x=alt.X('Date_display:O', title=lang['date'], sort=domain),
        y=alt.Y('Count:Q', title='Count'),
        color=alt.Color('Type:N', scale=alt.Scale(
            domain=['TP', 'SL'],
            range=['#36b37e', '#ff5630']
        )),
        tooltip=[
            alt.Tooltip('Date_display:O', title=lang['date']),
            alt.Tooltip('Type:N', title='Type'),
            alt.Tooltip('Count:Q', title='Count')
        ]
    ).properties(height=300)
    
    return chart

# -------- STREAMLIT APP --------
def main():
    # Initialize session state for language preference
    if 'language' not in st.session_state:
        st.session_state.language = "id"
    
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
            lang = LANGUAGES[st.session_state.language]
            st.rerun()
    
    st.title(lang["main_title"])
    
    # Add image below title
    try:
        from PIL import Image
        image_path = Path(IMAGE_PATH)
        if image_path.exists():
            st.image(IMAGE_PATH, use_column_width=True)
        else:
            st.warning(f"Gambar {IMAGE_PATH} tidak ditemukan. Pastikan file gambar tersedia di repositori GitHub Anda.")
    except Exception as e:
        st.warning(f"Tidak dapat menampilkan gambar: {str(e)}")
    
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
                            col1.metric(lang["total_signals"], int(stats['total_signals']))
                            col2.metric(lang["total_tp"], int(stats['total_tp']))
                            col3.metric(lang["total_sl"], int(stats['total_sl']))
                            
                            col4, col5, col6 = st.columns(3)
                            col4.metric(lang["overall_winrate"], f"{stats['overall_winrate']:.1f}%")
                            col5.metric(lang["completion_rate"], f"{stats['completion_rate']:.1f}%")
                        
                        # Create and display charts
                        st.markdown(lang["winrate_chart_title"])
                        winrate_chart = create_winrate_chart(filtered_df, lang)
                        if winrate_chart:
                            st.altair_chart(winrate_chart, use_container_width=True)
                        else:
                            st.info("Chart winrate tidak dapat ditampilkan (data winrate tidak ditemukan)")
                        
                        st.markdown(lang["tpsl_chart_title"])
                        tpsl_chart = create_tpsl_chart(filtered_df, lang)
                        if tpsl_chart:
                            st.altair_chart(tpsl_chart, use_container_width=True)
                        else:
                            st.info("Chart TP/SL tidak dapat ditampilkan (data TP/SL tidak ditemukan)")
                        
                        # Display detailed data table
                        st.markdown(lang["data_table_title"])
                        
                        # Prepare display columns
                        display_cols = []
                        available_cols = ['Date', 'Total_Signal', 'Finished', 'TP', 'SL', 'Winrate_pct']
                        for col in available_cols:
                            if col in filtered_df.columns:
                                display_cols.append(col)
                        
                        # Display the data table
                        if display_cols:
                            st.dataframe(
                                filtered_df[display_cols],
                                use_container_width=True
                            )
                        else:
                            st.dataframe(filtered_df, use_container_width=True)
            
            except Exception as e:
                st.error(f"{lang['error_message']}{str(e)}")
                # Show debug information
                st.error(f"Debug info: {type(e).__name__}")
    
    # Configuration information
    with st.expander(lang["config_header"]):
        st.markdown(lang["config_text"])
    
    # Footer
    st.markdown("---")
    st.markdown(lang["footer"], unsafe_allow_html=True)

if __name__ == "__main__":
    main()
