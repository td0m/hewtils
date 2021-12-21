from pytest import raises
from clone import get_path

domain, user, repo = "github.com", "hello", "world"
url = f"{domain}/{user}/{repo}"
sshurl = f"git@{domain}:{user}/{repo}.git"

aliases = {"gh": "github.com", "github": "github.com"}


def f(url: str) -> list[str]:
    return get_path(url, domain, user, aliases)


def test_default():
    assert f(url) == [domain, user, repo]


def test_protocol_agnostic():
    assert f(url) == f("https://" + url)
    assert f(url) == f("wtfisthisproto://" + url)


def test_default_domain():
    assert f(url) == f(f"{user}/{repo}")


def test_default_domain_and_user():
    assert f(url) == f(repo)


def test_ssh():
    assert f(sshurl) == f(url)


def test_bad_length():
    with raises(ValueError):
        f("")


def test_alias():
    assert f(url.replace(domain, "gh")) == f(url)
