import os
import configparser

def write_to_output(org, repo, files):
    with open(os.path.join(repos_directory, f"{org}_{repo}.txt"), "w") as f:
        for file in files:
            f.write(f"{file}\n")

def read_config(config_file='config.ini'):
    # Read configuration from an INI file.
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
    # Determine if the file is relevant based on its extension or other properties.
    
    # Check if the file is in an irrelevant folder
    for folder in irrelevant_folders:
        if folder in filepath.split(os.path.sep):
            return False
        
    # Check if the file's name
    if os.path.basename(filepath) in irrelevant_filenames:
        return False

    # Check the file's extension
    _, ext = os.path.splitext(filepath)
    if ext in irrelevant_extensions:
        return False

    # Otherwise, it's relevant
    return True

def list_relevant_files(directory, irrelevant_extensions, irrelevant_filenames, irrelevant_folders):
    # Traverse the directory and list relevant files.
    relevant_files = []

    for root, _, files in os.walk(directory):
        for file in files:
            filepath = os.path.join(root, file)
            if is_relevant_file(filepath, irrelevant_extensions, irrelevant_filenames, irrelevant_folders):
                relevant_files.append(filepath)

    return relevant_files

if __name__ == "__main__":
    # Read configurations from the config file
    config = read_config()
    repo_directory = config["repo_directory"]
    output_directory = config["output_directory"]

    # Ensure output directories exist
    surql_directory = os.path.join(output_directory, "surql")
    repos_directory = os.path.join(output_directory, "repos")

    # make the directories
    os.makedirs(surql_directory, exist_ok=True)
    os.makedirs(repos_directory, exist_ok=True)

    # Iterate through organizations and repositories based on directory structure
    for org in os.listdir(repo_directory):
        org_path = os.path.join(repo_directory, org)
        
        if os.path.isdir(org_path):
            for repo_name in os.listdir(org_path):
                repo_path = os.path.join(org_path, repo_name)
                git_path = os.path.join(repo_path, ".git")

                if os.path.isdir(repo_path) and os.path.exists(git_path):
                    files = list_relevant_files(repo_path, config["irrelevant_extensions"], config["irrelevant_filenames"], config["irrelevant_folders"])
                    write_to_output(org, repo_name, files)
