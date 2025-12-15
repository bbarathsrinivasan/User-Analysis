# Active traders across markets



This report summarizes users in `all_markets_output` with the highest number of trades across all markets, split by YES and NO token activity.



## Methodology



- We scanned every `user_...` directory in `all_markets_output`.
- For each CSV file inside a user directory, we interpreted the filename: if it contains `yes` we treat it as YES-token trades; if it contains `no` we treat it as NO-token trades; otherwise trades are counted as `unknown`.
- Each CSV row is treated as one trade. We aggregate counts per user across all markets.
- `markets_traded` counts distinct CSV files (markets) where the user has at least one trade.

## Top active users (by total trades)


| Rank | User address | Total trades | YES trades | NO trades | Markets traded | Basic insight |

| ---- | ------------ | ------------ | ---------- | --------- | -------------- | ------------- |

| 1 | `0xa58d4f278d7953cd38eeb929f7e242bfc7c0b9b8` | 511 | 184 | 327 | 2 | mixed YES/NO activity, multi-market trader |

| 2 | `0xf0b0ef1d6320c6be896b4c9c54dd74407e7f8cab` | 422 | 250 | 172 | 2 | mixed YES/NO activity, multi-market trader |

| 3 | `0x0db290495bbde756199381b4ff2389c7c1e54e2f` | 404 | 201 | 203 | 2 | mixed YES/NO activity, multi-market trader |

| 4 | `0xabac536449439bb713d80d4dd41f3694c9386c97` | 297 | 157 | 140 | 2 | mixed YES/NO activity, multi-market trader |

| 5 | `0xd218e474776403a330142299f7796e8ba32eb5c9` | 287 | 35 | 252 | 2 | strong NO bias, multi-market trader |

| 6 | `0xb02ea57dbc3e69e08e7aaee78ef6122e301f25e5` | 269 | 175 | 94 | 2 | mixed YES/NO activity, multi-market trader |

| 7 | `0xb7d54bf1d0a362beb916d9cb58a04c41d67e0789` | 267 | 134 | 133 | 2 | mixed YES/NO activity, multi-market trader |

| 8 | `0x63d43bbb87f85af03b8f2f9e2fad7b54334fa2f1` | 264 | 15 | 249 | 2 | strong NO bias, multi-market trader |

| 9 | `0x993c072519306017fe9a6b3ee6fa4a02b3056787` | 262 | 138 | 124 | 2 | mixed YES/NO activity, multi-market trader |

| 10 | `0x5f390e4b7d6f06d6756a6c92afdbf7b3176aa78c` | 254 | 102 | 152 | 2 | mixed YES/NO activity, multi-market trader |

| 11 | `0x7e0cf40bf007ca211bb4afd31434c0f0b9a869b9` | 209 | 209 | 0 | 1 | strong YES bias, single-market trader |

| 12 | `0x3a8651c42ac19aa3e3141531a298abc72f51dea8` | 201 | 201 | 0 | 1 | strong YES bias, single-market trader |

| 13 | `0x4eb85167e92a59b671478bbdaaa901551a6a9231` | 199 | 86 | 113 | 2 | mixed YES/NO activity, multi-market trader |

| 14 | `0xb49f468c15c49783f2664c7198a4949ade1b12e6` | 198 | 0 | 198 | 1 | strong NO bias, single-market trader |

| 15 | `0xa8b7f8b34185e9cc62c471e1d353595148a3ee3c` | 197 | 149 | 48 | 2 | strong YES bias, multi-market trader |

| 16 | `0x96b59f71f635da5da031e3e93448c54fe226f5e7` | 183 | 183 | 0 | 1 | strong YES bias, single-market trader |

| 17 | `0xe3726a1b9c6ba2f06585d1c9e01d00afaedaeb38` | 177 | 177 | 0 | 1 | strong YES bias, single-market trader |

| 18 | `0x6b7ec4ba079c0a258435ea36025f6190cd424562` | 175 | 142 | 33 | 2 | strong YES bias, multi-market trader |

| 19 | `0xfe911a4e80ee71b47cd1ee690733ac4062e970ff` | 172 | 101 | 71 | 2 | mixed YES/NO activity, multi-market trader |

| 20 | `0x57d494d8aecd90fb4f48423974f7e48ec1f9ac0d` | 168 | 124 | 44 | 2 | strong YES bias, multi-market trader |



## User-level insights


### 1. `0xa58d4f278d7953cd38eeb929f7e242bfc7c0b9b8`



- **Total activity**: 511 trades across 2 market(s).

- **YES vs NO**: 184 YES trades, 327 NO trades, 0 unknown-labeled trades.

- **Interpretation**: Balanced usage of YES and NO tokens, more consistent with market-making, hedging, or opportunistic trading on both sides.

