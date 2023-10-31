from __future__ import annotations
from collections.abc import Callable, Iterable, Iterator
from dataclasses import dataclass, field
from itertools import chain
import json
from typing import Any, NewType, TypeAlias
import click
import ghreq
from ghtoken import get_ghtoken
from . import __url__, __version__

Repo = NewType("Repo", dict[str, Any])

RepoFilter: TypeAlias = Callable[[Repo], bool]


class Client(ghreq.Client):
    def get_my_repos(self) -> Iterator[Repo]:
        return map(Repo, self.paginate("/user/repos"))

    def get_repos_for_owner(self, owner: str) -> Iterator[Repo]:
        return map(Repo, self.paginate(f"/users/{owner}/repos"))


@dataclass
class Matcher:
    filters: list[RepoFilter] = field(init=False, default_factory=list)

    def add(self, rf: RepoFilter) -> None:
        self.filters.append(rf)

    def __call__(self, r: Repo) -> bool:
        return all(rf(r) for rf in self.filters)


def field_filter(field: str, value: Any) -> RepoFilter:
    def filterfunc(r: Repo) -> bool:
        return bool(r[field] == value)

    return filterfunc


def language_filter(language: str) -> RepoFilter:
    language = language.lower()

    def filterfunc(r: Repo) -> bool:
        if (lang := r["language"]) is not None:
            return bool(lang.lower() == language)
        else:
            return False

    return filterfunc


def topic_filter(topic: str) -> RepoFilter:
    topic = topic.lower()

    def filterfunc(r: Repo) -> bool:
        return topic in r["topics"]

    return filterfunc


def null_filter(_: Repo) -> bool:
    return True


@click.command(context_settings={"help_option_names": ["-h", "--help"]})
@click.version_option(
    __version__,
    "-V",
    "--version",
    message="%(prog)s %(version)s",
)
@click.option(
    "-A",
    "--archived",
    "archive_filter",
    flag_value=null_filter,
    type=click.UNPROCESSED,
    help="Include archived repositories",
)
@click.option(
    "--archived-only",
    "archive_filter",
    flag_value=field_filter("archived", True),
    type=click.UNPROCESSED,
    help="Only list archived repositories",
)
@click.option(
    "-F",
    "--forks",
    "fork_filter",
    flag_value=null_filter,
    type=click.UNPROCESSED,
    help="Include forks",
)
@click.option(
    "--forks-only",
    "fork_filter",
    flag_value=field_filter("fork", True),
    type=click.UNPROCESSED,
    help="Only list forks",
)
@click.option(
    "-J",
    "--json",
    "dump_json",
    is_flag=True,
    help="Output JSON objects for each repository",
)
@click.option(
    "-L",
    "--language",
    help="Only show repositories for the given programming language",
    metavar="NAME",
)
@click.option(
    "-T",
    "--topic",
    help="Only show repositories with the given topic",
    metavar="TOPIC",
    multiple=True,
)
@click.argument("owner", nargs=-1)
def main(
    owner: tuple[str, ...],
    dump_json: bool,
    archive_filter: RepoFilter | None,
    fork_filter: RepoFilter | None,
    language: str | None,
    topic: tuple[str, ...],
) -> None:
    """
    List & filter GitHub repositories

    Visit <https://github.com/jwodder/repolist> for more information.
    """
    matcher = Matcher()
    if archive_filter is not None:
        matcher.add(archive_filter)
    else:
        matcher.add(field_filter("archived", False))
    if fork_filter is not None:
        matcher.add(fork_filter)
    else:
        matcher.add(field_filter("fork", False))
    if language is not None:
        matcher.add(language_filter(language))
    for t in topic:
        matcher.add(topic_filter(t))
    with Client(
        token=get_ghtoken(),
        user_agent=ghreq.make_user_agent("repolist", __version__, url=__url__),
    ) as client:
        repos: Iterable[Repo]
        if owner:
            repos = chain.from_iterable(client.get_repos_for_owner(o) for o in owner)
        else:
            repos = client.get_my_repos()
        for r in repos:
            if matcher(r):
                if dump_json:
                    print(json.dumps(r, indent=4))
                else:
                    print(r["full_name"])


if __name__ == "__main__":
    main()
