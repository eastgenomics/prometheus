"""handles all functions related to git and github
"""

from git import Repo
import subprocess
import os
from github import Github
from github import Auth
from github_release import gh_release_create


class GitHandler:
    """Handles all git and github interactions for Prometheus
    """
    def __init__(
        self, repo_directory, github_repo_name, remote_repo_url, branch_name,
        github_token
    ) -> None:
        """sets up git and github

        Args:
        repo_directory (str): path to directory containing local repo
        github_repo_name (str): name of remote repo on github
        remote_repo_url (str): url to remote repo
        branch_name (str): name of branch to select from remote repo
        """
        # github setup
        self.open_github_instance(github_token)
        self.set_github_repo(github_repo_name)
        self.github_token = github_token
        self.github_repo_name = github_repo_name
        # git setup
        self.repo = Repo.init(repo_directory, bare=False)
        try:
            self.origin = self.repo.create_remote(
                "origin", url=remote_repo_url
            )
        except Exception:
            # ignore if origin already exists
            self.origin = self.repo.remotes["origin"]
            pass
        self.origin.fetch()
        # Set up a local tracking branch of a remote branch
        # create local branch branch_name from remote branch_name
        try:
            self.repo.create_head(branch_name, self.origin.refs[branch_name])
        except OSError:
            # ignore if main branch already exists
            pass
        # set local branch_name to track remote branch_name
        (self.repo.heads[branch_name]
            .set_tracking_branch(self.origin.refs[branch_name]))
        # checkout local branch_name to working tree
        self.repo.heads[branch_name].checkout()

    def pull_repo(self) -> None:
        """pulls git repo from remote source
        """
        self.origin.pull()

    def rename_file(self, filepath, old_name, new_name) -> None:
        """renames file in git for active git repo

        Args:
        filepath (str): path to directory containing file to be renamed
        old_name (str): name of file to be renamed
        new_name (str): new name of file
        """
        # TODO: replace subprocess with gitpython API call
        mv_input = ["git", "mv", old_name, new_name]
        os.chdir(filepath)
        subprocess.run(mv_input, stderr=subprocess.STDOUT)
        os.chdir("..")
        os.chdir("..")

    def push_to_remote(self) -> None:
        """pushes staged changes to remote
        """
        self.origin.push()

    def add_file(self, file_name) -> None:
        """stages file in active git repo

        Args:
        file_name (str): name of file to be added
        """
        self.repo.index.add([file_name])

    def commit_changes(self, commit_message) -> None:
        """commits changes in active repo

        Args:
        commit_message (str): message of commit
        """
        self.repo.index.commit(commit_message)

    def make_branch(self, branch_name) -> None:
        """creates new branch on local git repo

        Args
        branch_name (str): name of branch to create
        """
        new_branch = self.repo.create_head(branch_name)
        self.repo.head.reference = new_branch

    def make_branch_github(self, branch_name, source_branch) -> None:
        """creates new branch on remote github repo

        Args:
            branch_name (str): name of new branch
            source_branch (str): name of branch to create from (e.g., main)
        """
        sb = self.github_repo.get_branch(source_branch)
        self.github_repo.create_git_ref(
            ref='refs/heads/' + branch_name, sha=sb.commit.sha
        )
        # set local branch_name to track remote branch_name
        self.origin.fetch()
        (self.repo.heads[branch_name]
            .set_tracking_branch(self.origin.refs[branch_name]))

    def switch_branch(self, branch_name) -> None:
        """switches active branch of active local git repo

        Args:
            branch_name (str): name of branch to switch to
        """
        self.repo.heads[branch_name].checkout()

    def make_pull_request(
        self, branch_name, base_name, title, body
    ) -> int:
        """creates pull request for branch of remote repo

        Args:
            branch_name (str): branch to merge
            base_name (dtr): branch to merge into
            title (str): title of pull request
            body (str): body of pull request

        Returns:
            int: ID of pull request used by github
        """
        pr = self.github_repo.create_pull(
            title=title, body=body, head=branch_name, base=base_name
        )
        return pr.number

    def merge_pull_request(self, pr_number) -> None:
        """merges pull request on github by PR number

        Args:
            pr_number (int): ID of pull request used by github
        """
        pr = self.github_repo.get_pull(pr_number)
        pr.merge()

    def make_release(self, version, comment) -> None:
        """makes release on github

        Args:
            version (str): release version
            comment (str): release comment
        """
        os.environ["GITHUB_TOKEN"] = self.github_token
        gh_release_create(
            self.github_repo_name, f"v{version}", publish=True,
            name=f"v{version}", body=comment
        )

    def open_github_instance(self, github_token) -> None:
        """sets up new github instance

        Args:
            github_token (str): github API token
        """
        # auth token
        self.auth = Auth.Token(github_token)
        # github instance
        self.github = Github(auth=self.auth)

    def set_github_repo(self, repo_name) -> None:
        """sets active github repo

        Args:
            repo_name (str): name of github repo

        Raises:
            Exception: Github repo not found
        """
        repo = self.github.get_repo(repo_name)
        if repo:
            self.github_repo = repo
        else:
            raise Exception(f"Github repo {repo_name} not found")

    def exit_github(self) -> None:
        """closes github instance
        """
        self.github.close()
