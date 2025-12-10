import csv
import random
import time
from typing import List, Set

import pandas as pd
import requests

from config.constant import *
from util.requests_timer import delay_next_request
from util.util import *

logger = configure_logger('github-data_logger', 'logging_file.log')

PROGRESS_DIR = "./progress"
os.makedirs(PROGRESS_DIR, exist_ok=True)
STAR_SPLITS = [0, 10, 30, 50, 60, 80, 100, 500, 1000, 5000, 10000]
GITHUB_HEADERS = lambda: {
    "Authorization": f"Bearer {random.choice(GitHub_CONFIG['token'])}",
    "Accept": "application/vnd.github+json"
}

def build_star_queries() -> List[str]:
    ranges = [f"{STAR_SPLITS[i]}..{STAR_SPLITS[i + 1]}" for i in range(len(STAR_SPLITS) - 1)]
    ranges.append(f">{STAR_SPLITS[-1]}")
    return ranges

def get_total_count_for_code_query(query: str) -> int:
    url = "https://api.github.com/search/code"
    params = {
        "q": query,
        "per_page": 1,
        "page": 1
    }
    try:
        response = requests.get(url, headers=GITHUB_HEADERS(), params=params)
        delay_next_request()
        if response.status_code == 200:
            return response.json().get("total_count", 0)
        else:
            logger.warning(f"Query failed: {response.status_code} - {response.text}")
            return 0
    except requests.RequestException as e:
        logger.error(f"Failed to get total count for query '{query}': {e}")
        return 0

def fetch_and_store(query: str, output_file: str, seen: Set[str], progress_file: str):
    """
    Fetch repositories from GitHub code search API using a specific query, page by page,
    and store unique repository full names into a CSV file.

    - Saves progress using a JSON file so the function can resume after interruption.
    - Avoids duplicate entries using a provided set of seen repo full names.
    - Implements retry logic for temporary errors.
    - Stops fetching when no more results are returned or fewer than the per_page value.

    :param query: GitHub code search query string
    :param output_file: Path to the CSV file for saving results
    :param seen: Set to track already recorded repository full names
    :param progress_file: JSON file to store last processed page for resumability
    :param max_retries: Maximum retry attempts on failure
    """

    page = load_progress_pac(progress_file)

    while True:
        response = None
        params = {
            "q": query,
            "per_page": GitHub_CONFIG["per_page"],
            "page": page
        }

        attempts = 0
        while attempts < GitHub_CONFIG["max_retries"]:
            try:
                response = requests.get(
                    "https://api.github.com/search/code",
                    headers=GITHUB_HEADERS(),
                    params=params
                )
                delay_next_request()
                if response.status_code == 200:
                    print("Response 200")
                    break
                else:
                    logger.warning(f"[Page {page}] Status {response.status_code}: {response.text}")
                    attempts += 1
                    time.sleep(3 * attempts)
                    break
            except requests.RequestException as e:
                attempts += 1
                logger.warning(f"[Page {page}] Request error (attempt {attempts}): {e}")
                time.sleep(3 * attempts)
                break

        if attempts == GitHub_CONFIG["max_retries"] or not response:
            logger.error(f"Max retries exceeded or no response on page {page}. Skipping.")
            page += 1
            break

        data = response.json()
        items = data.get("items", [])
        logger.info(f"[Page {page}] Retrieved {len(items)} items")
        if items:
            print("Saving items")
            with open(output_file, "a", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=["full_name"])
                if f.tell() == 0:
                    writer.writeheader()
                for item in items:
                    full_name = item["repository"]["full_name"]
                    if full_name not in seen:
                        writer.writerow({"full_name": full_name})
                        seen.add(full_name)

            logger.info(f"[Page {page}] {len(items)} results added.")
            save_progress_pac(progress_file, page)
            page += 1
            delay_next_request()

            if len(items) < GitHub_CONFIG["per_page"]:
                logger.info(f"Final page reached (received {len(items)} < {GitHub_CONFIG['per_page']}).")
                break
        else:
            logger.info("No more items returned.")
            break

