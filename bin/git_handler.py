"""handles all functions related to git and github
"""

from git import Repo
import subprocess


class GitHandler:
    def __init__(self, repo_directory, remote_repo_url, branch_name):
        self.repo = Repo.init(repo_directory, bare=True)
        self.origin = self.repo.create_remote("origin",
                                              remote_repo_url)
        # Setup a local tracking branch of a remote branch
        # create local branch branch_name from remote branch_name
        self.repo.create_head(branch_name, self.origin.refs[branch_name])
        # set local branch_name to track remote branch_name
        (self.repo.heads[branch_name]
         .set_tracking_branch(self.origin.refs[branch_name]))
        # checkout local branch_name to working tree
        self.repo.heads[branch_name].checkout()

    def pull_repo(self):
        # pull remote repo
        self.origin.pull()

    def rename_file(self, folder, old_name, new_name):
        mv_input = ["git",
                    "mv"
                    "{}/{}".format(folder, old_name),
                    "{}/{}".format(folder, new_name)]
        subprocess.run(mv_input, stderr=subprocess.STDOUT)

    def push_to_remote(self):
        self.origin.push()

    def add_file(self, file_name):
        self.repo.index.add([file_name])

    def commit_changes(self, commit_message):
        self.repo.index.commit(commit_message)

    def make_branch(self):
        pass

    def switch_branch(self):
        pass

    def make_pull_request(self, branch_name):
        pass

    def merge_pull_request(self, branch_name, merge_into_branch):
        pass
