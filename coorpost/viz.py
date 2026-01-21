"""
Visualization functions for coordination networks.

Provides tools for visualizing and plotting coordination networks
using matplotlib and networkx layout algorithms.
"""

import matplotlib.pyplot as plt
import pandas as pd
import networkx as nx
import numpy as np
from typing import Optional, Dict, Any, Tuple


def visualize_network(
    network: nx.Graph,
    layout: str = 'spring',
    node_size: int = 300,
    node_color: str = 'skyblue',
    edge_width: float = 1.0,
    with_labels: bool = False,
    figsize: Tuple[int, int] = (12, 8),
    title: Optional[str] = None,
    save_path: Optional[str] = None,
    **kwargs
) -> None:
    """
    Visualize a coordination network.
    
    Creates a network graph visualization with customizable appearance.
    Supports various layout algorithms and styling options.
    
    Parameters
    ----------
    network : nx.Graph
        Network graph to visualize
    layout : str, optional (default='spring')
        Layout algorithm: 'spring', 'circular', 'kamada_kawai', 'shell', 'random'
    node_size : int, optional (default=300)
        Size of nodes
    node_color : str or list, optional (default='skyblue')
        Color of nodes. Can be single color or list of colors per node
    edge_width : float, optional (default=1.0)
        Width of edges. Can vary by edge weight
    with_labels : bool, optional (default=False)
        Whether to show node labels (account IDs)
    figsize : tuple, optional (default=(12, 8))
        Figure size (width, height) in inches
    title : str, optional
        Plot title
    save_path : str, optional
        Path to save figure. If None, displays interactively
    **kwargs : dict
        Additional arguments passed to nx.draw()
    
    Examples
    --------
    >>> # Basic visualization
    >>> visualize_network(network)
    
    >>> # Customized visualization
    >>> visualize_network(
    ...     network,
    ...     layout='kamada_kawai',
    ...     node_size=500,
    ...     node_color='lightcoral',
    ...     with_labels=True,
    ...     title='Facebook Coordination Network'
    ... )
    
    >>> # Color nodes by degree
    >>> degrees = dict(network.degree())
    >>> colors = [degrees[node] for node in network.nodes()]
    >>> visualize_network(network, node_color=colors, node_size=500)
    
    >>> # Save to file
    >>> visualize_network(network, save_path='network.png')
    """
    if len(network) == 0:
        print("Network is empty - nothing to visualize")
        return
    
    # Create figure
    fig, ax = plt.subplots(figsize=figsize)
    
    # Select layout
    if layout == 'spring':
        pos = nx.spring_layout(network, k=0.5, iterations=50)
    elif layout == 'circular':
        pos = nx.circular_layout(network)
    elif layout == 'kamada_kawai':
        pos = nx.kamada_kawai_layout(network)
    elif layout == 'shell':
        pos = nx.shell_layout(network)
    elif layout == 'random':
        pos = nx.random_layout(network)
    else:
        raise ValueError(f"Unknown layout: {layout}")
    
    # Determine edge widths based on weight
    if 'weight' in list(network.edges(data=True))[0][2]:
        weights = [network.edges[e]['weight'] for e in network.edges()]
        max_weight = max(weights) if weights else 1
        edge_widths = [edge_width * (w / max_weight) for w in weights]
    else:
        edge_widths = edge_width
    
    # Draw network
    nx.draw(
        network,
        pos,
        node_size=node_size,
        node_color=node_color,
        width=edge_widths,
        with_labels=with_labels,
        ax=ax,
        edge_color='gray',
        alpha=0.7,
        **kwargs
    )
    
    if title:
        ax.set_title(title, fontsize=16, pad=20)
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"Network visualization saved to {save_path}")
    else:
        plt.show()


