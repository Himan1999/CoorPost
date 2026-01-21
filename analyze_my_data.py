"""
Use this script to analyze YOUR OWN Facebook data

Instructions:
1. Put your CSV file in this folder (or update the file path below)
2. Update the column names to match your CSV
3. Run: python analyze_my_data.py
"""

import pandas as pd
from coorpost import prep_data, detect_groups, generate_coordinated_network, account_stats, visualize_network

# ========================================
# CONFIGURATION - UPDATE THESE VALUES
# ========================================

# Path to your CSV file
CSV_FILE = "example_data_template.csv"  # Change this!

# Your column names (adjust to match your CSV)
COLUMN_MAPPING = {
    'object_id': 'shared_url',      # Column with URLs/content shared
    'account_id': 'page_id',        # Column with page/user IDs
    'content_id': 'post_id',        # Column with post IDs
    'timestamp_share': 'created_time'  # Column with timestamps
}

# Analysis parameters
TIME_WINDOW = 60          # Seconds - accounts sharing within this window are coordinated
MIN_PARTICIPATION = 2     # Minimum number of posts per account to include
EDGE_WEIGHT = 0.5        # Keep top 50% of edges (0.0 to 1.0)

# ========================================
# ANALYSIS - NO NEED TO CHANGE BELOW
# ========================================

def main():
    print("=" * 70)
    print("CooRPost - Analyze Your Facebook Data")
    print("=" * 70)
    
    # Load data
    print(f"\n[1/6] Loading data from {CSV_FILE}...")
    try:
        data = pd.read_csv(CSV_FILE)
        print(f"      ✓ Loaded {len(data)} rows")
        print(f"      ✓ Columns found: {data.columns.tolist()}")
    except FileNotFoundError:
        print(f"      ✗ ERROR: File '{CSV_FILE}' not found!")
        print(f"      → Please create your CSV file or update CSV_FILE path")
        print(f"      → See example_data_template.csv for format")
        return
    except Exception as e:
        print(f"      ✗ ERROR loading file: {e}")
        return
    
    # Check required columns exist
    print(f"\n[2/6] Checking column mapping...")
    missing_cols = []
    for coorpost_col, your_col in COLUMN_MAPPING.items():
        if your_col not in data.columns:
            missing_cols.append(your_col)
    
    if missing_cols:
        print(f"      ✗ ERROR: These columns are missing from your CSV:")
        for col in missing_cols:
            print(f"         - {col}")
        print(f"      → Update COLUMN_MAPPING to match your column names")
        print(f"      → Your columns are: {data.columns.tolist()}")
        return
    
    print(f"      ✓ All required columns found")
    
    # Clean data
    print(f"\n[3/6] Cleaning data...")
    original_len = len(data)
    
    # Remove rows with missing values in key columns
    required_cols = list(COLUMN_MAPPING.values())
    data = data.dropna(subset=required_cols)
    
    # Remove duplicates
    data = data.drop_duplicates(subset=[COLUMN_MAPPING['content_id']])
    
    print(f"      ✓ Removed {original_len - len(data)} invalid/duplicate rows")
    print(f"      ✓ Working with {len(data)} clean posts")
    
    if len(data) < 10:
        print(f"      ⚠ WARNING: Very few posts remaining. Results may not be meaningful.")
    
    # Prepare data
    print(f"\n[4/6] Preparing data for analysis...")
    try:
        prepared = prep_data(
            data,
            object_id=COLUMN_MAPPING['object_id'],
            account_id=COLUMN_MAPPING['account_id'],
            content_id=COLUMN_MAPPING['content_id'],
            timestamp_share=COLUMN_MAPPING['timestamp_share']
        )
        print(f"      ✓ Data prepared successfully")
    except Exception as e:
        print(f"      ✗ ERROR preparing data: {e}")
        print(f"      → Check that timestamp column has valid dates")
        return
    
    # Detect coordination
    print(f"\n[5/6] Detecting coordinated behavior...")
    print(f"      Parameters:")
    print(f"         - Time window: {TIME_WINDOW} seconds")
    print(f"         - Min participation: {MIN_PARTICIPATION} posts")
    
    result = detect_groups(
        prepared,
        time_window=TIME_WINDOW,
        min_participation=MIN_PARTICIPATION
    )
    
    if len(result) == 0:
        print(f"      ⚠ No coordination detected!")
        print(f"      → Try increasing TIME_WINDOW (currently {TIME_WINDOW})")
        print(f"      → Try decreasing MIN_PARTICIPATION (currently {MIN_PARTICIPATION})")
        print(f"      → Your data may not contain coordinated behavior")
        return
    
    print(f"      ✓ Found {len(result)} coordinated actions")
    print(f"      ✓ Involving {result['account_id'].nunique()} unique accounts")
    print(f"      ✓ On {result['object_id'].nunique()} shared objects")
    
    # Show top coordinated content
    print(f"\n      Top coordinated content:")
    top_content = result['object_id'].value_counts().head(5)
    for content, count in top_content.items():
        content_short = content[:50] + "..." if len(content) > 50 else content
        print(f"         - {content_short}: {count} coordinated pairs")
    
    # Build network
    print(f"\n[6/6] Building coordination network...")
    network = generate_coordinated_network(
        result,
        edge_weight=EDGE_WEIGHT,
        subgraph=1
    )
    
    print(f"      ✓ Network: {network.number_of_nodes()} nodes, {network.number_of_edges()} edges")
    
    # Calculate statistics
    stats = account_stats(network, result)
    
    print(f"\n      Network Statistics:")
    print(f"         - Average coordination time: {stats['avg_time_delta'].mean():.1f} seconds")
    print(f"         - Average connections per account: {stats['degree'].mean():.1f}")
    print(f"         - Average edge symmetry: {stats['avg_edge_symmetry_score'].mean():.3f}")
    
    print(f"\n      Most Coordinated Accounts:")
    top_accounts = stats.head(5)
    for idx, row in top_accounts.iterrows():
        print(f"         {idx+1}. {row['account_id']}: {row['degree']:.0f} connections, "
              f"{row['coord_shares']:.0f} shares, avg {row['avg_time_delta']:.1f}s")
    
    # Save results
    print(f"\n[OUTPUT] Saving results...")
    
    # Save coordinated pairs
    result_file = "coordination_results.csv"
    result.to_csv(result_file, index=False)
    print(f"      ✓ Coordinated pairs saved to: {result_file}")
    
    # Save account statistics
    stats_file = "account_statistics.csv"
    stats.to_csv(stats_file, index=False)
    print(f"      ✓ Account stats saved to: {stats_file}")
    
    # Create visualization
    print(f"\n      Creating network visualization...")
    try:
        visualize_network(
            network,
            title=f'Coordination Network (time_window={TIME_WINDOW}s)',
            layout='spring',
            node_size=300,
            save_path='coordination_network.png'
        )
        print(f"      ✓ Visualization saved to: coordination_network.png")
    except Exception as e:
        print(f"      ⚠ Could not create visualization: {e}")
    
    print("\n" + "=" * 70)
    print("✓ ANALYSIS COMPLETE!")
    print("=" * 70)
    print("\nGenerated files:")
    print(f"  1. {result_file} - All coordinated pairs")
    print(f"  2. {stats_file} - Account-level statistics")
    print(f"  3. coordination_network.png - Network visualization")
    print("\nNext steps:")
    print("  - Review the CSV files for detailed results")
    print("  - Adjust TIME_WINDOW and MIN_PARTICIPATION for different sensitivity")
    print("  - See DATA_PREPARATION_GUIDE.md for advanced analysis")

if __name__ == "__main__":
    main()
