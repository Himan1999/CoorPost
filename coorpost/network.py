"""
Network generation and analysis functions.

This module handles the creation of coordination networks from detected
coordinated pairs, including edge weight calculations, symmetry scores,
and graph filtering.
"""

import pandas as pd
import numpy as np
import networkx as nx
from typing import Optional, Union


def generate_coordinated_network(
    result: pd.DataFrame,
    edge_weight: float = 0.5,
    subgraph: int = 0,
    objects: bool = False
) -> nx.Graph:
    """
    Generate a coordination network from detected coordinated pairs.
    
    Creates an undirected network where nodes are accounts and edges represent
    coordinated behavior. Edge weights indicate the frequency of coordination,
    and various filtering options allow extraction of specific subnetworks.
    
    Parameters
    ----------
    result : pd.DataFrame
        Output from detect_groups() containing coordinated pairs
    
    edge_weight : float, optional (default=0.5)
        Percentile threshold (0-1) for filtering edges by weight.
        - 0.5 keeps edges in top 50th percentile
        - 0.9 keeps only top 10% of edges
        Higher values = stricter filtering = fewer edges
    
    subgraph : int, optional (default=0)
        Subgraph extraction mode:
        - 0: Return full graph with weight_threshold attribute
        - 1: Return only edges exceeding edge_weight threshold
        - 2: Return fast network (requires flag_speed_share)
        - 3: Return fast network + contextual neighbors
    
    objects : bool, optional (default=False)
        If True, store shared object_ids as edge attributes.
        Useful for group_stats() but increases memory usage.
    
    Returns
    -------
    nx.Graph
        Undirected network with the following attributes:
        
        Node attributes:
        - None by default
        
        Edge attributes:
        - weight: Number of coordinated shares between accounts
        - avg_time_delta: Mean time difference for coordinated actions
        - n_content_id: Number of unique posts from first account
        - n_content_id_y: Number of unique posts from second account
        - edge_symmetry_score: Balance of coordination (0-1)
        - weight_threshold: Binary flag (1 if exceeds threshold)
        - object_ids: Comma-separated object IDs (if objects=True)
    
    Examples
    --------
    >>> # Basic usage
    >>> network = generate_coordinated_network(result, edge_weight=0.5)
    >>> print(f"Nodes: {network.number_of_nodes()}")
    >>> print(f"Edges: {network.number_of_edges()}")
    
    >>> # Filtered network
    >>> network_filtered = generate_coordinated_network(
    ...     result, edge_weight=0.7, subgraph=1
    ... )
    
    >>> # With object tracking
    >>> network_objects = generate_coordinated_network(
    ...     result, edge_weight=0.5, objects=True
    ... )
    >>> # Access shared objects for an edge
    >>> edge_data = network_objects.edges[('user_a', 'user_b')]
    >>> print(edge_data['object_ids'])
    
    Notes
    -----
    Edge Symmetry Score:
        Measures how balanced the coordination is between two accounts.
        Formula: min(n1, n2) / max(n1, n2)
        - 1.0: Perfectly balanced (both accounts contribute equally)
        - 0.5: One account contributes twice as much as the other
        - 0.0: Extremely imbalanced coordination
    
    Edge Weight Threshold:
        Uses percentile-based filtering to identify strong coordination.
        The edge_weight parameter determines what percentage of edges to keep.
        Example: edge_weight=0.8 keeps only edges in the top 20% by weight.
    
    References
    ----------
    Giglietto, F., Righetti, N., Rossi, L., & Marino, G. (2020).
    It takes a village to manipulate the media: coordinated link sharing
    behavior during 2018 and 2019 Italian elections.
    Information, Communication & Society, 23(6), 867-891.
    """
    if not isinstance(edge_weight, (int, float)) or edge_weight < 0 or edge_weight > 1:
        raise ValueError("edge_weight must be a number between 0 and 1")
    
    if len(result) == 0:
        return nx.Graph()
    
    df = result.copy()
    
    # Standardize order: ensure consistent account pairing
    # (account_id should be <= account_id_y alphabetically)
    swap_mask = df['account_id'] > df['account_id_y']
    if swap_mask.any():
        df.loc[swap_mask, ['account_id', 'account_id_y']] = \
            df.loc[swap_mask, ['account_id_y', 'account_id']].values
        df.loc[swap_mask, ['content_id', 'content_id_y']] = \
            df.loc[swap_mask, ['content_id_y', 'content_id']].values
    
    # Aggregate edges and compute metrics
    agg_dict = {
        'time_delta': ['count', 'mean'],  # count = weight, mean = avg_time_delta
        'content_id': 'nunique',
        'content_id_y': 'nunique',
    }
    
    if objects:
        agg_dict['object_id'] = lambda x: ','.join(x.unique())
    
    edge_data = df.groupby(['account_id', 'account_id_y']).agg(agg_dict).reset_index()
    
    # Flatten column names
    edge_data.columns = [
        'account_id', 'account_id_y', 'weight', 'avg_time_delta',
        'n_content_id', 'n_content_id_y'
    ] + (['object_ids'] if objects else [])
    
    # Calculate edge symmetry score
    edge_data['edge_symmetry_score'] = edge_data.apply(
        lambda row: min(row['n_content_id'], row['n_content_id_y']) /
                    max(row['n_content_id'], row['n_content_id_y']),
        axis=1
    )
    
    # Create graph from edge data
    G = nx.Graph()
    
    for _, row in edge_data.iterrows():
        attrs = {
            'weight': int(row['weight']),
            'avg_time_delta': float(row['avg_time_delta']),
            'n_content_id': int(row['n_content_id']),
            'n_content_id_y': int(row['n_content_id_y']),
            'edge_symmetry_score': float(row['edge_symmetry_score'])
        }
        
        if objects:
            attrs['object_ids'] = row['object_ids']
        
        G.add_edge(row['account_id'], row['account_id_y'], **attrs)
    
    # Calculate edge weight threshold
    if len(G.edges()) > 0:
        weights = np.array([G.edges[e]['weight'] for e in G.edges()])
        threshold_value = np.percentile(weights, edge_weight * 100)
        
        # Add weight_threshold attribute to edges
        for edge in G.edges():
            if G.edges[edge]['weight'] >= threshold_value:
                G.edges[edge]['weight_threshold'] = 1
            else:
                G.edges[edge]['weight_threshold'] = 0
    
    # Handle subgraph extraction
    if subgraph == 1:
        # Keep only edges exceeding threshold
        edges_to_keep = [e for e in G.edges() if G.edges[e]['weight_threshold'] == 1]
        G = G.edge_subgraph(edges_to_keep).copy()
    
    elif subgraph == 2:
        # Fast network - requires flag_speed_share to have been called
        time_window_cols = [col for col in df.columns if col.startswith('time_window_')]
        if not time_window_cols:
            raise ValueError(
                "subgraph=2 requires fast network data. "
                "Use flag_speed_share() first."
            )
        
        fast_col = time_window_cols[0]
        df_fast = df[df[fast_col] == 1]
        
        # Rebuild network with only fast edges
        G_fast = _build_graph_from_result(df_fast, objects)
        G = G_fast
    
    elif subgraph == 3:
        # Fast network + contextual neighbors
        time_window_cols = [col for col in df.columns if col.startswith('time_window_')]
        if not time_window_cols:
            raise ValueError(
                "subgraph=3 requires fast network data. "
                "Use flag_speed_share() first."
            )
        
        fast_col = time_window_cols[0]
        df_fast = df[df[fast_col] == 1]
        
        # Get fast edges
        fast_pairs = set(
            tuple(sorted([row['account_id'], row['account_id_y']]))
            for _, row in df_fast.iterrows()
        )
        
        # Get all nodes involved in fast edges
        fast_nodes = set()
        for pair in fast_pairs:
            fast_nodes.update(pair)
        
        # Get neighbors of fast nodes
        all_neighbors = set(fast_nodes)
        for node in fast_nodes:
            if node in G:
                all_neighbors.update(G.neighbors(node))
        
        # Create subgraph with fast nodes and their neighbors
        G = G.subgraph(all_neighbors).copy()
        
        # Add color attribute: 1 for coordinated, 0 for neighbors
        for node in G.nodes():
            G.nodes[node]['color_v'] = 1 if node in fast_nodes else 0
    
    return G


