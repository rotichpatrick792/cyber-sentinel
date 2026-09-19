# Random Forest — Feature Importance

Model: `random_forest_v1.joblib`

Total features: 78

## Top 20 features

| Rank | Feature | Importance | Cumulative |
|---:|---|---:|---:|
| 1 | `Destination Port` | 0.087229 | 0.087229 |
| 2 | `Init_Win_bytes_backward` | 0.045699 | 0.132928 |
| 3 | `Avg Bwd Segment Size` | 0.040353 | 0.173280 |
| 4 | `Total Length of Fwd Packets` | 0.039581 | 0.212861 |
| 5 | `Average Packet Size` | 0.036244 | 0.249105 |
| 6 | `Subflow Fwd Bytes` | 0.035982 | 0.285088 |
| 7 | `Bwd Packet Length Max` | 0.035149 | 0.320236 |
| 8 | `Max Packet Length` | 0.034817 | 0.355053 |
| 9 | `Avg Fwd Segment Size` | 0.033142 | 0.388195 |
| 10 | `Packet Length Mean` | 0.032115 | 0.420309 |
| 11 | `Fwd Packet Length Mean` | 0.031485 | 0.451795 |
| 12 | `Fwd Packet Length Max` | 0.029532 | 0.481326 |
| 13 | `Fwd Header Length.1` | 0.023420 | 0.504746 |
| 14 | `Bwd Header Length` | 0.023323 | 0.528069 |
| 15 | `Bwd Packet Length Std` | 0.023089 | 0.551157 |
| 16 | `Bwd Packet Length Mean` | 0.022782 | 0.573940 |
| 17 | `Total Length of Bwd Packets` | 0.021869 | 0.595809 |
| 18 | `Fwd Header Length` | 0.021357 | 0.617166 |
| 19 | `Subflow Bwd Bytes` | 0.020528 | 0.637694 |
| 20 | `Flow Bytes/s` | 0.019663 | 0.657357 |

## Cumulative thresholds

- **90%** of importance: 40 features
- **95%** of importance: 48 features
- **99%** of importance: 57 features
## Experiment: top-40 model

A model trained on the top 40 features achieves macro F1 = 0.9317 vs 0.9320 for the full 78-feature model. This confirms the remaining features carry negligible signal. The reduced model is adopted for deployment.
