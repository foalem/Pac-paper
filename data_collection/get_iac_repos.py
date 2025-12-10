import random

import requests
import pandas as pd

from config.constant import GitHub_CONFIG
from util.log import configure_logger
from util.requests_timer import delay_next_request
from util.util import *

logger = configure_logger('github-data_logger', 'logging_file.log')


def search_code_in_repo(owner: str, repo: str, query: str) -> bool:
    """
    Searches code in the specified 'owner/repo' with the given 'query'.
    Returns True if there is at least 1 matching item, False if none or error.

    :param owner: The repository owner's name, e.g. 'hashicorp'
    :param repo: The repository name, e.g. 'terraform'
    :param query: The code search query, e.g. 'filename:Dockerfile'
    """
    url = "https://api.github.com/search/code"
    # We combine the user-supplied query with 'repo:owner/repo'
    # so GitHub looks specifically in that repo.
    # Example final query: "filename:Dockerfile repo:hashicorp/terraform"
    full_query = f"repo:{owner}/{repo} {query}"

    headers = {
        "Authorization": f"Bearer {random.choice(GitHub_CONFIG['token'])}",
        "Accept": "application/vnd.github+json"
    }
    params = {
        "q": full_query,
        "per_page": 1  # We only need to know if at least 1 match exists
    }

    try:
        resp = requests.get(url, headers=headers, params=params)
        if resp.status_code == 200:
            data = resp.json()
            count = data.get('total_count', 0)
            return count > 0
        else:
            logger.error(
                f"Code search error {resp.status_code} for {owner}/{repo}, query='{full_query}': {resp.text}"
            )
            return False
    except requests.exceptions.RequestException as e:
        logger.error(f"Exception during code search: {e}")
        return False

def check_docker_code_search(full_name: str ) -> bool:
    """
    Return True if there's at least one Dockerfile in the repo, or any other pattern you want.
    """
    owner, repo = full_name.split('/')
    # For Docker, the simplest approach is searching for a Dockerfile
    query = "filename:Dockerfile"
    return search_code_in_repo(owner, repo, query )

def check_ansible_code_search(full_name: str ) -> bool:
    """
    Return True if there's Ansible content in the repo,
    for example by searching for:
      - 'ansible.cfg'
      - 'ansible' in .yml
      - 'hosts:' in .yml or .yaml
      - path:ansible (common roles/playbooks folder)
    """
    owner, repo = full_name.split('/')

    # We combine multiple conditions with OR:
    #  1) filename:ansible.cfg
    #  2) path:ansible
    #  3) ansible in:file extension:yml
    #  4) "hosts:" in:file extension:yml
    #  5) "hosts:" in:file extension:yaml
    #
    # A final search query might look like:
    #   filename:ansible.cfg OR path:ansible OR ansible in:file extension:yml
    #   OR "hosts:" in:file extension:yml OR "hosts:" in:file extension:yaml
    query = (
        "filename:ansible.cfg "
        "OR ansible in:path"
        # "OR ansible in:file extension:yml"
        # "OR hosts in:file extension:yml "
        # "OR hosts in:file extension:yaml"
    )

    return search_code_in_repo(owner, repo, query )

def check_terraform_code_search(full_name: str ) -> bool:
    """
    Return True if the repo contains .tf files (Terraform).
    """
    owner, repo = full_name.split('/')
    # e.g., searching for files with extension:.tf
    query = "extension:tf"
    return search_code_in_repo(owner, repo, query )

def check_vagrant_code_search(full_name: str ) -> bool:
    """
    Return True if there's Vagrant usage in the repo, for instance by:
      - searching for 'Vagrantfile'
      - path:vagrant
    """
    owner, repo = full_name.split('/')
    query = (
        "filename:Vagrantfile "
        "OR vagrant in:path"
    )
    return search_code_in_repo(owner, repo, query )


def check_kubernetes_code_search(full_name: str ) -> bool:
    """
    Return True if there's Kubernetes usage in the repo, e.g. by:
      - 'k8s' or 'kubernetes' in YAML files
      - 'filename:deployment.yaml' (common K8s deployment file)
      - path:k8s
    """
    owner, repo = full_name.split('/')
    query = (
        "deployment OR kubernetes in:file extension:yaml"
        # "OR kind in:file extension:yaml "
        # "OR kubernetes in:file extension:yml "
        # "OR kubernetes in:file extension:yaml"
        # "OR k8s in:file extension:yml "
        # "OR k8s in:file extension:yaml "
        # "OR k8s in:path"
    )
    return search_code_in_repo(owner, repo, query )


