"""
Core coordination detection functions.

This module implements the primary algorithm for detecting coordinated behavior
on social media by identifying accounts that share the same content within
specific time windows.
"""

import pandas as pd
import numpy as np
from typing import Optional


def detect_groups(
    data: pd.DataFrame,
    time_window: int = 10,
    min_participation: int = 2,
    remove_loops: bool = True
) -> pd.DataFrame:
    """
    Detect pairs of accounts that share the same objects within a time window.
    
    This function identifies coordinated behavior by finding accounts that share
    identical content (URLs, images, hashtags, etc.) within a specified time window.
    It groups data by object_id and calculates time differences between all content
    pairs within groups, filtering out pairs exceeding the time_window threshold.
    
    Parameters
    ----------
    data : pd.DataFrame
        Input data with required columns:
        - object_id: Unique identifier for shared content (str/int)
        - account_id: Account identifier (str/int)
        - content_id: Post identifier (str/int)
        - timestamp_share: Unix timestamp (int)
    
    time_window : int, optional (default=10)
        Time window in seconds within which shares are considered coordinated.
        Larger values detect less strict coordination patterns.
    
    min_participation : int, optional (default=2)
        Minimum number of posts required for an account to be included in analysis.
        This filters out low-activity accounts that may not represent genuine
        coordination.
    
    remove_loops : bool, optional (default=True)
        If True, removes self-loops (same account sharing same content multiple times).
        Recommended to keep True for most analyses.
    
    Returns
    -------
    pd.DataFrame
        DataFrame with coordinated content pairs containing columns:
        - object_id: Shared content identifier
        - account_id: First account (older post)
        - account_id_y: Second account (newer post)
        - content_id: First post identifier (older)
        - content_id_y: Second post identifier (newer)
        - time_delta: Time difference in seconds (absolute value)
    
    Examples
    --------
    >>> import pandas as pd
    >>> data = pd.DataFrame({
    ...     'object_id': ['url_1', 'url_1', 'url_2'],
    ...     'account_id': ['user_a', 'user_b', 'user_c'],
    ...     'content_id': ['post_1', 'post_2', 'post_3'],
    ...     'timestamp_share': [1609459200, 1609459205, 1609459300]
    ... })
    >>> result = detect_groups(data, time_window=60, min_participation=1)
    >>> print(result)
    
    Notes
    -----
    - The function preserves temporal order: account_id represents the earlier post
    - Time deltas are always positive (absolute values)
    - Large datasets may require significant processing time
    
    References
    ----------
    Righetti, N., & Balluff, P. (2025). CooRTweet: A Generalized R Software for
    Coordinated Network Detection. Computational Communication Research, 7(1), 1.
    """
    # Validate input data
    required_cols = ['object_id', 'account_id', 'content_id', 'timestamp_share']
    missing_cols = [col for col in required_cols if col not in data.columns]
    
    if missing_cols:
        raise ValueError(
            f"Missing required columns: {missing_cols}. "
            f"Data must include: {required_cols}"
        )
    
    # Convert to appropriate types
    df = data.copy()
    df['object_id'] = df['object_id'].astype(str)
    df['account_id'] = df['account_id'].astype(str)
    df['content_id'] = df['content_id'].astype(str)
    df['timestamp_share'] = df['timestamp_share'].astype(int)
    
    # Pre-filter: Keep only accounts with minimum participation
    account_counts = df.groupby('account_id').size()
    valid_accounts = account_counts[account_counts >= min_participation].index
    df = df[df['account_id'].isin(valid_accounts)]
    
    if len(df) == 0:
        return pd.DataFrame(columns=required_cols + ['account_id_y', 'content_id_y', 'time_delta'])
    
    # Calculate combinations within each object_id group
    result_list = []
    
    for obj_id, group in df.groupby('object_id'):
        group = group.sort_values('timestamp_share').reset_index(drop=True)
        
        # Create all pairwise combinations
        for i in range(len(group)):
            for j in range(i + 1, len(group)):
                row_i = group.iloc[i]
                row_j = group.iloc[j]
                
                time_delta = abs(row_j['timestamp_share'] - row_i['timestamp_share'])
                
                # Only keep pairs within time window
                if time_delta <= time_window:
                    result_list.append({
                        'object_id': obj_id,
                        'content_id': row_i['content_id'],
                        'content_id_y': row_j['content_id'],
                        'account_id': row_i['account_id'],
                        'account_id_y': row_j['account_id'],
                        'time_delta': time_delta,
                        'timestamp_A': row_i['timestamp_share'],
                        'timestamp_B': row_j['timestamp_share']
                    })
    
    if not result_list:
        return pd.DataFrame(columns=required_cols + ['account_id_y', 'content_id_y', 'time_delta'])
    
    result = pd.DataFrame(result_list)
    
    # Remove loops (same account sharing same object)
    if remove_loops:
        result = result[result['account_id'] != result['account_id_y']]
    
    # Refine filtering by min_participation
    if min_participation >= 1:
        # Get all content_ids in the result
        all_content_ids = pd.concat([result['content_id'], result['content_id_y']]).unique()
        
        # Count posts per account that are in coordinated pairs
        temp_df = df[df['content_id'].isin(all_content_ids)]
        account_coord_counts = temp_df.groupby('account_id').size()
        valid_coord_accounts = account_coord_counts[account_coord_counts >= min_participation].index
        
        # Filter result to only include valid accounts
        result = result[
            result['account_id'].isin(valid_coord_accounts) &
            result['account_id_y'].isin(valid_coord_accounts)
        ]
    
    # Ensure older post is in account_id/content_id columns
    # Swap if needed based on timestamps
    swap_mask = result['timestamp_A'] > result['timestamp_B']
    if swap_mask.any():
        result.loc[swap_mask, ['account_id', 'account_id_y']] = \
            result.loc[swap_mask, ['account_id_y', 'account_id']].values
        result.loc[swap_mask, ['content_id', 'content_id_y']] = \
            result.loc[swap_mask, ['content_id_y', 'content_id']].values
    
    # Drop temporary timestamp columns
    result = result.drop(columns=['timestamp_A', 'timestamp_B'])
    
    # Ensure time_delta is always positive
    result['time_delta'] = result['time_delta'].abs()
    
    return result.reset_index(drop=True)


