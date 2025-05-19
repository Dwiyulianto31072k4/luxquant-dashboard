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
SPREADSHEET_ID = "1g3XL1EllHoWV3jhmi7gT3at6MtCNTJBo8DQ1WyWhMEo"  # You can replace this with your sheet ID
SHEET_NAME = "Sheet1"

# -------- IMAGE PATH --------
# Path to the image relative to the app.py file
IMAGE_PATH = "logo.png"  # Ganti dengan nama file gambar Anda

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
        if any(row[:5]):  # Check first 5 columns which should contain date, signals, etc.
            last_index = i
    
    # Get only rows up to the last non-empty row
    valid_data_rows = data_rows[:last_index + 1]
    
    # Convert to DataFrame
    if valid_data_rows:
        df = pd.DataFrame(valid_data_rows, columns=header_row)
        
        # Process numeric columns
        # First, identify potential numeric columns
        numeric_columns = []
        date_column = None
        winrate_column = None
        
        for col in df.columns:
            col_lower = col.lower()
            # Identify date column
            if 'date' in col_lower or 'tanggal' in col_lower or 'tgl' in col_lower:
                date_column = col
            # Identify potential numeric columns
            elif any(kw in col_lower for kw in ['signal', 'tp', 'sl', 'finish']):
                numeric_columns.append(col)
            # Identify winrate column
            elif 'winrate' in col_lower or 'win rate' in col_lower or 'win_rate' in col_lower:
                winrate_column = col
        
        # Convert numeric columns
        for col in numeric_columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)
        
        # Process winrate column (e.g., "85.5%" -> 85.5)
        if winrate_column:
            df['Winrate_num'] = df[winrate_column].astype(str).str.rstrip('%').replace('', '0')
            df['Winrate_num'] = pd.to_numeric(df['Winrate_num'], errors='coerce').fillna(0)
        
        # Process date column
        if date_column:
            # Create a new column for the parsed date
            df['Date_parsed'] = None
            
            # Use regex to extract date patterns from the date strings
            for idx, date_str in enumerate(df[date_column]):
                if pd.isna(date_str) or date_str == '':
                    continue
                
                # Try different date patterns
                # Pattern for dates like "18 April 2023", "18 Apr 2023"
                day_month_year = re.search(r'(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})', str(date_str))
                if day_month_year:
                    day, month, year = day_month_year.groups()
                    try:
                        date_obj = pd.to_datetime(f"{day} {month} {year}", format='%d %B %Y', errors='coerce')
                        if pd.isna(date_obj):
                            date_obj = pd.to_datetime(f"{day} {month} {year}", format='%d %b %Y', errors='coerce')
                        df.at[idx, 'Date_parsed'] = date_obj
                        continue
                    except:
                        pass
                
                # Pattern for dates like "2023-04-18", "2023/04/18"
                year_month_day = re.search(r'(\d{4})[-/](\d{1,2})[-/](\d{1,2})', str(date_str))
                if year_month_day:
                    year, month, day = year_month_day.groups()
                    try:
                        df.at[idx, 'Date_parsed'] = pd.to_datetime(f"{year}-{month}-{day}", format='%Y-%m-%d')
                        continue
                    except:
                        pass
                
                # Pattern for dates like "04/18/2023", "04-18-2023"
                month_day_year = re.search(r'(\d{1,2})[-/](\d{1,2})[-/](\d{4})', str(date_str))
                if month_day_year:
                    month, day, year = month_day_year.groups()
                    try:
                        df.at[idx, 'Date_parsed'] = pd.to_datetime(f"{year}-{month}-{day}", format='%Y-%m-%d')
                        continue
                    except:
                        pass
                
                # If all specific patterns fail, try generic parsing as a last resort
                try:
                    df.at[idx, 'Date_parsed'] = pd.to_datetime(date_str, errors='coerce')
                except:
                    # If parsing fails, use index as an ordinal date
                    df.at[idx, 'Date_parsed'] = pd.to_datetime('today') - pd.Timedelta(days=len(df)-idx-1)
            
            # If date parsing failed, use index as an ordinal date
            if df['Date_parsed'].isna().all():
                for idx in range(len(df)):
                    df.at[idx, 'Date_parsed'] = pd.to_datetime('today') - pd.Timedelta(days=len(df)-idx-1)
        
        # Sort DataFrame by parsed date
        if 'Date_parsed' in df.columns and not df['Date_parsed'].isna().all():
            # Make sure Date_parsed is actually datetime type before using dt accessor
            df['Date_parsed'] = pd.to_datetime(df['Date_parsed'], errors='coerce')
            df = df.sort_values('Date_parsed')
            # Create a formatted date display string that will be properly sorted
            # Only use dt accessor on non-null values
            mask = ~df['Date_parsed'].isna()
            df.loc[mask, 'Date_display'] = df.loc[mask, 'Date_parsed'].dt.strftime('%Y-%m-%d')
            # For null values, use original date column or index
            if date_column:
                df.loc[~mask, 'Date_display'] = df.loc[~mask, date_column]
            else:
                df.loc[~mask, 'Date_display'] = (df.loc[~mask].index + 1).astype(str)
        else:
            # Create a display column for the x-axis in charts if no date is available
            df['Date_display'] = df[date_column] if date_column else (df.index + 1).astype(str)
        
        # Add derived columns for analysis
        if 'TP' in df.columns and 'SL' in df.columns:
            df['TP_plus_SL'] = df['TP'] + df['SL']
        
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
            # Last 7 days or last 7 rows, whichever is smaller
            rows_to_keep = min(7, total_rows)
            return df.iloc[-rows_to_keep:]
        elif period == 'month':
            # Last 30 days or last 30 rows, whichever is smaller
            rows_to_keep = min(30, total_rows)
            return df.iloc[-rows_to_keep:]
        else:
            # All data
            return df
    
    # We have parsed dates, so use them for filtering
    if period == 'week':
        # Last 7 days
        start_date = today - datetime.timedelta(days=7)
        filtered_df = df[df['Date_parsed'] >= start_date]
        
        # If we got no results (maybe due to old dates), fall back to last 7 rows
        if filtered_df.empty:
            return df.tail(7)
        return filtered_df
    
    elif period == 'month':
        # Last 30 days
        start_date = today - datetime.timedelta(days=30)
        filtered_df = df[df['Date_parsed'] >= start_date]
        
        # If we got no results (maybe due to old dates), fall back to last 30 rows
        if filtered_df.empty:
            return df.tail(30)
        return filtered_df
    
    else:
        # All data
        return df

