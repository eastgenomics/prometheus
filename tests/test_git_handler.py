import unittest
import sys
import os
sys.path.append(os.path.abspath(
    os.path.join(os.path.realpath(__file__), '../../bin')
))
from bin.util.git_handler import GitHandler
from unittest.mock import Mock, patch, mock_open


class testGitHandler(unittest.TestCase):
    @patch("bin.util.git_handler.Repo.create_head")
    @patch("bin.util.git_handler.Repo.create_remote")
    @patch("bin.util.git_handler.Repo.init")
    @patch("bin.util.git_handler.GitHandler.set_github_repo")
    @patch("bin.util.git_handler.Github")
    def generate_git_handler(
        self, mock_instance, mock_set_repo, mock_init, mock_remote, mock_head
    ) -> GitHandler:
        repo_directory = ""
        github_repo_name = ""
        remote_repo_url = ""
        branch_name = ""
        github_token = "1234"
        handler = GitHandler(
            repo_directory, github_repo_name, remote_repo_url,
            branch_name, github_token
        )
        return handler

    def test_make_git_handler(self):
        assert self.generate_git_handler() is not None

    # TODO: fix patch import error
    #@patch("bin.util.git_handler.Repo.Remote.pull")
    #def test_pull_repo(self, mock_pull):
    #    handler = self.generate_git_handler()
    #    assert handler.pull_repo() is None

    @patch("bin.util.git_handler.subprocess.run")
    @patch("bin.util.git_handler.os.chdir")
    def test_rename_file(self, mock_chdir, mock_run):
        handler = self.generate_git_handler()
        assert handler.rename_file("", "", "") is None

    # TODO: fix patch import error
    #@patch("bin.util.git_handler.Repo.Remote.push")
    #def test_push_to_remote(self, mock_pull):
    #    handler = self.generate_git_handler()
    #    assert handler.push_to_remote() is None

    def test_add_file(self):
        handler = self.generate_git_handler()
        assert handler.add_file("file.txt") is None

    def test_commit_changes(self):
        handler = self.generate_git_handler()
        assert handler.commit_changes("message") is None

    def test_make_branch(self):
        handler = self.generate_git_handler()
        assert handler.make_branch("new_branch") is None

    # TODO: fix patch import error
    #@patch("bin.util.git_handler.Github.Repository.create_git_ref")
    #@patch("bin.util.git_handler.Github.Repository.get_branch")
    #def test_make_branch_github(self, mock_branch, mock_ref):
    #    handler = self.generate_git_handler()
    #    assert handler.make_branch_github("new_branch") is None

    def test_switch_branch(self):
        handler = self.generate_git_handler()
        assert handler.switch_branch("new_branch") is None

    # TODO: fix patch import error
    #@patch("bin.util.git_handler.Github.Repository.create_git_ref")
    #def test_make_pull_request(self, mock_ref):
    #    handler = self.generate_git_handler()
    #    assert handler.make_pull_request("", "", "", "") is None

    @patch("bin.util.git_handler.gh_release_create")
    def test_make_release(self, mock_release):
        handler = self.generate_git_handler()
        assert handler.make_release("", "") is None

    @patch("bin.util.git_handler.Github")
    def test_open_github_instance(self, mock_github):
        handler = self.generate_git_handler()
        assert handler.open_github_instance("1234") is None

    @patch("bin.util.git_handler.Github.get_repo")
    def test_set_github_repo(self, mock_repo):
        handler = self.generate_git_handler()
        assert handler.set_github_repo("my_repo") is None

    def test_exit_github(self):
        handler = self.generate_git_handler()
        assert handler.exit_github() is None
