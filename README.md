# CooRPost - Coordinated Post Detection for Facebook

**CooRPost** is a Python package for detecting and analyzing coordinated behavior on Facebook and other social media platforms. It is inspired by and adapted from the [CooRTweet](https://github.com/nicolarighetti/CooRTweet) R package, which detects coordinated networks on Twitter.

## Overview

CooRPost helps researchers and analysts identify accounts that coordinate their activities on social media by sharing the same content within specific time windows. The package is platform-independent and content-independent, making it suitable for analyzing:

- **Link sharing** (coordinated URL sharing)
- **Image sharing** (using perceptual hashing)
- **Hashtag usage** (coordinated hashtag campaigns)
- **Multi-modal analysis** (combining multiple content types)
- **Cross-platform analysis** (Facebook, Instagram, etc.)

## Key Features

1. **Flexible Data Handling**: Works with mono-modal, multi-modal, and cross-platform datasets
2. **Customizable Thresholds**: Set time windows and minimum participation levels
3. **Network Analysis**: Generates coordination networks using NetworkX
4. **Statistical Summaries**: Account and group statistics
5. **Visualization**: Built-in network visualization capabilities

## Installation

```bash
# Install from source
git clone https://github.com/yourusername/CoorPost.git
cd CoorPost
pip install -e .
```

### Requirements

```
python >= 3.8
pandas >= 1.3.0
numpy >= 1.20.0
networkx >= 2.6.0
matplotlib >= 3.4.0
```

## Quick Start

### 1. Prepare Your Data

Your input data should be a pandas DataFrame with these columns:

- `object_id`: Unique identifier for shared content (URL, image hash, etc.)
- `account_id`: User/account identifier
- `content_id`: Unique ID of the post
- `timestamp_share`: Unix timestamp (integer) when content was shared

```python
import pandas as pd
from coorpost import detect_groups, generate_coordinated_network

# Load your Facebook data
data = pd.DataFrame({
    'object_id': ['url_1', 'url_1', 'url_2', 'url_2'],
    'account_id': ['user_a', 'user_b', 'user_a', 'user_b'],
    'content_id': ['post_1', 'post_2', 'post_3', 'post_4'],
    'timestamp_share': [1609459200, 1609459205, 1609459300, 1609459310]
})
```

### 2. Detect Coordinated Groups

```python
# Find accounts sharing the same content within 60 seconds
result = detect_groups(
    data,
    time_window=60,  # seconds
    min_participation=2  # minimum posts per account
)

print(result.head())
```

### 3. Generate Coordination Network

```python
# Create a network graph
network = generate_coordinated_network(
    result,
    edge_weight=0.5,  # percentile threshold (0-1)
    subgraph=1  # filter by edge weight
)

print(f"Nodes: {network.number_of_nodes()}")
print(f"Edges: {network.number_of_edges()}")
```

### 4. Analyze and Visualize

```python
from coorpost import account_stats, visualize_network

# Get account statistics
stats = account_stats(network, result)
print(stats.head())

# Visualize the network
visualize_network(network, layout='spring', node_size=300)
```

## Advanced Usage

### Multi-Modal Analysis

Detect coordination across multiple content types:

```python
from coorpost import prep_data

# Prepare URL data
url_data = prep_data(
    facebook_data,
    object_id='shared_url',
    account_id='user_id',
    content_id='post_id',
    timestamp_share='created_time'
)

# Prepare image data
image_data = prep_data(
    facebook_data,
    object_id='image_hash',
    account_id='user_id',
    content_id='post_id',
    timestamp_share='created_time'
)

# Detect coordinated behavior for each type
url_result = detect_groups(url_data, time_window=30)
image_result = detect_groups(image_data, time_window=30)

# Combine results
combined = pd.concat([url_result, image_result], ignore_index=True)

# Generate combined network
multi_network = generate_coordinated_network(combined, edge_weight=0.5)
```

### Image Hashing

Use perceptual hashing to detect coordinated image sharing:

```python
from coorpost.utils import compute_image_hash
from PIL import Image

# Compute perceptual hash for an image
img = Image.open('path/to/image.jpg')
phash = compute_image_hash(img)
print(f"Image hash: {phash}")
```

### Export Results

```python
# Export network to various formats
from coorpost.io import export_network

# Export to GEXF (for Gephi)
export_network(network, 'coordination_network.gexf', format='gexf')

# Export to GraphML
export_network(network, 'coordination_network.graphml', format='graphml')

# Export to edge list
export_network(network, 'edges.csv', format='edgelist')
```

## Data Format

### Input Data Structure

```python
{
    'object_id': str or int,     # Identifier of shared content
    'account_id': str or int,    # Account identifier  
    'content_id': str or int,    # Post identifier
    'timestamp_share': int       # Unix timestamp
}
```

### Output from `detect_groups()`

```python
{
    'object_id': str or int,      # Shared content ID
    'account_id': str or int,     # First account
    'account_id_y': str or int,   # Second account
    'content_id': str or int,     # First post (older)
    'content_id_y': str or int,   # Second post (newer)
    'time_delta': int             # Time difference in seconds
}
```

## Methodology

CooRPost uses a two-step process to detect coordinated behavior:

### Step 1: Detect Groups (`detect_groups`)

1. **Group by Content**: Groups posts by `object_id` (shared content)
2. **Calculate Time Differences**: Computes time differences between all post pairs
3. **Filter by Time Window**: Keeps only pairs within the specified `time_window`
4. **Filter by Participation**: Removes accounts below `min_participation` threshold

### Step 2: Generate Network (`generate_coordinated_network`)

1. **Build Graph**: Creates an undirected network where nodes are accounts
2. **Calculate Edge Weights**: Weight = number of coordinated actions between account pairs
3. **Compute Edge Symmetry**: Measures how balanced the coordination is
4. **Apply Threshold**: Filters edges based on percentile threshold
5. **Extract Subgraphs**: Optionally extracts specific subnetworks

### Key Metrics

- **Edge Weight**: Number of times two accounts shared the same content within time window
- **Edge Symmetry Score**: Ratio measuring balance in coordination (0 to 1)
  - 1 = perfectly balanced
  - 0 = highly imbalanced
- **Average Time Delta**: Mean time difference for coordinated actions

## Examples

See the [examples](examples/) directory for complete worked examples:

- [Basic Usage](examples/01_basic_usage.py)
- [Multi-Modal Analysis](examples/02_multimodal_analysis.py)
- [Visualization](examples/03_visualization.py)
- [Cross-Platform Analysis](examples/04_cross_platform.py)

## API Reference

### Core Functions

#### `detect_groups(data, time_window=10, min_participation=2, remove_loops=True)`

Detects pairs of accounts sharing the same content within a time window.

**Parameters:**
- `data` (DataFrame): Input data with required columns
- `time_window` (int): Seconds within which shares are considered coordinated
- `min_participation` (int): Minimum posts required per account
- `remove_loops` (bool): Remove self-shares

**Returns:** DataFrame with coordinated pairs

#### `generate_coordinated_network(result, edge_weight=0.5, subgraph=0)`

Generates a coordination network from detected groups.

**Parameters:**
- `result` (DataFrame): Output from `detect_groups()`
- `edge_weight` (float): Percentile threshold (0-1) for filtering edges
- `subgraph` (int): Subgraph extraction mode (0, 1, 2, or 3)

**Returns:** NetworkX Graph object

#### `prep_data(data, object_id=None, account_id=None, content_id=None, timestamp_share=None)`

Prepares and standardizes column names.

**Parameters:**
- `data` (DataFrame): Input dataframe
- `object_id` (str): Column name to rename to 'object_id'
- `account_id` (str): Column name to rename to 'account_id'
- `content_id` (str): Column name to rename to 'content_id'
- `timestamp_share` (str): Column name to rename to 'timestamp_share'

**Returns:** DataFrame with standardized columns

### Analysis Functions

#### `account_stats(network, result, weight_threshold='none')`

Calculate statistics for each account in the network.

**Returns:** DataFrame with account-level statistics

#### `group_stats(network, weight_threshold='none')`

Calculate statistics for shared objects in the network.

**Returns:** DataFrame with object-level statistics

### Visualization

#### `visualize_network(network, layout='spring', **kwargs)`

Visualize the coordination network.

**Parameters:**
- `network` (Graph): NetworkX graph
- `layout` (str): Layout algorithm ('spring', 'circular', 'kamada_kawai')
- `**kwargs`: Additional arguments for matplotlib

## Facebook API Integration

While this package doesn't include Facebook API integration, you can collect data using:

- [facebook-sdk](https://github.com/mobolic/facebook-sdk)
- Facebook Graph API
- [CrowdTangle](https://www.crowdtangle.com/) (for researchers)

Example using Facebook Graph API:

```python
import requests
import pandas as pd
from datetime import datetime

def fetch_facebook_posts(access_token, page_id):
    url = f"https://graph.facebook.com/v12.0/{page_id}/posts"
    params = {
        'access_token': access_token,
        'fields': 'id,created_time,shares,link'
    }
    response = requests.get(url, params=params)
    data = response.json()
    
    # Convert to CooRPost format
    posts = []
    for post in data.get('data', []):
        posts.append({
            'object_id': post.get('link', ''),
            'account_id': page_id,
            'content_id': post['id'],
            'timestamp_share': int(datetime.fromisoformat(
                post['created_time'].replace('Z', '+00:00')
            ).timestamp())
        })
    
    return pd.DataFrame(posts)
```

## Testing

Run the test suite:

```bash
pytest tests/
```

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## Citation

If you use CooRPost in your research, please cite:

```bibtex
@software{coorpost2026,
  title = {CooRPost: Coordinated Post Detection for Facebook},
  author = {Your Name},
  year = {2026},
  url = {https://github.com/yourusername/CoorPost}
}
```

Also cite the original CooRTweet package:

```bibtex
@article{righetti2025coortweet,
  title={CooRTweet: A Generalized R Software for Coordinated Network Detection},
  author={Righetti, Nicola and Balluff, Paul},
  journal={Computational Communication Research},
  volume={7},
  number={1},
  pages={1},
  year={2025}
}
```

## References

- Righetti, N., & Balluff, P. (2025). CooRTweet: A Generalized R Software for Coordinated Network Detection. *Computational Communication Research*, 7(1), 1.
- Giglietto, F., Righetti, N., Rossi, L., & Marino, G. (2020). It takes a village to manipulate the media: coordinated link sharing behavior during 2018 and 2019 Italian elections. *Information, Communication & Society*, 23(6), 867-891.
- Keller, F. B., Schoch, D., Stier, S., & Yang, J. (2020). Political astroturfing on Twitter: How to coordinate a disinformation campaign. *Political Communication*, 37(2), 256-280.

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Acknowledgments

This package is inspired by and adapted from:
- [CooRTweet](https://github.com/nicolarighetti/CooRTweet) by Nicola Righetti & Paul Balluff
- [CooRnet](https://github.com/fabiogiglietto/CooRnet) by Fabio Giglietto et al.

## Support

For questions, issues, or feature requests:
- Open an [issue](https://github.com/Himan1999/CoorPost/issues)
- Email: your.email@example.com

## Changelog

### Version 1.0.0 (2026-01-20)
- Initial release
- Core coordination detection algorithms
- Network generation and analysis
- Multi-modal support
- Visualization tools
