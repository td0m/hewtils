#!/bin/env python3
import os
from argparse import ArgumentParser, BooleanOptionalAction

GIT_USER = "td0m"
GIT_DOMAIN = "github.com"
BASE_DIR = os.path.join(os.environ["HOME"], "Git")
ALIAS = {
    "gh": "github.com",
}

# apply domain alias to standardized path
# path in form of [domain, user, repo]
def apply_alias(path: list[str], alias: dict[str, str]) -> list[str]:
    if path[0] in alias:
        path[0] = alias[path[0]]
    return path


# takes an absolute or relative url to a git repository
# returns a standardized absolute path to repository
def get_path(
    url: str,
    domain: str = "domain",
    user: str = "user",
    alias: dict[str, str] = {},
) -> list[str]:
    sshprefix, sshpostfix = "git@", ".git"
    # ssh support (git@domain:user/repo.git)
    if url.startswith(sshprefix):
        url = url[len(sshprefix) :]
        [domain, path] = url.split(":")
        [user, repo] = path.split("/")
        if repo.endswith(sshpostfix):
            repo = repo[: -len(sshpostfix)]
        return apply_alias([domain, user, repo], alias)

    path: list[str] = url.split("/")
    if len(path) == 0 or len(url) == 0:
        raise ValueError("invalid path")

    # strip protocol, such as https://... or http://...
    if path[0].endswith(":") and len(path[1]) == 0:
        path = path[2:]

    if len(path) > 3:
        path = path[:3]
        # raise ValueError("path too long!")

    # autofill default properties
    return apply_alias([domain, user][: 3 - len(path)] + path, alias)


def print_path(path: list[str]) -> str:
    return "https://" + "/".join(path)


# will clone git repo and open shell in the same directory
def clone_and_cd(
    path: list[str],
    base_dir: str = "./git",
):
    directory = os.path.join(base_dir, path[0], path[1])
    # make and cd to directory
    os.makedirs(directory, exist_ok=True)
    os.chdir(directory)
    # clone repository
    os.system(f"git clone {print_path(path)}")
    # open directory and start a shell in it
    os.chdir(path[2])
    os.system("$SHELL")


if __name__ == "__main__":
    parser = ArgumentParser(description="clone git repos. faster. better.")
    parser.add_argument("url", type=str, help="url of the git repo.")
    args = parser.parse_args()

    path = get_path(
        args.url,
        domain=GIT_DOMAIN,
        user=GIT_USER,
        alias=ALIAS,
    )
    print("Repository " + "/".join(path))

    clone_and_cd(
        path,
        base_dir=BASE_DIR,
    )