def check_chef_code_search(full_name: str ) -> bool:
    """
    Return True if there's Chef usage in the repo, commonly indicated by:
      - 'chef' in Ruby files
      - 'filename:metadata.rb' (Chef Cookbook metadata)
      - path:cookbooks (common Chef folder)
    """
    owner, repo = full_name.split('/')
    query = (
        # "filename:metadata.rb "
        "filename:Policyfile.rb "
        "OR cookbooks in:path"
        # "OR chef in:file extension:rb"
    )
    return search_code_in_repo(owner, repo, query )


def check_puppet_code_search(full_name: str ) -> bool:
    """
    Return True if there's Puppet usage in the repo, e.g.:
      - .pp files (Puppet manifests)
      - path:manifests
    """
    owner, repo = full_name.split('/')
    query = (
        "extension:pp "
        "OR manifests in:path"
    )
    return search_code_in_repo(owner, repo, query )

def check_apache_brooklyn_code_search(full_name: str ) -> bool:
    """
    Return True if there's Apache Brooklyn usage in the repo, for instance by:
      - references to 'apache-brooklyn' in code
      - 'filename:blueprint.yaml' or 'filename:blueprints.yaml' (common Brooklyn blueprint file)
    """
    owner, repo = full_name.split('/')
    query = (
        "apache-brooklyn in:file "
        # "OR filename:blueprint.yaml "
        "OR filename:blueprints.yaml"
    )
    return search_code_in_repo(owner, repo, query )

def check_packer_code_search(full_name: str ) -> bool:
    """
    Return True if there's HashiCorp Packer usage in the repo, for example:
      - 'filename:packer.json'
      - files with extension '.pkr.hcl' (common in newer Packer templates)
      - 'packer' in .hcl or .json
    """
    owner, repo = full_name.split('/')
    query = (
        "filename:packer.json "
        "OR extension:.pkr.hcl"
        # "OR packer in:file extension:json"
    )
    return search_code_in_repo(owner, repo, query )

def check_cloudformation_code_search(full_name: str ) -> bool:
    """
    Return True if there's AWS CloudFormation usage, for instance:
      - 'filename:template.yaml' or 'filename:template.yml'
      - 'filename:template.json'
      - path:cloudformation
      - 'AWSTemplateFormatVersion' is a typical marker in CloudFormation templates
    """
    owner, repo = full_name.split('/')
    query = (
        # "cloudformation in:path "
        "AWSTemplateFormatVersion in:file extension:yaml, json"
        # "OR AWSTemplateFormatVersion in:file extension:yaml"
    )
    return search_code_in_repo(owner, repo, query )

def check_tosca_code_search(full_name: str ) -> bool:
    """
    Return True if there's TOSCA usage, for example:
      - 'tosca_definitions_version' in .yaml
      - extension:csar (TOSCA Cloud Service Archive) if unzipped
      - 'filename:service-template.yaml'
    """
    owner, repo = full_name.split('/')
    query = (
        "tosca_definitions_version in:file extension:yaml "
        "OR filename:service-template.yaml"
        # "OR extension:csar"
    )
    return search_code_in_repo(owner, repo, query )

def check_salt_code_search(full_name: str ) -> bool:
    """
    Return True if there's SaltStack usage in the repo, e.g.:
      - '.sls' files
      - references to salt in .conf or .py files
      - path:states (common salt states folder)
    """
    owner, repo = full_name.split('/')
    query = (
        "extension:sls "
        "OR salt in:file extension:conf"
        # "OR salt in:file extension:py "
        # "OR states in:path"
    )
    return search_code_in_repo(owner, repo, query )

# def check_shell_scripts_code_search(full_name: str ) -> bool:
#     """
#     Return True if there's Shell scripts usage in the repo, e.g.:
#       - extension:sh
#       - #!/bin/bash or #!/bin/sh
#     WARNING: This can produce many false positives because shell scripts are very common.
#     """
#     owner, repo = full_name.split('/')
#     # Searching for files with extension:sh or #!/bin/bash in any file
#     query = (
#         "extension:sh "
#         "OR \"#!/bin/bash\" in:file "
#         "OR \"#!/bin/sh\" in:file"
#     )
#     return search_code_in_repo(owner, repo, query )

