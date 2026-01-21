# Data Preparation Guide for CooRPost

This guide explains how to prepare your Facebook (or other social media) data to work with CooRPost.

## Required Data Format

CooRPost needs **4 essential columns**:

| Column Name | Description | Example |
|-------------|-------------|---------|
| `object_id` | What was shared (URL, image hash, hashtag) | `https://example.com/news` |
| `account_id` | Who shared it (page ID, user ID) | `page_123456` |
| `content_id` | Unique identifier for the post/share | `post_789012` |
| `timestamp_share` | When it was posted (Unix timestamp or datetime) | `1704067200` or `2024-01-01 00:00:00` |

## Method 1: Using Your Own Facebook Data

### Option A: From Facebook Graph API

```python
import requests
import pandas as pd
from coorpost import prep_data

# Example: Get posts from a Facebook page
access_token = "YOUR_ACCESS_TOKEN"
page_id = "YOUR_PAGE_ID"

# Get posts with shared links
url = f"https://graph.facebook.com/v18.0/{page_id}/posts"
params = {
    'access_token': access_token,
    'fields': 'id,created_time,message,link,from',
    'limit': 100
}

response = requests.get(url, params=params)
posts = response.json()['data']

# Convert to DataFrame
data = pd.DataFrame(posts)

# Prepare for CooRPost
prepared = prep_data(
    data,
    object_id='link',         # The shared URL
    account_id='from.id',     # Page/user who posted
    content_id='id',          # Post ID
    timestamp_share='created_time'  # When posted
)

# Now ready to use!
from coorpost import detect_groups
result = detect_groups(prepared, time_window=60)
```

### Option B: From CSV Export

If you have a CSV file with Facebook data:

**Your CSV might look like:**
```csv
page_id,post_id,shared_url,created_time,post_text
123456,789012,https://example.com/news1,2024-01-01 12:00:00,Check this out!
789012,345678,https://example.com/news1,2024-01-01 12:00:30,Breaking news
```

**Load and prepare:**
```python
import pandas as pd
from coorpost import prep_data, detect_groups

# Load CSV
data = pd.read_csv('facebook_data.csv')

# Prepare for CooRPost
prepared = prep_data(
    data,
    object_id='shared_url',      # Column with URLs/content
    account_id='page_id',        # Column with page/user IDs
    content_id='post_id',        # Column with post IDs
    timestamp_share='created_time'  # Column with timestamps
)

# Detect coordination
result = detect_groups(prepared, time_window=60)
print(f"Found {len(result)} coordinated actions!")
```

## Method 2: Using Built-in Sample Data

For testing and learning:

```python
from coorpost.utils import create_facebook_sample_data
from coorpost import prep_data, detect_groups

# Generate sample data
data = create_facebook_sample_data(
    n_posts=200  # Number of posts to generate
)

# Already formatted, but show how to prepare
prepared = prep_data(
    data,
    object_id='shared_url',
    account_id='page_id',
    content_id='post_id',
    timestamp_share='created_time'
)

# Run analysis
result = detect_groups(prepared, time_window=60)
```

## Method 3: Multi-Modal Analysis

### Analyzing Image Coordination

```python
import pandas as pd
from coorpost import prep_data, detect_groups
from coorpost.utils import compute_image_hash

# Your data with image URLs
data = pd.DataFrame({
    'page_id': ['page1', 'page2', 'page3'],
    'post_id': ['p1', 'p2', 'p3'],
    'image_url': [
        'https://example.com/img1.jpg',
        'https://example.com/img2.jpg',  # Similar to img1
        'https://example.com/img3.jpg'
    ],
    'created_time': [
        '2024-01-01 12:00:00',
        '2024-01-01 12:00:15',
        '2024-01-01 12:05:00'
    ]
})

# Download and hash images
def hash_image_from_url(url):
    import requests
    from io import BytesIO
    from PIL import Image
    
    response = requests.get(url)
    img = Image.open(BytesIO(response.content))
    return compute_image_hash(img)

# Add image hashes as object_id
data['image_hash'] = data['image_url'].apply(hash_image_from_url)

# Prepare and analyze
prepared = prep_data(
    data,
    object_id='image_hash',  # Use image hash instead of URL
    account_id='page_id',
    content_id='post_id',
    timestamp_share='created_time'
)

result = detect_groups(prepared, time_window=60)
```

### Analyzing Hashtag Coordination

