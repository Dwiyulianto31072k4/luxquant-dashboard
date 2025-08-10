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
from typing import Optional, Dict, Any

# ==================== CONFIGURATION ====================
class Config:
    """Central configuration class"""
    SPREADSHEET_ID = "1g3XL1EllHoWV3jhmi7gT3at6MtCNTJBo8DQ1WyWhMEo"
    SHEET_NAME = "Sheet1"
    
    # Binance Color Scheme - Enhanced for better readability
    COLORS = {
        'primary': '#F0B90B',      # Binance Yellow
        'secondary': '#EAECEF',    # Light Gray Text
        'background': '#0B0E11',   # Dark Background
        'card_bg': '#181A20',      # Card Background
        'border': '#2B3139',       # Border Gray
        'text_primary': '#FFFFFF', # Primary Text - White for max contrast
        'text_secondary': '#E8E8E8', # Secondary Text - Lighter for better readability
        'text_muted': '#C7C7C7',   # Muted text - Better contrast than previous
        'success': '#0ECB81',      # Binance Green
        'danger': '#F6465D',       # Binance Red
        'warning': '#F0B90B',      # Binance Yellow
        'grid': '#2B3139',         # Grid Lines
        'hover': '#1E2329'         # Hover Background
    }

# ==================== STYLING ====================
class StyleManager:
    """Manages all CSS styling for the application"""
    
    @staticmethod
    def apply_custom_css():
        """Apply comprehensive responsive CSS styling with improved readability"""
        st.markdown("""
        <style>
        /* Import Binance-like fonts */
        @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@300;400;500;600;700&display=swap');
        
        /* Main app styling with Binance colors */
        .stApp {
            background: #0B0E11;
            color: #FFFFFF;
            font-family: 'IBM Plex Sans', sans-serif;
        }
        
        /* Responsive container */
        .main-container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 0 1rem;
        }
        
        /* Header styling with Binance theme - Responsive */
        .main-header {
            text-align: center;
            padding: 2rem 1rem;
            background: linear-gradient(135deg, #181A20 0%, #1E2329 100%);
            border-radius: 16px;
            margin-bottom: 2rem;
            border: 1px solid #2B3139;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
        }
        
        .main-title {
            font-size: clamp(1.8rem, 4vw, 3.2rem);
            font-weight: 700;
            background: linear-gradient(135deg, #F0B90B 0%, #FCD535 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 0.8rem;
            text-shadow: 0 0 30px rgba(240, 185, 11, 0.4);
            font-family: 'IBM Plex Sans', sans-serif;
            line-height: 1.2;
        }
        
        .subtitle {
            font-size: clamp(0.9rem, 2vw, 1.1rem);
            color: #E8E8E8;
            margin-bottom: 1rem;
            font-weight: 400;
            line-height: 1.5;
            max-width: 600px;
            margin-left: auto;
            margin-right: auto;
        }
        
        .accuracy-badge {
            background: linear-gradient(135deg, #F0B90B 0%, #FCD535 100%);
            color: #0B0E11;
            padding: 0.6rem 1.2rem;
            border-radius: 8px;
            font-weight: 600;
            display: inline-block;
            margin: 0.3rem;
            font-size: clamp(0.8rem, 2vw, 0.95rem);
            box-shadow: 0 4px 12px rgba(240, 185, 11, 0.3);
            transition: all 0.3s ease;
        }
        
        /* Mobile specific badge adjustments */
        @media (max-width: 768px) {
            .accuracy-badge {
                display: block;
                margin: 0.5rem auto;
                max-width: 280px;
                text-align: center;
            }
        }
        
        .accuracy-badge:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(240, 185, 11, 0.4);
        }
        
        /* Binance-style stats cards - Enhanced readability */
        .stat-card {
            background: linear-gradient(135deg, #181A20 0%, #1E2329 100%);
            border: 1px solid #2B3139;
            border-radius: 12px;
            padding: clamp(1rem, 3vw, 1.8rem);
            text-align: center;
            min-height: 120px;
            transition: all 0.3s ease;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
            display: flex;
            flex-direction: column;
            justify-content: center;
        }
        
        .stat-card:hover {
            border-color: #F0B90B;
            transform: translateY(-2px);
            box-shadow: 0 4px 20px rgba(240, 185, 11, 0.1);
        }
        
        .stat-icon {
            font-size: clamp(1.5rem, 4vw, 2.2rem);
            margin-bottom: 0.5rem;
            filter: brightness(1.2);
        }
        
        .stat-value {
            font-size: clamp(1.8rem, 5vw, 2.8rem);
            font-weight: 700;
            color: #F0B90B;
            margin: 0.5rem 0;
            text-shadow: 0 0 15px rgba(240, 185, 11, 0.3);
            font-family: 'IBM Plex Sans', sans-serif;
            line-height: 1.1;
        }
        
        .stat-label {
            font-size: clamp(0.75rem, 2vw, 0.9rem);
            color: #FFFFFF;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            font-weight: 500;
            line-height: 1.3;
        }
        
        /* Chart containers - Enhanced */
        .chart-container {
            background: linear-gradient(135deg, #181A20 0%, #1E2329 100%);
            border: 1px solid #2B3139;
            border-radius: 12px;
            padding: clamp(0.8rem, 2vw, 1.5rem);
            margin: 1rem 0;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
            overflow-x: auto;
        }
        
        /* Binance-style buttons - Enhanced */
        .stButton button {
            background: linear-gradient(135deg, #F0B90B 0%, #FCD535 100%);
            color: #0B0E11;
            border: none;
            border-radius: 8px;
            padding: clamp(0.7rem, 2vw, 0.9rem) clamp(1.5rem, 4vw, 2.2rem);
            font-weight: 600;
            font-size: clamp(0.9rem, 2vw, 1rem);
            transition: all 0.3s ease;
            width: 100%;
            box-shadow: 0 4px 12px rgba(240, 185, 11, 0.3);
            text-transform: uppercase;
            letter-spacing: 0.5px;
            font-family: 'IBM Plex Sans', sans-serif;
            min-height: 48px;
        }
        
        .stButton button:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(240, 185, 11, 0.4);
            background: linear-gradient(135deg, #FCD535 0%, #F0B90B 100%);
        }
        
        /* Radio buttons with better visibility */
        .stRadio > div {
            background: linear-gradient(135deg, #181A20 0%, #1E2329 100%);
            border-radius: 12px;
            padding: clamp(1rem, 3vw, 1.5rem);
            border: 1px solid #2B3139;
            text-align: center;
        }
        
        .stRadio label {
            color: #FFFFFF !important;
            font-size: clamp(0.9rem, 2vw, 1.1rem) !important;
            font-weight: 600 !important;
        }
        
        /* Radio button text styling */
        .stRadio div[role="radiogroup"] label {
            color: #FFFFFF !important;
        }
        
        .stRadio div[role="radiogroup"] span {
            color: #FFFFFF !important;
        }
        
        /* Selected radio button */
        .stRadio div[role="radiogroup"] input:checked + div {
            color: #F0B90B !important;
        }
        
        /* Radio button hover state */
        .stRadio div[role="radiogroup"] label:hover {
            color: #F0B90B !important;
        }
        
        .stRadio div[role="radiogroup"] {
            display: flex;
            flex-direction: column;
            gap: 0.8rem;
            align-items: center;
        }
        
        @media (min-width: 768px) {
            .stRadio div[role="radiogroup"] {
                flex-direction: row;
                justify-content: center;
                gap: 2rem;
            }
        }
        
        /* Data table styling - Enhanced readability */
        .stDataFrame {
            background: #181A20;
            border-radius: 8px;
            border: 1px solid #2B3139;
            overflow-x: auto;
        }
        
        .stDataFrame table {
            color: #FFFFFF !important;
        }
        
        .stDataFrame th {
            background-color: #2B3139 !important;
            color: #F0B90B !important;
            font-weight: 600 !important;
        }
        
        .stDataFrame td {
            color: #FFFFFF !important;
            background-color: #181A20 !important;
        }
        
        @media (max-width: 768px) {
            .stDataFrame {
                font-size: 0.85rem;
            }
        }
        
        /* Text color overrides - Enhanced contrast */
        .stMarkdown p, .stMarkdown span, .stMarkdown div {
            color: #FFFFFF !important;
        }
        
        h1, h2, h3, h4, h5, h6 {
            color: #F0B90B !important;
            font-family: 'IBM Plex Sans', sans-serif !important;
            font-size: clamp(1.2rem, 3vw, 1.8rem) !important;
            text-align: center;
            margin-bottom: 1rem !important;
        }
        
        /* Success/Warning/Error messages */
        .stSuccess {
            background: linear-gradient(135deg, #0ECB81 0%, #03A66D 100%);
            border-radius: 8px;
            border: none;
            margin: 1rem 0;
            color: #FFFFFF !important;
        }
        
        .stWarning {
            background: linear-gradient(135deg, #F0B90B 0%, #D9A441 100%);
            border-radius: 8px;
            border: none;
            margin: 1rem 0;
            color: #0B0E11 !important;
        }
        
        .stError {
            background: linear-gradient(135deg, #F6465D 0%, #D73C52 100%);
            border-radius: 8px;
            border: none;
            margin: 1rem 0;
            color: #FFFFFF !important;
        }
        
        /* Streamlit specific overrides */
        .stSelectbox label, .stRadio label, .stTextInput label {
            color: #FFFFFF !important;
            font-weight: 600 !important;
        }
        
        /* Period selector responsive */
        .period-selector-container {
            max-width: 600px;
            margin: 0 auto;
            padding: 0 1rem;
        }
        
        /* Footer responsive */
        .footer-container {
            padding: clamp(1rem, 3vw, 2rem);
            margin-top: 2rem;
            text-align: center;
        }
        
        /* Mobile specific optimizations */
        @media (max-width: 480px) {
            .main-header {
                padding: 1.5rem 0.8rem;
                margin-bottom: 1.5rem;
            }
            
            .chart-container {
                padding: 0.8rem;
                margin: 0.8rem 0;
            }
            
            .stat-card {
                min-height: 100px;
                padding: 1rem;
            }
        }
        
        /* Large screen optimizations */
        @media (min-width: 1200px) {
            .stApp > .main > .block-container {
                max-width: 1200px;
                margin: 0 auto;
            }
        }
        </style>
        """, unsafe_allow_html=True)

