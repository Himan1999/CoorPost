# Methodology and Theoretical Framework

## Overview

CooRPost implements a two-step algorithm for detecting coordinated behavior on social media, adapted from the methodology developed for CooRTweet (Righetti & Balluff, 2025).

## Theoretical Background

### What is Coordinated Behavior?

Coordinated behavior on social media refers to synchronized or orchestrated actions by multiple accounts to amplify specific content. This can include:

- **Coordinated Link Sharing**: Multiple accounts sharing the same URL within a short time window
- **Coordinated Image Sharing**: Distributing identical images across accounts
- **Coordinated Hashtag Usage**: Simultaneous use of same hashtags
- **Cross-platform Coordination**: Synchronized activity across multiple platforms

### Why Detect Coordination?

Coordination detection is important for:

1. **Disinformation Research**: Identifying inauthentic amplification campaigns
2. **Political Communication**: Studying astroturfing and grassroots movements
3. **Social Movements**: Analyzing activist coordination strategies
4. **Platform Integrity**: Detecting manipulation attempts

## The CooRPost Algorithm

### Step 1: Detect Groups

**Purpose**: Identify account pairs that share identical content within a time window

**Process**:
1. Group posts by `object_id` (shared content identifier)
2. For each group, calculate time differences between all post pairs
3. Filter pairs where time_delta ≤ `time_window`
4. Remove accounts below `min_participation` threshold
5. Optionally remove self-loops (same account, same content)

**Mathematical Formulation**:

For a set of posts P sharing object o:
```
CoordinatedPairs(o) = {(p₁, p₂) | p₁, p₂ ∈ P, |t(p₂) - t(p₁)| ≤ w}
```

Where:
- t(p) = timestamp of post p
- w = time_window parameter

**Output**: DataFrame of coordinated pairs with:
- object_id, account_id, account_id_y
- content_id, content_id_y
- time_delta

### Step 2: Generate Network

**Purpose**: Create a coordination network and identify repeated coordination

**Process**:
1. Build undirected graph where nodes = accounts, edges = coordination
2. Calculate edge weight = frequency of coordination between account pairs
3. Compute edge symmetry score = balance of coordination
4. Apply percentile threshold to filter weak edges
5. Extract subgraphs based on filtering criteria

**Edge Weight Calculation**:

For accounts a and b:
```
weight(a,b) = |{(p₁, p₂) | p₁ posted by a, p₂ posted by b, (p₁, p₂) ∈ CoordinatedPairs}|
```

**Edge Symmetry Score**:

```
symmetry(a,b) = min(n_a, n_b) / max(n_a, n_b)
```

Where:
- n_a = number of unique posts by account a in coordinated pairs with b
- n_b = number of unique posts by account b in coordinated pairs with a

**Interpretation**:
- symmetry = 1.0: Perfect balance (both accounts contribute equally)
- symmetry < 0.5: Imbalanced (one account dominates)

## Parameters and Thresholds

### time_window

**Definition**: Maximum time difference (seconds) between posts to be considered coordinated

**Selection Guidelines**:
- **10-60 seconds**: Very tight coordination (likely automated or pre-planned)
- **5-30 minutes**: Moderate coordination (coordinated campaigns)
- **1-24 hours**: Loose coordination (organic spreading or slower campaigns)

**Considerations**:
- Platform characteristics (Facebook typically slower than Twitter)
- Content type (news articles vs. images)
- Research question (strict vs. broad coordination)

### min_participation

**Definition**: Minimum number of posts an account must have to be included

**Purpose**: Filter out low-activity or incidental accounts

**Recommendations**:
- **2-5**: Standard for most analyses
- **10+**: Focus on highly active coordinating accounts
- **1**: Include all accounts (use cautiously, may include noise)

### edge_weight

**Definition**: Percentile threshold for filtering edges (0-1)

**How it works**:
- 0.5 = keep top 50% of edges by weight
- 0.8 = keep top 20% of edges (stricter)
- 0.9 = keep top 10% (very strict)

**Selection**:
- **0.3-0.5**: Inclusive network (exploratory analysis)
- **0.6-0.8**: Moderate filtering (standard analysis)
- **0.9+**: Strict filtering (core coordination only)

## Advanced Features

### Fast Network Detection

**Purpose**: Identify subsets of coordination that occur even faster

**Method**:
1. Run `detect_groups()` with larger time_window (e.g., 60s)
2. Use `flag_speed_share()` to mark faster coordination (e.g., 10s)
3. Generate network with fast subgraph option

**Use Case**: Distinguish automated vs. manual coordination

### Multi-Modal Analysis

**Purpose**: Detect coordination across different content types

**Approach**:
1. Prepare data separately for each modality (URLs, images, hashtags)
2. Run `detect_groups()` on each
3. Combine results using `pd.concat()`
4. Generate unified network

**Benefit**: Captures diverse coordination strategies

### Edge Symmetry Score

**Purpose**: Measure balance in coordination relationships

**Interpretation**:

| Score Range | Interpretation |
|-------------|---------------|
| 0.8 - 1.0 | Mutual coordination (balanced partnership) |
| 0.5 - 0.8 | Moderately imbalanced |
| 0.2 - 0.5 | Highly imbalanced (leader-follower) |
| 0.0 - 0.2 | Extreme imbalance (amplifier relationship) |

**Application**: Identify coordination roles and network structure

## Validation and Limitations

### Strengths

✓ Platform-independent methodology
✓ Content-type agnostic
✓ Scalable to large datasets
✓ Validated against known coordination cases
✓ Flexible thresholds for different research contexts

### Limitations

⚠ Cannot determine intent (coordination ≠ inauthenticity)
⚠ May miss slower, less synchronous coordination
⚠ Sensitive to parameter selection
⚠ Does not account for organic viral spreading
⚠ Requires access to timestamp data

### Best Practices

1. **Triangulate**: Combine with qualitative analysis
2. **Validate**: Check results against known cases
3. **Test Parameters**: Try multiple thresholds
4. **Document**: Record all parameter choices
5. **Context**: Consider platform norms and content types

## Comparison with Other Methods

### vs. CooRTweet (Original)

- **Same**: Core algorithm, edge weight calculation
- **Different**: Python implementation, Facebook-focused

### vs. CooRnet

- **CooRnet**: Facebook/Instagram specific, link-sharing focused
- **CooRPost**: Multi-platform, multi-modal, more flexible

### vs. Botometer

- **Botometer**: Detects bot-like behavior
- **CooRPost**: Detects coordination (regardless of automation)

## References

Righetti, N., & Balluff, P. (2025). CooRTweet: A Generalized R Software for Coordinated Network Detection. *Computational Communication Research*, 7(1), 1.

Giglietto, F., Righetti, N., Rossi, L., & Marino, G. (2020). It takes a village to manipulate the media: coordinated link sharing behavior during 2018 and 2019 Italian elections. *Information, Communication & Society*, 23(6), 867-891.

Keller, F. B., Schoch, D., Stier, S., & Yang, J. (2020). Political astroturfing on Twitter: How to coordinate a disinformation campaign. *Political Communication*, 37(2), 256-280.

## Citation

When using CooRPost, please cite:

```bibtex
@software{coorpost2026,
  title = {CooRPost: Coordinated Post Detection for Facebook},
  author = {Your Name},
  year = {2026},
  url = {https://github.com/yourusername/CoorPost}
}

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
