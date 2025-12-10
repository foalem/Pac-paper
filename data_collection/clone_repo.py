import os
import pandas as pd
import subprocess
from pathlib import Path
import time

from util.log import configure_logger

logger = configure_logger('github-data_logger', 'logging_file.log')

def clone_repos_from_csv(csv_path: str, clone_dir: str = "./data/clone", delay: float = 1.0):
    """
    Reads a CSV file containing GitHub repository full names (owner/repo) and clones each
    repository into the specified directory.

    :param csv_path: Path to the CSV file with a column 'full_name'
    :param clone_dir: Directory to clone repositories into
    :param delay: Delay (in seconds) between successive clone attempts
    """
    # Ensure clone directory exists
    Path(clone_dir).mkdir(parents=True, exist_ok=True)

    # Read CSV
    df = pd.read_csv(csv_path)
    if "full_name" not in df.columns:
        raise ValueError("CSV must contain a 'full_name' column")

    # Remove duplicates and nulls
    repo_names = df["full_name"].dropna().drop_duplicates()

    for repo in repo_names:
        repo_url = f"https://github.com/{repo}.git"
        repo_dir = os.path.join(clone_dir, repo.replace("/", "__"))

        if os.path.exists(repo_dir):
            logger.info(f"[SKIP] Already cloned: {repo}")
            continue

        logger.info(f"[CLONE] Cloning {repo_url} ...")
        try:
            subprocess.run(["git", "clone", repo_url, repo_dir], check=True)
        except subprocess.CalledProcessError as e:
            logger.info(f"[ERROR] Failed to clone {repo}: {e}")
        time.sleep(delay)

    logger.info("[DONE] Cloning completed.")
