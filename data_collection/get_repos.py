import requests
from config.constant import *
from typing import List, Dict
import random
from util.log import *
from util.requests_timer import *
from util.util import *

logger = configure_logger('github-data_logger', 'logging_file.log')


def search_repositories_custom(query_string: str, start_page: int = 1) -> List[Dict]:
    """
    Executes a GitHub repository search for the given query_string (which already
    includes all necessary qualifiers like 'fork:false', 'size:>0', star ranges, etc.).

    Returns all results (up to GitHub's 1,000 max) and writes partial data to file.
    """
    url = 'https://api.github.com/search/repositories'

    page = start_page
    results: List[Dict] = []
    total_count = None
    consecutive_empty_pages = 0
    MAX_EMPTY_PAGES = 5

    while True:
        params = {
            "q": query_string,
            "page": page,
            "per_page": GitHub_CONFIG['per_page'],
            "sort": "stars",
            "order": "desc"
        }
        headers = {
            "Authorization": f"Bearer {random.choice(GitHub_CONFIG['token'])}",
            "Accept": "application/vnd.github+json"
        }

        max_tries = GitHub_CONFIG['max_retries']
        attempts = 0
        response = None

        # Retry loop
        while attempts < max_tries:
            try:
                response = requests.get(url, headers=headers, params=params, timeout=30)
                break
            except requests.exceptions.ConnectionError as ce:
                attempts += 1
                logger.error(f"Connection error (page {page}, attempt {attempts}/{max_tries}): {ce}")
                if attempts < max_tries:
                    logger.info("Retrying in 10 seconds...")
                    time.sleep(10)
            except requests.exceptions.Timeout as te:
                attempts += 1
                logger.error(f"Timeout error (page {page}, attempt {attempts}/{max_tries}): {te}")
                if attempts < max_tries:
                    logger.info("Retrying in 10 seconds...")
                    time.sleep(10)

        if not response:
            logger.warning(f"Skipping page {page} due to repeated connection issues.")
            page += 1
            continue

        if response.status_code == 200:
            data = response.json()

            if total_count is None:
                total_count = data.get('total_count', 0)
                logger.info(f"Query='{query_string}' => total_count={total_count}")

            items = data.get("items", [])
            if items:
                consecutive_empty_pages = 0
                results.extend(items)
                logger.info(f"Saving Page {page}: {len(items)} items")
                append_repos_to_file(query_string, items)  # Or pass a topic-based filename
                save_progress(query_string, page)

                # If we have retrieved all possible items (or up to total_count), break
                if len(results) >= total_count:
                    logger.info("All matching repositories have been fetched for this sub-query.")
                    break
                # -- Check the 1,000 limit --
                if len(results) >= 1000:
                    logger.info(
                        "Reached GitHub's 1,000 result limit for this query. "
                        "Stopping and moving to next subrange (if any)."
                    )
                    break
            else:
                consecutive_empty_pages += 1
                logger.info(f"No items on page {page}. (consecutive_empty_pages={consecutive_empty_pages})")
                if consecutive_empty_pages >= MAX_EMPTY_PAGES:
                    logger.info("Reached max consecutive empty pages. Breaking.")
                    break
        else:
            # Non-200 response: Could be 422 (limit reached), 403 (rate limit), etc.
            logger.warning(f"HTTP {response.status_code}: {response.text}")
            # Usually means no more data or we've exceeded 1000 if "message": "Only the first 1000 search results..."
            break

        delay_next_request()
        page += 1

    return results

def generate_star_ranges() -> List[str]:
    """
    Returns a list of star range strings, e.g., "3..50", "51..100", "101..500", etc.,
    plus a final range for 'stars:>10000' or similar.
    Adjust these ranges to fit your dataset.
    """
    ranges = []
    # Example breakpoints:3, 50, 100, 500, 1000, 5000, 10000
    split_points = [3, 50, 100, 500, 1000, 5000, 10000]
    # split_points = [3, 50]
    # Start from the first
    for i in range(len(split_points) - 1):
        low = split_points[i]
        high = split_points[i+1]
        # e.g. "3..50", "51..100", etc.
        ranges.append(f"{low}..{high}")
    # Add final range for > last split
    ranges.append(f">{split_points[-1]}")
    return ranges


def get_total_count_for_query(query: str) -> int:
    """
    Make a single request with per_page=1 just to retrieve 'total_count'.
    """
    url = 'https://api.github.com/search/repositories'
    headers = {
        "Authorization": f"Bearer {random.choice(GitHub_CONFIG['token'])}",
        "Accept": "application/vnd.github+json"
    }
    params = {
        "q": query,
        "per_page": 1,
        "page": 1
    }
    response = requests.get(url, headers=headers, params=params, timeout=30)
    if response.status_code == 200:
        data = response.json()
        return data.get('total_count', 0)
    else:
        logger.warning(
            f"Failed to retrieve total_count. HTTP {response.status_code}: {response.text}"
        )
        return 0


def search_repositories(topic: str) -> List[Dict]:
    """
    1) Build a base query for the topic.
    2) Make a single request with per_page=1 to get total_count.
    3) If total_count <= 1000, fetch them all with one call.
    4) Otherwise, break down the query by star ranges and fetch each subrange.
    """

    # 1) Base query
    base_query = (
        f"{topic} in:name,description,readme "
        f"topic:{topic} fork:false size:>0 forks:>2 stars:>2"
    )

    # 2) Get total_count for the base query
    total_count = get_total_count_for_query(base_query)
    logger.info(f"Total count for '{topic}': {total_count}")

    # 3) If <= 1000, do a single pass
    if total_count <= 1000:
        logger.info(f"Fetching all {total_count} items in one pass.")
        results = search_repositories_custom(base_query, start_page=1)
        return results

    # 4) Otherwise, break down by star range
    logger.info(f"total_count > 1000. Splitting by star range...")
    aggregated: List[Dict] = []
    for star_range in generate_star_ranges():
        sub_query = (
            f"{topic} in:name,description,readme "
            f"topic:{topic} fork:false size:>0 forks:>2 stars:{star_range}"
        )
        segment_results = search_repositories_custom(sub_query, start_page=1)
        aggregated.extend(segment_results)

    logger.info(f"Done collecting star-split results for topic '{topic}'. Total collected: {len(aggregated)}")
    # Optionally deduplicate aggregated here
    return aggregated

def collect_repo() -> None:
    """
    Iterates over each synonym, collects data,
    and saves for each topic. Splits queries by star range if needed.
    """
    for conf in REPO_CONFIG['synonyms']:
        logger.info(f"Starting collection for topic: {conf}")

        # We no longer need partial progress logic here if each sub-query
        # has its own internal progress, but you could still do it if desired.
        # For simplicity, we'll assume that each time we run this, we start fresh
        # or rely on the internal "save_progress(...)" for partial restarts.

        results = search_repositories(conf)
        logger.info(f"Collected {len(results)} total repos for topic: {conf}")

        # Possibly do more processing or extra saving if desired
        delay_next_request()