def flag_speed_share(
    data: pd.DataFrame,
    result: pd.DataFrame,
    time_window: int,
    min_participation: int
) -> pd.DataFrame:
    """
    Flag coordinated shares that occurred within a narrower time window.
    
    This function identifies a subset of coordinated behavior that occurred
    even faster than the original time_window, allowing for analysis of
    "fast" vs "slower" coordination patterns.
    
    Parameters
    ----------
    data : pd.DataFrame
        Original input data used in detect_groups()
    result : pd.DataFrame
        Output from detect_groups()
    time_window : int
        Narrower time window in seconds
    min_participation : int
        Minimum participation threshold
    
    Returns
    -------
    pd.DataFrame
        Result dataframe with additional column indicating fast shares
    
    Examples
    --------
    >>> result_fast = flag_speed_share(data, result, time_window=5, min_participation=2)
    >>> print(result_fast['time_window_5'].sum())  # Count of fast coordinated pairs
    """
    # Filter to narrower time window
    result_update = result[result['time_delta'] <= time_window].copy()
    
    # Apply min_participation filter
    if min_participation >= 1:
        all_content_ids = pd.concat([
            result_update['content_id'],
            result_update['content_id_y']
        ]).unique()
        
        temp_df = data[data['content_id'].isin(all_content_ids)]
        account_counts = temp_df.groupby('account_id').size()
        valid_accounts = account_counts[account_counts >= min_participation].index
        
        result_update = result_update[
            result_update['account_id'].isin(valid_accounts) &
            result_update['account_id_y'].isin(valid_accounts)
        ]
    
    # Create column name
    col_name = f'time_window_{time_window}'
    
    # Initialize column to 0
    result[col_name] = 0
    
    # Mark fast shares
    merge_cols = ['object_id', 'content_id', 'content_id_y', 'account_id', 'account_id_y']
    fast_pairs = result_update[merge_cols]
    
    # Set to 1 for matching pairs
    result = result.merge(
        fast_pairs.assign(**{col_name: 1}),
        on=merge_cols,
        how='left',
        suffixes=('', '_flag')
    )
    
    # Fill NaN with 0
    result[col_name] = result[col_name].fillna(0).astype(int)
    
    return result


def simulate_data(
    n_accounts_coord: int = 5,
    n_accounts_noncoord: int = 4,
    n_objects: int = 5,
    min_participation: int = 3,
    time_window: int = 10,
    approx_size: int = 200
) -> tuple:
    """
    Generate simulated coordinated and non-coordinated data for testing.
    
    Creates synthetic data with known coordinated accounts for validation
    and testing purposes.
    
    Parameters
    ----------
    n_accounts_coord : int
        Number of coordinated accounts to simulate
    n_accounts_noncoord : int
        Number of non-coordinated accounts to simulate
    n_objects : int
        Number of shared objects to simulate
    min_participation : int
        Minimum participation level for coordinated accounts
    time_window : int
        Time window for coordination (seconds)
    approx_size : int
        Approximate size of resulting dataset
    
    Returns
    -------
    tuple
        (input_data, expected_output) - DataFrames for testing
    
    Examples
    --------
    >>> input_data, expected = simulate_data(n_accounts_coord=10, n_objects=5)
    >>> result = detect_groups(input_data, time_window=10)
    >>> # Compare result with expected
    """
    np.random.seed(42)
    
    # Create account IDs
    account_ids_coord = [f'coord_{i:03d}' for i in range(n_accounts_coord)]
    account_ids_noncoord = [f'noncoord_{i:03d}' for i in range(n_accounts_noncoord)]
    
    # Create object IDs
    object_ids = [f'object_{i:03d}' for i in range(n_objects)]
    
    # Generate coordinated shares
    coord_data = []
    share_id = 0
    
    for obj in object_ids:
        # Coordinated accounts share within time_window
        base_time = np.random.randint(1609459200, 1609459200 + 86400)
        
        for acc in account_ids_coord[:min_participation + 1]:
            offset = np.random.randint(0, time_window)
            coord_data.append({
                'object_id': obj,
                'account_id': acc,
                'content_id': f'share_{share_id:06d}',
                'timestamp_share': base_time + offset
            })
            share_id += 1
    
    # Generate non-coordinated shares
    noncoord_data = []
    
    for obj in object_ids:
        for acc in account_ids_noncoord:
            # Random times, unlikely to be coordinated
            random_time = np.random.randint(1609459200, 1609459200 + 86400)
            noncoord_data.append({
                'object_id': obj,
                'account_id': acc,
                'content_id': f'share_{share_id:06d}',
                'timestamp_share': random_time
            })
            share_id += 1
    
    input_data = pd.DataFrame(coord_data + noncoord_data)
    
    # Generate expected output (coordinated pairs)
    expected_output = detect_groups(
        pd.DataFrame(coord_data),
        time_window=time_window,
        min_participation=min_participation
    )
    
    return input_data, expected_output