def check_cloudify_code_search(full_name: str ) -> bool:
    """
    Return True if there's Cloudify usage in the repo:
      - 'cloudify' references in .yaml
      - 'filename:blueprint.yaml' sometimes used by Cloudify
      - path:blueprints
    """
    owner, repo = full_name.split('/')
    query = (
        "cloudify in:file extension:yaml "
        # "OR cloudify in:file extension:yml"
        "OR filename:blueprint.yaml"
        # "OR blueprints in:path"
    )
    return search_code_in_repo(owner, repo, query )

def check_octopus_deploy_code_search(full_name: str ) -> bool:
    """
    Return True if there's Octopus Deploy usage, for instance:
      - 'octopus' references in code or config
      - 'filename:octopus.config'
    """
    owner, repo = full_name.split('/')
    query = (
        "octopus in:file "
        "OR filename:octopus.config"
    )
    return search_code_in_repo(owner, repo, query )

def check_azure_devops_code_search(full_name: str ) -> bool:
    """
    Return True if there's Azure DevOps usage in the repo, for example:
      - 'filename:azure-pipelines.yml' (classic Azure Pipelines config)
      - 'azure devops' references in code
      - path:.azure
    """
    owner, repo = full_name.split('/')
    query = (
        "filename:azure-pipelines.yml "
        "OR filename:azure-pipelines.yaml"
        # "OR azure devops in:file "
        # "OR azure in:path"
    )
    return search_code_in_repo(owner, repo, query )


# def enrich_csv_with_iac_tools_code_search(
#         input_csv: str, output_csv: str
# ) -> None:
#     """
#     Reads the CSV containing repo info, for each row calls one or more IaC tool checks,
#     adds columns (one per tool) with True/False, then saves the enriched CSV.
#
#     :param input_csv: Path to the CSV with repos
#     :param output_csv: Where to save the updated CSV
#     """
#     df = pd.read_csv(input_csv)
#
#     # Ensure 'full_name' column is valid (it should look like "owner/repo")
#     df['full_name'] = df['full_name'].fillna("").astype(str)
#
#     # Create new columns
#     docker_col = []
#     ansible_col = []
#     terraform_col = []
#     vagrant_col = []
#     kubernetes_col = []
#     chef_col = []
#     puppet_col = []
#     apache_brooklyn_col = []
#     packer_col = []
#     cloudformation_col = []
#     tosca_col = []
#     salt_col = []
#     # shell_scripts_col = []
#     cloudify_col = []
#     octopus_deploy_col = []
#     azure_devops_col = []
#     # ... add columns for all the tools you want ...
#
#     for idx, row in df.iterrows():
#         full_name = row['full_name']
#
#         # If the row is missing a valid 'owner/repo' skip
#         if "/" not in full_name:
#             docker_col.append(False)
#             ansible_col.append(False)
#             terraform_col.append(False)
#             vagrant_col.append(False)
#             kubernetes_col.append(False)
#             chef_col.append(False)
#             puppet_col.append(False)
#             apache_brooklyn_col.append(False)
#             packer_col.append(False)
#             cloudformation_col.append(False)
#             tosca_col.append(False)
#             salt_col.append(False)
#             # shell_scripts_col.append(False)
#             cloudify_col.append(False)
#             octopus_deploy_col.append(False)
#             azure_devops_col.append(False)
#             # ...
#             continue
#
#         # Docker check
#         has_docker = check_docker_code_search(full_name )
#         docker_col.append(has_docker)
#         delay_next_request()
#         # Ansible check
#         has_ansible = check_ansible_code_search(full_name )
#         ansible_col.append(has_ansible)
#         delay_next_request()
#         # Terraform check
#         has_terraform = check_terraform_code_search(full_name )
#         terraform_col.append(has_terraform)
#         delay_next_request()
#         # Vagrant check
#         has_vagrant = check_vagrant_code_search(full_name )
#         vagrant_col.append(has_vagrant)
#         delay_next_request()
#         # Kubernetes check
#         has_kubernetes = check_kubernetes_code_search(full_name )
#         kubernetes_col.append(has_kubernetes)
#         delay_next_request()
#         # Chef check
#         has_chef = check_chef_code_search(full_name )
#         chef_col.append(has_chef)
#         delay_next_request()
#         # Puppet check
#         has_puppet = check_puppet_code_search(full_name )
#         puppet_col.append(has_puppet)
#         delay_next_request()
#         # Apache Brooklyn check
#         has_apache_brooklyn = check_apache_brooklyn_code_search(full_name )
#         apache_brooklyn_col.append(has_apache_brooklyn)
#         delay_next_request()
#         # Packer check
#         has_packer = check_packer_code_search(full_name )
#         packer_col.append(has_packer)
#         delay_next_request()
#         # CloudFormation check
#         has_cloudformation = check_cloudformation_code_search(full_name )
#         cloudformation_col.append(has_cloudformation)
#         delay_next_request()
#         # TOSCA check
#         has_tosca = check_tosca_code_search(full_name )
#         tosca_col.append(has_tosca)
#         delay_next_request()
#         # Salt check
#         has_salt = check_salt_code_search(full_name )
#         salt_col.append(has_salt)
#         delay_next_request()
#         # Cloudify check
#         has_cloudify = check_cloudify_code_search(full_name )
#         cloudify_col.append(has_cloudify)
#         delay_next_request()
#         # Octopus Deploy check
#         has_octopus_deploy = check_octopus_deploy_code_search(full_name )
#         octopus_deploy_col.append(has_octopus_deploy)
#         delay_next_request()
#         # Azure DevOps check
#         has_azure_devops = check_azure_devops_code_search(full_name )
#         azure_devops_col.append(has_azure_devops)
#         delay_next_request()
#         logger.info(f"Checked {full_name} for IaC tools")
#         # ... repeat for each tool ...
#
#         # Rate limit courtesy sleep
#         # delay_next_request()
#
#     # Attach columns to DataFrame
#     df['has_docker'] = docker_col
#     df['has_ansible'] = ansible_col
#     df['has_terraform'] = terraform_col
#     df['has_vagrant'] = vagrant_col
#     df['has_kubernetes'] = kubernetes_col
#     df['has_chef'] = chef_col
#     df['has_puppet'] = puppet_col
#     df['has_apache_brooklyn'] = apache_brooklyn_col
#     df['has_packer'] = packer_col
#     df['has_cloudformation'] = cloudformation_col
#     df['has_tosca'] = tosca_col
#     df['has_salt'] = salt_col
#     # df['has_shell_scripts'] = shell_scripts_col
#     df['has_cloudify'] = cloudify_col
#     df['has_octopus_deploy'] = octopus_deploy_col
#     df['has_azure_devops'] = azure_devops_col
#
#     # Save the updated CSV
#     df.to_csv(output_csv, index=False)
#     print(f"Enriched CSV saved to {output_csv}")