# def fetch_and_store(query: str, output_file: str, seen: set):
#     page = 1
#     while True:
#         params = {
#             "q": query,
#             "per_page": GitHub_CONFIG["per_page"],
#             "page": page
#         }
#         try:
#             response = requests.get("https://api.github.com/search/code", headers=GITHUB_HEADERS(), params=params, timeout=30)
#             if response.status_code != 200:
#                 logger.error(f"GitHub search failed: {response.status_code} - {response.text}")
#                 break
#
#             items = response.json().get("items", [])
#             if not items:
#                 break
#
#             with open(output_file, "a", newline="", encoding="utf-8") as f:
#                 writer = csv.DictWriter(f, fieldnames=["full_name"])
#                 if f.tell() == 0:
#                     writer.writeheader()
#                 for item in items:
#                     full_name = item["repository"]["full_name"]
#                     if full_name not in seen:
#                         writer.writerow({"full_name": full_name})
#                         seen.add(full_name)
#
#             logger.info(f"[Page {page}] {len(items)} results added.")
#             if len(items) < GitHub_CONFIG["per_page"]:
#                 break
#
#             page += 1
#             delay_next_request()
#
#         except requests.RequestException as e:
#             logger.error(f"Request failed: {e}")
#             break

# def search_pac_repos_by_extension(extension: str):
#     base_query = f"extension:{extension}"
#     output_file = f"pac_repos_{extension}.csv"
#     progress_file_base = os.path.join(PROGRESS_DIR, f"{extension.replace('.', '')}_progress.json")
#     seen = set()
#
#     # Load existing CSV if it exists
#     if os.path.exists(output_file):
#         with open(output_file, "r", encoding="utf-8") as f:
#             reader = csv.DictReader(f)
#             seen = {row["full_name"] for row in reader}
#     total_count = get_total_count_for_code_query(base_query)
#     logger.info(f"{extension}: total_count={total_count}")
#
#     if total_count <= 1000:
#         fetch_and_store(base_query, output_file, seen, progress_file_base)
#     else:
#         for size_range in build_star_queries():
#             sub_query = f"{base_query} size:{size_range}"
#             safe_range = size_range.replace("..", "_").replace(">", "gt")
#             sub_progress_file = os.path.join(PROGRESS_DIR, f"{extension.replace('.', '')}_size_{safe_range}.json")
#             logger.info(f"Splitting query: {sub_query}")
#             fetch_and_store(sub_query, output_file, seen, sub_progress_file)

