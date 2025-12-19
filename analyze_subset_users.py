"""
Script to analyze all users in the subset data based on date_group_token.csv files.
This script analyzes users from subset_all_markets_output and generates subset_all_users_analysis.csv.
"""
from analyze_all_users import analyze_all_users


if __name__ == "__main__":
    analyze_all_users(
        base_path="subset_all_markets_output",
        output_file="subset_all_users_analysis.csv"
    )
