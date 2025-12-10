import csv

import pandas as pd
import requests

from util.requests_timer import delay_next_request
from util.util import *
from config.constant import GitHub_CONFIG
import random

logger = configure_logger('github-data_logger', 'logging_file.log')

GITHUB_API_URL = "https://api.github.com"

FIELDS_TO_COLLECT = [
    "created_at",
    "updated_at",
    "size",
    "stargazers_count",
    "language",
    "has_issues",
    "forks_count",
    "archived",
    "open_issues_count",
    "topics",
    "open_issues",
    "description",
    "fork"
]

def GITHUB_HEADERS():
    return {
        "Authorization": f"Bearer {random.choice(GitHub_CONFIG['token'])}",
        "Accept": "application/vnd.github+json"
    }

def fetch_repo_metadata(full_name: str) -> dict:
    url = f"{GITHUB_API_URL}/repos/{full_name}"
    try:
        resp = requests.get(url, headers=GITHUB_HEADERS(), timeout=30)
        if resp.status_code == 200:
            return resp.json()
        else:
            logger.warning(f"[{full_name}] GitHub API error {resp.status_code}: {resp.text}")
    except requests.RequestException as e:
        logger.error(f"Request exception for {full_name}: {e}")
    return {}

def enrich_repos_incrementally(input_csv: str, output_csv: str, progress_file: str):
    df = pd.read_csv(input_csv)
    df['full_name'] = df['full_name'].fillna("").astype(str)
    seen = set()

    if os.path.exists(output_csv):
        existing = pd.read_csv(output_csv)
        seen = set(existing['full_name'])

    start_index = load_progress_pac(progress_file)

    with open(output_csv, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["full_name"] + FIELDS_TO_COLLECT)
        if f.tell() == 0:
            writer.writeheader()

        for idx, row in df.iloc[start_index:].iterrows():
            full_name = row['full_name']

            if not full_name or full_name in seen:
                continue

            metadata = fetch_repo_metadata(full_name)
            delay_next_request()

            if not metadata:
                continue

            output_row = {"full_name": full_name}
            for field in FIELDS_TO_COLLECT:
                value = metadata.get(field, None)
                if field == "topics":
                    value = ",".join(value) if isinstance(value, list) else ""
                output_row[field] = value

            writer.writerow(output_row)
            seen.add(full_name)
            logger.info(f"Saved metadata for {full_name}")
            save_progress_pac(progress_file, idx + 1)

def get_contributor_count(full_name: str) -> int:
    """
    Get the total number of contributors by paginating through all contributor pages.
    Uses the GitHub API endpoint: GET /repos/{owner}/{repo}/contributors

    :param full_name: 'owner/repo' format
    :return: Total number of contributors (including anonymous if available)
    """
    owner, repo = full_name.split("/")
    url = f"https://api.github.com/repos/{owner}/{repo}/contributors"
    per_page = 100
    page = 1
    total_contributors = 0

    while True:
        params = {
            "per_page": per_page,
            "page": page,
            "anon": "true"
        }

        try:
            response = requests.get(url, headers=GITHUB_HEADERS(), params=params)
            delay_next_request()

            if response.status_code == 200:
                contributors = response.json()
                if not contributors:
                    break
                total_contributors += len(contributors)

                if len(contributors) < per_page:
                    break  # Last page
                page += 1
            elif response.status_code == 403:
                logger.warning(f"Rate limited on {full_name}")
                return -1
            else:
                logger.warning(f"Failed to get contributors for {full_name} - Status {response.status_code}")
                return -1
        except requests.RequestException as e:
            logger.error(f"Error while fetching contributors for {full_name}: {e}")
            return -1

    return total_contributors

