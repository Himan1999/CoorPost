"""
Statistical analysis functions for coordination networks.

Provides account-level and group-level statistics for analyzing
coordination patterns and network characteristics.
"""

import pandas as pd
import networkx as nx
from typing import Optional


def account_stats(
    network: nx.Graph,
    result: pd.DataFrame,
    weight_threshold: str = 'none'
) -> pd.DataFrame:
    """
    Calculate comprehensive statistics for each account in the network.
    
    Computes metrics including average time delta, edge symmetry score,
    and share counts for accounts participating in coordinated behavior.
    
    Parameters
    ----------
    network : nx.Graph
        Coordination network from generate_coordinated_network()
    result : pd.DataFrame
        Original result from detect_groups()
    weight_threshold : str, optional (default='none')
        Threshold level for filtering:
        - 'none': All edges in the network
        - 'full': Only edges exceeding weight threshold
        - 'fast': Only edges from fast network (requires flag_speed_share)
    
    Returns
    -------
    pd.DataFrame
        Statistics for each account with columns:
        - account_id: Account identifier
        - avg_time_delta: Average time difference for coordinated actions
        - avg_edge_symmetry_score: Average balance of coordination
        - unique_shares_count: Number of unique posts
        - degree: Number of connections (coordinated accounts)
    
    Examples
    --------
    >>> stats = account_stats(network, result)
    >>> print(stats.head())
    >>> # Sort by most connected accounts
    >>> print(stats.sort_values('degree', ascending=False).head())
    
    Notes
    -----
    - Accounts with higher avg_edge_symmetry_score show more balanced coordination
    - Low symmetry scores may indicate "follower" accounts
    - degree metric shows the breadth of coordination (number of partners)
    """
    if len(network.edges()) == 0:
        return pd.DataFrame(columns=[
            'account_id', 'avg_time_delta', 'avg_edge_symmetry_score',
            'unique_shares_count', 'degree'
        ])
    
    # Check if we have fast/full network data
    has_threshold = any('weight_threshold' in data for _, _, data in network.edges(data=True))
    
    # Filter edges based on weight_threshold parameter
    if weight_threshold == 'full' and has_threshold:
        edges_to_use = [
            (u, v, data) for u, v, data in network.edges(data=True)
            if data.get('weight_threshold', 0) == 1
        ]
    elif weight_threshold == 'fast':
        # Check for fast network indicator
        edges_to_use = [
            (u, v, data) for u, v, data in network.edges(data=True)
            if data.get('weight_threshold_fast', 0) == 1
        ]
        if not edges_to_use:
            print("Warning: No fast network data found. Using all edges.")
            edges_to_use = list(network.edges(data=True))
    else:
        edges_to_use = list(network.edges(data=True))
    
    # Collect statistics per account
    account_data = {}
    
    for u, v, data in edges_to_use:
        for account in [u, v]:
            if account not in account_data:
                account_data[account] = {
                    'time_deltas': [],
                    'symmetry_scores': [],
                    'connections': set()
                }
            
            account_data[account]['time_deltas'].append(data.get('avg_time_delta', 0))
            account_data[account]['symmetry_scores'].append(data.get('edge_symmetry_score', 0))
            account_data[account]['connections'].add(v if account == u else u)
    
    # Calculate averages
    stats_list = []
    for account, data in account_data.items():
        stats_list.append({
            'account_id': account,
            'avg_time_delta': np.mean(data['time_deltas']) if data['time_deltas'] else 0,
            'avg_edge_symmetry_score': np.mean(data['symmetry_scores']) if data['symmetry_scores'] else 0,
            'degree': len(data['connections'])
        })
    
    stats_df = pd.DataFrame(stats_list)
    
    # Add share counts from original result
    shares_from_result = pd.concat([
        result[['account_id', 'content_id']].rename(columns={'content_id': 'shares'}),
        result[['account_id_y', 'content_id_y']].rename(columns={'account_id_y': 'account_id', 'content_id_y': 'shares'})
    ])
    
    share_counts = shares_from_result.groupby('account_id')['shares'].nunique().reset_index()
    share_counts.columns = ['account_id', 'unique_shares_count']
    
    # Merge with stats
    stats_df = stats_df.merge(share_counts, on='account_id', how='left')
    stats_df['unique_shares_count'] = stats_df['unique_shares_count'].fillna(0).astype(int)
    
    return stats_df.sort_values('degree', ascending=False).reset_index(drop=True)