def calculate_statistics(df):
    """Calculate trading statistics from DataFrame"""
    if df is None or df.empty:
        return None
    
    # Determine column names based on what's available in the dataframe
    tp_col = next((col for col in df.columns if col.upper() == 'TP' or 'TAKE' in col.upper()), None)
    sl_col = next((col for col in df.columns if col.upper() == 'SL' or 'STOP' in col.upper()), None)
    total_signal_col = next((col for col in df.columns if 'SIGNAL' in col.upper() or 'TOTAL' in col.upper()), None)
    finished_col = next((col for col in df.columns if 'FINISH' in col.upper()), None)
    
    if not all([tp_col, sl_col]):
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
    
    # Calculate total signals and completion rate if available
    if total_signal_col:
        total_signals = pd.to_numeric(df[total_signal_col], errors='coerce').fillna(0).sum()
        stats['total_signals'] = int(total_signals)
        
        # Calculate completion rate
        if total_signals > 0:
            stats['completion_rate'] = 100 * (stats['total_tp'] + stats['total_sl']) / total_signals
        else:
            stats['completion_rate'] = 0
    elif finished_col:
        # Use finished column if available
        finished = pd.to_numeric(df[finished_col], errors='coerce').fillna(0).sum()
        stats['total_signals'] = int(finished) + 0  # Assuming finished = TP + SL
        stats['completion_rate'] = 100  # Assuming 100% completion if using finished
    else:
        # Estimate total signals if neither is available
        stats['total_signals'] = int(stats['total_tp'] + stats['total_sl'])
        stats['completion_rate'] = 100  # Assume 100% completion rate
    
    return stats

