import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import sys
import os

from src.data_loader import load_data
from src.mobility_processor import process_mobility_data
from src.resilience_calculator import calculate_resilience_for_all_cbgs, get_resilience_summary

st.set_page_config(
    page_title="Community Resilience Dashboard",
    page_icon="🏘️",
    layout="wide",
    initial_sidebar_state="collapsed",
    menu_items={
        'Get Help': None,
        'Report a bug': None,
        'About': None
    }
)

st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        color: #1f77b4;
        text-align: left;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #ffffff;
        padding: 1rem;
        border-radius: 0.5rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    /* Hide Streamlit menu and deploy button */
    #MainMenu {visibility: hidden;}
    .stDeployButton {visibility: hidden;}
    header {visibility: hidden;}
    .stAppDeployButton {visibility: hidden;}
    .css-1rs6os {visibility: hidden;}
    .css-17eq0hr {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

def load_and_process_data():
    with st.spinner("Loading mobility data..."):
        df = load_data()
    
    with st.spinner("Processing mobility patterns..."):
        inflow_df = process_mobility_data(df)
    
    with st.spinner("Calculating resilience metrics..."):
        resilience_df = calculate_resilience_for_all_cbgs(inflow_df)
    
    return df, inflow_df, resilience_df

def main():
    st.markdown('<h1 class="main-header">Community Resilience Dashboard</h1>', unsafe_allow_html=True)
    st.markdown('<h3 style="text-align: left; color: #666;">Port Arthur, Texas - Tropical Storm Imelda Analysis</h3>', unsafe_allow_html=True)
    
    df, inflow_df, resilience_df = load_and_process_data()
    summary = get_resilience_summary(resilience_df)
    
    tab1, tab2, tab3 = st.tabs([
        "Overview", 
        "CBG Analysis", 
        "Resilience Patterns"
    ])
    
    with tab1:
        st.header("Analysis Overview")
        
        st.subheader("Dataset Overview")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Mobility Records", f"{len(df):,}")
        with col2:
            st.metric("Census Block Groups", f"{inflow_df['destination_cbg'].nunique()}")
        with col3:
            st.metric("Analysis Period", "Jan 1 - Dec 31, 2019")
        with col4:
            st.metric("CBGs Analyzed", summary['total_cbgs'])
        
        st.subheader("Resilience Summary")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                label="Average Resilience", 
                value=f"{summary['resilience_ratio']['mean']:.3f}",
                help="Mean resilience ratio (higher = more resilient)"
            )
            
        with col2:
            st.metric(
                label="Avg Disruption",
                value=f"{summary['avg_disruption_days']:.1f} days",
                help="Average recovery time"
            )
            
        with col3:
            st.metric(
                label="Most Resilient",
                value=f"{summary['resilience_ratio']['max']:.3f}",
                help="Highest resilience ratio achieved"
            )
            
        with col4:
            st.metric(
                label="Resilience Range", 
                value=f"{summary['resilience_ratio']['min']:.3f} - {summary['resilience_ratio']['max']:.3f}",
                help="Range of resilience ratios"
            )
        
        st.subheader("Visit Patterns")
        
        # Create visit patterns plot for Streamlit
        df_visits = df.copy()
        df_visits['date'] = pd.to_datetime(df_visits['date'])
        df_visits = df_visits[(df_visits['date'] >= '2019-09-01') & (df_visits['date'] <= '2019-09-30')]
        
        # Define visit types
        df_visits['visit_type'] = df_visits.apply(
            lambda row: 'own' if row['origin_census_block_group'] == row['destination_cbg']
            else 'inward' if row['origin_census_block_group'][:5] != row['destination_cbg'][:5]
            else 'outward',
            axis=1
        )
        
        # Aggregate
        visit_counts = df_visits.groupby(['date', 'visit_type'])['destination_device_count'].sum().reset_index()
        
        # Create plotly line chart
        fig = px.line(
            visit_counts, 
            x='date', 
            y='destination_device_count',
            color='visit_type',
            title='Time Series of Visits in Port Arthur',
            labels={
                'date': 'Date',
                'destination_device_count': 'Number of Visits',
                'visit_type': 'Visit Type'
            }
        )
        
        # Add shaded impact window
        fig.add_vrect(
            x0='2019-09-17', x1='2019-09-19',
            fillcolor='gray', opacity=0.3,
            annotation_text="Impact Window", annotation_position="top left"
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        st.header("CBG Analysis")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Most Resilient CBGs")
            top_cbgs = resilience_df.nlargest(5, 'resilience_ratio')[['cbg', 'resilience_ratio', 'total_disruption_days']]
            st.dataframe(top_cbgs, hide_index=True)
        
        with col2:
            st.subheader("Least Resilient CBGs") 
            bottom_cbgs = resilience_df.nsmallest(5, 'resilience_ratio')[['cbg', 'resilience_ratio', 'total_disruption_days']]
            st.dataframe(bottom_cbgs, hide_index=True)
        
        st.subheader("Individual CBG Analysis")
        cbg_options = sorted(resilience_df['cbg'].unique())
        default_cbg = "482450063002"
        default_index = cbg_options.index(default_cbg) if default_cbg in cbg_options else 0
        
        selected_cbg = st.selectbox(
            "Select a Census Block Group for detailed analysis:",
            options=cbg_options,
            index=default_index,
            help="Choose a CBG to see its detailed resilience pattern"
        )
        
        if selected_cbg:
            cbg_data = resilience_df[resilience_df['cbg'] == selected_cbg].iloc[0]
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Resilience Ratio", f"{cbg_data['resilience_ratio']:.3f}")
            with col2:
                st.metric("Days to Impact", f"{cbg_data['days_to_impact']}")
            with col3:
                st.metric("Days to Recovery", f"{cbg_data['days_to_recovery']}")
            
            st.subheader(f"Mobility Pattern for CBG {selected_cbg}")
            fig, ax = plt.subplots(figsize=(12, 6))
            
            cbg_mobility = inflow_df[inflow_df['destination_cbg'] == selected_cbg].copy()
            cbg_mobility = cbg_mobility[(cbg_mobility['date'] >= '2019-09-01') & 
                                       (cbg_mobility['date'] <= '2019-09-30')].sort_values('date')
            
            ax.plot(cbg_mobility['date'], cbg_mobility['normalized_inflow'], 
                   linewidth=2, label='Normalized Inflow')
            ax.axhline(cbg_data['baseline'], color='gray', linestyle='--', label='Baseline')
            ax.axvline(cbg_data['t0'], color='orange', linestyle=':', label='Disaster Start')
            ax.axvline(cbg_data['tD'], color='red', linestyle=':', label='Maximum Impact')
            ax.axvline(cbg_data['t1'], color='green', linestyle=':', label='Recovery')
            
            ax.set_xlabel('Date')
            ax.set_ylabel('Normalized Inflow')
            ax.set_title(f'CBG {selected_cbg} - Resilience Pattern')
            ax.legend()
            ax.grid(True, alpha=0.3)
            
            st.pyplot(fig)
    
    with tab3:
        st.header("Resilience Patterns")
        
        st.subheader("Resilience Distribution")
        col1, col2 = st.columns(2)
        
        with col1:
            fig = px.histogram(
                resilience_df, 
                x='resilience_ratio',
                nbins=30,
                title='Distribution of Resilience Ratios',
                labels={'resilience_ratio': 'Resilience Ratio', 'count': 'Number of CBGs'}
            )
            fig.add_vline(x=summary['resilience_ratio']['mean'], line_dash="dash", 
                         annotation_text=f"Mean: {summary['resilience_ratio']['mean']:.3f}")
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            fig = px.box(
                resilience_df, 
                y='resilience_ratio',
                title='Resilience Ratio Distribution',
                labels={'resilience_ratio': 'Resilience Ratio'}
            )
            st.plotly_chart(fig, use_container_width=True)
        
        st.subheader("Vulnerability Distribution")
        col1, col2 = st.columns(2)
        
        with col1:
            fig = px.histogram(
                resilience_df, 
                x='vulnerability',
                nbins=30,
                title='Distribution of Vulnerability',
                labels={'vulnerability': 'Vulnerability', 'count': 'Number of CBGs'}
            )
            fig.add_vline(x=resilience_df['vulnerability'].mean(), line_dash="dash", 
                         annotation_text=f"Mean: {resilience_df['vulnerability'].mean():.3f}")
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            fig = px.box(
                resilience_df, 
                y='vulnerability',
                title='Vulnerability Distribution',
                labels={'vulnerability': 'Vulnerability'}
            )
            st.plotly_chart(fig, use_container_width=True)
        
        st.subheader("Robustness Distribution")
        col1, col2 = st.columns(2)
        
        with col1:
            fig = px.histogram(
                resilience_df, 
                x='robustness',
                nbins=30,
                title='Distribution of Robustness',
                labels={'robustness': 'Robustness', 'count': 'Number of CBGs'}
            )
            fig.add_vline(x=resilience_df['robustness'].mean(), line_dash="dash", 
                         annotation_text=f"Mean: {resilience_df['robustness'].mean():.3f}")
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            fig = px.box(
                resilience_df, 
                y='robustness',
                title='Robustness Distribution',
                labels={'robustness': 'Robustness'}
            )
            st.plotly_chart(fig, use_container_width=True)

if __name__ == "__main__":
    main() 