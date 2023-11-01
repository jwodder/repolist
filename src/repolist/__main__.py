from __future__ import annotations
from collections.abc import Callable, Iterable, Iterator
from dataclasses import dataclass, field
from itertools import chain
import json
from textwrap import indent
from types import TracebackType
from typing import TYPE_CHECKING, Any, NewType, Protocol, TypeAlias
import click
import ghreq
from ghtoken import get_ghtoken
from . import __url__, __version__

if TYPE_CHECKING:
    from typing_extensions import Self

Repo = NewType("Repo", dict[str, Any])

RepoFilter: TypeAlias = Callable[[Repo], bool]


class Client(ghreq.Client):
    def get_my_repos(
        self, visibility: str | None, affiliation: str | None
    ) -> Iterator[Repo]:
        return map(
            Repo,
            self.paginate(
                "/user/repos",
                params={
                    "visibility": visibility,
                    "affiliation": affiliation,
                    "per_page": 100,
                },
            ),
        )

    def get_repos_for_owner(self, owner: str) -> Iterator[Repo]:
        return map(
            Repo, self.paginate(f"/users/{owner}/repos", params={"per_page": 100})
        )


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


def affiliation_validator(s: str) -> str:
    if any(
        opt not in {"owner", "collaborator", "organization_member"}
        for opt in s.split(",")
    ):
        raise ValueError(
            '--affilition value must be a comma-separated list of "owner",'
            ' "collaborator", and/or "organization_member"'
        )
    return s


class Formatter(Protocol):
    def __enter__(self) -> Self:
        ...

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        ...

    def show(self, repo: Repo) -> None:
        ...


@dataclass
class FullNameFormatter:
    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        _exc_val: BaseException | None,
        _exc_tb: TracebackType | None,
    ) -> None:
        pass

    def show(self, repo: Repo) -> None:
        print(repo["full_name"])


@dataclass
class JsonFormatter:
    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        _exc_val: BaseException | None,
        _exc_tb: TracebackType | None,
    ) -> None:
        pass

    def show(self, repo: Repo) -> None:
        print(json.dumps(repo, indent=4))


@dataclass
class ArrayFormatter:
    first: bool = field(init=False, default=True)

    def __enter__(self) -> Self:
        print("[", end="")
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        _exc_val: BaseException | None,
        _exc_tb: TracebackType | None,
    ) -> None:
        if exc_type is None:
            if not self.first:
                print()
            print("]")

    def show(self, repo: Repo) -> None:
        if self.first:
            print()
            self.first = False
        else:
            print(",")
        print(indent(json.dumps(repo, indent=4), " " * 4), end="")


@click.command(context_settings={"help_option_names": ["-h", "--help"]})
@click.option(
    "--affiliation",
    type=affiliation_validator,
    help=(
        "Only show repositories with the given affiliations.  The value must be"
        ' a comma-separated list of "owner", "collaborator", and/or'
        ' "organization_member".  (Only for the authenticating user)'
    ),
    metavar="AFFILIATION",
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
    "--array",
    "formatter",
    flag_value=ArrayFormatter,
    type=click.UNPROCESSED,
    is_flag=True,
    help="Output an array of JSON objects",
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
    "formatter",
    flag_value=JsonFormatter,
    type=click.UNPROCESSED,
    is_flag=True,
    help="Output a JSON object for each repository",
)
@click.option(
    "-L",
    "--language",
    help="Only show repositories for the given programming language",
    metavar="NAME",
)
@click.option(
    "--private-only",
    "visibility",
    flag_value="private",
    help="Only show private repositories (Only for the authenticating user)",
)
@click.option(
    "--public-only",
    "visibility",
    flag_value="public",
    help="Only show public repositories (Only for the authenticating user)",
)
@click.option(
    "-T",
    "--topic",
    help="Only show repositories with the given topic",
    metavar="TOPIC",
    multiple=True,
)
@click.option(
    "--no-topics", is_flag=True, help="Only show repositories without any topics"
)
@click.version_option(
    __version__,
    "-V",
    "--version",
    message="%(prog)s %(version)s",
)
@click.argument("owner", nargs=-1)
def main(
    owner: tuple[str, ...],
    formatter: type[Formatter] | None,
    archive_filter: RepoFilter | None,
    fork_filter: RepoFilter | None,
    language: str | None,
    topic: tuple[str, ...],
    no_topics: bool,
    visibility: str | None,
    affiliation: str | None,
) -> None:
    """
    List & filter GitHub repositories

    Visit <https://github.com/jwodder/repolist> for more information.
    """
    if formatter is None:
        formatter = FullNameFormatter
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
    if no_topics:
        matcher.add(field_filter("topics", []))
    if visibility is not None and owner:
        raise click.UsageError(
            "Public/private options cannot be used when listing repositories"
            " for other users"
        )
    if affiliation is not None and owner:
        raise click.UsageError(
            "--affiliation cannot be used when listing repositories for other users"
        )
    with Client(
        token=get_ghtoken(),
        user_agent=ghreq.make_user_agent("repolist", __version__, url=__url__),
    ) as client:
        repos: Iterable[Repo]
        if owner:
            repos = chain.from_iterable(client.get_repos_for_owner(o) for o in owner)
        else:
            repos = client.get_my_repos(visibility=visibility, affiliation=affiliation)
        with formatter() as fmt:
            for r in repos:
                if matcher(r):
                    fmt.show(r)


if __name__ == "__main__":
    main()