# -------- VISUALIZATION FUNCTIONS --------
def create_winrate_chart(df, lang):
    """Create a line chart for winrate trend"""
    # Need date and winrate columns
    if df is None or df.empty or 'Winrate_num' not in df.columns:
        return None
    
    # Sort by date if available
    if 'Date_parsed' in df.columns and not df['Date_parsed'].isna().all():
        # Make sure we're working with clean data
        df = df.copy()
        df['Date_parsed'] = pd.to_datetime(df['Date_parsed'], errors='coerce')
        df = df.sort_values('Date_parsed')
    
    # Use a custom domain for the x-axis to ensure proper ordering
    domain = df['Date_display'].tolist()
    
    chart = alt.Chart(df).mark_line(point=True).encode(
        x=alt.X('Date_display:O', title=lang['date'], sort=domain),
        y=alt.Y('Winrate_num:Q', title=lang['winrate'] + ' (%)', scale=alt.Scale(domain=[0, 100])),
        tooltip=['Date_display', 'Winrate_num', alt.Tooltip('TP', title='TP'), alt.Tooltip('SL', title='SL')]
    ).properties(height=300)
    
    return chart

def create_tpsl_chart(df, lang):
    """Create a bar chart comparing TP vs SL by date"""
    if df is None or df.empty:
        return None
    
    # Determine TP and SL column names
    tp_col = next((col for col in df.columns if col.upper() == 'TP' or 'TAKE' in col.upper()), None)
    sl_col = next((col for col in df.columns if col.upper() == 'SL' or 'STOP' in col.upper()), None)
    
    if not tp_col or not sl_col:
        return None
    
    # Sort by date if available
    if 'Date_parsed' in df.columns and not df['Date_parsed'].isna().all():
        # Make sure we're working with clean data
        df = df.copy()
        df['Date_parsed'] = pd.to_datetime(df['Date_parsed'], errors='coerce')
        df = df.sort_values('Date_parsed')
    
    # Create a copy with required columns for melting
    chart_df = df[['Date_display', tp_col, sl_col]].copy()
    
    # Rename columns to standard TP/SL for chart
    chart_df.rename(columns={tp_col: 'TP', sl_col: 'SL'}, inplace=True)
    
    # Melt the dataframe for the stacked bar chart
    df_melted = pd.melt(
        chart_df, 
        id_vars=['Date_display'], 
        value_vars=['TP', 'SL'],
        var_name='Type', 
        value_name='Count'
    )
    
    # Use a custom domain for the x-axis to ensure proper ordering
    domain = df['Date_display'].tolist()
    
    chart = alt.Chart(df_melted).mark_bar().encode(
        x=alt.X('Date_display:O', title=lang['date'], sort=domain),
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
    
    # Tambahkan gambar di bawah judul
    # Coba cari gambar dari direktori lokal atau dari GitHub
    try:
        # Untuk Streamlit Cloud dan GitHub, gunakan format ini
        from PIL import Image
        
        # Cek apakah file gambar ada di direktori saat ini
        image_path = Path(IMAGE_PATH)
        if image_path.exists():
            st.image(IMAGE_PATH, use_column_width=True)
        else:
            # Alternatif jika gambar tidak ditemukan
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
                            # col6 dibiarkan kosong
                        
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
                        
                        # Determine columns to display
                        date_col = next((col for col in filtered_df.columns if 'date' in col.lower() and not col.startswith('Date_')), None)
                        numeric_cols = [col for col in filtered_df.columns if col in ['Total_Signal', 'TP', 'SL', 'Finished']]
                        winrate_col = next((col for col in filtered_df.columns if 'winrate' in col.lower() and col != 'Winrate_num'), None)
                        
                        display_cols = []
                        if date_col:
                            display_cols.append(date_col)
                        display_cols.extend(numeric_cols)
                        if winrate_col:
                            display_cols.append(winrate_col)
                        
                        # Sort dataframe by Date_parsed before displaying
                        if 'Date_parsed' in filtered_df.columns:
                            # Ensure Date_parsed is datetime type
                            filtered_df['Date_parsed'] = pd.to_datetime(filtered_df['Date_parsed'], errors='coerce')
                            # Only sort if we have valid dates
                            if not filtered_df['Date_parsed'].isna().all():
                                display_df = filtered_df.sort_values('Date_parsed')
                            else:
                                display_df = filtered_df
                        else:
                            display_df = filtered_df
                        
                        # Display the data table with specified columns or all columns if none specified
                        st.dataframe(
                            display_df[display_cols] if display_cols else display_df,
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
