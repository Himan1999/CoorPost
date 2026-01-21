# Installation and Setup Guide

## System Requirements

- Python 3.8 or higher
- pip (Python package manager)
- 4GB RAM minimum (8GB+ recommended for large datasets)

## Installation Steps

### 1. Install Python Dependencies

```bash
# Create a virtual environment (recommended)
python -m venv coorpost_env

# Activate virtual environment
# On Windows:
coorpost_env\Scripts\activate
# On macOS/Linux:
source coorpost_env/bin/activate

# Install CooRPost
cd CoorPost
pip install -e .

# Or install requirements directly
pip install -r requirements.txt
```

### 2. Verify Installation

```python
import coorpost
print(coorpost.__version__)

# Test with sample data
from coorpost.utils import create_facebook_sample_data
from coorpost import detect_groups

data = create_facebook_sample_data(50)
result = detect_groups(data, time_window=60)
print(f"Success! Detected {len(result)} coordinated pairs")
```

### 3. Optional: Install Development Tools

```bash
pip install pytest pytest-cov black flake8
```

## Running the Examples

```bash
# Basic usage
python examples/01_basic_usage.py

# Multi-modal analysis
python examples/02_multimodal_analysis.py

# Visualization
python examples/03_visualization.py
```

## Configuration

### For Large Datasets

If working with large datasets (>100K posts):

```python
# Use chunking for memory efficiency
import pandas as pd

chunks = []
for chunk in pd.read_csv('large_data.csv', chunksize=10000):
    prepared = prep_data(chunk, ...)
    result_chunk = detect_groups(prepared, ...)
    chunks.append(result_chunk)

final_result = pd.concat(chunks, ignore_index=True)
```

### Parallel Processing

For multi-core processing:

```python
from multiprocessing import Pool
import pandas as pd

def process_group(group_data):
    return detect_groups(group_data, time_window=60)

# Split by object_id or time period
groups = [group for _, group in data.groupby('object_id')]

with Pool(processes=4) as pool:
    results = pool.map(process_group, groups)

combined = pd.concat(results, ignore_index=True)
```

## Troubleshooting

### Issue: ImportError for imagehash

```bash
pip install imagehash pillow
```

### Issue: Memory Error with Large Networks

```python
# Use subgraph filtering
network = generate_coordinated_network(
    result,
    edge_weight=0.8,  # More strict filtering
    subgraph=1
)
```

### Issue: Slow Performance

```python
# Filter data before detection
data = data[data['timestamp_share'] > recent_date]

# Reduce time_window
result = detect_groups(data, time_window=30)  # Instead of 60
```

## Next Steps

1. Read the [README.md](../README.md) for overview
2. Try the [examples](../examples/)
3. Check the [API documentation](API.md)
4. Explore [methodology notes](METHODOLOGY.md)

## Getting Help

- Issues: https://github.com/yourusername/CoorPost/issues
- Email: your.email@example.com
- Documentation: https://coorpost.readthedocs.io