- **Cross-market behavior**: Trades span multiple markets, so this user appears to be a cross-market participant rather than focused on a single contract.



### 2. `0xf0b0ef1d6320c6be896b4c9c54dd74407e7f8cab`



- **Total activity**: 422 trades across 2 market(s).

- **YES vs NO**: 250 YES trades, 172 NO trades, 0 unknown-labeled trades.

- **Interpretation**: Balanced usage of YES and NO tokens, more consistent with market-making, hedging, or opportunistic trading on both sides.

- **Cross-market behavior**: Trades span multiple markets, so this user appears to be a cross-market participant rather than focused on a single contract.



### 3. `0x0db290495bbde756199381b4ff2389c7c1e54e2f`



- **Total activity**: 404 trades across 2 market(s).

- **YES vs NO**: 201 YES trades, 203 NO trades, 0 unknown-labeled trades.

- **Interpretation**: Balanced usage of YES and NO tokens, more consistent with market-making, hedging, or opportunistic trading on both sides.

- **Cross-market behavior**: Trades span multiple markets, so this user appears to be a cross-market participant rather than focused on a single contract.



### 4. `0xabac536449439bb713d80d4dd41f3694c9386c97`



- **Total activity**: 297 trades across 2 market(s).

- **YES vs NO**: 157 YES trades, 140 NO trades, 0 unknown-labeled trades.

- **Interpretation**: Balanced usage of YES and NO tokens, more consistent with market-making, hedging, or opportunistic trading on both sides.

- **Cross-market behavior**: Trades span multiple markets, so this user appears to be a cross-market participant rather than focused on a single contract.



### 5. `0xd218e474776403a330142299f7796e8ba32eb5c9`



- **Total activity**: 287 trades across 2 market(s).

- **YES vs NO**: 35 YES trades, 252 NO trades, 0 unknown-labeled trades.

- **Interpretation**: Strong preference for NO tokens, indicating a tendency to bet against events (skeptical or contrarian stance).

- **Cross-market behavior**: Trades span multiple markets, so this user appears to be a cross-market participant rather than focused on a single contract.



### 6. `0xb02ea57dbc3e69e08e7aaee78ef6122e301f25e5`



- **Total activity**: 269 trades across 2 market(s).

- **YES vs NO**: 175 YES trades, 94 NO trades, 0 unknown-labeled trades.

- **Interpretation**: Balanced usage of YES and NO tokens, more consistent with market-making, hedging, or opportunistic trading on both sides.

- **Cross-market behavior**: Trades span multiple markets, so this user appears to be a cross-market participant rather than focused on a single contract.



### 7. `0xb7d54bf1d0a362beb916d9cb58a04c41d67e0789`



- **Total activity**: 267 trades across 2 market(s).

- **YES vs NO**: 134 YES trades, 133 NO trades, 0 unknown-labeled trades.

- **Interpretation**: Balanced usage of YES and NO tokens, more consistent with market-making, hedging, or opportunistic trading on both sides.

- **Cross-market behavior**: Trades span multiple markets, so this user appears to be a cross-market participant rather than focused on a single contract.



### 8. `0x63d43bbb87f85af03b8f2f9e2fad7b54334fa2f1`



- **Total activity**: 264 trades across 2 market(s).

- **YES vs NO**: 15 YES trades, 249 NO trades, 0 unknown-labeled trades.

- **Interpretation**: Strong preference for NO tokens, indicating a tendency to bet against events (skeptical or contrarian stance).

- **Cross-market behavior**: Trades span multiple markets, so this user appears to be a cross-market participant rather than focused on a single contract.



### 9. `0x993c072519306017fe9a6b3ee6fa4a02b3056787`



- **Total activity**: 262 trades across 2 market(s).

- **YES vs NO**: 138 YES trades, 124 NO trades, 0 unknown-labeled trades.

- **Interpretation**: Balanced usage of YES and NO tokens, more consistent with market-making, hedging, or opportunistic trading on both sides.

- **Cross-market behavior**: Trades span multiple markets, so this user appears to be a cross-market participant rather than focused on a single contract.



### 10. `0x5f390e4b7d6f06d6756a6c92afdbf7b3176aa78c`



- **Total activity**: 254 trades across 2 market(s).

- **YES vs NO**: 102 YES trades, 152 NO trades, 0 unknown-labeled trades.

- **Interpretation**: Balanced usage of YES and NO tokens, more consistent with market-making, hedging, or opportunistic trading on both sides.

- **Cross-market behavior**: Trades span multiple markets, so this user appears to be a cross-market participant rather than focused on a single contract.



### 11. `0x7e0cf40bf007ca211bb4afd31434c0f0b9a869b9`



- **Total activity**: 209 trades across 1 market(s).

