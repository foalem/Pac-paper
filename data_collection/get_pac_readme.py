import os
import pandas as pd
import re

import os

def save_readmes_as_raw_files(
    base_path: str = "C:/Users/fpatr/OneDrive/Documents/Adoption of policies as code in ML based application/clone",
    output_dir: str = "./output/readmes_raw"
) -> None:
    """
    Walks through each cloned repository in `base_path`,
    extracts the README file content (if found),
    and saves it as a raw .txt file in `output_dir` using the repo name.

    Parameters:
        base_path (str): Path where repositories are cloned.
        output_dir (str): Directory to save README files as text.
    """
    os.makedirs(output_dir, exist_ok=True)

    for repo_name in os.listdir(base_path):
        repo_path = os.path.join(base_path, repo_name)
        if not os.path.isdir(repo_path):
            continue

        readme_found = False
        for file in os.listdir(repo_path):
            if file.lower().startswith("readme"):
                file_path = os.path.join(repo_path, file)
                try:
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()

                    output_file = os.path.join(output_dir, f"{repo_name}.txt")
                    with open(output_file, "w", encoding="utf-8") as out_f:
                        out_f.write(content)
                    readme_found = True
                    break
                except Exception as e:
                    print(f"[Error reading README in {repo_name}]: {e}")
                    break

        if not readme_found:
            print(f"[No README found for]: {repo_name}")

    print(f"✅ README extraction complete. Files saved in: {output_dir}")


def clean_excel_string(s: str) -> str:
    """
    Remove characters not allowed in Excel XML (invalid control chars).
    """
    # Remove control characters except \n, \r, \t
    return re.sub(r"[\x00-\x08\x0B-\x0C\x0E-\x1F]", "", s)

def extract_readmes_to_excel(
    base_path: str = "C:/Users/fpatr/OneDrive/Documents/Adoption of policies as code in ML based application/clone",
    output_excel: str = "./repo_readmes_cleaned.xlsx"
):
    """
    Walks through each cloned repository in the base_path directory,
    extracts README file content (if found), cleans it, and saves to Excel.

    Parameters:
        base_path (str): Path where repositories are cloned.
        output_excel (str): Output Excel file path to save the extracted content.

    Returns:
        str: Path to the saved Excel file.
    """
    results = []

    for repo_name in os.listdir(base_path):
        repo_path = os.path.join(base_path, repo_name)
        if not os.path.isdir(repo_path):
            continue

        readme_content = ""
        for file in os.listdir(repo_path):
            if file.lower().startswith("readme"):
                file_path = os.path.join(repo_path, file)
                try:
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        raw_content = f.read().strip()
                        readme_content = clean_excel_string(raw_content)
                    break
                except Exception:
                    readme_content = "[Error reading file]"
                    break

        results.append({
            "full_name": repo_name,
            "readme_content": readme_content
        })

    df = pd.DataFrame(results)
    df.to_excel(output_excel, index=False, engine="openpyxl")

    return output_excel