```python
# Data with hashtags
data = pd.DataFrame({
    'user_id': ['u1', 'u2', 'u3'],
    'tweet_id': ['t1', 't2', 't3'],
    'hashtags': ['#ClimateAction', '#ClimateAction', '#SaveOceans'],
    'timestamp': [1704067200, 1704067230, 1704067300]
})

# Prepare
prepared = prep_data(
    data,
    object_id='hashtags',  # Hashtag as the coordinated object
    account_id='user_id',
    content_id='tweet_id',
    timestamp_share='timestamp'
)

result = detect_groups(prepared, time_window=60)
```

## Method 4: Real Facebook Data Collection

### Step-by-Step Facebook Data Collection

#### 1. Get Facebook Access Token

```python
# Go to: https://developers.facebook.com/tools/explorer/
# 1. Select your app
# 2. Request these permissions:
#    - pages_read_engagement
#    - pages_read_user_content
# 3. Generate token
```

#### 2. Collect Posts from Multiple Pages

```python
import requests
import pandas as pd
from datetime import datetime, timedelta
import time

def collect_facebook_posts(page_ids, access_token, days_back=7):
    """
    Collect posts from multiple Facebook pages.
    
    Parameters
    ----------
    page_ids : list
        List of Facebook page IDs to monitor
    access_token : str
        Your Facebook Graph API access token
    days_back : int
        How many days back to collect posts
    
    Returns
    -------
    pd.DataFrame
        DataFrame with all collected posts
    """
    all_posts = []
    
    # Calculate date range
    since = int((datetime.now() - timedelta(days=days_back)).timestamp())
    until = int(datetime.now().timestamp())
    
    for page_id in page_ids:
        print(f"Collecting posts from page {page_id}...")
        
        url = f"https://graph.facebook.com/v18.0/{page_id}/posts"
        params = {
            'access_token': access_token,
            'fields': 'id,created_time,message,link,attachments',
            'since': since,
            'until': until,
            'limit': 100
        }
        
        # Paginate through results
        while url:
            response = requests.get(url, params=params)
            data = response.json()
            
            if 'data' in data:
                for post in data['data']:
                    # Extract shared link
                    shared_link = None
                    if 'link' in post:
                        shared_link = post['link']
                    elif 'attachments' in post:
                        attachments = post['attachments']['data']
                        if attachments and 'url' in attachments[0]:
                            shared_link = attachments[0]['url']
                    
                    if shared_link:  # Only keep posts with links
                        all_posts.append({
                            'page_id': page_id,
                            'post_id': post['id'],
                            'shared_url': shared_link,
                            'created_time': post['created_time'],
                            'message': post.get('message', '')
                        })
            
            # Get next page
            url = data.get('paging', {}).get('next')
            params = {}  # URL already has params
            time.sleep(1)  # Rate limiting
    
    return pd.DataFrame(all_posts)

# Example usage
page_ids = [
    '123456789',  # Page 1
    '987654321',  # Page 2
    # Add more page IDs
]

access_token = "YOUR_ACCESS_TOKEN_HERE"

# Collect data
raw_data = collect_facebook_posts(page_ids, access_token, days_back=30)
print(f"Collected {len(raw_data)} posts with shared links")

# Save raw data
raw_data.to_csv('facebook_raw_data.csv', index=False)

# Prepare for CooRPost
from coorpost import prep_data, detect_groups

prepared = prep_data(
    raw_data,
    object_id='shared_url',
    account_id='page_id',
    content_id='post_id',
    timestamp_share='created_time'
)

# Detect coordination
result = detect_groups(
    prepared,
    time_window=60,      # 60 seconds
    min_participation=2   # At least 2 posts per page
)

print(f"\nFound {len(result)} coordinated actions")
print(f"Involving {result['account_id'].nunique()} unique pages")
```

#### 3. Collect Posts by Search Query

```python
def search_facebook_posts(query, access_token, limit=100):
    """
    Search public Facebook posts containing specific keywords.
    
    Parameters
    ----------
    query : str
        Search query (keywords, hashtags, URLs)
    access_token : str
        Facebook access token
    limit : int
        Maximum posts to retrieve
    """
    url = "https://graph.facebook.com/v18.0/search"
    params = {
        'access_token': access_token,
        'q': query,
        'type': 'post',
        'fields': 'id,created_time,message,link,from',
        'limit': limit
    }
    
    response = requests.get(url, params=params)
    posts = response.json().get('data', [])
    
    data = []
    for post in posts:
        if 'link' in post:
            data.append({
                'page_id': post.get('from', {}).get('id'),
                'post_id': post['id'],
                'shared_url': post['link'],
                'created_time': post['created_time']
            })
    
    return pd.DataFrame(data)

# Example: Find all posts sharing a specific URL
url_to_track = "https://example.com/article"
data = search_facebook_posts(url_to_track, access_token)
```