def group_stats(
    network: nx.Graph,
    weight_threshold: str = 'none'
) -> pd.DataFrame:
    """
    Calculate statistics for shared objects in the coordination network.
    
    Analyzes which objects (URLs, images, hashtags) were most frequently
    coordinated and by how many accounts.
    
    Parameters
    ----------
    network : nx.Graph
        Coordination network with object_ids stored (objects=True required)
    weight_threshold : str, optional (default='none')
        Threshold level: 'none', 'full', or 'fast'
    
    Returns
    -------
    pd.DataFrame
        Statistics for each shared object with columns:
        - object_id: Object identifier
        - num_accounts: Number of unique accounts sharing this object
        - num_edges: Number of coordinated pairs for this object
    
    Examples
    --------
    >>> # Network must be created with objects=True
    >>> network = generate_coordinated_network(result, objects=True)
    >>> obj_stats = group_stats(network)
    >>> print(obj_stats.sort_values('num_accounts', ascending=False).head())
    
    Notes
    -----
    - Requires network to be generated with objects=True parameter
    - Objects shared by more accounts indicate broader coordination
    - Can identify which content types are most frequently coordinated
    """
    if len(network.edges()) == 0:
        return pd.DataFrame(columns=['object_id', 'num_accounts', 'num_edges'])
    
    # Check if object_ids are stored
    sample_edge = list(network.edges(data=True))[0]
    if 'object_ids' not in sample_edge[2]:
        raise ValueError(
            "Object IDs not found in network. "
            "Network must be created with objects=True parameter."
        )
    
    # Filter edges based on threshold
    if weight_threshold == 'full':
        edges_to_use = [
            (u, v, data) for u, v, data in network.edges(data=True)
            if data.get('weight_threshold', 0) == 1
        ]
    elif weight_threshold == 'fast':
        edges_to_use = [
            (u, v, data) for u, v, data in network.edges(data=True)
            if data.get('weight_threshold_fast', 0) == 1
        ]
    else:
        edges_to_use = list(network.edges(data=True))
    
    # Collect object statistics
    object_data = {}
    
    for u, v, data in edges_to_use:
        object_ids = data['object_ids'].split(',')
        
        for obj_id in object_ids:
            if obj_id not in object_data:
                object_data[obj_id] = {
                    'accounts': set(),
                    'edges': 0
                }
            
            object_data[obj_id]['accounts'].update([u, v])
            object_data[obj_id]['edges'] += 1
    
    # Convert to dataframe
    stats_list = []
    for obj_id, data in object_data.items():
        stats_list.append({
            'object_id': obj_id,
            'num_accounts': len(data['accounts']),
            'num_edges': data['edges']
        })
    
    return pd.DataFrame(stats_list).sort_values('num_accounts', ascending=False).reset_index(drop=True)


import numpy as np  # Add this import at the top


def network_summary(network: nx.Graph) -> dict:
    """
    Get comprehensive summary statistics for the network.
    
    Parameters
    ----------
    network : nx.Graph
        Coordination network
    
    Returns
    -------
    dict
        Dictionary with network metrics
    
    Examples
    --------
    >>> summary = network_summary(network)
    >>> for key, value in summary.items():
    ...     print(f"{key}: {value}")
    """
    if len(network) == 0:
        return {
            'num_nodes': 0,
            'num_edges': 0,
            'density': 0,
            'num_components': 0,
            'largest_component_size': 0,
            'avg_degree': 0,
            'avg_clustering': 0
        }
    
    # Calculate metrics
    components = list(nx.connected_components(network))
    largest_component = max(components, key=len) if components else set()
    
    summary = {
        'num_nodes': network.number_of_nodes(),
        'num_edges': network.number_of_edges(),
        'density': nx.density(network),
        'num_components': len(components),
        'largest_component_size': len(largest_component),
        'avg_degree': sum(dict(network.degree()).values()) / network.number_of_nodes(),
        'avg_clustering': nx.average_clustering(network)
    }
    
    return summary