- **YES vs NO**: 209 YES trades, 0 NO trades, 0 unknown-labeled trades.

- **Interpretation**: Strong preference for YES tokens, suggesting they generally take positions that events will occur (optimistic or pro-outcome stance).

- **Cross-market behavior**: Activity is confined to a single market, pointing to specialized interest or concentrated conviction.



### 12. `0x3a8651c42ac19aa3e3141531a298abc72f51dea8`



- **Total activity**: 201 trades across 1 market(s).

- **YES vs NO**: 201 YES trades, 0 NO trades, 0 unknown-labeled trades.

- **Interpretation**: Strong preference for YES tokens, suggesting they generally take positions that events will occur (optimistic or pro-outcome stance).

- **Cross-market behavior**: Activity is confined to a single market, pointing to specialized interest or concentrated conviction.



### 13. `0x4eb85167e92a59b671478bbdaaa901551a6a9231`



- **Total activity**: 199 trades across 2 market(s).

- **YES vs NO**: 86 YES trades, 113 NO trades, 0 unknown-labeled trades.

- **Interpretation**: Balanced usage of YES and NO tokens, more consistent with market-making, hedging, or opportunistic trading on both sides.

- **Cross-market behavior**: Trades span multiple markets, so this user appears to be a cross-market participant rather than focused on a single contract.



### 14. `0xb49f468c15c49783f2664c7198a4949ade1b12e6`



- **Total activity**: 198 trades across 1 market(s).

- **YES vs NO**: 0 YES trades, 198 NO trades, 0 unknown-labeled trades.

- **Interpretation**: Strong preference for NO tokens, indicating a tendency to bet against events (skeptical or contrarian stance).

- **Cross-market behavior**: Activity is confined to a single market, pointing to specialized interest or concentrated conviction.



### 15. `0xa8b7f8b34185e9cc62c471e1d353595148a3ee3c`



- **Total activity**: 197 trades across 2 market(s).

- **YES vs NO**: 149 YES trades, 48 NO trades, 0 unknown-labeled trades.

- **Interpretation**: Strong preference for YES tokens, suggesting they generally take positions that events will occur (optimistic or pro-outcome stance).

- **Cross-market behavior**: Trades span multiple markets, so this user appears to be a cross-market participant rather than focused on a single contract.



### 16. `0x96b59f71f635da5da031e3e93448c54fe226f5e7`



- **Total activity**: 183 trades across 1 market(s).

- **YES vs NO**: 183 YES trades, 0 NO trades, 0 unknown-labeled trades.

- **Interpretation**: Strong preference for YES tokens, suggesting they generally take positions that events will occur (optimistic or pro-outcome stance).

- **Cross-market behavior**: Activity is confined to a single market, pointing to specialized interest or concentrated conviction.



### 17. `0xe3726a1b9c6ba2f06585d1c9e01d00afaedaeb38`



- **Total activity**: 177 trades across 1 market(s).

- **YES vs NO**: 177 YES trades, 0 NO trades, 0 unknown-labeled trades.

- **Interpretation**: Strong preference for YES tokens, suggesting they generally take positions that events will occur (optimistic or pro-outcome stance).

- **Cross-market behavior**: Activity is confined to a single market, pointing to specialized interest or concentrated conviction.



### 18. `0x6b7ec4ba079c0a258435ea36025f6190cd424562`



- **Total activity**: 175 trades across 2 market(s).

- **YES vs NO**: 142 YES trades, 33 NO trades, 0 unknown-labeled trades.

- **Interpretation**: Strong preference for YES tokens, suggesting they generally take positions that events will occur (optimistic or pro-outcome stance).

- **Cross-market behavior**: Trades span multiple markets, so this user appears to be a cross-market participant rather than focused on a single contract.



### 19. `0xfe911a4e80ee71b47cd1ee690733ac4062e970ff`



- **Total activity**: 172 trades across 2 market(s).

- **YES vs NO**: 101 YES trades, 71 NO trades, 0 unknown-labeled trades.

- **Interpretation**: Balanced usage of YES and NO tokens, more consistent with market-making, hedging, or opportunistic trading on both sides.

- **Cross-market behavior**: Trades span multiple markets, so this user appears to be a cross-market participant rather than focused on a single contract.



### 20. `0x57d494d8aecd90fb4f48423974f7e48ec1f9ac0d`



- **Total activity**: 168 trades across 2 market(s).

- **YES vs NO**: 124 YES trades, 44 NO trades, 0 unknown-labeled trades.

- **Interpretation**: Strong preference for YES tokens, suggesting they generally take positions that events will occur (optimistic or pro-outcome stance).

- **Cross-market behavior**: Trades span multiple markets, so this user appears to be a cross-market participant rather than focused on a single contract.


