import pandas as pd
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from config.analysis_config import DISASTER_START, DISASTER_END, BASELINE_START, RECOVERY_END

def compute_resilience_for_cbg(df_cbg, baseline_start, baseline_end, disaster_start, recovery_end):
    df_cbg = df_cbg.sort_values('date').copy()

    baseline_period = df_cbg[(df_cbg['date'] >= baseline_start) & (df_cbg['date'] <= baseline_end)]
    if baseline_period.empty:
        return None
    baseline = baseline_period['normalized_inflow'].mean()

    t0 = disaster_start

    df_post = df_cbg[df_cbg['date'] >= t0]
    if df_post.empty:
        return None

    tD_row = df_post.loc[df_post['normalized_inflow'].idxmin()]
    tD = tD_row['date']
    min_val = tD_row['normalized_inflow']

    df_after_tD = df_cbg[df_cbg['date'] > tD]
    recovery_rows = df_after_tD[df_after_tD['normalized_inflow'] >= baseline]
    t1 = recovery_rows['date'].min() if not recovery_rows.empty else df_cbg['date'].max()

    if not (t0 <= tD <= t1):
        return None

    df_triangle = df_cbg[(df_cbg['date'] >= t0) & (df_cbg['date'] <= t1)].copy()
    df_triangle['baseline'] = baseline
    df_triangle['loss'] = baseline - df_triangle['normalized_inflow']
    df_triangle['loss'] = df_triangle['loss'].clip(lower=0)

    area_loss = df_triangle['loss'].sum()

    days = (t1 - t0).days + 1
    area_baseline = baseline * days

    resilience_ratio = 1 - (area_loss / area_baseline) if area_baseline > 0 else None

    vulnerability = (baseline - min_val) / max(1, (tD - t0).days)
    
    robustness = (baseline - min_val) / max(1, (t1 - tD).days)

    return {
        'cbg': df_cbg['destination_cbg'].iloc[0],
        'baseline': baseline,
        't0': t0,
        'tD': tD, 
        't1': t1,
        'resilience_ratio': resilience_ratio,
        'vulnerability': vulnerability,
        'robustness': robustness,
        'area_loss': area_loss,
        'area_baseline': area_baseline,
        'min_val': min_val,
        'days_to_impact': (tD - t0).days,
        'days_to_recovery': (t1 - tD).days,
        'total_disruption_days': (t1 - t0).days
    }

def calculate_resilience_for_all_cbgs(inflow_df, baseline_start=None, baseline_end=None, 
                                    disaster_start=None, recovery_end=None):
    if disaster_start is None:
        disaster_start = pd.to_datetime(DISASTER_START)
    else:
        disaster_start = pd.to_datetime(disaster_start)
        
    if baseline_start is None:
        baseline_start = pd.to_datetime(BASELINE_START)
    else:
        baseline_start = pd.to_datetime(baseline_start)
        
    if recovery_end is None:
        recovery_end = pd.to_datetime(RECOVERY_END)
    else:
        recovery_end = pd.to_datetime(recovery_end)
        
    if baseline_end is None:
        baseline_end = disaster_start - pd.Timedelta(days=1)
    else:
        baseline_end = pd.to_datetime(baseline_end)

    analysis_window_df = inflow_df[
        (inflow_df['date'] >= baseline_start) &
        (inflow_df['date'] <= recovery_end)
    ]

    resilience_results = []
    cbgs = analysis_window_df['destination_cbg'].unique()
    
    print(f"Calculating resilience for {len(cbgs)} CBGs...")
    processed_count = 0
    
    for cbg in cbgs:
        df_cbg = analysis_window_df[analysis_window_df['destination_cbg'] == cbg]
        result = compute_resilience_for_cbg(
            df_cbg,
            baseline_start=baseline_start,
            baseline_end=baseline_end,
            disaster_start=disaster_start,
            recovery_end=recovery_end
        )
        if result:
            resilience_results.append(result)
            processed_count += 1
            
        if processed_count % 50 == 0:
            print(f"Processed {processed_count}/{len(cbgs)} CBGs...")

    print(f"Successfully calculated resilience for {len(resilience_results)} CBGs")
    
    resilience_df = pd.DataFrame(resilience_results)
    
    return resilience_df

def get_resilience_summary(resilience_df):
    if resilience_df.empty:
        return {"error": "No resilience data available"}
    
    summary = {
        "total_cbgs": len(resilience_df),
        "resilience_ratio": {
            "mean": resilience_df['resilience_ratio'].mean(),
            "median": resilience_df['resilience_ratio'].median(),
            "std": resilience_df['resilience_ratio'].std(),
            "min": resilience_df['resilience_ratio'].min(),
            "max": resilience_df['resilience_ratio'].max()
        },
        "most_resilient_cbgs": resilience_df.nlargest(5, 'resilience_ratio')[['cbg', 'resilience_ratio']].to_dict('records'),
        "least_resilient_cbgs": resilience_df.nsmallest(5, 'resilience_ratio')[['cbg', 'resilience_ratio']].to_dict('records'),
        "avg_disruption_days": resilience_df['total_disruption_days'].mean(),
        "avg_baseline": resilience_df['baseline'].mean()
    }
    
    return summary

if __name__ == "__main__":
    from data_loader import load_data
    from mobility_processor import process_mobility_data
    
    print("Loading and processing mobility data...")
    df = load_data()
    inflow_df = process_mobility_data(df)
    
    print("\nCalculating resilience metrics...")
    resilience_df = calculate_resilience_for_all_cbgs(inflow_df)
    
    print(f"\nResilience calculation complete!")
    print(f"Results shape: {resilience_df.shape}")
    print(f"Columns: {list(resilience_df.columns)}")
    
    print("\nSample resilience results:")
    print(resilience_df.head())
    
    print("\nResilience Summary:")
    summary = get_resilience_summary(resilience_df)
    print(f"Total CBGs analyzed: {summary['total_cbgs']}")
    print(f"Average resilience ratio: {summary['resilience_ratio']['mean']:.3f}")
    print(f"Resilience range: {summary['resilience_ratio']['min']:.3f} - {summary['resilience_ratio']['max']:.3f}")
    print(f"Average disruption period: {summary['avg_disruption_days']:.1f} days") 