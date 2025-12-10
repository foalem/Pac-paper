import os
import shutil

from util.log import configure_logger

logger = configure_logger('github-data_logger', 'logging_file.log')

def extract_and_save_policy_files(
    base_path: str = "C:/Users/fpatr/OneDrive/Documents/Adoption of policies as code in ML based application/clone",
    output_root: str = "./policies"
) -> None:
    """
    Recursively scan cloned repositories in `base_path`, detect policy files associated
    with known Policy-as-Code (PaC) tools, and copy them into a structured folder
    hierarchy: ./policies/{tool_name}/{repo_name}/

    Each policy file is saved in its original form for future inspection or analysis.

    Parameters:
        base_path (str): Root folder where all repositories are cloned.
        output_root (str): Base folder to store extracted policy files by tool.
    """

    def contains_keywords(file_path, keywords):
        """Check if a file contains any of the specified keywords."""
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
                return any(keyword in content for keyword in keywords)
        except Exception:
            return False

    for repo_name in os.listdir(base_path):
        repo_path = os.path.join(base_path, repo_name)
        if not os.path.isdir(repo_path):
            continue

        for root, _, files in os.walk(repo_path):
            for file in files:
                file_path = os.path.join(root, file)
                fname = file.lower()
                file_path = os.path.normpath(file_path)

                # Match for each known PaC tool and copy accordingly
                def save(tool_name):
                    dest_dir = os.path.join(output_root, tool_name, repo_name)
                    os.makedirs(dest_dir, exist_ok=True)
                    dest_file_path = os.path.join(dest_dir, file)
                    dest_file_path = os.path.normpath(dest_file_path)
                    try:
                        shutil.copy2(file_path, dest_file_path)
                    except (FileNotFoundError, OSError) as e:
                        logger.warning(f"[Skipping] Could not copy file: {file_path} -> {dest_file_path}. Reason: {e}")

                if fname.endswith(".sentinel"):
                    save("HashiCorp Sentinel")
                elif fname.endswith(".rego"):
                    save("Open Policy Agent (OPA)")
                elif fname.endswith(".go") and contains_keywords(file_path, ["pulumi-policy"]):
                    save("Pulumi")
                elif fname.endswith(".py") and contains_keywords(file_path, ["pulumi_policy"]):
                    save("Pulumi")
                elif fname.endswith(".java") and contains_keywords(file_path, ["com.pulumi"]):
                    save("Pulumi")
                elif fname.endswith((".js", ".ts")) and contains_keywords(file_path, ["@pulumi"]):
                    save("Pulumi")
                elif fname.endswith(".cedar") or fname.endswith(".cedar.json") or fname.endswith(".cedarschema.json"):
                    save("Cedar Policy Language (CPL)")
                elif fname.endswith((".yaml", ".yml")) and contains_keywords(file_path, ["ClusterPolicy"]):
                    save("Kyverno OSS")
                elif fname.endswith((".yaml", ".yml")) and contains_keywords(file_path, ["custodian"]):
                    save("Cloud Custodian")
                elif fname.endswith(".guard"):
                    save("AWS Config")
                elif fname.endswith(".json") and contains_keywords(file_path, ["PolicyText", "PolicyRuntime"]):
                    save("AWS Config")
                elif fname.endswith((".yaml", ".yml")) and contains_keywords(file_path, ["ConstraintTemplate"]):
                    save("OpagateKeeper")
                elif fname.endswith((".yaml", ".yml")) and contains_keywords(file_path, ["PolicyServer"]):
                    save("Kubewarden")
                elif fname.endswith((".yaml", ".yml")) and contains_keywords(file_path, ["ClusterAdmissionPolicy"]):
                    save("Kubewarden")