# ==================== DATA MANAGER ====================
class DataManager:
    """Handles all data operations including Google Sheets connection"""
    
    def __init__(self):
        self._sheet = None
    
    @st.cache_resource
    def connect_to_gsheet(_self):
        """Establish connection to Google Sheets"""
        try:
            credentials_info = _self._get_credentials()
            credentials = Credentials.from_service_account_info(
                credentials_info,
                scopes=[
                    "https://www.googleapis.com/auth/spreadsheets",
                    "https://www.googleapis.com/auth/drive",
                ]
            )
            client = gspread.authorize(credentials)
            sheet = client.open_by_key(Config.SPREADSHEET_ID).worksheet(Config.SHEET_NAME)
            return sheet
        except Exception as e:
            st.error(f"Google Sheets connection error: {str(e)}")
            raise e
    
    def _get_credentials(self) -> Dict[str, Any]:
        """Get Google Sheets credentials from various sources"""
        if "gcp_service_account" in st.secrets:
            return st.secrets["gcp_service_account"]
        elif "credentials_json" in st.secrets:
            if isinstance(st.secrets["credentials_json"], dict):
                return st.secrets["credentials_json"]
            else:
                return json.loads(st.secrets["credentials_json"])
        else:
            credentials_json_str = os.environ.get("CREDENTIALS_JSON")
            if credentials_json_str:
                return json.loads(credentials_json_str)
            else:
                raise ValueError("Google Sheets credentials not found")
    
    def get_sheet_data(self) -> Optional[pd.DataFrame]:
        """Get all data from Google Sheets and convert to DataFrame"""
        try:
            sheet = self.connect_to_gsheet()
            all_values = sheet.get_all_values()
            
            if not all_values or len(all_values) < 2:
                return None
            
            header_row = all_values[0]
            data_rows = all_values[1:]
            
            # Find last row with data
            last_index = self._find_last_data_row(data_rows)
            valid_data_rows = data_rows[:last_index + 1] if data_rows else []
            
            if not valid_data_rows:
                return None
            
            df = pd.DataFrame(valid_data_rows, columns=header_row)
            df = self._clean_dataframe(df)
            
            return df if not df.empty else None
            
        except Exception as e:
            st.error(f"Error fetching data: {str(e)}")
            return None
    
    def _find_last_data_row(self, data_rows: list) -> int:
        """Find the last row containing data"""
        last_index = 0
        for i, row in enumerate(data_rows):
            if any(row[:6]):  # Check first 6 columns for data
                last_index = i
        return last_index
    
    def _clean_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and process the DataFrame"""
        # Remove empty rows
        df = df[df.iloc[:, :6].any(axis=1)]
        df.columns = df.columns.str.strip()
        
        # Map columns
        df = self._map_columns(df)
        
        # Process numeric columns
        df = self._process_numeric_columns(df)
        
        # Process winrate
        df = self._process_winrate(df)
        
        # Process dates
        df = self._process_dates(df)
        
        # Sort by date if available
        if 'Date_parsed' in df.columns and not df['Date_parsed'].isna().all():
            df['Date_parsed'] = pd.to_datetime(df['Date_parsed'], errors='coerce')
            df = df.sort_values('Date_parsed')
        
        return df
    
    def _map_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Map column names to standard format"""
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
        
        return df.rename(columns=column_mapping)
    
    def _process_numeric_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Process numeric columns"""
        numeric_columns = ['Total_Signal', 'Finished', 'TP', 'SL']
        for col in numeric_columns:
            if col in df.columns:
                df[col] = df[col].astype(str).str.replace(r'[^\d]', '', regex=True)
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)
        return df
    
    def _process_winrate(self, df: pd.DataFrame) -> pd.DataFrame:
        """Process winrate column"""
        if 'Winrate_pct' in df.columns:
            df['Winrate_num'] = df['Winrate_pct'].astype(str).str.replace('%', '').str.strip()
            df['Winrate_num'] = pd.to_numeric(df['Winrate_num'], errors='coerce').fillna(0)
        return df
    
    def _process_dates(self, df: pd.DataFrame) -> pd.DataFrame:
        """Process date column"""
        if 'Date' not in df.columns:
            return df
        
        df['Date_parsed'] = None
        df['Date_display'] = df['Date'].astype(str)
        
        for idx, date_str in enumerate(df['Date']):
            if pd.isna(date_str) or date_str == '' or str(date_str).strip() == '':
                continue
            
            parsed_date = self._parse_date_string(str(date_str).strip(), idx, len(df))
            if parsed_date:
                df.at[idx, 'Date_parsed'] = parsed_date
                df.at[idx, 'Date_display'] = parsed_date.strftime('%Y-%m-%d')
        
        return df
    
    def _parse_date_string(self, date_str: str, idx: int, total_rows: int) -> Optional[datetime.datetime]:
        """Parse individual date string"""
        # Handle date ranges
        range_pattern = re.search(r'(\d{2})/(\d{2})-(\d{2})/(\d{2})', date_str)
        if range_pattern:
            start_month, start_day, end_month, end_day = range_pattern.groups()
            try:
                current_year = datetime.datetime.now().year
                return pd.to_datetime(f"{current_year}-{end_month}-{end_day}", format='%Y-%m-%d')
            except:
                pass
        
        # Handle standard date formats
        date_patterns = [
            r'(\d{4})-(\d{1,2})-(\d{1,2})',
            r'(\d{1,2})/(\d{1,2})/(\d{4})',
            r'(\d{1,2})-(\d{1,2})-(\d{4})',
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, date_str)
            if match:
                try:
                    if pattern == date_patterns[0]:
                        year, month, day = match.groups()
                    else:
                        month, day, year = match.groups()
                    
                    return pd.to_datetime(f"{year}-{month}-{day}", format='%Y-%m-%d')
                except:
                    continue
        
        # Try pandas parsing
        try:
            parsed_date = pd.to_datetime(date_str, errors='coerce')
            if not pd.isna(parsed_date):
                return parsed_date
        except:
            pass
        
        # Default fallback
        base_date = datetime.datetime.now() - pd.Timedelta(days=total_rows-idx-1)
        return base_date

# ==================== ANALYTICS ENGINE ====================
class AnalyticsEngine:
    """Handles all analytics and data processing operations"""
    
    @staticmethod
    def filter_data_by_period(df: Optional[pd.DataFrame], period: str) -> Optional[pd.DataFrame]:
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
            return filtered_df if not filtered_df.empty else df.tail(7)
        elif period == 'month':
            start_date = today - datetime.timedelta(days=30)
            filtered_df = df[df['Date_parsed'] >= start_date]
            return filtered_df if not filtered_df.empty else df.tail(30)
        else:
            return df
    
    @staticmethod
    def calculate_statistics(df: Optional[pd.DataFrame]) -> Optional[Dict[str, Any]]:
        """Calculate trading statistics from DataFrame"""
        if df is None or df.empty:
            return None
        
        # Check required columns
        if 'TP' not in df.columns or 'SL' not in df.columns:
            return None
        
        tp_data = pd.to_numeric(df['TP'], errors='coerce').fillna(0)
        sl_data = pd.to_numeric(df['SL'], errors='coerce').fillna(0)
        
        stats = {
            'total_tp': int(tp_data.sum()),
            'total_sl': int(sl_data.sum()),
        }
        
        # Calculate winrate
        if stats['total_tp'] + stats['total_sl'] > 0:
            stats['overall_winrate'] = 100 * stats['total_tp'] / (stats['total_tp'] + stats['total_sl'])
        else:
            stats['overall_winrate'] = 0
        
        # Calculate total signals and completion rate
        if 'Total_Signal' in df.columns:
            total_signals = pd.to_numeric(df['Total_Signal'], errors='coerce').fillna(0).sum()
            stats['total_signals'] = int(total_signals)
            
            if total_signals > 0:
                finished_total = stats['total_tp'] + stats['total_sl']
                stats['completion_rate'] = 100 * finished_total / total_signals
            else:
                stats['completion_rate'] = 0
        else:
            stats['total_signals'] = int(stats['total_tp'] + stats['total_sl'])
            stats['completion_rate'] = 100
        
        return stats

# ==================== CHART BUILDER ====================
class ChartBuilder:
    """Handles all chart creation and visualization"""
    
    @staticmethod
    def create_winrate_chart(df: Optional[pd.DataFrame]) -> Optional[go.Figure]:
        """Create an enhanced winrate chart with better readability"""
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
            line=dict(color=Config.COLORS['primary'], width=4),
            marker=dict(size=10, color=Config.COLORS['primary'], 
                       line=dict(width=3, color=Config.COLORS['background'])),
            hovertemplate='<b>Date:</b> %{x}<br><b>Winrate:</b> %{y}%<extra></extra>'
        ))
        
        # Add average line
        avg_winrate = df['Winrate_num'].mean()
        fig.add_hline(y=avg_winrate, line_dash="dash", line_color=Config.COLORS['primary'], 
                      line_width=2, annotation_text=f"Average: {avg_winrate:.1f}%", 
                      annotation_font_color=Config.COLORS['primary'], annotation_font_size=14)
        
        # Add target line
        fig.add_hline(y=70, line_dash="dot", line_color="#FCD535", line_width=2,
                      annotation_text="Target: 70%", 
                      annotation_font_color="#FCD535", annotation_font_size=12)
        
        fig.update_layout(
            title=dict(text="Winrate Trend", font=dict(size=18, color=Config.COLORS['primary'])),
            xaxis_title=dict(text="Date", font=dict(color=Config.COLORS['text_primary'])),
            yaxis_title=dict(text="Winrate (%)", font=dict(color=Config.COLORS['text_primary'])),
            plot_bgcolor=Config.COLORS['background'],
            paper_bgcolor=Config.COLORS['background'],
            font=dict(color=Config.COLORS['text_primary'], size=12),
            height=350,
            showlegend=False,
            yaxis=dict(range=[0, 100], gridcolor=Config.COLORS['grid'], 
                      tickfont=dict(color=Config.COLORS['text_primary'], size=11), dtick=10),
            xaxis=dict(gridcolor=Config.COLORS['grid'], 
                      tickfont=dict(color=Config.COLORS['text_primary'], size=11)),
            margin=dict(l=60, r=60, t=60, b=60)
        )
        
        return fig
    
    @staticmethod
    def create_tpsl_chart(df: Optional[pd.DataFrame]) -> Optional[go.Figure]:
        """Create TP/SL comparison chart with better readability"""
        if df is None or df.empty or 'TP' not in df.columns or 'SL' not in df.columns:
            return None
        
        if 'Date_parsed' in df.columns and not df['Date_parsed'].isna().all():
            df = df.copy()
            df['Date_parsed'] = pd.to_datetime(df['Date_parsed'], errors='coerce')
            df = df.sort_values('Date_parsed')
        
        fig = go.Figure()
        
        # Add TP bars with Binance green
        fig.add_trace(go.Bar(
            x=df['Date_display'], y=df['TP'], name='Take Profit',
            marker_color=Config.COLORS['success'],
            hovertemplate='<b>Date:</b> %{x}<br><b>TP:</b> %{y}<extra></extra>',
            opacity=0.9
        ))
        
        # Add SL bars with Binance red
        fig.add_trace(go.Bar(
            x=df['Date_display'], y=df['SL'], name='Stop Loss',
            marker_color=Config.COLORS['danger'],
            hovertemplate='<b>Date:</b> %{x}<br><b>SL:</b> %{y}<extra></extra>',
            opacity=0.9
        ))
        
        fig.update_layout(
            title=dict(text="TP vs SL", font=dict(size=18, color=Config.COLORS['primary'])),
            xaxis_title=dict(text="Date", font=dict(color=Config.COLORS['text_primary'])),
            yaxis_title=dict(text="Count", font=dict(color=Config.COLORS['text_primary'])),
            plot_bgcolor=Config.COLORS['background'],
            paper_bgcolor=Config.COLORS['background'],
            font=dict(color=Config.COLORS['text_primary'], size=12),
            height=350, barmode='group',
            legend=dict(x=0, y=1, font=dict(color=Config.COLORS['text_primary'], size=12),
                       bgcolor=Config.COLORS['background']),
            yaxis=dict(gridcolor=Config.COLORS['grid'], 
                      tickfont=dict(color=Config.COLORS['text_primary'], size=11)),
            xaxis=dict(gridcolor=Config.COLORS['grid'], 
                      tickfont=dict(color=Config.COLORS['text_primary'], size=11)),
            margin=dict(l=60, r=60, t=60, b=60)
        )
        
        return fig
    
    @staticmethod
    def create_combined_dashboard_chart(df: Optional[pd.DataFrame]) -> Optional[go.Figure]:
        """Create combined dashboard chart with enhanced readability"""
        if df is None or df.empty:
            return None
        
        # Create subplots
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('Winrate Trend', 'TP vs SL', 'Cumulative Performance', 'Daily Signals'),
            specs=[[{"secondary_y": False}, {"secondary_y": False}],
                   [{"secondary_y": False}, {"secondary_y": False}]],
            vertical_spacing=0.12, horizontal_spacing=0.1
        )
        
        # Winrate trend
        if 'Winrate_num' in df.columns:
            fig.add_trace(
                go.Scatter(x=df['Date_display'], y=df['Winrate_num'], 
                          mode='lines+markers', name='Winrate',
                          line=dict(color=Config.COLORS['primary'], width=3),
                          marker=dict(size=6, color=Config.COLORS['primary'])),
                row=1, col=1
            )
            fig.update_yaxes(range=[0, 100], row=1, col=1)
        
        # TP vs SL
        if 'TP' in df.columns and 'SL' in df.columns:
            fig.add_trace(
                go.Bar(x=df['Date_display'], y=df['TP'], name='TP', 
                       marker_color=Config.COLORS['success'], opacity=0.9),
                row=1, col=2
            )
            fig.add_trace(
                go.Bar(x=df['Date_display'], y=df['SL'], name='SL',
                       marker_color=Config.COLORS['danger'], opacity=0.9),
                row=1, col=2
            )
            
            # Cumulative performance
            cumulative_tp = df['TP'].cumsum()
            cumulative_sl = df['SL'].cumsum()
            fig.add_trace(
                go.Scatter(x=df['Date_display'], y=cumulative_tp, 
                          mode='lines', name='Cumulative TP',
                          line=dict(color=Config.COLORS['success'], width=3)),
                row=2, col=1
            )
            fig.add_trace(
                go.Scatter(x=df['Date_display'], y=cumulative_sl,
                          mode='lines', name='Cumulative SL',
                          line=dict(color=Config.COLORS['danger'], width=3)),
                row=2, col=1
            )
        
        # Daily signals
        if 'Total_Signal' in df.columns:
            fig.add_trace(
                go.Bar(x=df['Date_display'], y=df['Total_Signal'], 
                       name='Daily Signals', marker_color=Config.COLORS['primary'], opacity=0.9),
                row=2, col=2
            )
        
        # Update layout with better readability
        fig.update_layout(
            height=700,
            plot_bgcolor=Config.COLORS['background'],
            paper_bgcolor=Config.COLORS['background'],
            font=dict(color=Config.COLORS['text_primary'], size=12),
            title_text="LuxQuant VIP Trading Dashboard",
            title_font=dict(size=20, color=Config.COLORS['primary']),
            showlegend=True,
            legend=dict(font=dict(color=Config.COLORS['text_primary']),
                       bgcolor=Config.COLORS['background'])
        )
        
        # Update subplot titles with better contrast
        for i in fig['layout']['annotations']:
            i['font'] = dict(color=Config.COLORS['primary'], size=14)
        
        # Update axes with better readability
        fig.update_xaxes(gridcolor=Config.COLORS['grid'],
                        tickfont=dict(color=Config.COLORS['text_primary'], size=10))
        fig.update_yaxes(gridcolor=Config.COLORS['grid'],
                        tickfont=dict(color=Config.COLORS['text_primary'], size=10))
        
        return fig

# ==================== UI COMPONENTS ====================
class UIComponents:
    """Manages all UI components and rendering"""
    
    @staticmethod
    def render_header():
        """Render main header with branding"""
        st.markdown("""
        <div class="main-header">
            <div class="main-title">LuxQuant VIP | 智汇尊享会</div>
            <div class="subtitle">Tools for Automated Crypto Trading Setup 24/7</div>
            <div class="subtitle">Help traders identify market opportunities without having to monitor charts continuously.</div>
            <div class="accuracy-badge">⚡ 24/7 Automated Signals ⚡</div>
            <div class="accuracy-badge" style="margin-top: 0.5rem;">Historical Accuracy of 87.9% (No Future Guarantee)</div>
        </div>
        """, unsafe_allow_html=True)
    
    @staticmethod
    def render_period_selector():
        """Render responsive period selector"""
        st.markdown('<h3 style="color: #F0B90B; font-size: clamp(1.2rem, 3vw, 1.8rem); font-weight: 700; margin-bottom: 1rem; text-align: center;">📊 Trading Performance Analysis</h3>', unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Use responsive container
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            st.markdown('<div class="period-selector-container">', unsafe_allow_html=True)
            st.markdown('<p style="color: #FFFFFF; font-size: clamp(1rem, 2.5vw, 1.2rem); font-weight: 600; margin-bottom: 1rem; text-align: center;">Select Time Period:</p>', unsafe_allow_html=True)
            
            period = st.radio(
                "",
                options=["week", "month", "all"],
                format_func=lambda x: {"week": "📅 Last Week", "month": "📆 Last Month", "all": "📈 All Time"}[x],
                horizontal=True,
                key="period_selector"
            )
            
            st.markdown('<div style="margin-top: 1.5rem;"></div>', unsafe_allow_html=True)
            load_button = st.button("🚀 LOAD TRADING STATISTICS", use_container_width=True, type="primary")
            st.markdown('</div>', unsafe_allow_html=True)
        
        return period, load_button
    
    @staticmethod
    def render_stats_cards(stats: Dict[str, Any]):
        """Render statistics cards with completion rate instead of global users"""
        st.markdown('<h3 style="color: #F0B90B; font-size: clamp(1.2rem, 3vw, 1.8rem); font-weight: 700; margin-bottom: 1.5rem; text-align: center;">📈 Key Performance Metrics</h3>', unsafe_allow_html=True)
        
        # Use responsive columns
        col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
        
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
                <div class="stat-icon">✅</div>
                <div class="stat-value">{stats['completion_rate']:.1f}%</div>
                <div class="stat-label">Completion<br>Rate</div>
            </div>
            """, unsafe_allow_html=True)
    
    @staticmethod
    def render_insights(stats: Dict[str, Any], filtered_df: pd.DataFrame):
        """Render trading insights with enhanced readability"""
        st.markdown('<h3 style="color: #F0B90B; font-size: clamp(1.2rem, 3vw, 1.8rem); font-weight: 700; margin: 2rem 0 1.5rem 0; text-align: center;">💡 Trading Insights</h3>', unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Performance assessment
            if stats['overall_winrate'] >= 70:
                insight_color = Config.COLORS['success']
                insight_icon = "🟢"
                insight_text = "Excellent Performance"
            elif stats['overall_winrate'] >= 60:
                insight_color = Config.COLORS['warning']
                insight_icon = "🟡"
                insight_text = "Good Performance"
            else:
                insight_color = Config.COLORS['danger']
                insight_icon = "🔴"
                insight_text = "Needs Improvement"
            
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-icon">{insight_icon}</div>
                <div class="stat-label" style="color: {insight_color}; font-weight: 600;">{insight_text}</div>
                <div style="font-size: clamp(0.75rem, 2vw, 0.9rem); margin-top: 0.5rem; color: #FFFFFF;">
                    Winrate: {stats['overall_winrate']:.1f}%
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            # Trend analysis
            if len(filtered_df) >= 3 and 'Winrate_num' in filtered_df.columns:
                recent_avg = filtered_df['Winrate_num'].tail(3).mean()
                overall_avg = filtered_df['Winrate_num'].mean()
                
                if recent_avg > overall_avg:
                    trend_icon = "📈"
                    trend_text = "Improving Trend"
                    trend_color = Config.COLORS['success']
                else:
                    trend_icon = "📉"
                    trend_text = "Declining Trend"
                    trend_color = Config.COLORS['danger']
            else:
                trend_icon = "📊"
                trend_text = "Stable Performance"
                trend_color = "#2196F3"
            
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-icon">{trend_icon}</div>
                <div class="stat-label" style="color: {trend_color}; font-weight: 600;">{trend_text}</div>
                <div style="font-size: clamp(0.75rem, 2vw, 0.9rem); margin-top: 0.5rem; color: #FFFFFF;">
                    Recent Performance Analysis
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            # Completion rate insight
            if stats['completion_rate'] >= 90:
                completion_icon = "🟢"
                completion_text = "High Completion"
                completion_color = Config.COLORS['success']
            elif stats['completion_rate'] >= 70:
                completion_icon = "🟡"
                completion_text = "Good Completion"
                completion_color = Config.COLORS['warning']
            else:
                completion_icon = "🔴"
                completion_text = "Low Completion"
                completion_color = Config.COLORS['danger']
            
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-icon">{completion_icon}</div>
                <div class="stat-label" style="color: {completion_color}; font-weight: 600;">{completion_text}</div>
                <div style="font-size: clamp(0.75rem, 2vw, 0.9rem); margin-top: 0.5rem; color: #FFFFFF;">
                    {stats['completion_rate']:.1f}% Signals Closed
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    @staticmethod
    def render_footer():
        """Render responsive footer with better contrast"""
        st.markdown("---")
        st.markdown("""
        <div class='footer-container' style='text-align: center; padding: clamp(1rem, 3vw, 2rem); background: linear-gradient(135deg, rgba(255, 255, 255, 0.1) 0%, rgba(255, 255, 255, 0.05) 100%); backdrop-filter: blur(10px); border-radius: 15px; margin-top: 2rem;'>
            <h3 style='color: #F0B90B; margin-bottom: 1rem; font-size: clamp(1.2rem, 3vw, 1.5rem);'>Ready to Start Automated Trading?</h3>
            <p style='color: #FFFFFF; margin-bottom: 1.5rem; font-size: clamp(0.9rem, 2vw, 1rem);'>Join thousands of traders using LuxQuant VIP for automated crypto trading signals.</p>
            <p style='color: #C7C7C7; font-size: clamp(0.8rem, 1.5vw, 0.9rem);'>Made with ❤️ by LuxQuant VIP | 智汇尊享会 | Historical accuracy does not guarantee future results</p>
        </div>
        """, unsafe_allow_html=True)

# ==================== MAIN APPLICATION ====================
class LuxQuantDashboard:
    """Main application class that orchestrates all components"""
    
    def __init__(self):
        self.data_manager = DataManager()
        self.analytics = AnalyticsEngine()
        self.chart_builder = ChartBuilder()
        self.ui = UIComponents()
    
    def configure_page(self):
        """Configure Streamlit page with responsive settings"""
        st.set_page_config(
            page_title="LuxQuant VIP | Trading Dashboard",
            page_icon="📊",
            layout="wide",
            initial_sidebar_state="collapsed",
        )
        
        # Initialize session state
        if 'mobile_view' not in st.session_state:
            st.session_state.mobile_view = False
    
    def run(self):
        """Main application runner"""
        self.configure_page()
        StyleManager.apply_custom_css()
        
        # Render header
        self.ui.render_header()
        
        # Period selector and load button
        period, load_button = self.ui.render_period_selector()
        
        if load_button:
            self._handle_data_loading(period)
        
        # Action buttons and footer
        self.ui.render_action_buttons()
        self.ui.render_footer()
    
    def _handle_data_loading(self, period: str):
        """Handle data loading and display logic"""
        with st.spinner("🔄 Loading trading data..."):
            try:
                # Get and filter data
                df = self.data_manager.get_sheet_data()
                
                if df is None or df.empty:
                    st.warning("⚠️ No trading data available for the selected period.")
                    return
                
                filtered_df = self.analytics.filter_data_by_period(df, period)
                
                if filtered_df is None or filtered_df.empty:
                    st.warning("⚠️ No data available for the selected period.")
                    return
                
                st.success("✅ Trading data loaded successfully!")
                
                # Calculate and display statistics
                stats = self.analytics.calculate_statistics(filtered_df)
                
                if stats:
                    self.ui.render_stats_cards(stats)
                
                # Render charts
                self._render_charts(filtered_df)
                
                # Render data table
                self._render_data_table(filtered_df)
                
                # Render insights
                if stats:
                    self.ui.render_insights(stats, filtered_df)
                
            except Exception as e:
                st.error(f"❌ Error loading data: {str(e)}")
                st.error(f"Debug info: {type(e).__name__}")
    
    def _render_charts(self, filtered_df: pd.DataFrame):
        """Render all charts with enhanced readability"""
        st.markdown('<h3 style="color: #F0B90B; font-size: clamp(1.2rem, 3vw, 1.8rem); font-weight: 700; margin: 2rem 0 1.5rem 0; text-align: center;">📊 Performance Analytics</h3>', unsafe_allow_html=True)
        
        # Combined dashboard - responsive height
        combined_chart = self.chart_builder.create_combined_dashboard_chart(filtered_df)
        if combined_chart:
            # Update chart for mobile responsiveness
            combined_chart.update_layout(
                height=600 if st.session_state.get('mobile_view', False) else 700,
                margin=dict(l=40, r=40, t=60, b=40)
            )
            st.markdown('<div class="chart-container">', unsafe_allow_html=True)
            st.plotly_chart(combined_chart, use_container_width=True, config={'responsive': True})
            st.markdown('</div>', unsafe_allow_html=True)
        
        # Individual charts with responsive grid
        col1, col2 = st.columns([1, 1])
        
        with col1:
            winrate_chart = self.chart_builder.create_winrate_chart(filtered_df)
            if winrate_chart:
                # Update chart for responsiveness
                winrate_chart.update_layout(
                    height=300 if st.session_state.get('mobile_view', False) else 350,
                    margin=dict(l=40, r=40, t=50, b=40)
                )
                st.markdown('<div class="chart-container">', unsafe_allow_html=True)
                st.plotly_chart(winrate_chart, use_container_width=True, config={'responsive': True})
                st.markdown('</div>', unsafe_allow_html=True)
        
        with col2:
            tpsl_chart = self.chart_builder.create_tpsl_chart(filtered_df)
            if tpsl_chart:
                # Update chart for responsiveness
                tpsl_chart.update_layout(
                    height=300 if st.session_state.get('mobile_view', False) else 350,
                    margin=dict(l=40, r=40, t=50, b=40)
                )
                st.markdown('<div class="chart-container">', unsafe_allow_html=True)
                st.plotly_chart(tpsl_chart, use_container_width=True, config={'responsive': True})
                st.markdown('</div>', unsafe_allow_html=True)
    
    def _render_data_table(self, filtered_df: pd.DataFrame):
        """Render responsive detailed data table with enhanced styling"""
        st.markdown('<h3 style="color: #F0B90B; font-size: clamp(1.2rem, 3vw, 1.8rem); font-weight: 700; margin: 2rem 0 1.5rem 0; text-align: center;">📋 Detailed Trading Records</h3>', unsafe_allow_html=True)
        
        # Prepare display columns
        display_cols = []
        available_cols = ['Date', 'Total_Signal', 'Finished', 'TP', 'SL', 'Winrate_pct']
        for col in available_cols:
            if col in filtered_df.columns:
                display_cols.append(col)
        
        # Display the data table with enhanced styling
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        if display_cols:
            # Create a responsive dataframe display
            display_df = filtered_df[display_cols].copy()
            
            # Format for better mobile display
            if len(display_df.columns) > 4:
                st.markdown(
                    '<div style="overflow-x: auto; -webkit-overflow-scrolling: touch;">',
                    unsafe_allow_html=True
                )
            
            st.dataframe(
                display_df, 
                use_container_width=True, 
                height=250 if st.session_state.get('mobile_view', False) else 300
            )
            
            if len(display_df.columns) > 4:
                st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.dataframe(
                filtered_df, 
                use_container_width=True, 
                height=250 if st.session_state.get('mobile_view', False) else 300
            )
        st.markdown('</div>', unsafe_allow_html=True)

# ==================== APPLICATION ENTRY POINT ====================
def main():
    """Application entry point"""
    app = LuxQuantDashboard()
    app.run()

if __name__ == "__main__":
    main()