def visualize_network_with_stats(
    network: nx.Graph,
    result: pd.DataFrame,
    layout: str = 'spring',
    figsize: Tuple[int, int] = (16, 10)
) -> None:
    """
    Visualize network with statistics panels.
    
    Creates a multi-panel visualization showing the network graph
    alongside degree distribution and other statistics.
    
    Parameters
    ----------
    network : nx.Graph
        Network to visualize
    result : pd.DataFrame
        Result from detect_groups()
    layout : str, optional (default='spring')
        Layout algorithm
    figsize : tuple, optional (default=(16, 10))
        Figure size
    
    Examples
    --------
    >>> visualize_network_with_stats(network, result)
    """
    import pandas as pd
    from .stats import account_stats
    
    if len(network) == 0:
        print("Network is empty - nothing to visualize")
        return
    
    fig = plt.figure(figsize=figsize)
    
    # Create grid
    gs = fig.add_gridspec(2, 2, hspace=0.3, wspace=0.3)
    
    # Network plot
    ax1 = fig.add_subplot(gs[:, 0])
    
    # Layout
    if layout == 'spring':
        pos = nx.spring_layout(network, k=0.5, iterations=50)
    elif layout == 'kamada_kawai':
        pos = nx.kamada_kawai_layout(network)
    else:
        pos = nx.spring_layout(network)
    
    # Color by degree
    degrees = dict(network.degree())
    colors = [degrees[node] for node in network.nodes()]
    
    nx.draw(
        network,
        pos,
        node_color=colors,
        node_size=300,
        cmap=plt.cm.YlOrRd,
        with_labels=False,
        ax=ax1,
        edge_color='gray',
        alpha=0.7
    )
    ax1.set_title('Coordination Network', fontsize=14)
    
    # Degree distribution
    ax2 = fig.add_subplot(gs[0, 1])
    degree_values = list(degrees.values())
    ax2.hist(degree_values, bins=20, color='skyblue', edgecolor='black')
    ax2.set_xlabel('Degree')
    ax2.set_ylabel('Frequency')
    ax2.set_title('Degree Distribution', fontsize=12)
    ax2.grid(True, alpha=0.3)
    
    # Top accounts
    ax3 = fig.add_subplot(gs[1, 1])
    stats = account_stats(network, result)
    top_accounts = stats.head(10)
    
    ax3.barh(range(len(top_accounts)), top_accounts['degree'], color='coral')
    ax3.set_yticks(range(len(top_accounts)))
    ax3.set_yticklabels([str(x)[:20] for x in top_accounts['account_id']], fontsize=8)
    ax3.set_xlabel('Degree (Connections)')
    ax3.set_title('Top 10 Most Connected Accounts', fontsize=12)
    ax3.invert_yaxis()
    ax3.grid(True, alpha=0.3, axis='x')
    
    plt.tight_layout()
    plt.show()


def plot_time_series(
    result: pd.DataFrame,
    data: pd.DataFrame,
    bins: int = 24,
    figsize: Tuple[int, int] = (12, 6)
) -> None:
    """
    Plot time series of coordinated activity.
    
    Shows temporal patterns of coordination over time.
    
    Parameters
    ----------
    result : pd.DataFrame
        Output from detect_groups()
    data : pd.DataFrame
        Original data with timestamps
    bins : int, optional (default=24)
        Number of time bins
    figsize : tuple, optional (default=(12, 6))
        Figure size
    
    Examples
    --------
    >>> plot_time_series(result, data, bins=48)
    """
    import pandas as pd
    
    # Merge to get timestamps
    merged = result.merge(
        data[['content_id', 'timestamp_share']],
        on='content_id',
        how='left'
    )
    
    # Convert to datetime
    merged['datetime'] = pd.to_datetime(merged['timestamp_share'], unit='s')
    
    # Count coordinated actions over time
    merged = merged.set_index('datetime')
    counts = merged.resample('H').size()
    
    # Plot
    fig, ax = plt.subplots(figsize=figsize)
    counts.plot(ax=ax, color='steelblue', linewidth=2)
    ax.set_xlabel('Time')
    ax.set_ylabel('Number of Coordinated Actions')
    ax.set_title('Temporal Pattern of Coordinated Activity')
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.show()


def export_network_image(
    network: nx.Graph,
    output_path: str,
    layout: str = 'spring',
    dpi: int = 300,
    **kwargs
) -> None:
    """
    Export network visualization to image file.
    
    Parameters
    ----------
    network : nx.Graph
        Network to export
    output_path : str
        Path to save image (e.g., 'network.png', 'network.pdf')
    layout : str, optional (default='spring')
        Layout algorithm
    dpi : int, optional (default=300)
        Resolution for raster formats
    **kwargs : dict
        Additional arguments for visualization
    
    Examples
    --------
    >>> export_network_image(network, 'coordination_network.png')
    >>> export_network_image(network, 'network.pdf', layout='kamada_kawai')
    """
    visualize_network(
        network,
        layout=layout,
        save_path=output_path,
        **kwargs
    )
