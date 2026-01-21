"""
Utility functions for data preparation and processing.

Includes functions for data formatting, timestamp conversion,
and image hashing for coordinated image detection.
"""

import pandas as pd
import numpy as np
from datetime import datetime
from typing import Optional, Union
import hashlib


def prep_data(
    data: pd.DataFrame,
    object_id: Optional[str] = None,
    account_id: Optional[str] = None,
    content_id: Optional[str] = None,
    timestamp_share: Optional[str] = None
) -> pd.DataFrame:
    """
    Prepare and standardize data for coordination detection.
    
    Renames columns to standard names required by detect_groups() and
    converts timestamps to Unix format if needed.
    
    Parameters
    ----------
    data : pd.DataFrame
        Input dataframe with social media data
    object_id : str, optional
        Column name to rename to 'object_id'
    account_id : str, optional
        Column name to rename to 'account_id'
    content_id : str, optional
        Column name to rename to 'content_id'
    timestamp_share : str, optional
        Column name to rename to 'timestamp_share'
        Will be converted to Unix timestamp if not already
    
    Returns
    -------
    pd.DataFrame
        DataFrame with standardized column names
    
    Examples
    --------
    >>> df = pd.DataFrame({
    ...     'user_id': ['u1', 'u2'],
    ...     'post_id': ['p1', 'p2'],
    ...     'url': ['url1', 'url1'],
    ...     'created_at': ['2021-01-01 00:00:00', '2021-01-01 00:00:05']
    ... })
    >>> prepared = prep_data(
    ...     df,
    ...     object_id='url',
    ...     account_id='user_id',
    ...     content_id='post_id',
    ...     timestamp_share='created_at'
    ... )
    >>> print(prepared.columns.tolist())
    ['object_id', 'account_id', 'content_id', 'timestamp_share']
    """
    df = data.copy()
    
    # Rename columns
    rename_map = {}
    if object_id:
        rename_map[object_id] = 'object_id'
    if account_id:
        rename_map[account_id] = 'account_id'
    if content_id:
        rename_map[content_id] = 'content_id'
    if timestamp_share:
        rename_map[timestamp_share] = 'timestamp_share'
    
    df = df.rename(columns=rename_map)
    
    # Convert timestamp if needed
    if 'timestamp_share' in df.columns:
        df['timestamp_share'] = convert_to_unix_timestamp(df['timestamp_share'])
    
    return df


def convert_to_unix_timestamp(timestamps: pd.Series) -> pd.Series:
    """
    Convert timestamps to Unix format (seconds since epoch).
    
    Handles various timestamp formats including:
    - Unix timestamps (int)
    - ISO format strings
    - datetime objects
    
    Parameters
    ----------
    timestamps : pd.Series
        Series of timestamps in various formats
    
    Returns
    -------
    pd.Series
        Unix timestamps (integers)
    
    Examples
    --------
    >>> import pandas as pd
    >>> ts = pd.Series(['2021-01-01 00:00:00', '2021-01-01 00:00:10'])
    >>> unix_ts = convert_to_unix_timestamp(ts)
    >>> print(unix_ts.tolist())
    """
    # Already Unix timestamps
    if pd.api.types.is_integer_dtype(timestamps):
        return timestamps.astype(int)
    
    # Try to convert to datetime then to Unix
    try:
        dt_series = pd.to_datetime(timestamps, utc=True)
        return dt_series.astype(int) // 10**9
    except Exception as e:
        raise ValueError(
            f"Unable to convert timestamps to Unix format. "
            f"Timestamps should be integers or parseable datetime strings. "
            f"Error: {e}"
        )


def compute_image_hash(image, hash_size: int = 8) -> str:
    """
    Compute perceptual hash of an image for detecting duplicate images.
    
    Uses difference hashing (dHash) algorithm which is robust to minor
    modifications like resizing, compression, and color adjustments.
    
    Parameters
    ----------
    image : PIL.Image or np.ndarray or str
        Image object, numpy array, or path to image file
    hash_size : int, optional (default=8)
        Size of the hash. Larger values = more precise but less tolerant
        of variations. Common values: 8, 16, 32
    
    Returns
    -------
    str
        Hexadecimal hash string
    
    Examples
    --------
    >>> from PIL import Image
    >>> img = Image.open('photo.jpg')
    >>> hash1 = compute_image_hash(img)
    >>> print(hash1)
    
    >>> # From file path
    >>> hash2 = compute_image_hash('photo.jpg')
    >>> print(hash1 == hash2)  # True
    
    Notes
    -----
    - Similar images will have similar (or identical) hashes
    - Use hamming distance to compare hash similarity
    - For coordination detection, identical hashes indicate coordinated image sharing
    """
    try:
        import imagehash
        from PIL import Image
    except ImportError:
        raise ImportError(
            "Image hashing requires 'imagehash' and 'Pillow' packages. "
            "Install with: pip install imagehash pillow"
        )
    
    # Handle different input types
    if isinstance(image, str):
        # File path
        image = Image.open(image)
    elif isinstance(image, np.ndarray):
        # NumPy array
        image = Image.fromarray(image)
    elif not hasattr(image, 'convert'):
        raise TypeError("Image must be PIL Image, numpy array, or file path")
    
    # Compute perceptual hash (dHash)
    phash = imagehash.dhash(image, hash_size=hash_size)
    
    return str(phash)


