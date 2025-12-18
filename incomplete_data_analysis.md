# Analysis of Markets with Incomplete Data



This report identifies events and markets where data export reached the maximum threshold of **1,000,000 rows**, indicating potentially incomplete data.



## Summary



- **Total markets analyzed**: 66
- **Markets with incomplete data**: 9
- **Events with incomplete markets**: 2
- **Threshold**: 1,000,000 data rows (1,000,001 total rows including header)



⚠️ **Warning**: The following markets have reached the export limit and may have incomplete data.



## Events with Incomplete Markets



### Event: `next-senate-majority-leader`



**Number of incomplete markets**: 7



- Total data rows across incomplete markets: 7,000,000
- Average rows per market: 1,000,000
- ⚠️ **All markets in this event are exactly at the threshold**



| Market Slug | File Path | Data Rows | Status |

| ----------- | --------- | --------- | ------ |

| `will-jd-vance-be-the-next-senate-majority-leader` | `next-senate-majority-leader/trades/will-jd-vance-be-the-next-senate-majority-leader_trades.csv` | 1,000,000 | ⚠️ AT LIMIT |

| `will-john-barrasso-be-the-next-senate-majority-leader` | `next-senate-majority-leader/trades/will-john-barrasso-be-the-next-senate-majority-leader_trades.csv` | 1,000,000 | ⚠️ AT LIMIT |

| `will-john-cornyn-be-the-next-seante-majority-leader` | `next-senate-majority-leader/trades/will-john-cornyn-be-the-next-seante-majority-leader_trades.csv` | 1,000,000 | ⚠️ AT LIMIT |

| `will-john-thune-be-the-next-seante-majority-leader` | `next-senate-majority-leader/trades/will-john-thune-be-the-next-seante-majority-leader_trades.csv` | 1,000,000 | ⚠️ AT LIMIT |

| `will-joni-ernst-be-the-next-senate-majority-leader` | `next-senate-majority-leader/trades/will-joni-ernst-be-the-next-senate-majority-leader_trades.csv` | 1,000,000 | ⚠️ AT LIMIT |

| `will-rick-scott-be-the-next-senate-majority-leader` | `next-senate-majority-leader/trades/will-rick-scott-be-the-next-senate-majority-leader_trades.csv` | 1,000,000 | ⚠️ AT LIMIT |

| `will-steve-daines-be-the-next-senate-majority-leader` | `next-senate-majority-leader/trades/will-steve-daines-be-the-next-senate-majority-leader_trades.csv` | 1,000,000 | ⚠️ AT LIMIT |



### Event: `arizona-senate-election-margin-of-victory`



**Number of incomplete markets**: 2



- Total data rows across incomplete markets: 2,000,000
- Average rows per market: 1,000,000
- ⚠️ **All markets in this event are exactly at the threshold**



| Market Slug | File Path | Data Rows | Status |

| ----------- | --------- | --------- | ------ |

| `will-gallego-win-arizona-senate-election-by-2-3-or-more` | `arizona-senate-election-margin-of-victory/trades/will-gallego-win-arizona-senate-election-by-2-3-or-more_trades.csv` | 1,000,000 | ⚠️ AT LIMIT |

| `will-kari-lake-win-arizona-senate-election-by-2-or-more` | `arizona-senate-election-margin-of-victory/trades/will-kari-lake-win-arizona-senate-election-by-2-or-more_trades.csv` | 1,000,000 | ⚠️ AT LIMIT |



## Detailed Breakdown



### All Markets Analyzed



| Event ID | Market Slug | Data Rows | Status |

| -------- | ----------- | --------- | ------ |

| `arizona-senate-election-margin-of-victory` | `will-gallego-win-arizona-senate-election-by-2-3-or-more` | 1,000,000 | ⚠️ INCOMPLETE |

| `arizona-senate-election-margin-of-victory` | `will-kari-lake-win-arizona-senate-election-by-2-or-more` | 1,000,000 | ⚠️ INCOMPLETE |

| `next-senate-majority-leader` | `will-jd-vance-be-the-next-senate-majority-leader` | 1,000,000 | ⚠️ INCOMPLETE |

| `next-senate-majority-leader` | `will-john-barrasso-be-the-next-senate-majority-leader` | 1,000,000 | ⚠️ INCOMPLETE |

| `next-senate-majority-leader` | `will-john-cornyn-be-the-next-seante-majority-leader` | 1,000,000 | ⚠️ INCOMPLETE |

| `next-senate-majority-leader` | `will-john-thune-be-the-next-seante-majority-leader` | 1,000,000 | ⚠️ INCOMPLETE |

