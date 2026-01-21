"""
Multi-Modal Coordination Analysis Example

This script demonstrates how to detect coordination across multiple types of content:
1. URL-based coordination (exact URL matches)
2. Domain-based coordination (same domain, different URLs)
3. Combined multi-modal analysis

Uses real Facebook data from posts_data.csv
"""

import pandas as pd
import os
from coorpost import (
    prep_data,
    detect_groups,
    generate_coordinated_network,
    account_stats,
    network_summary,
    visualize_network
)
from coorpost.utils import extract_domain


def main():
    print("=" * 70)
    print("CooRPost - Multi-Modal Coordination Analysis")
    print("=" * 70)
    
    # Load data
    print("\n[1/5] Loading Facebook data from CSV...")
    script_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(script_dir, "posts_data.csv")
    data = pd.read_csv(csv_path)
    
    # Convert created_time to proper timestamp format
    import time
    base_timestamp = int(time.time()) - 86400
    
    def parse_time(time_str):
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
    
    print(f"   ✓ Loaded {len(data)} posts from {data['page_id'].nunique()} pages")
    
    # Extract domains from URLs for domain-level analysis
    print("\n[2/5] Extracting domains from URLs...")
    data['domain'] = extract_domain(data['shared_url'])
    print(f"   ✓ Found {data['domain'].nunique()} unique domains")
    print(f"\n   Top 5 domains:")
    top_domains = data['domain'].value_counts().head()
    for domain, count in top_domains.items():
        print(f"      - {domain}: {count} posts")
    
    # ========================================
    # ANALYSIS 1: URL-Based Coordination
    # ========================================
    print("\n" + "=" * 70)
    print("ANALYSIS 1: URL-Based Coordination (Exact Matches)")
    print("=" * 70)
    
    print("\nDetecting coordination on exact URL matches...")
    prepared_url = prep_data(
        data,
        object_id='shared_url',
        account_id='page_id',
        content_id='post_id',
        timestamp_share='created_time'
    )
    
    result_url = detect_groups(
        prepared_url,
        time_window=3600,  # 1 hour window
        min_participation=2
    )
    
    if len(result_url) > 0:
        print(f"✓ Found {len(result_url)} URL-based coordinated pairs")
        print(f"✓ Involving {result_url['account_id'].nunique()} unique pages")
        print(f"✓ On {result_url['object_id'].nunique()} shared URLs")
        
        # Show top coordinated URLs
        print("\nTop 5 most coordinated URLs:")
        top_urls = result_url['object_id'].value_counts().head()
        for i, (url, count) in enumerate(top_urls.items(), 1):
            url_short = url[:60] + "..." if len(url) > 60 else url
            print(f"   {i}. {url_short}")
            print(f"      Coordinated pairs: {count}")
        
        # Build network
        network_url = generate_coordinated_network(
            result_url,
            edge_weight=0.3,
            subgraph=1
        )
        print(f"\n✓ URL Network: {network_url.number_of_nodes()} nodes, {network_url.number_of_edges()} edges")
        
        # Network statistics
        summary = network_summary(network_url)
        print(f"   - Density: {summary['density']:.4f}")
        print(f"   - Avg degree: {summary['avg_degree']:.2f}")
        print(f"   - Connected components: {summary['num_components']}")
    else:
        print("⚠ No URL-based coordination detected")
        network_url = None
    
    # ========================================
    # ANALYSIS 2: Domain-Based Coordination
    # ========================================
    print("\n" + "=" * 70)
    print("ANALYSIS 2: Domain-Based Coordination")
    print("=" * 70)
    print("(Detects pages coordinating on content from same domain)")
    
    print("\nDetecting coordination at domain level...")
    prepared_domain = prep_data(
        data,
        object_id='domain',
        account_id='page_id',
        content_id='post_id',
        timestamp_share='created_time'
    )
    
    result_domain = detect_groups(
        prepared_domain,
        time_window=3600,  # 1 hour window
        min_participation=2
    )
    
    if len(result_domain) > 0:
        print(f"✓ Found {len(result_domain)} domain-based coordinated pairs")
        print(f"✓ Involving {result_domain['account_id'].nunique()} unique pages")
        print(f"✓ On {result_domain['object_id'].nunique()} domains")
        
        # Show top coordinated domains
        print("\nTop 5 most coordinated domains:")
        top_domains_coord = result_domain['object_id'].value_counts().head()
        for i, (domain, count) in enumerate(top_domains_coord.items(), 1):
            print(f"   {i}. {domain}")
            print(f"      Coordinated pairs: {count}")
        
        # Build network
        network_domain = generate_coordinated_network(
            result_domain,
            edge_weight=0.3,
            subgraph=1
        )
        print(f"\n✓ Domain Network: {network_domain.number_of_nodes()} nodes, {network_domain.number_of_edges()} edges")
        
        # Network statistics
        summary = network_summary(network_domain)
        print(f"   - Density: {summary['density']:.4f}")
        print(f"   - Avg degree: {summary['avg_degree']:.2f}")
        print(f"   - Connected components: {summary['num_components']}")
    else:
        print("⚠ No domain-based coordination detected")
        network_domain = None
    
    # ========================================
    # ANALYSIS 3: Comparative Analysis
    # ========================================
    print("\n" + "=" * 70)
    print("ANALYSIS 3: Comparative Analysis")
    print("=" * 70)
    
    if len(result_url) > 0 and len(result_domain) > 0:
        print("\nComparing URL vs Domain coordination:")
        
        # Compare account involvement
        url_accounts = set(result_url['account_id'].unique()) | set(result_url['account_id_y'].unique())
        domain_accounts = set(result_domain['account_id'].unique()) | set(result_domain['account_id_y'].unique())
        
        both_accounts = url_accounts & domain_accounts
        only_url = url_accounts - domain_accounts
        only_domain = domain_accounts - url_accounts
        
        print(f"\n   Account Overlap:")
        print(f"   - In both analyses: {len(both_accounts)} accounts")
        print(f"   - Only URL coordination: {len(only_url)} accounts")
        print(f"   - Only domain coordination: {len(only_domain)} accounts")
        
        # Compare timing
        print(f"\n   Average Coordination Speed:")
        print(f"   - URL-based: {result_url['time_delta'].mean():.1f} seconds")
        print(f"   - Domain-based: {result_domain['time_delta'].mean():.1f} seconds")
        
        # Account statistics comparison
        if network_url and network_domain:
            stats_url = account_stats(network_url, result_url)
            stats_domain = account_stats(network_domain, result_domain)
            
            print(f"\n   Network Comparison:")
            print(f"   - URL network density: {network_summary(network_url)['density']:.4f}")
            print(f"   - Domain network density: {network_summary(network_domain)['density']:.4f}")
    
    # ========================================
    # ANALYSIS 4: Time-Based Patterns
    # ========================================
    print("\n" + "=" * 70)
    print("ANALYSIS 4: Time-Based Coordination Patterns")
    print("=" * 70)
    
    if len(result_url) > 0:
        print("\nAnalyzing coordination timing patterns...")
        
        # Classify by speed
        result_url['speed_category'] = pd.cut(
            result_url['time_delta'],
            bins=[0, 60, 300, 1800, 3600],
            labels=['Very Fast (0-60s)', 'Fast (1-5min)', 'Medium (5-30min)', 'Slow (30-60min)']
        )
        
        print("\nCoordination by speed:")
        speed_dist = result_url['speed_category'].value_counts()
        for category, count in speed_dist.items():
            pct = (count / len(result_url)) * 100
            print(f"   - {category}: {count} pairs ({pct:.1f}%)")
        
        # Identify fastest coordinators
        fastest = result_url.nsmallest(10, 'time_delta')[['account_id', 'account_id_y', 'object_id', 'time_delta']]
        print("\nTop 5 fastest coordinated pairs:")
        for i, row in fastest.head().iterrows():
            url_short = row['object_id'][:50] + "..." if len(row['object_id']) > 50 else row['object_id']
            print(f"   {i+1}. {row['account_id']} ↔ {row['account_id_y']}")
            print(f"      Time: {row['time_delta']:.1f} seconds | URL: {url_short}")
    
    # ========================================
    # VISUALIZATIONS
    # ========================================
    print("\n" + "=" * 70)
    print("Creating Visualizations")
    print("=" * 70)
    
    if network_url and network_url.number_of_nodes() > 0:
        print("\nGenerating URL coordination network visualization...")
        try:
            visualize_network(
                network_url,
                layout='spring',
                node_size=500,
                title='URL-Based Coordination Network',
                with_labels=True,
                save_path=os.path.join(script_dir, 'url_coordination_network.png')
            )
            print("   ✓ Saved: url_coordination_network.png")
        except Exception as e:
            print(f"   ⚠ Could not create visualization: {e}")
    
    if network_domain and network_domain.number_of_nodes() > 0:
        print("\nGenerating domain coordination network visualization...")
        try:
            visualize_network(
                network_domain,
                layout='kamada_kawai',
                node_size=500,
                title='Domain-Based Coordination Network',
                with_labels=True,
                save_path=os.path.join(script_dir, 'domain_coordination_network.png')
            )
            print("   ✓ Saved: domain_coordination_network.png")
        except Exception as e:
            print(f"   ⚠ Could not create visualization: {e}")
    
    # ========================================
    # SAVE RESULTS
    # ========================================
    print("\n" + "=" * 70)
    print("Saving Results")
    print("=" * 70)
    
    if len(result_url) > 0:
        url_file = os.path.join(script_dir, 'url_coordination_results.csv')
        result_url.to_csv(url_file, index=False)
        print(f"   ✓ URL coordination results: url_coordination_results.csv")
    
    if len(result_domain) > 0:
        domain_file = os.path.join(script_dir, 'domain_coordination_results.csv')
        result_domain.to_csv(domain_file, index=False)
        print(f"   ✓ Domain coordination results: domain_coordination_results.csv")
    
    # ========================================
    # SUMMARY
    # ========================================
    print("\n" + "=" * 70)
    print("ANALYSIS SUMMARY")
    print("=" * 70)
    
    print(f"\n✓ Dataset: {len(data)} posts from {data['page_id'].nunique()} pages")
    print(f"✓ URL-based coordination: {len(result_url) if len(result_url) > 0 else 0} pairs")
    print(f"✓ Domain-based coordination: {len(result_domain) if len(result_domain) > 0 else 0} pairs")
    
    if len(result_url) > 0:
        print(f"\n   URL Analysis:")
        print(f"   - {result_url['account_id'].nunique()} coordinating accounts")
        print(f"   - Avg coordination time: {result_url['time_delta'].mean():.1f} seconds")
        print(f"   - {result_url['object_id'].nunique()} coordinated URLs")
    
    if len(result_domain) > 0:
        print(f"\n   Domain Analysis:")
        print(f"   - {result_domain['account_id'].nunique()} coordinating accounts")
        print(f"   - Avg coordination time: {result_domain['time_delta'].mean():.1f} seconds")
        print(f"   - {result_domain['object_id'].nunique()} coordinated domains")
    
    print("\n" + "=" * 70)
    print("✓ MULTI-MODAL ANALYSIS COMPLETE!")
    print("=" * 70)
    
    print("\nKey Insights:")
    print("• Domain-level analysis captures broader coordination patterns")
    print("• URL-level analysis identifies exact content coordination")
    print("• Combine both for comprehensive coordination detection")
    print("• Different modalities may reveal different coordination strategies")


if __name__ == '__main__':
    main()
