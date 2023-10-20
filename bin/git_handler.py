"""handles all functions related to git and github
"""

from git import Repo
import subprocess
from github import Github
from github import Auth
from github_release import gh_release_create


class GitHandler:
    def __init__(self, repo_directory, github_repo_name, remote_repo_url,
                 branch_name, github_token):
        # github setup
        self.open_github_instance(github_token)
        self.set_github_repo(github_repo_name)
        self.github_token = github_token
        self.github_repo_name = github_repo_name
        # git setup
        self.repo = Repo.init(repo_directory, bare=False)
        self.origin = self.repo.create_remote("origin",
                                              url=remote_repo_url)
        self.origin.fetch()
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
                    "mv",
                    "{}/{}".format(folder, old_name),
                    "{}/{}".format(folder, new_name)]
        subprocess.run(mv_input, stderr=subprocess.STDOUT)

    def push_to_remote(self):
        self.origin.push()

    def add_file(self, file_name):
        self.repo.index.add([file_name])

    def commit_changes(self, commit_message):
        self.repo.index.commit(commit_message)

    def make_branch(self, branch_name):
        new_branch = self.repo.create_head(branch_name)
        self.repo.head.reference = new_branch

    def switch_branch(self, branch_name):
        self.repo.heads[branch_name].checkout()

    def make_pull_request(self, branch_name, base_name, title, body):
        pr = self.github_repo.create_pull(title=title,
                                          body=body,
                                          head=branch_name,
                                          base=base_name)
        return pr["number"]

    def merge_pull_request(self, pr_number):
        pr = self.github_repo.get_pull(pr_number)
        pr.merge()

    def make_release(self, version, comment):
        gh_release_create(self.github_repo_name,
                          "v{}".format(version),
                          publish=True,
                          name="v{}".format(version),
                          body=comment,
                          asset_pattern="dist/*")

    def open_github_instance(self, github_token):
        # auth token
        self.auth = Auth.Token(github_token)
        # github instance
        self.github = Github(auth=self.auth)

    def set_github_repo(self, repo_name):
        repo = self.github.get_repo(repo_name)
        if repo:
            self.github_repo = repo
        else:
            raise Exception("Github repo {} not found"
                            .format(repo_name))

    def exit_github(self):
        self.github.close()