def enrich_with_contributor_count(input_csv: str, output_csv: str, progress_file: str):
    """
    Adds a `contributors_count` column to enriched.csv and saves progress after each query.
    """
    if not os.path.exists(input_csv):
        raise FileNotFoundError(f"Input file {input_csv} not found.")

    df = pd.read_csv(input_csv)

    # Load progress
    last_index = 0
    if os.path.exists(progress_file):
        with open(progress_file, "r", encoding="utf-8") as f:
            try:
                progress = json.load(f)
                last_index = progress.get("last_index", 0)
            except Exception:
                pass

    # Fill column if not present
    if "contributors_count" not in df.columns:
        df["contributors_count"] = -1

    for idx in range(last_index, len(df)):
        full_name = df.loc[idx, "full_name"]
        count = get_contributor_count(full_name)
        df.at[idx, "contributors_count"] = count
        logger.info(f"[{idx + 1}/{len(df)}] {full_name} contributors: {count}")

        # Save after each row
        df.to_csv(output_csv, index=False)
        with open(progress_file, "a", encoding="utf-8") as f:
            json.dump({"last_index": idx + 1}, f)

        delay_next_request()

    logger.info("Contributor enrichment complete.")


def compile_repo_data_to_csv(data_dir: str, output_csv: str) -> None:
    """
    Scans 'data_dir' for all JSON files ending with '_data.json'.
    Loads each file (list of repositories in JSON), extracts the desired fields,
    removes duplicates, and writes the final DataFrame to 'output_csv'.
    """

    # The files we want are those that end with "_data.json"
    data_files = get_data_json_files(data_dir)  # Provided separately

    all_repos = []

    # Fields we want from each repository
    fields = [
        "full_name",
        "created_at",
        "updated_at",
        "size",
        "stargazers_count",
        "language",
        "has_issues",
        "forks_count",
        "archived",
        "open_issues_count",
        "topics",
        "open_issues",
        "description"
    ]

    # Iterate over each data file
    for file_path in data_files:
        # Load JSON (list of repositories)
        with open(file_path, "r", encoding="utf-8") as f:
            try:
                repos = json.load(f)
            except json.JSONDecodeError:
                # If file is corrupt or not valid JSON, skip it
                continue

        # For each repo object, extract only the fields we need
        for repo in repos:
            # Build a dictionary of the required fields (handle missing keys with .get)
            extracted = {
                field: repo.get(field) for field in fields
            }
            # Optionally convert 'topics' list to a comma-joined string or keep it as-is
            if isinstance(extracted.get("topics"), list):
                extracted["topics"] = ",".join(extracted["topics"])

            all_repos.append(extracted)

    # Convert all_repos to a DataFrame
    df = pd.DataFrame(all_repos, columns=fields)

    # Remove duplicates based on 'full_name' (you could also use 'id' if available)
    df.drop_duplicates(subset=["full_name"], inplace=True)

    # Save to CSV (no index column)
    df.to_csv(output_csv, index=False)

    logger.info(f"Successfully compiled {len(df)} unique repositories into {output_csv}.")


def get_commit_dates_from_csv(input_csv: str, output_csv: str) -> None:
    """
    Read repository names from a CSV file and write commit dates to another CSV file.

    :param input_csv: Path to the input CSV file containing a column 'full_name' with repository names.
    :param output_csv: Path to the output CSV file to write repository names and commit dates.
    :param token: Optional GitHub personal access token for higher rate limits.
    """
    # headers = {"Accept": "application/vnd.github+json"}
    # if token:
    #     headers["Authorization"] = f"Bearer {token}"

    df_input = pd.read_excel(input_csv)
    commit_data = []

    for repo in df_input['full_name']:
        url = f"https://api.github.com/repos/{repo}/commits"
        response = requests.get(url, headers=GITHUB_HEADERS())
        delay_next_request()

        if response.status_code == 200:
            commits = response.json()
            if commits:
                first_commit_date = commits[0]['commit']['author']['date']
                last_commit_date = commits[-1]['commit']['author']['date']
            else:
                first_commit_date = None
                last_commit_date = None
        else:
            first_commit_date = None
            last_commit_date = None

        commit_data.append({
            'repository': repo,
            'first_commit_date': first_commit_date,
            'last_commit_date': last_commit_date
        })
        logger.info(f"Processed {repo}: first commit on {first_commit_date}, last commit on {last_commit_date}")

    df_output = pd.DataFrame(commit_data)
    df_output.to_csv(output_csv, index=False)