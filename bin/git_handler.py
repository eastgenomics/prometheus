"""handles all functions related to git and github
"""

from git import Repo


class GitHandler:
    def __init__(self, repo_directory):
        self.repo = Repo.init(repo_directory, bare=True)

    def clone_repo(self, url):
        # clone remote repo to manage locally
        pass

    def rename_file(self, old_name, new_name):
        pass

    def push_to_remote(self):
        pass

    def commit_changes(self, commit_message):
        pass
