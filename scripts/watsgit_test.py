import logging
import os
from os.path import join
from re import I
from tempfile import mkdtemp
from git import Repo
from git.exc import GitCommandError
import json

import git
from git.objects.commit import Commit
from git.refs.remote import RemoteReference

DISPOSABLE_GIT_REMOTE = "https://github.com/td0m/hewtils-test"

temp_dir = mkdtemp()

logger = logging.getLogger(__name__)


class RepoStatus:
    def __init__(
        self,
        untracked: list[str],
        staged: list[str] = [],
        unstaged: list[str] = [],
        branches: dict[str, (str, str)] = {},
        noremote: list[str] = [],
    ):
        self.untracked = untracked
        self.staged = staged
        self.unstaged = unstaged
        self.branches = branches
        self.noremote = noremote

    def __eq__(self, other):
        if not isinstance(self, other.__class__):
            return False
        return self.__dict__ == other.__dict__

def status(repo: Repo) -> RepoStatus:
    untracked = repo._get_untracked_files()

    unstaged: list[git.Diff] = repo.index.diff(None)
    staged: list[git.Diff] = repo.head.commit.diff()

    has_remote: dict[str, bool] = {}
    for ref in repo.references:
        if isinstance(ref, git.RemoteReference):
            has_remote[ref.remote_head] = True

    branches = {}
    for head in repo.branches:
        branch = head.name
        unpushed, unpulled = commit_diff(repo, branch)
        branches[branch] = (branch in has_remote, unpushed, unpulled)

    return RepoStatus(
        untracked=untracked,
        staged=[d.b_path for d in staged],
        unstaged=[d.b_path for d in unstaged],
        branches=branches,
    )


def commit_diff(repo: Repo, branch: str) -> tuple[list[Commit], list[Commit]]:
    diff = lambda unpulled: [
        r.binsha.hex()
        for r in repo.iter_commits(
            f"{branch}@{{u}}..{branch}" if not unpulled else f"{branch}..{branch}@{{u}}"
        )
    ]
    try:
        return diff(False), diff(True)
    except GitCommandError as e:
        logging.warning(e.stderr)
        return [], []

def make_repo(full_path: str) -> Repo:
    os.makedirs(full_path)
    return Repo.init(full_path)


def echo(file: str, txt: str):
    os.system(f"echo {txt} >> {file}")


def test_empty():
    base = mkdtemp()
    repo = make_repo(join(base, "empty"))
    f_committed_and_pushed = join(base, "empty", "pushed.txt")
    f_unpulled = join(base, "empty", "unpulled.txt")
    f_unpushed = join(base, "empty", "unpushed.txt")
    f_uncommited1 = join(base, "empty", "uncommitted1.txt")
    f_uncommited2 = join(base, "empty", "uncommitted2.txt")
    f_untracked = join(base, "empty", "untracked.txt")
    f_other = join(base, "empty", "other.txt")

    # create untracked file
    echo(f_untracked, "1")

    # committed file - used for unstaged changes and to
    # reset remote - since to reset we need to push at
    # least one commit
    echo(f_committed_and_pushed, "2")
    repo.index.add([f_committed_and_pushed])
    repo.index.commit("committed and pushed")

    # upload single commit to git remote
    remote_name = "origin"
    repo.create_remote(remote_name, DISPOSABLE_GIT_REMOTE)
    rem_ref = RemoteReference(repo, f"refs/remotes/{remote_name}/{repo.active_branch}")
    repo.head.reference.set_tracking_branch(rem_ref)
    repo.remotes.origin.push(repo.active_branch, force=True)

    # create new commit, push, and checkout to previous commit
    # to simulate unpulled commit
    echo(f_unpulled, "1")
    repo.index.add([f_unpulled])
    unpulled = repo.index.commit("new unpulled")
    repo.remotes.origin.push(repo.active_branch)
    repo.git.reset("HEAD~1", hard=True)

    # unpushed
    echo(f_unpushed, "1")
    repo.index.add([f_unpushed])
    unpushed = repo.index.commit("new unpushed")

    # checkout to another branch, commit a change, checkout back
    repo.git.checkout("HEAD", b="other")
    echo(f_other, "1")
    repo.index.add([f_other])
    other = repo.index.commit("new other")
    repo.git.checkout("main")

    # new staged file
    echo(f_uncommited1, "1")
    echo(f_uncommited2, "1")
    repo.index.add([f_uncommited1, f_uncommited2])

    # unstaged file
    echo(f_committed_and_pushed, "420")


    # TODO: extract filenames instead of hard coding
    assert (
        status(repo).__dict__
        ==
        RepoStatus(
            untracked=["untracked.txt"],
            unstaged=["pushed.txt"],
            staged=["uncommitted1.txt", "uncommitted2.txt"],
            branches={
                "main": (True, [unpushed.binsha.hex()], [unpulled.binsha.hex()]),
                "other": (False, [], []),
            },
        ).__dict__
    )
