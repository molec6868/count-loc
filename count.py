"""Count the lines of code in all repos"""
import json
import os
from pathlib import Path
import shutil
from git import Repo
from ghapi.all import GhApi
from ghapi.all import paged

def main():
    """Main method"""
    # connect to GitHub
    github_key = Path('github.key').read_text(encoding="utf-8")
    gh = GhApi(token=github_key)
    # test the connection
    gh.orgs.get("ucl-isd")

    count_by_repo = {}
    count_by_extension = {}
    total_count = 0

    # get all repos by page
    pages = paged(gh.repos.list_for_org, org='ucl-isd')

    i = 0
    # loop over all pages
    for page in pages:
        # loop over all repos on the page
        for repo in page:
            i = i + 1
            print(f"Processing {i} {repo.name}")

            # clone the repo
            clone_url = repo.clone_url.replace("https://github.com",
                                               f"https://{github_key}@github.com")
            Repo.clone_from(clone_url, repo.name)

            excluded_extensions = []

            # loop over all files in the repo
            repo_lines_of_code = 0
            for walk_tuple in os.walk(repo.name):
                root = walk_tuple[0]
                filenames = walk_tuple[2]
                for filename in filenames:
                    file_path = os.path.join(root, filename)
                    file_extension = Path(file_path).suffix
                    if file_extension in excluded_extensions or os.path.islink(file_path):
                        file_count = 0
                    else:
                        try:
                            with open(file_path, 'r', encoding="utf-8") as fp:
                                file_count = sum(1 for line in fp)
                        except UnicodeDecodeError:
                            file_count = 0
                    if file_count > 0:
                        if file_count > 1000:
                            print(f"{file_path} {file_count}")

                        repo_lines_of_code = repo_lines_of_code + file_count

                        if file_extension in count_by_extension:
                            count_by_extension[file_extension] =\
                                count_by_extension[file_extension] + file_count
                        else:
                            count_by_extension[file_extension] = file_count

            count_by_repo[repo.name] = repo_lines_of_code
            total_count = total_count + repo_lines_of_code

            # delete the clone
            shutil.rmtree(repo.name)

        # Write the results to file
        count_by_repo["total"] = total_count
        sorted_count_by_repo = dict(sorted(count_by_repo.items(), key=lambda x: x[1], reverse=True))
        with open("results_by_repo.csv", "w", encoding="utf-8") as fp:
            for key, value in sorted_count_by_repo.items():
                fp.write(f"{key},{value}\n")
        sorted_count_by_extension = dict(sorted(count_by_extension.items(),
                                                key=lambda x: x[1], reverse=True))
        with open("results_by_extension.csv", "w", encoding="utf-8") as fp:
            for key, value in sorted_count_by_extension.items():
                fp.write(f"{key},{value}\n")


main()
