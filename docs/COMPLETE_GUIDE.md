# Complete CooRPost Guide: Understanding and Implementation

## Table of Contents
1. [Project Overview](#project-overview)
2. [What Each Component Does](#what-each-component-does)
3. [How to Run on Your System](#how-to-run-on-your-system)
4. [Step-by-Step Workflow](#step-by-step-workflow)
5. [Understanding the Algorithm](#understanding-the-algorithm)
6. [Optimization Suggestions](#optimization-suggestions)
7. [Common Issues and Solutions](#common-issues-and-solutions)

---

## Project Overview

**CooRPost** (Coordinated Post Detection) is a Python package adapted from CooRTweet (R package) for detecting coordinated behavior on Facebook and other social media platforms.

### What It Does
- Identifies accounts that share the same content (URLs, images, hashtags) within specific time windows
- Builds networks showing coordination relationships
- Provides statistical analysis of coordination patterns
- Supports multi-platform and multi-modal analysis

### Original vs. Adaptation

| Aspect | CooRTweet (Original) | CooRPost (This Project) |
|--------|---------------------|------------------------|
| Language | R | Python |
| Primary Platform | Twitter/X | Facebook (but platform-agnostic) |
| Data Format | data.table | pandas DataFrame |
| Network Library | igraph | NetworkX |
| Key Innovation | — | Better Facebook API integration examples |

---

## What Each Component Does

### 1. Core Detection Module (`coorpost/detect.py`)

**Purpose**: Identifies coordinated behavior

**Key Functions**:

#### `detect_groups()`
- **What it does**: Finds account pairs sharing identical content within a time window
- **Input**: DataFrame with posts/shares
- **Output**: DataFrame of coordinated pairs
- **Algorithm**:
  1. Groups posts by `object_id` (shared content)
  2. Calculates time differences between all pairs within groups
  3. Filters pairs where time_delta ≤ time_window
  4. Applies minimum participation filter
  
```python
# Example usage
result = detect_groups(
    data,
    time_window=60,  # 60 seconds
    min_participation=2  # minimum 2 posts per account
)
```

#### `flag_speed_share()`
- **What it does**: Identifies even faster coordination within results
- **Use case**: Distinguish automated vs. manual coordination
- **How**: Adds a binary flag for shares within narrower time window

### 2. Network Module (`coorpost/network.py`)

**Purpose**: Converts coordinated pairs into network graphs

#### `generate_coordinated_network()`
- **What it does**: Creates coordination network from detected pairs
- **Process**:
  1. Nodes = accounts
  2. Edges = coordination relationships
  3. Edge weight = frequency of coordination
  4. Edge attributes include symmetry scores and time deltas
  
- **Key Innovation**: Edge Symmetry Score
  - Measures balance in coordination
  - Formula: `min(posts_A, posts_B) / max(posts_A, posts_B)`
  - 1.0 = perfectly balanced
  - 0.0 = highly imbalanced (one-sided amplification)

```python
network = generate_coordinated_network(
    result,
    edge_weight=0.5,  # Keep top 50% of edges
    subgraph=1  # Filter by threshold
)
```

### 3. Statistics Module (`coorpost/stats.py`)

**Purpose**: Analyze coordination patterns

#### `account_stats()`
- **Metrics**:
  - Average time delta (how quickly they coordinate)
  - Average edge symmetry (balance of relationships)
  - Degree (number of coordination partners)
  - Unique shares count

#### `group_stats()`
- **Metrics**: Which content was most coordinated
- **Requires**: Network built with `objects=True`

#### `network_summary()`
- **Metrics**: Overall network characteristics
  - Density, clustering coefficient
  - Connected components
  - Average degree

### 4. Utilities Module (`coorpost/utils.py`)

**Purpose**: Data preparation and helper functions

#### `prep_data()`
- **What it does**: Standardizes column names
- **Why**: detect_groups() requires specific column names
- **Converts**: Timestamps to Unix format automatically

```python
prepared = prep_data(
    facebook_data,
    object_id='shared_url',
    account_id='page_id',
    content_id='post_id',
    timestamp_share='created_time'
)
```

#### `compute_image_hash()`
- **What it does**: Creates perceptual hash of images
- **Why**: Detect coordinated image sharing even with minor modifications
- **Algorithm**: dHash (difference hash)

```python
hash1 = compute_image_hash('image1.jpg')
hash2 = compute_image_hash('image2.jpg')
distance = hash_hamming_distance(hash1, hash2)
if distance < 10:
    print("Images are very similar - likely coordinated")
```

### 5. Visualization Module (`coorpost/viz.py`)

**Purpose**: Visual analysis of networks

#### `visualize_network()`
- Creates network graphs with customizable layouts
- Supports multiple layout algorithms (spring, circular, kamada_kawai)
- Can color nodes by metrics

#### `visualize_network_with_stats()`
- Multi-panel view with network + statistics
- Shows degree distribution
- Highlights top coordinated accounts

---

## How to Run on Your System

### Prerequisites
```bash
# 1. Install Python 3.8+
python --version  # Should show 3.8 or higher

# 2. Install pip
pip --version
```

### Installation Steps

```bash
# 1. Navigate to project directory
cd D:\Dev_Work\CoorPost

# 2. Create virtual environment (recommended)
python -m venv venv

# 3. Activate virtual environment
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# 4. Install package
pip install -e .

# Or install requirements directly
pip install -r requirements.txt
```

### Verify Installation
```bash
python -c "import coorpost; print('Success! Version:', coorpost.__version__)"
```

### Run Examples
```bash
# Basic example
python examples/01_basic_usage.py

# This will:
# 1. Create sample Facebook data
# 2. Detect coordination
# 3. Build network
# 4. Show visualization
```

---

## Step-by-Step Workflow

### Scenario: Analyzing Facebook Page Coordination

#### Step 1: Collect Your Data

You need a CSV or DataFrame with:
- `page_id` or `user_id`: Account identifier
- `post_id`: Unique post identifier
- `shared_url` or `content`: What was shared
- `created_time`: When it was posted

Example CSV:
```csv
page_id,post_id,shared_url,created_time
page_123,post_456,https://example.com/article1,2024-01-01 12:00:00
page_789,post_101,https://example.com/article1,2024-01-01 12:00:30
```

#### Step 2: Load and Prepare Data

```python
import pandas as pd
from coorpost import prep_data

# Load data
data = pd.read_csv('facebook_data.csv')

# Convert to CooRPost format
prepared = prep_data(
    data,
    object_id='shared_url',  # What was shared
    account_id='page_id',  # Who shared it
    content_id='post_id',  # Post identifier
    timestamp_share='created_time'  # When
)
```

#### Step 3: Detect Coordination

```python
from coorpost import detect_groups

result = detect_groups(
    prepared,
    time_window=60,  # 60 seconds
    min_participation=2
)

print(f"Found {len(result)} coordinated actions")
print(f"Involving {result['account_id'].nunique()} unique accounts")
```

**Understanding the output**:
- Each row = one coordinated pair
- `account_id` = earlier post
- `account_id_y` = later post
- `time_delta` = seconds between posts

#### Step 4: Build Network

```python
from coorpost import generate_coordinated_network

network = generate_coordinated_network(
    result,
    edge_weight=0.5,  # Keep top 50% strongest connections
    subgraph=1  # Apply filtering
)

print(f"Network: {network.number_of_nodes()} nodes, {network.number_of_edges()} edges")
```

#### Step 5: Analyze

```python
from coorpost import account_stats

stats = account_stats(network, result)

# Top coordinating accounts
print("Most connected accounts:")
print(stats.head(10))

# Find suspicious patterns
suspicious = stats[
    (stats['degree'] > 10) &  # Highly connected
    (stats['avg_time_delta'] < 30)  # Very quick coordination
]
print("\nPotentially automated accounts:")
print(suspicious)
```

#### Step 6: Visualize

```python
from coorpost import visualize_network

visualize_network(
    network,
    layout='spring',
    node_size=500,
    title='Facebook Page Coordination Network',
    save_path='coordination_network.png'
)
```

---

## Understanding the Algorithm

### The Coordination Detection Process

#### Phase 1: Pairwise Comparison

```
For each shared object (URL, image, etc.):
    Get all posts sharing this object
    For each pair of posts (A, B):
        Calculate time_delta = |timestamp_B - timestamp_A|
        If time_delta ≤ time_window:
            Mark as coordinated pair
```

**Example**:
```
Object: https://example.com/news
Posts:
- Page A: 12:00:00
- Page B: 12:00:15  (15 sec later)
- Page C: 12:05:00  (5 min later)

With time_window=60 seconds:
✓ A-B coordinated (15 sec)
✓ A-C coordinated (300 sec, but > 60, so NO)
✗ B-C not coordinated (285 sec)
```

#### Phase 2: Network Construction

```
For each unique pair of accounts that coordinated:
    Count how many times they coordinated (edge weight)
    Calculate symmetry score
    Add edge to network
```

**Example**:
```
Account A and B coordinated on:
- URL1 (3 posts from A, 2 posts from B)
- URL2 (1 post from A, 1 post from B)
- URL3 (2 posts from A, 3 posts from B)

Edge weight = 3 coordinated objects
Symmetry = average of individual symmetries
```

#### Phase 3: Filtering

```
Calculate edge weight percentile threshold
For each edge:
    If weight >= threshold:
        Keep edge
    Else:
        Remove edge
```

---

## Optimization Suggestions

### 1. Performance Optimizations

#### Current Implementation
```python
# Basic approach - works for small/medium datasets
result = detect_groups(data, time_window=60)
```

#### Better Approach for Large Data (>100K posts)
```python
# Chunk by time periods
from datetime import datetime, timedelta

chunks = []
start_date = data['timestamp_share'].min()
end_date = data['timestamp_share'].max()

# Process 1 day at a time
current = start_date
while current < end_date:
    next_day = current + 86400  # 1 day in seconds
    
    chunk_data = data[
        (data['timestamp_share'] >= current) &
        (data['timestamp_share'] < next_day)
    ]
    
    chunk_result = detect_groups(chunk_data, time_window=60)
    chunks.append(chunk_result)
    
    current = next_day

final_result = pd.concat(chunks, ignore_index=True)
```

#### Even Better: Parallel Processing
```python
from multiprocessing import Pool
import numpy as np

def process_chunk(chunk_data):
    return detect_groups(chunk_data, time_window=60)

# Split data into chunks
n_chunks = 4  # Number of CPU cores
chunks = np.array_split(data, n_chunks)

# Process in parallel
with Pool(processes=n_chunks) as pool:
    results = pool.map(process_chunk, chunks)

final_result = pd.concat(results, ignore_index=True)
```

### 2. Memory Optimizations

#### Current Approach
```python
# Loads entire network into memory
network = generate_coordinated_network(result, edge_weight=0.5)
```

#### Better for Large Networks
```python
# More aggressive filtering
network = generate_coordinated_network(
    result,
    edge_weight=0.8,  # Only top 20% of edges
    subgraph=1
)

# Or process subgraphs separately
for object_id in result['object_id'].unique():
    subset = result[result['object_id'] == object_id]
    subnetwork = generate_coordinated_network(subset)
    # Analyze subnetwork
```

### 3. Algorithm Improvements

#### Current: Symmetric Comparison
```python
# Compares every pair twice (A-B and B-A)
for i in range(len(group)):
    for j in range(i + 1, len(group)):
        # Compare i and j
```

#### Better: Use Sorted Timestamps
```python
# Only compare forward in time
group = group.sort_values('timestamp_share')
for i in range(len(group)):
    for j in range(i + 1, len(group)):
        time_delta = group.iloc[j]['timestamp_share'] - group.iloc[i]['timestamp_share']
        if time_delta > time_window:
            break  # No need to check further
        # Process pair
```

### 4. Data Structure Improvements

#### Consider Using:
- **numpy arrays** instead of pandas for time calculations
- **dict** lookups instead of DataFrame filtering
- **sets** for membership testing

```python
# Instead of:
valid_accounts = df[df['post_count'] >= min_participation]['account_id'].unique()
df = df[df['account_id'].isin(valid_accounts)]

# Use:
account_counts = df['account_id'].value_counts()
valid_accounts = set(account_counts[account_counts >= min_participation].index)
df = df[df['account_id'].map(lambda x: x in valid_accounts)]
```

---

## Common Issues and Solutions

### Issue 1: "Memory Error" with Large Datasets

**Symptom**: Program crashes when processing >100K posts

**Solutions**:
1. Process in chunks (see optimization section)
2. Increase edge_weight threshold (filter more aggressively)
3. Use time-based filtering before detection
4. Consider using Dask for larger-than-memory processing

```python
# Filter to recent data only
recent_cutoff = pd.Timestamp.now() - pd.Timedelta(days=30)
data = data[data['created_time'] >= recent_cutoff]
```

### Issue 2: No Coordination Detected

**Symptoms**: `detect_groups()` returns empty DataFrame

**Possible Causes**:
1. time_window too small
2. min_participation too high
3. Data doesn't have coordinated behavior
4. Timestamp format issues

**Solutions**:
```python
# 1. Try larger time_window
result = detect_groups(data, time_window=300)  # 5 minutes

# 2. Lower min_participation
result = detect_groups(data, time_window=60, min_participation=1)

# 3. Check timestamp format
print(data['timestamp_share'].dtype)  # Should be int64
print(data['timestamp_share'].head())  # Should be Unix timestamps
```

### Issue 3: Slow Performance

**Symptoms**: Takes hours to process moderate datasets

**Diagnosis**:
```python
import time

# Time each step
start = time.time()
result = detect_groups(data)
print(f"Detection took {time.time() - start:.2f} seconds")

start = time.time()
network = generate_coordinated_network(result)
print(f"Network generation took {time.time() - start:.2f} seconds")
```

**Solutions**:
1. Use chunking/parallel processing
2. Filter data before analysis
3. Use faster time window calculations
4. Consider sampling large datasets

### Issue 4: Visualization Crashes

**Symptoms**: Network plot fails or shows nothing

**Solutions**:
```python
# For large networks, filter first
if network.number_of_nodes() > 1000:
    # Keep only high-degree nodes
    degrees = dict(network.degree())
    top_nodes = sorted(degrees, key=degrees.get, reverse=True)[:100]
    network_subset = network.subgraph(top_nodes)
    visualize_network(network_subset)
```

---

## Conclusion

CooRPost provides a robust, Python-based implementation of coordination detection algorithms. The modular design allows:

✓ Flexible adaptation to different platforms
✓ Multi-modal analysis
✓ Scalable processing
✓ Comprehensive network analysis

**Next Steps**:
1. Try the examples in `examples/`
2. Adapt to your specific data source
3. Experiment with parameters
4. Validate results against known cases
5. Contribute improvements!

**Support**: Open issues on GitHub or contact the maintainers.

**Citation**: Remember to cite both CooRPost and the original CooRTweet paper when publishing research using this tool.
