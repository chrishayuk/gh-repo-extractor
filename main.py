import os
import configparser
import hashlib

def write_to_output(org, repo, files):
    with open(os.path.join(repos_directory, f"{org}_{repo}.txt"), "w") as f:
        for file in files:
            f.write(f"{file}\n")

def read_config(config_file='config.ini'):
    config = configparser.ConfigParser()
    config.read(config_file)
    return {
        "repo_directory": config.get("DEFAULT", "repo_directory", fallback="./cloned_repos"),
        "output_directory": config.get("DEFAULT", "output_directory", fallback="./output"),
        "irrelevant_extensions": config.get("FileFilters", "irrelevant_extensions").split(", "),
        "irrelevant_filenames": config.get("FileFilters", "irrelevant_filenames").split(", "),
        "irrelevant_folders": config.get("FileFilters", "irrelevant_folders").split(", ")
    }

def is_relevant_file(filepath, irrelevant_extensions, irrelevant_filenames, irrelevant_folders):
    for folder in irrelevant_folders:
        if folder in filepath.split(os.path.sep):
            return False
    if os.path.basename(filepath) in irrelevant_filenames:
        return False
    _, ext = os.path.splitext(filepath)
    if ext in irrelevant_extensions:
        return False
    return True

def list_relevant_files(directory, irrelevant_extensions, irrelevant_filenames, irrelevant_folders):
    relevant_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            filepath = os.path.join(root, file)
            if is_relevant_file(filepath, irrelevant_extensions, irrelevant_filenames, irrelevant_folders):
                relevant_files.append(filepath)
    return relevant_files

def compute_sha256(file_path):
    """Compute the SHA256 hash of a file."""
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for block in iter(lambda: f.read(65536), b""):
            sha256.update(block)
    return sha256.hexdigest()

def generate_surql_for_file(repo_key, filepath, repo_path):
    relative_path = os.path.relpath(filepath, repo_path)
    _, ext = os.path.splitext(filepath)
    filename = os.path.basename(filepath)
    file_hash = compute_sha256(filepath)
    
    query = f"""
CREATE repo_file:{file_hash} SET
    repo = {repo_key},
    path = '{relative_path}',
    extension = '{ext}',
    filename = '{filename}',
    hash = '{file_hash}',
    ingested_at = time::now()
;
"""
    return query

def write_files_to_surql_script(repo_key, files, repo_path, org, repo_name):
    surql_script_file = os.path.join(surql_directory, f"{org}_{repo_name}.surql")
    with open(surql_script_file, "w") as f:
        for file in files:
            query = generate_surql_for_file(repo_key, file, repo_path)
            f.write(query + "\n\n")

if __name__ == "__main__":
    config = read_config()
    repo_directory = config["repo_directory"]
    output_directory = config["output_directory"]

    surql_directory = os.path.join(output_directory, "surql")
    repos_directory = os.path.join(output_directory, "repos")

    os.makedirs(surql_directory, exist_ok=True)
    os.makedirs(repos_directory, exist_ok=True)

    for org in os.listdir(repo_directory):
        org_path = os.path.join(repo_directory, org)

        if os.path.isdir(org_path):
            for repo_name in os.listdir(org_path):
                repo_path = os.path.join(org_path, repo_name)
                git_path = os.path.join(repo_path, ".git")

                if os.path.isdir(repo_path) and os.path.exists(git_path):
                    files = list_relevant_files(repo_path, config["irrelevant_extensions"], config["irrelevant_filenames"], config["irrelevant_folders"])
                    repo_key = f"provider:'github', org:'{org}', repo:'{repo_name}'"
                    
                    # Write relevant files to the original output file
                    write_to_output(org, repo_name, files)

                    # Write SURQL commands to a separate script file for each repo
                    write_files_to_surql_script(repo_key, files, repo_path, org, repo_name)
