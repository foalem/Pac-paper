import os
import csv
from collections import defaultdict

def contains_keywords(file_path, keywords):
    """
    Check if the file at file_path contains any of the specified keywords.

    Parameters:
    - file_path (str): Path to the file to inspect.
    - keywords (list): List of keywords to search for in the file content.

    Returns:
    - bool: True if any keyword is found, False otherwise or if the file cannot be read.
    """
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
            return any(keyword in content for keyword in keywords)
    except Exception:
        return False

def scan_repositories_updated(base_path="C:/Users/fpatr/OneDrive/Documents/Adoption of policies as code in ML based application/clone", output_csv="./pac_usage_summary_updated_with_Kubewarden.csv"):
    """
       Recursively scans repositories in the given base directory for Policy-as-Code (PaC) usage.

       This function identifies the presence of various PaC tools based on specific file extensions
       or keyword patterns inside code/config files. It counts how many files related to each tool
       are found per repository and writes the summary to a CSV file.

       Parameters:
       - base_path (str): Path to the directory containing cloned repositories.
       - output_csv (str): Path to the CSV file to save summary results.

       Returns:
       - str: Path to the CSV file containing the summary of detected PaC tools.

       Explanation of:
       - **tool_file_counts: This unpacks the defaultdict of file counts (e.g., {'Pulumi': 3, 'OPA': 2})
         into the result dictionary, merging those key-value pairs into the main row for CSV output.
       """
    results = []

    for repo_name in os.listdir(base_path):
        repo_path = os.path.join(base_path, repo_name)
        if not os.path.isdir(repo_path):
            continue
        # A dictionary to count occurrences of files matching PaC patterns for each tool
        tool_file_counts = defaultdict(int)
        # Walk through all files in the repository
        for root, _, files in os.walk(repo_path):
            for file in files:
                file_path = os.path.join(root, file)
                fname = file.lower()
                # Identify tool usage based on filename extensions or keyword patterns
                # HashiCorp Sentinel
                if fname.endswith(".sentinel"):
                    tool_file_counts["HashiCorp Sentinel"] += 1

                # Open Policy Agent (OPA)
                elif fname.endswith(".rego"):
                    tool_file_counts["Open Policy Agent (OPA)"] += 1

                # Pulumi patterns
                elif fname.endswith(".go") and contains_keywords(file_path, ["pulumi-policy"]):
                    tool_file_counts["Pulumi"] += 1
                elif fname.endswith(".py") and contains_keywords(file_path, ["pulumi_policy"]):
                    tool_file_counts["Pulumi"] += 1
                elif fname.endswith(".java") and contains_keywords(file_path, ["com.pulumi"]):
                    tool_file_counts["Pulumi"] += 1
                elif fname.endswith(".js") and contains_keywords(file_path, ["@pulumi"]):
                    tool_file_counts["Pulumi"] += 1
                elif fname.endswith(".ts") and contains_keywords(file_path, ["@pulumi"]):
                    tool_file_counts["Pulumi"] += 1

                # Cedar Policy Language (CPL)
                elif fname.endswith(".cedar") or fname.endswith(".cedar.json") or fname.endswith(".cedarschema.json"):
                    tool_file_counts["Cedar Policy Language (CPL)"] += 1

                # Kyverno OSS
                elif fname.endswith((".yaml", ".yml")) and contains_keywords(file_path, ["ClusterPolicy"]):
                    tool_file_counts["Kyverno OSS"] += 1

                # Cloud Custodian
                elif fname.endswith((".yaml", ".yml")) and contains_keywords(file_path, ["custodian"]):
                    tool_file_counts["Cloud Custodian"] += 1

                # AWS Config
                elif fname.endswith(".guard"):
                    tool_file_counts["AWS Config"] += 1
                elif fname.endswith(".json") and contains_keywords(file_path, ["PolicyText", "PolicyRuntime"]):
                    tool_file_counts["AWS Config"] += 1

                # OpagateKeeper
                elif fname.endswith((".yaml", ".yml")) and contains_keywords(file_path, ["ConstraintTemplate"]):
                    tool_file_counts["OpagateKeeper"] += 1

                # Kubewarden
                elif fname.endswith(".yaml") and contains_keywords(file_path, ["PolicyServer", "ClusterAdmissionPolicy"]):
                    tool_file_counts["Kubewarden"] += 1
        # Store results for the current repository
        results.append({
            "full_name": repo_name,
            **tool_file_counts  # Unpacks all tool counts into the dictionary
        })

    # Gather all tools for column ordering
    # Define columns for the CSV (fixed order)
    all_tools = [
        "HashiCorp Sentinel", "Open Policy Agent (OPA)", "Pulumi",
        "Cedar Policy Language (CPL)", "Kyverno OSS", "Cloud Custodian",
        "AWS Config", "OpagateKeeper", "Kubewarden"
    ]
    # Write the results to a CSV file
    with open(output_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["full_name"] + all_tools)
        writer.writeheader()
        for row in results:
            # Ensure every tool has a value (0 if missing)
            for tool in all_tools:
                row.setdefault(tool, 0)
            writer.writerow(row)

    return output_csv

