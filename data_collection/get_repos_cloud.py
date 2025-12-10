import os
import csv
import random

import requests
import time
import json
import logging
import pandas as pd

from config.constant import GitHub_CONFIG
from util.requests_timer import delay_next_request

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

GITHUB_API_URL = "https://api.github.com"

HEADERS = {
    "Authorization": f"Bearer {random.choice(GitHub_CONFIG['token'])}",
    "Accept": "application/vnd.github+json"
}

# File to store valid repositories
OUTPUT_FILE = "filtered_repos.csv"


def fetch_repo_details(owner_repo: str) -> dict:
    """
    Queries the GitHub API for repository details.

    :param owner_repo: The "owner/repo" format string.
    :return: Dictionary with repo details or None if an error occurs.
    """
    url = f"{GITHUB_API_URL}/repos/{owner_repo}"
    response = requests.get(url, headers=HEADERS)

    if response.status_code == 200:
        # print(response.json())
        return response.json()
    else:
        logger.warning(f"Failed to fetch repo: {owner_repo} (HTTP {response.status_code})")
        return None


def check_keywords_in_repo(repo_data: dict, keywords: list) -> bool:
    """
    Checks if any keyword exists in the repository's name, description, or topics.

    :param repo_data: Dictionary containing repo metadata from GitHub API.
    :param keywords: List of keywords to check.
    :return: True if any keyword is found, otherwise False.
    """
    name = repo_data.get("name", "").lower()
    description = repo_data.get("description", "").lower() if repo_data.get("description") else ""
    topics = [topic.lower() for topic in repo_data.get("topics", [])]

    return any(
        keyword in name or
        keyword in description or
        any(keyword in topic for topic in topics)
        for keyword in keywords
    )

def save_valid_repo(repo_data: dict, output_file: str):
    """
    Saves valid repository data into a CSV file.

    :param repo_data: Dictionary containing repo details.
    :param output_file: CSV file path to store results.
    """
    fieldnames = [
        "full_name", "created_at", "updated_at", "size", "stargazers_count", "language",
        "has_issues", "forks_count", "archived", "open_issues_count", "topics", "open_issues", "description"
    ]

    file_exists = os.path.exists(output_file)

    with open(output_file, mode="a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)

        # Write header only if the file is new
        if not file_exists:
            writer.writeheader()

        writer.writerow({
            "full_name": repo_data["full_name"],
            "created_at": repo_data["created_at"],
            "updated_at": repo_data["updated_at"],
            "size": repo_data["size"],
            "stargazers_count": repo_data["stargazers_count"],
            "language": repo_data["language"],
            "has_issues": repo_data["has_issues"],
            "forks_count": repo_data["forks_count"],
            "archived": repo_data["archived"],
            "open_issues_count": repo_data["open_issues_count"],
            "topics": ",".join(repo_data.get("topics", [])),
            "open_issues": repo_data["open_issues_count"],
            "description": repo_data.get("description", "")
        })

    logger.info(f"Saved: {repo_data['full_name']}")


def process_repositories(csv_file: str, keywords: list, output_file: str):
    """
    Reads a CSV file containing repositories, checks if they match the given keywords,
    and saves matching repositories to an output file.

    :param csv_file: Path to the input CSV file.
    :param keywords: List of keywords to search for.
    :param output_file: Path to the output CSV file.
    """
    idx: int
    df = pd.read_csv(csv_file)

    if "project_name" not in df.columns:
        raise ValueError("CSV file must contain a 'project_name' column.")

    total_repos = len(df)
    for idx, row in df.iterrows():
        owner_repo = row["project_name"]

        logger.info(f"Processing {idx + 1}/{total_repos}: {owner_repo}")

        # Fetch repo metadata
        repo_data = fetch_repo_details(owner_repo)
        if not repo_data:
            continue  # Skip if repo not found

        # Check if repo matches any keyword
        if check_keywords_in_repo(repo_data, keywords):
            save_valid_repo(repo_data, output_file)

        # Respect API rate limits
        delay_next_request()

    logger.info("Processing complete!")

