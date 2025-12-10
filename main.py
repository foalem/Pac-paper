import argparse
import os

from data_collection.clone_repo import clone_repos_from_csv
from data_collection.get_iac_repos import *
from data_collection.get_pac_repo import *
from data_collection.get_repo_metrics import *
from data_collection.get_repos import *
from data_collection.get_repos_cloud import process_repositories
from data_collection.get_repos_cloud import *
from data_collection.get_pac_usage import *
from data_collection.get_pac_readme import *
from data_collection.get_pac_policy import *

logger = configure_logger('github-data_logger', 'logging_file.log')

progress_file = "progress/enrich_repos_4.json"

def main() -> None:
    parser = argparse.ArgumentParser(description='Fetch GitHub repositories for a given topic.')
    parser.add_argument('-c', '--collect', help='Collect repositories for a given topic.', dest='DATA', action='store_true')
    parser.add_argument('-m', '--metric', help='Collect repositories metrics', dest='METRICS', action='store_true')
    parser.add_argument('-i', '--iac', help='Output CSV file for collected repositories with IaC information.', dest='IAC', action='store_true')
    parser.add_argument('-cd', '--cloud', help='Output CSV file for collected repositories with cloud information.', dest='CLOUD', action='store_true')
    parser.add_argument('-p', '--pac', help='Output CSV file for collected repositories with PaC information.', dest='PAC', action='store_true')
    parser.add_argument('-a', '--all', help='Clone all repos.', dest='ALL', action='store_true')
    parser.add_argument('-u', '--usage', help='Collecting PaC usage.', dest='USAGE', action='store_true')
    parser.add_argument('-r', '--readme', help='Collecting README files.', dest='README', action='store_true')
    parser.add_argument('-o', '--output', help='Collecting polycies from repositories.', dest='OUTPUT', action='store_true')
    args = parser.parse_args()

    if args.DATA:
        collect_repo()
    if args.METRICS:
        # compile_repo_data_to_csv(PATH_FILE['data'], PATH_FILE['output'])
        # enrich_repos_incrementally("pac_repos_Kubewarden.csv", "pac_repos_Kubewarden_enriched.csv", progress_file)
        # enrich_with_contributor_count("pac_repos_Kubewarden.csv", "pac_repos_Kubewarden_enriched_contributor.csv", progress_file)
        get_commit_dates_from_csv("./data_analysis/Dataset_PaC_Used.xlsx", "commit_dates.csv")
    if args.IAC:
        enrich_csv_with_iac_tools_code_search(PATH_FILE['output'], PATH_FILE['output_iac'])
    if args.CLOUD:
        process_repositories(PATH_FILE['gcp'], REPO_CONFIG['synonyms'], PATH_FILE['cloud'])
    if args.PAC:
        # enrich_csv_with_pac(PATH_FILE['output_iac'], PATH_FILE['output_iac'])
        search_pac_repos_by_extension("PolicyServer in:file extension:yaml")
        search_pac_repos_by_extension("ClusterAdmissionPolicy in:file extension:yaml")
        # search_pac_repos_by_extension('"com.pulumi" in:file+extension:java"')
        # search_pac_repos_by_extension("ClusterPolicy in:file extension:yaml")
        # merge_pac_repo_outputs(
        #     rego_file="pac_repos_PolicyText_AWS_Config.csv",
        #     sentinel_file="pac_repos_PolicyRuntime_AWS_Config.csv",
        #     output_file="merged_pac_repos_AWS_Config.csv"
        # )
    if args.ALL:
        # clone_repos_from_csv("PaC_Repos_final_Dataset.csv")
        clone_repos_from_csv("RQ2_Final_label.csv")
    if args.USAGE:
        scan_repositories_updated()
    if args.README:
        save_readmes_as_raw_files()
    if args.OUTPUT:
        extract_and_save_policy_files()
# def print_hi(name):
#     # Use a breakpoint in the code line below to debug your script.
#     print(f'Hi, {name}')  # Press Ctrl+F8 to toggle the breakpoint.


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    # print_hi('PyCharm')
    main()
# See PyCharm help at https://www.jetbrains.com/help/pycharm/
