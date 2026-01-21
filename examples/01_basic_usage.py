"""
Basic usage example for CooRPost.

This script demonstrates the fundamental workflow:
1. Load/prepare Facebook data
2. Detect coordinated groups
3. Generate coordination network
4. Analyze and visualize results
"""

import pandas as pd
import os
from coorpost import (
    prep_data,
    detect_groups,
    generate_coordinated_network,
    account_stats,
    visualize_network
)

def main():
    print("=== CooRPost Basic Usage Example ===\n")
    
    # Step 1: Load data from CSV
    print("Step 1: Loading Facebook data from CSV...")
    # Get the directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(script_dir, "posts_data.csv")
    data = pd.read_csv(csv_path)
    
    # Convert created_time to proper timestamp format
    # The CSV has time in MM:SS.S format, convert to Unix timestamps
    import time
    base_timestamp = int(time.time()) - 86400  # Yesterday as base
    
    def parse_time(time_str):
        """Convert MM:SS.S format to Unix timestamp"""
        try:
            parts = str(time_str).split(':')
            if len(parts) == 2:
                minutes = float(parts[0])
                seconds = float(parts[1])
                offset = int(minutes * 60 + seconds)
                return base_timestamp + offset
            return base_timestamp
        except:
            return base_timestamp
    
    data['created_time'] = data['created_time'].apply(parse_time)
    
    print(f"Loaded {len(data)} posts from {data['page_id'].nunique()} pages\n")
    print("Sample data:")
    print(data.head())
    print()
    
    # Step 2: Prepare data for analysis
    print("Step 2: Preparing data...")
    prepared_data = prep_data(
        data,
        object_id='shared_url',
        account_id='page_id',
        content_id='post_id',
        timestamp_share='created_time'
    )
    print("Data prepared with columns:", prepared_data.columns.tolist())
    print()
    
    # Step 3: Detect coordinated groups
    print("Step 3: Detecting coordinated behavior...")
    result = detect_groups(
        prepared_data,
        time_window=60,  # 60 seconds
        min_participation=2  # At least 2 posts per account
    )
    print(f"Found {len(result)} coordinated pairs")
    print(f"Involving {result['account_id'].nunique() + result['account_id_y'].nunique()} unique accounts\n")
    
    if len(result) > 0:
        print("Sample coordinated pairs:")
        print(result.head())
        print()
        
        # Step 4: Generate coordination network
        print("Step 4: Generating coordination network...")
        network = generate_coordinated_network(
            result,
            edge_weight=0.5,  # Keep top 50% of edges
            subgraph=1  # Filter by edge weight
        )
        print(f"Network has {network.number_of_nodes()} nodes and {network.number_of_edges()} edges\n")
        
        # Step 5: Analyze accounts
        print("Step 5: Analyzing account statistics...")
        stats = account_stats(network, result)
        print("Top 5 most connected accounts:")
        print(stats.head())
        print()
        
        # Step 6: Visualize network
        print("Step 6: Visualizing network...")
        visualize_network(
            network,
            layout='spring',
            node_size=500,
            title='Facebook Coordination Network (Basic Example)',
            with_labels=True
        )
        
        print("\n=== Analysis Complete ===")
        print(f"✓ Detected {len(result)} coordinated interactions")
        print(f"✓ Network: {network.number_of_nodes()} accounts, {network.number_of_edges()} connections")
        print(f"✓ Most connected account has {stats['degree'].max()} connections")
    else:
        print("No coordinated behavior detected in this sample.")
        print("Try adjusting time_window or min_participation parameters.")


if __name__ == '__main__':
    main()
