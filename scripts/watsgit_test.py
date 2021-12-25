import logging
import os
from os.path import join
from re import I
from tempfile import mkdtemp
from git import Repo

from git.refs.remote import RemoteReference

from scripts.watsgit import RepoStatus, status

DISPOSABLE_GIT_REMOTE = "https://github.com/td0m/hewtils-test"

temp_dir = mkdtemp()

logger = logging.getLogger(__name__)

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