def enrich_csv_with_iac_tools_code_search(input_csv: str, output_csv: str) -> None:
    """
    Reads the CSV containing repo info, for each row calls one or more IaC tool checks,
    adds columns (one per tool) with True/False, then saves the enriched CSV.
    If interrupted, resumes from the last completed row.
    """
    idx: int
    df = pd.read_csv(input_csv)

    # Ensure 'full_name' column is valid
    df['full_name'] = df['full_name'].fillna("").astype(str)

    # # If the file already exists, load it to keep processed data
    # if os.path.exists(output_csv):
    #     df_existing = pd.read_csv(output_csv)
    # else:
    #     df_existing = None

    # Get last processed index
    last_processed_index = load_progress_iac()

    # Iterate through repositories
    for idx, row in df.iterrows():
        if idx < last_processed_index:
            continue  # Skip already processed rows

        full_name = row['full_name']
        if "/" not in full_name:
            continue  # Skip invalid entries

        # Perform checks for each IaC tool
        results = {
            "has_docker": check_docker_code_search(full_name),
            # "has_ansible": check_ansible_code_search(full_name),
            "has_terraform": check_terraform_code_search(full_name),
            # "has_vagrant": check_vagrant_code_search(full_name),
            # "has_kubernetes": check_kubernetes_code_search(full_name),
            # "has_chef": check_chef_code_search(full_name),
            # "has_puppet": check_puppet_code_search(full_name),
            # "has_apache_brooklyn": check_apache_brooklyn_code_search(full_name),
            # "has_packer": check_packer_code_search(full_name),
            # "has_cloudformation": check_cloudformation_code_search(full_name),
            # "has_tosca": check_tosca_code_search(full_name),
            # "has_salt": check_salt_code_search(full_name),
            # "has_cloudify": check_cloudify_code_search(full_name),
            # "has_octopus_deploy": check_octopus_deploy_code_search(full_name),
            # "has_azure_devops": check_azure_devops_code_search(full_name),
        }

        # Update the DataFrame row with new values
        for key, value in results.items():
            df.at[idx, key] = value

        # Save progress every row (incremental updates)
        df.iloc[:idx + 1].to_csv(output_csv, index=False)
        save_progress_iac(idx)

        logger.info(f"Processed {idx+1}/{len(df)}: {full_name}")

        # Rate limit courtesy sleep
        delay_next_request()

    print(f"Enriched CSV saved to {output_csv}")