def search_pac_repos_by_extension(query_or_extension: str):
    """
    Search GitHub code for a given file extension or full query (e.g., 'ClusterPolicy in:file extension:yaml')
    and save repository results in a CSV file.

    :param query_or_extension: either a raw GitHub search query or a file extension (e.g. 'rego')
    """
    # Determine if user passed full query (contains spaces or special GitHub qualifiers)
    if " " in query_or_extension or ":" in query_or_extension:
        base_query = query_or_extension
        label = re.sub(r'[^a-zA-Z0-9]', '_', query_or_extension)
    else:
        base_query = f"extension:{query_or_extension}"
        label = query_or_extension.replace(".", "")

    output_file = f"pac_repos_{label}.csv"
    progress_file_base = os.path.join(PROGRESS_DIR, f"{label}_progress.json")
    seen = set()

    # Load existing CSV if it exists
    if os.path.exists(output_file):
        with open(output_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            seen = {row["full_name"] for row in reader}

    total_count = get_total_count_for_code_query(base_query)
    logger.info(f"{label}: total_count={total_count}")

    if total_count <= 1000:
        fetch_and_store(base_query, output_file, seen, progress_file_base)
    else:
        for size_range in build_star_queries():
            sub_query = f"{base_query} size:{size_range}"
            safe_range = size_range.replace("..", "_").replace(">", "gt")
            sub_progress_file = os.path.join(PROGRESS_DIR, f"{label}_size_{safe_range}.json")
            logger.info(f"Splitting query: {sub_query}")
            fetch_and_store(sub_query, output_file, seen, sub_progress_file)


def merge_pac_repo_outputs(rego_file: str, sentinel_file: str, output_file: str) -> None:
    """
    Merge two CSV files (rego and sentinel results) into one file with flags for each extension.

    :param rego_file: Path to the CSV containing repos with `.rego` files.
    :param sentinel_file: Path to the CSV containing repos with `.sentinel` files.
    :param output_file: Path to save the merged CSV file.
    """
    df_rego = pd.read_csv(rego_file)
    df_rego["has_rego"] = True

    df_sentinel = pd.read_csv(sentinel_file)
    df_sentinel["has_sentinel"] = True

    # Merge on full_name (outer join to preserve all repos)
    df_merged = pd.merge(df_rego, df_sentinel, on="full_name", how="outer")

    # Fill missing indicators
    df_merged["has_rego"] = df_merged["has_rego"].fillna(False)
    df_merged["has_sentinel"] = df_merged["has_sentinel"].fillna(False)

    # Save merged CSV
    df_merged.to_csv(output_file, index=False)
    logger.info(f"Merged CSV written to {output_file}")
# def search_pac_repos_by_extension(extension: str):
#     base_query = f"extension:{extension} fork:false size:>0"
#     output_file = f"pac_repos_{extension}.csv"
#     seen = set()
#
#     # Load existing CSV if it exists
#     if os.path.exists(output_file):
#         with open(output_file, "r", encoding="utf-8") as f:
#             reader = csv.DictReader(f)
#             seen = {row["full_name"] for row in reader}
#
#     total_count = get_total_count_for_code_query(base_query)
#     logger.info(f"{extension}: total_count={total_count}")
#
#     if total_count <= 1000:
#         fetch_and_store(base_query, output_file, seen)
#     else:
#         for star_range in build_star_queries():
#             sub_query = f"{base_query} stars:{star_range}"
#             logger.info(f"Splitting query: {sub_query}")
#             fetch_and_store(sub_query, output_file, seen)


# def search_repos_with_pac_files() -> list:
#     """
#     Search GitHub for repositories containing .rego or .sentinel files.
#     Returns a list of unique repository full names (owner/repo).
#     """
#     url = "https://api.github.com/search/code"
#     query = "extension:rego OR extension:sentinel"
#
#     headers = {
#         "Authorization": f"Bearer {random.choice(GitHub_CONFIG['token'])}",
#         "Accept": "application/vnd.github+json"
#     }
#
#     repos = set()
#     for page in range(1, GitHub_CONFIG["max_pages"] + 1):
#         params = {
#             "q": query,
#             "per_page": GitHub_CONFIG["per_page"],
#             "page": page
#         }
#
#         logger.info(f"Querying page {page}...")
#         try:
#             response = requests.get(url, headers=headers, params=params, timeout=30)
#
#             if response.status_code == 200:
#                 data = response.json()
#                 items = data.get("items", [])
#                 if not items:
#                     break
#
#                 for item in items:
#                     repo_info = item.get("repository", {})
#                     full_name = repo_info.get("full_name")
#                     if full_name:
#                         repos.add(full_name)
#
#                 logger.info(f"Collected {len(repos)} repositories so far.")
#                 delay_next_request()
#             else:
#                 logger.warning(f"GitHub API returned {response.status_code}: {response.text}")
#                 break
#
#         except requests.exceptions.RequestException as e:
#             logger.error(f"Request failed: {e}")
#             break
#
#     return sorted(repos)

# def check_policy_as_code(full_name: str) -> bool:
#     """
#     Checks if a repository contains Policy as Code files (OPA `.rego` or Sentinel `.sentinel`).
#     Uses a single GitHub API request with 'extension:rego OR extension:sentinel'.
#     """
#     owner, repo = full_name.split("/")
#
#     # Single query for both OPA (`.rego`) and Sentinel (`.sentinel`) files
#     query = "extension:rego OR extension:sentinel"
#
#     return search_code_in_repo(owner, repo, query)
#
#
# def enrich_csv_with_pac(input_csv: str, output_csv: str):
#     """
#     Reads the CSV, filters repos with Docker or Terraform, checks for Policy as Code (PaC),
#     and updates the CSV with a `has_pac` column, avoiding duplicate checks.
#     """
#     # Load CSV
#     df = pd.read_csv(input_csv)
#
#     # Ensure required columns exist
#     if "has_docker" not in df.columns or "has_terraform" not in df.columns:
#         raise ValueError("CSV file must contain 'has_docker' and 'has_terraform' columns.")
#
#     # Initialize new column
#     df["has_pac"] = False
#
#     # **Filter repositories that have Docker or Terraform & remove duplicates**
#     filtered_df = df[(df["has_docker"] == True) | (df["has_terraform"] == True)]
#     filtered_df = filtered_df.drop_duplicates(subset=["full_name"])  # 🚀 Avoids duplicate processing
#
#     for idx, row in filtered_df.iterrows():
#         full_name = row["full_name"]
#
#         logger.info(f"Checking PaC for: {full_name}")
#
#         if check_policy_as_code(full_name):
#             df.loc[df["full_name"] == full_name, "has_pac"] = True  # ✅ Update only relevant rows
#             logger.info(f"{full_name} has Policy as Code")
#
#         # Respect API rate limits
#         delay_next_request()
#
#         # Save the updated CSV
#         df.to_csv(output_csv, index=False)
#     logger.info(f"Updated CSV saved to {output_csv}")