| `next-senate-majority-leader` | `will-joni-ernst-be-the-next-senate-majority-leader` | 1,000,000 | ⚠️ INCOMPLETE |

| `next-senate-majority-leader` | `will-rick-scott-be-the-next-senate-majority-leader` | 1,000,000 | ⚠️ INCOMPLETE |

| `next-senate-majority-leader` | `will-steve-daines-be-the-next-senate-majority-leader` | 1,000,000 | ⚠️ INCOMPLETE |

| `arizona-senate-election-margin-of-victory` | `will-gallego-win-arizona-senate-election-by-1-2` | 1,465 | ✅ Complete |

| `arizona-senate-election-margin-of-victory` | `will-gallego-win-arizona-senate-election-by-3-or-more` | 1,424 | ✅ Complete |

| `arizona-senate-election-margin-of-victory` | `will-kari-lake-win-arizona-senate-election-by-0-1` | 1,272 | ✅ Complete |

| `arizona-senate-election-margin-of-victory` | `will-gallego-win-arizona-senate-election-by-0-1` | 1,127 | ✅ Complete |

| `will-fischer-win-nebraska-senate-election-by-7-points` | `will-fischer-win-nebraska-senate-election-by-7-points` | 1,044 | ✅ Complete |

| `arizona-senate-election-margin-of-victory` | `will-kari-lake-win-arizona-senate-election-by-1-2` | 988 | ✅ Complete |

| `nebraska-senate-special-election` | `will-a-candidate-from-another-party-win-nebraska-special-senate-election` | 171 | ✅ Complete |

| `nebraska-senate-special-election` | `will-a-republican-win-nebraska-special-senate-election` | 130 | ✅ Complete |

| `nebraska-senate-special-election` | `will-a-democrat-win-nebraska-special-senate-election` | 91 | ✅ Complete |

| `nebraska-senate-election-winner` | `will-the-republicans-win-the-nebraska-senate-race-in-2026` | 84 | ✅ Complete |

| `maine-senate-election-winner` | `will-the-democrats-win-the-maine-senate-race-in-2026` | 74 | ✅ Complete |

| `nevada-senate-republican-primary-winner` | `will-sam-brown-win-the-2024-nevada-senate-republican-primary` | 71 | ✅ Complete |

| `new-jersey-senate-election-winner` | `will-the-democrats-win-the-new-jersey-senate-race-in-2026` | 55 | ✅ Complete |

| `virginia-senate-republican-primary-winner` | `will-hung-cao-win-the-2024-virginia-senate-republican-primary` | 55 | ✅ Complete |

| `texas-senate-election-winner` | `will-the-republicans-win-the-texas-senate-race-in-2026` | 46 | ✅ Complete |

| `nevada-senate-democratic-primary-winner` | `will-jacky-rosen-win-the-2024-nevada-senate-democratic-primary` | 45 | ✅ Complete |

| `massachusetts-senate-election-winner` | `will-the-democrats-win-the-massachusetts-senate-race-in-2026` | 37 | ✅ Complete |

| `nevada-senate-democratic-primary-winner` | `will-mike-schaefer-win-the-2024-nevada-senate-democratic-primary` | 37 | ✅ Complete |

| `nebraska-senate-election-winner` | `will-the-democrats-win-the-nebraska-senate-race-in-2026` | 36 | ✅ Complete |

| `nevada-senate-republican-primary-winner` | `will-jeff-gunter-win-the-2024-nevada-senate-republican-primary` | 34 | ✅ Complete |

| `ohio-senate-election-winner` | `will-the-republicans-win-the-ohio-senate-race-in-2026` | 34 | ✅ Complete |

| `nevada-senate-democratic-primary-winner` | `will-another-candidate-win-the-2024-nevada-senate-democratic-primary` | 32 | ✅ Complete |

| `nevada-senate-democratic-primary-winner` | `will-troy-walker-win-the-2024-nevada-senate-democratic-primary` | 32 | ✅ Complete |

| `maine-senate-election-winner` | `will-the-republicans-win-the-maine-senate-race-in-2026` | 30 | ✅ Complete |

| `new-jersey-senate-election-winner` | `will-the-republicans-win-the-new-jersey-senate-race-in-2026` | 30 | ✅ Complete |

| `nevada-senate-republican-primary-winner` | `will-tony-grady-win-the-2024-nevada-senate-republican-primary` | 29 | ✅ Complete |

| `virginia-senate-republican-primary-winner` | `will-another-person-win-the-2024-virginia-senate-republican-primary` | 25 | ✅ Complete |

| `nevada-senate-republican-primary-winner` | `will-jim-marchant-win-the-2024-nevada-senate-republican-primary` | 24 | ✅ Complete |

