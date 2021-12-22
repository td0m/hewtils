#!/bin/env python3
import os
from git import Repo
from argparse import ArgumentParser, BooleanOptionalAction
import json

from git.refs.remote import RemoteReference

from scripts.clone import get_path, print_path

# TODO: run on all branches
# TODO: test
# TODO: auto fix "no upstream URL" by using url convention and passing "--fix-upstream"
# TODO: auto push changes by passing "--push"

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


# recurisvely visit directories until we find a git repo
def visit_dir(prefix: str, path: str = "", **kwargs):
    if len(path) == 0:
        path = prefix

    if os.path.isdir(path):
        if os.path.exists(os.path.join(path, ".git")):

            statuses = list(git_status(prefix, path, **kwargs))
            if len(statuses) > 0:
                print(f"{bcolors.BOLD}{path[len(prefix)+1:]}{bcolors.ENDC}")
                for msg in statuses:
                    print(f"  {msg}{bcolors.ENDC}")
                print()

            return
        for subdir in os.listdir(path):
            visit_dir(prefix, os.path.join(path, subdir), **kwargs)


def push_f(repo, branch):
    infos = repo.remotes.origin.push()
    for info in infos:
        yield bcolors.OKGREEN + f"Pushed '{branch}' to '{info.remote_ref}'"

def git_status(
    prefix: str, path: str, push: bool = False, debug: bool = False, add_remote=False
):
    repo = Repo(path)
    pathlist = get_path(path[len(prefix)+1:])

    if repo.is_dirty(untracked_files=True):
        # TODO: include number of changes in the message
        yield f"{bcolors.WARNING}Untracked/uncommitted changes"

    branch = repo.active_branch
    pbranch = f"'{branch}'"

    unpushed = []
    unpulled = []
    try:
        unpushed = list(repo.iter_commits(f"{branch}@{{u}}..{branch}"))
        unpulled = list(repo.iter_commits(f"{branch}..{branch}@{{u}}"))
    except Exception as e:
        err: str = e.args[-1].decode("utf-8")
        if err.startswith("fatal: bad revision"):
            if push:
                yield from push_f(repo, branch)
            else:
                yield bcolors.FAIL + f"Upstream of branch {pbranch} has no commits."
        elif err.startswith("fatal: no such branch:"):
            yield bcolors.FAIL + f"No branch {pbranch}."
        elif err.startswith("fatal: no upstream configured"):
            if add_remote:
                v = print_path(pathlist)
                remote_name = "origin"
                #repo.create_remote(remote_name, v)
                rem_ref = RemoteReference(repo, f"refs/remotes/{remote_name}/{branch}")
                repo.head.reference.set_tracking_branch(rem_ref)
                yield bcolors.OKCYAN + f"Adding remote {v}..."
            else:
                yield bcolors.FAIL + f"No upstream remote configured for branch {pbranch}."
                yield "  '--add-remote' will add one automatically for you."
        if debug:
            for arg in e.args[:-1]:
                yield str(arg)
            yield bcolors.FAIL + err
        return

    if len(unpushed) > 0:
        if push:
            yield from push_f(repo, branch)
        else:
            yield bcolors.WARNING + f"Unpushed changes on {pbranch}"

    if len(unpulled) > 0:
        yield bcolors.OKCYAN + f"Unpulled changes from {pbranch}"
    return


if __name__ == "__main__":
    parser = ArgumentParser(description="Git status for multiple directories")
    parser.add_argument(
        "-p", "--push", help="auto push changes", action=BooleanOptionalAction
    )
    parser.add_argument(
        "--add-remote",
        help="automatically add remote if missing",
        action=BooleanOptionalAction,
    )
    parser.add_argument(
        "-v",
        "--verbose",
        help="enable some extra debug logs",
        action=BooleanOptionalAction,
    )

    args = parser.parse_args()

    visit_dir("/home/dom/Git", push=args.push, debug=args.verbose, add_remote=args.add_remote)