def hash_hamming_distance(hash1: str, hash2: str) -> int:
    """
    Calculate Hamming distance between two perceptual hashes.
    
    Hamming distance measures how many bits differ between two hashes.
    Lower distance = more similar images.
    
    Parameters
    ----------
    hash1 : str
        First hash string
    hash2 : str
        Second hash string
    
    Returns
    -------
    int
        Number of differing bits
    
    Examples
    --------
    >>> h1 = compute_image_hash('image1.jpg')
    >>> h2 = compute_image_hash('image2.jpg')
    >>> distance = hash_hamming_distance(h1, h2)
    >>> if distance < 10:
    ...     print("Images are very similar")
    """
    try:
        import imagehash
    except ImportError:
        raise ImportError("Requires 'imagehash' package")
    
    hash1_obj = imagehash.hex_to_hash(hash1)
    hash2_obj = imagehash.hex_to_hash(hash2)
    
    return hash1_obj - hash2_obj


def normalize_urls(urls: pd.Series) -> pd.Series:
    """
    Normalize URLs for consistent matching.
    
    Removes protocol, www, trailing slashes, and query parameters.
    
    Parameters
    ----------
    urls : pd.Series
        Series of URL strings
    
    Returns
    -------
    pd.Series
        Normalized URLs
    
    Examples
    --------
    >>> import pandas as pd
    >>> urls = pd.Series([
    ...     'https://www.example.com/page?id=123',
    ...     'http://example.com/page',
    ...     'www.example.com/page/'
    ... ])
    >>> normalized = normalize_urls(urls)
    >>> print(normalized.unique())  # All should be the same
    """
    normalized = urls.copy()
    
    # Remove protocol
    normalized = normalized.str.replace(r'https?://', '', regex=True)
    
    # Remove www
    normalized = normalized.str.replace(r'^www\.', '', regex=True)
    
    # Remove trailing slash
    normalized = normalized.str.rstrip('/')
    
    # Remove query parameters (optional - comment out if you want to keep them)
    # normalized = normalized.str.split('?').str[0]
    
    # Convert to lowercase
    normalized = normalized.str.lower()
    
    return normalized


def extract_domain(urls: pd.Series) -> pd.Series:
    """
    Extract domain names from URLs.
    
    Parameters
    ----------
    urls : pd.Series
        Series of URL strings
    
    Returns
    -------
    pd.Series
        Domain names
    
    Examples
    --------
    >>> import pandas as pd
    >>> urls = pd.Series([
    ...     'https://www.example.com/page',
    ...     'https://subdomain.example.com/article'
    ... ])
    >>> domains = extract_domain(urls)
    >>> print(domains.tolist())
    ['example.com', 'subdomain.example.com']
    """
    domains = urls.copy()
    
    # Remove protocol
    domains = domains.str.replace(r'https?://', '', regex=True)
    
    # Remove www
    domains = domains.str.replace(r'^www\.', '', regex=True)
    
    # Extract domain (before first /)
    domains = domains.str.split('/').str[0]
    
    # Convert to lowercase
    domains = domains.str.lower()
    
    return domains


def create_facebook_sample_data(n_posts: int = 100) -> pd.DataFrame:
    """
    Generate sample Facebook-like data for testing and examples.
    
    Creates synthetic data with coordinated and non-coordinated patterns.
    
    Parameters
    ----------
    n_posts : int, optional (default=100)
        Number of posts to generate
    
    Returns
    -------
    pd.DataFrame
        Sample Facebook data
    
    Examples
    --------
    >>> sample = create_facebook_sample_data(50)
    >>> print(sample.head())
    >>> # Use for testing
    >>> result = detect_groups(sample, time_window=60)
    """
    np.random.seed(42)
    
    # Create coordinated accounts (pages)
    coord_pages = [f'page_{i}' for i in range(5)]
    noncoord_pages = [f'page_{i}' for i in range(5, 15)]
    
    # Create shared URLs
    urls = [f'https://example.com/article{i}' for i in range(10)]
    
    posts = []
    post_id = 1
    base_time = 1609459200  # 2021-01-01 00:00:00
    
    # Generate coordinated posts
    for url in urls[:5]:
        coord_time = base_time + np.random.randint(0, 86400)
        
        for page in coord_pages[:3]:  # 3 pages coordinate
            # Post within 60 seconds of each other
            post_time = coord_time + np.random.randint(0, 60)
            posts.append({
                'post_id': f'post_{post_id}',
                'page_id': page,
                'shared_url': url,
                'created_time': post_time,
                'likes': np.random.randint(10, 1000),
                'shares': np.random.randint(5, 500)
            })
            post_id += 1
    
    # Generate non-coordinated posts
    for _ in range(n_posts - len(posts)):
        page = np.random.choice(noncoord_pages)
        url = np.random.choice(urls)
        post_time = base_time + np.random.randint(0, 86400)
        
        posts.append({
            'post_id': f'post_{post_id}',
            'page_id': page,
            'shared_url': url,
            'created_time': post_time,
            'likes': np.random.randint(10, 1000),
            'shares': np.random.randint(5, 500)
        })
        post_id += 1
    
    return pd.DataFrame(posts)