| `virginia-senate-republican-primary-winner` | `will-jonathan-walker-emord-win-the-2024-virginia-senate-republican-primary` | 23 | ✅ Complete |

| `west-virginia-senate-election-winner` | `will-the-republicans-win-the-west-virginia-senate-race-in-2026` | 23 | ✅ Complete |

| `nevada-senate-republican-primary-winner` | `will-another-candidate-win-the-2024-nevada-senate-republican-primary` | 22 | ✅ Complete |

| `virginia-senate-election-winner` | `will-the-democrats-win-the-virginia-senate-race-in-2026` | 18 | ✅ Complete |

| `virginia-senate-republican-primary-winner` | `will-chuck-smith-win-the-2024-virginia-senate-republican-primary` | 18 | ✅ Complete |

| `ohio-senate-election-winner` | `will-the-democrats-win-the-ohio-senate-race-in-2026` | 16 | ✅ Complete |

| `virginia-senate-republican-primary-winner` | `will-scott-parkinson-win-the-2024-virginia-senate-republican-primary` | 16 | ✅ Complete |

| `virginia-senate-republican-primary-winner` | `will-eddie-garcia-win-the-2024-virginia-senate-republican-primary` | 15 | ✅ Complete |

| `tennessee-senate-election-winner` | `will-the-republicans-win-the-tennessee-senate-race-in-2026` | 14 | ✅ Complete |

| `west-virginia-senate-election-winner` | `will-the-democrats-win-the-west-virginia-senate-race-in-2026` | 13 | ✅ Complete |

| `texas-senate-election-winner` | `will-the-democrats-win-the-texas-senate-race-in-2026` | 12 | ✅ Complete |

| `delaware-senate-election-winner` | `will-the-democrats-win-the-delaware-senate-race-in-2026` | 11 | ✅ Complete |

| `florida-senate-election-winner` | `will-the-republicans-win-the-florida-senate-race-in-2026` | 11 | ✅ Complete |

| `massachusetts-senate-election-winner` | `will-the-republicans-win-the-massachusetts-senate-race-in-2026` | 11 | ✅ Complete |

| `mississippi-senate-election-winner` | `will-the-republicans-win-the-mississippi-senate-race-in-2026` | 11 | ✅ Complete |

| `wyoming-senate-election-winner` | `will-the-democrats-win-the-wyoming-senate-race-in-2026` | 11 | ✅ Complete |

| `minnesota-senate-election-winner` | `will-the-democrats-win-the-minnesota-senate-race-in-2026` | 7 | ✅ Complete |

| `montana-senate-election-winner` | `will-the-republicans-win-the-montana-senate-race-in-2026` | 7 | ✅ Complete |

| `wyoming-senate-election-winner` | `will-the-republicans-win-the-wyoming-senate-race-in-2026` | 7 | ✅ Complete |

| `new-mexico-senate-election-winner` | `will-the-democrats-win-the-new-mexico-senate-race-in-2026` | 6 | ✅ Complete |

| `rhode-island-senate-election-winner` | `will-the-democrats-win-the-rhode-island-senate-race-in-2026` | 6 | ✅ Complete |

| `virginia-senate-election-winner` | `will-the-republicans-win-the-virginia-senate-race-in-2026` | 6 | ✅ Complete |

| `rhode-island-senate-election-winner` | `will-the-republicans-win-the-rhode-island-senate-race-in-2026` | 5 | ✅ Complete |

| `mississippi-senate-election-winner` | `will-the-democrats-win-the-mississippi-senate-race-in-2026` | 4 | ✅ Complete |

| `tennessee-senate-election-winner` | `will-the-democrats-win-the-tennessee-senate-race-in-2026` | 4 | ✅ Complete |

| `delaware-senate-election-winner` | `will-the-republicans-win-the-delaware-senate-race-in-2026` | 3 | ✅ Complete |

| `new-mexico-senate-election-winner` | `will-the-republicans-win-the-new-mexico-senate-race-in-2026` | 3 | ✅ Complete |

| `florida-senate-election-winner` | `will-the-democrats-win-the-florida-senate-race-in-2026` | 2 | ✅ Complete |

| `montana-senate-election-winner` | `will-the-democrats-win-the-montana-senate-race-in-2026` | 2 | ✅ Complete |



## Recommendations



1. **Re-export data** for markets marked as incomplete, using pagination or date filters to retrieve all records.
2. **Verify completeness** by checking if the last row timestamp matches the expected end date for each market.
3. **Consider data partitioning** for very large markets to avoid hitting export limits in the future.
4. **Monitor export processes** to ensure all data is captured before the threshold is reached.