def _build_graph_from_result(
    result: pd.DataFrame,
    objects: bool = False
) -> nx.Graph:
    """
    Helper function to build a graph from result dataframe.
    
    Used internally by generate_coordinated_network for fast network construction.
    """
    df = result.copy()
    
    # Standardize order
    swap_mask = df['account_id'] > df['account_id_y']
    if swap_mask.any():
        df.loc[swap_mask, ['account_id', 'account_id_y']] = \
            df.loc[swap_mask, ['account_id_y', 'account_id']].values
        df.loc[swap_mask, ['content_id', 'content_id_y']] = \
            df.loc[swap_mask, ['content_id_y', 'content_id']].values
    
    # Aggregate
    agg_dict = {
        'time_delta': ['count', 'mean'],
        'content_id': 'nunique',
        'content_id_y': 'nunique',
    }
    
    if objects:
        agg_dict['object_id'] = lambda x: ','.join(x.unique())
    
    edge_data = df.groupby(['account_id', 'account_id_y']).agg(agg_dict).reset_index()
    
    edge_data.columns = [
        'account_id', 'account_id_y', 'weight', 'avg_time_delta',
        'n_content_id', 'n_content_id_y'
    ] + (['object_ids'] if objects else [])
    
    edge_data['edge_symmetry_score'] = edge_data.apply(
        lambda row: min(row['n_content_id'], row['n_content_id_y']) /
                    max(row['n_content_id'], row['n_content_id_y']),
        axis=1
    )
    
    # Build graph
    G = nx.Graph()
    
    for _, row in edge_data.iterrows():
        attrs = {
            'weight': int(row['weight']),
            'avg_time_delta': float(row['avg_time_delta']),
            'n_content_id': int(row['n_content_id']),
            'n_content_id_y': int(row['n_content_id_y']),
            'edge_symmetry_score': float(row['edge_symmetry_score'])
        }
        
        if objects:
            attrs['object_ids'] = row['object_ids']
        
        G.add_edge(row['account_id'], row['account_id_y'], **attrs)
    
    return G
