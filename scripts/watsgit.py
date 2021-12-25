#!/bin/env python3
import os
from git import Repo
from argparse import ArgumentParser, BooleanOptionalAction
import git
from git.exc import GitCommandError
from git.objects.commit import Commit

from git.refs.remote import RemoteReference

# TODO: auto fix "no upstream URL" by using url convention and passing "--fix-upstream"


class bcolors:
    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKCYAN = "\033[96m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"


class RepoStatus:
    def __init__(
        self,
        untracked: list[str],
        staged: list[str] = [],
        unstaged: list[str] = [],
        branches: dict[str, (bool, str, str)] = {},
    ):
        self.untracked = untracked
        self.staged = staged
        self.unstaged = unstaged
        self.branches = branches

    def __eq__(self, other):
        if not isinstance(self, other.__class__):
            return False
        return self.__dict__ == other.__dict__

    def __repr__(self):
        return f"{len(self.untracked)}"


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
        return [], []


# recurisvely visit directories until we find a git repo
def visit_dir(prefix: str, path: str = "", **kwargs):
    if len(path) == 0:
        path = prefix

    if os.path.isdir(path):
        if os.path.exists(os.path.join(path, ".git")):
            lines = list(git_status(prefix, path, **kwargs))
            if len(lines) > 0:
                print(path[len(prefix) + 1 :])
                for line in lines:
                    print("  " + line)
                print()
            return
        for subdir in os.listdir(path):
            visit_dir(prefix, os.path.join(path, subdir), **kwargs)


def c(l: list) -> str:
    return "s" if len(l) > 1 else ""


def git_status(prefix: str, path: str):
    warn = lambda msg: bcolors.WARNING + msg + bcolors.ENDC
    err = lambda msg: bcolors.FAIL + msg + bcolors.ENDC

    repo = Repo(path)
    info = status(repo)

    if info.untracked:
        yield warn(f"{len(info.untracked)} untracked file{c(info.untracked)}")
    if info.unstaged:
        yield warn(f"{len(info.unstaged)} unstaged file{c(info.unstaged)}")
    if info.staged:
        yield warn(f"{len(info.staged)} staged file{c(info.staged)}")
    if info.branches:
        for branch, (has_remote, unpushed, unpulled) in info.branches.items():
            if not has_remote:
                yield err(f"{branch}: no remote")
            if unpushed:
                yield warn(f"{branch}: {len(unpushed)} unpushed commit{c(unpushed)}")
            if unpulled:
                yield warn(f"{branch}: {len(unpulled)} unpulled commit{c(unpulled)}")

if __name__ == "__main__":
    parser = ArgumentParser(description="Git status for multiple directories")
    args = parser.parse_args()

    visit_dir("/home/dom/Git")