## Common Data Issues and Fixes

### Issue 1: Timestamps in Wrong Format

```python
# If timestamps are strings
data['created_time'] = pd.to_datetime(data['created_time'])

# If timestamps are milliseconds (not seconds)
data['created_time'] = data['created_time'] / 1000

# prep_data() handles conversion automatically
prepared = prep_data(data, timestamp_share='created_time')
```

### Issue 2: Missing URLs

```python
# Remove posts without shared content
data = data.dropna(subset=['shared_url'])

# Or fill with placeholder
data['shared_url'] = data['shared_url'].fillna('NO_URL')
```

### Issue 3: Duplicate Posts

```python
# Remove duplicates by post_id
data = data.drop_duplicates(subset=['post_id'])
```

### Issue 4: Mixed Data Types

```python
# Ensure proper types
data['page_id'] = data['page_id'].astype(str)
data['post_id'] = data['post_id'].astype(str)
data['shared_url'] = data['shared_url'].astype(str)
```

## Complete Working Example

Save this as `prepare_my_data.py`:

```python
"""
Complete example: Load your CSV and run CooRPost analysis
"""

import pandas as pd
from coorpost import prep_data, detect_groups, generate_coordinated_network, visualize_network

# Step 1: Load your data
print("Loading data...")
data = pd.read_csv('your_facebook_data.csv')

# Step 2: Clean data
print("Cleaning data...")
data = data.dropna(subset=['shared_url', 'page_id', 'post_id', 'created_time'])
data = data.drop_duplicates(subset=['post_id'])

# Step 3: Prepare for CooRPost
print("Preparing data...")
prepared = prep_data(
    data,
    object_id='shared_url',      # Adjust to your column names
    account_id='page_id',        # Adjust to your column names
    content_id='post_id',        # Adjust to your column names
    timestamp_share='created_time'  # Adjust to your column names
)

# Step 4: Detect coordination
print("Detecting coordination...")
result = detect_groups(
    prepared,
    time_window=60,        # Adjust based on your needs
    min_participation=2    # Minimum posts per account
)

print(f"\n✓ Found {len(result)} coordinated actions")
print(f"✓ Involving {result['account_id'].nunique()} accounts")
print(f"✓ On {result['object_id'].nunique()} unique objects")

# Step 5: Build network
print("\nBuilding coordination network...")
network = generate_coordinated_network(
    result,
    edge_weight=0.5,  # Keep top 50% of edges
    subgraph=1
)

print(f"✓ Network: {network.number_of_nodes()} nodes, {network.number_of_edges()} edges")

# Step 6: Visualize
print("\nCreating visualization...")
visualize_network(
    network,
    title='Facebook Coordination Network',
    save_path='coordination_network.png'
)

print("\n✓ Done! Check coordination_network.png")

# Step 7: Export results
result.to_csv('coordination_results.csv', index=False)
print("✓ Results saved to coordination_results.csv")
```

## Quick Test

Run this to verify everything works:

```python
# test_data_preparation.py
from coorpost.utils import create_facebook_sample_data
from coorpost import prep_data, detect_groups

print("Testing data preparation...")

# Create sample data
data = create_facebook_sample_data(n_posts=50)
print(f"✓ Generated {len(data)} sample posts")

# Prepare
prepared = prep_data(
    data,
    object_id='shared_url',
    account_id='page_id',
    content_id='post_id',
    timestamp_share='created_time'
)
print(f"✓ Prepared data with columns: {prepared.columns.tolist()}")

# Detect
result = detect_groups(prepared, time_window=60)
print(f"✓ Detected {len(result)} coordinated actions")

if len(result) > 0:
    print("\n✓ SUCCESS! Everything is working correctly!")
else:
    print("\n⚠ No coordination found (may be normal with small random data)")
```

## Need Help?

- Check [docs/COMPLETE_GUIDE.md](docs/COMPLETE_GUIDE.md) for detailed workflow
- See [examples/01_basic_usage.py](examples/01_basic_usage.py) for working code
- Run `python test_data_preparation.py` to verify setup
