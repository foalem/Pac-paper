import json
import os
import re

from config.constant import PATH_FILE
from util.log import configure_logger

logger = configure_logger('github-data_logger', 'logging_file.log')
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # This is your Project Root
PROGRESS_FILE = "iac_progress.json"

def load_progress_pac(progress_file: str) -> int:
    if os.path.exists(progress_file):
        try:
            with open(progress_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("last_page", 1)
        except json.JSONDecodeError:
            return 1
    return 1

def save_progress_pac(progress_file: str, page: int):
    with open(progress_file, "w", encoding="utf-8") as f:
        json.dump({"last_page": page}, f)

def save_to_json(data, file, mode='w') -> None:
    with open(file, mode) as filey:
        filey.writelines(json.dumps(data, indent=4))


def load_progress_iac() -> int:
    """
    Load the last processed row index from a JSON file.
    Returns 0 if no progress file exists.
    """
    if os.path.exists(PROGRESS_FILE):
        try:
            with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("last_processed_index", 0)
        except json.JSONDecodeError:
            return 0
    return 0

def save_progress_iac(index: int) -> None:
    """
    Save the last processed row index to a JSON file.
    """
    with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
        json.dump({"last_processed_index": index}, f)



def load_progress(topic: str) -> int:
    """
    Attempts to load the last saved page number for the given topic.
    Returns 0 if there is no progress stored (meaning start from page 1).
    """
    # Build a simpler filename from topic by removing invalid chars
    safe_topic = re.sub(r'[<>:"/\\|?*]+', '_', topic)  # Replace invalid chars with '_'
    # Build the progress file path in the data directory
    progress_file = os.path.join(PATH_FILE['data'], f"{safe_topic}_progress.json")

    # If file does not exist yet, return 0 (meaning start from page 1)
    if not os.path.isfile(progress_file):
        return 0

    try:
        with open(progress_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("last_page", 0)
    except json.JSONDecodeError:
        # If the file is corrupt or invalid JSON, start from 0
        return 0

def save_progress(topic: str, page: int):
    """
    Saves the current page number to a progress file so we can resume later.
    """
    # Build a simpler filename from topic by removing invalid chars
    safe_topic = re.sub(r'[<>:"/\\|?*]+', '_', topic)  # Replace invalid chars with '_'
    # Build the progress file path
    progress_file = os.path.join(PATH_FILE['data'], f"{safe_topic}_progress.json")

    # Ensure the data directory exists
    os.makedirs(PATH_FILE['data'], exist_ok=True)

    with open(progress_file, "w", encoding="utf-8") as f:
        json.dump({"last_page": page}, f, indent=2)

def append_repos_to_file(topic: str, repo_items: list):
    """
    Appends newly fetched repository items to a file named after the topic.
    This ensures we don't lose data if the script stops mid-way.
    """

    # Build a simpler filename from topic by removing invalid chars
    safe_topic = re.sub(r'[<>:"/\\|?*]+', '_', topic)  # Replace invalid chars with '_'
    # Build the data file path
    data_file = os.path.join(PATH_FILE['data'], f"{safe_topic}_data.json")

    # Ensure the data directory exists
    os.makedirs(PATH_FILE['data'], exist_ok=True)

    # If file doesn't exist, create a new list. If it does, extend the existing list.
    existing = []
    if os.path.isfile(data_file):
        try:
            with open(data_file, "r", encoding="utf-8") as f:
                existing = json.load(f)
        except json.JSONDecodeError:
            # If the file is corrupt or invalid JSON, we start fresh
            existing = []

    existing.extend(repo_items)
    with open(data_file, "w", encoding="utf-8") as f:
        json.dump(existing, f, indent=2)


def get_data_json_files(directory: str):
    """
    Return a list of all JSON files in 'directory'
    that end with '_data.json'.

    :param directory: The path to the folder where we look for files.
    :return: A list of full paths to JSON files ending with '_data.json'.
    """
    if not os.path.isdir(directory):
        raise ValueError(f"The path '{directory}' is not a valid directory.")

    matching_files = []
    for filename in os.listdir(directory):
        # Check if the file ends with "_data.json"
        if filename.endswith("_data.json"):
            full_path = os.path.join(directory, filename)
            matching_files.append(full_path)

    return matching_files