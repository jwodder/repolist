|repostatus| |ci-status| |license|

.. |repostatus| image:: https://www.repostatus.org/badges/latest/concept.svg
    :target: https://www.repostatus.org/#concept
    :alt: Project Status: Concept – Minimal or no implementation has been done
          yet, or the repository is only intended to be a limited example,
          demo, or proof-of-concept.

.. |ci-status| image:: https://github.com/jwodder/repolist/actions/workflows/test.yml/badge.svg
    :target: https://github.com/jwodder/repolist/actions/workflows/test.yml
    :alt: CI Status

.. |license| image:: https://img.shields.io/github/license/jwodder/repolist.svg
    :target: https://opensource.org/licenses/MIT
    :alt: MIT License

`GitHub <https://github.com/jwodder/repolist>`_
| `Issues <https://github.com/jwodder/repolist/issues>`_

``repolist`` is a command for listing & filtering GitHub repositories belonging
to you or other users/organizations on GitHub.

Installation
============
``repolist`` requires Python 3.10 or higher.  Just use `pip
<https://pip.pypa.io>`_ for Python 3 (You have pip, right?) to install it::

    python3 -m pip install git+https://github.com/jwodder/repolist.git


Usage
=====

::

    repolist [<options>] [<user> ...]

When no arguments are given, ``repolist`` lists all repositories affiliated
with the authenticated user (i.e., you).  When one or more user and/or
organization names are given, ``repolist`` lists all public repositories
belonging to them.  In both cases, archived repositories and forks are omitted
from the output by default, but this can be changed via command-line options.

By default, only the fullname of each repository is shown, but the ``--array``
and ``--json`` options can be used to instead output the complete repository
objects returned by the GitHub REST API.


Options
-------

--affiliation AFFILIATION       Only list repositories affiliated with the
                                authenticated user in the given ways.  The
                                value must be a comma-separated list of
                                "owner", "collaborator", and/or
                                "organization_member".

                                This option can only be given when listing
                                repositories for the authenticated user, i.e.,
                                when no usernames are given on the command
                                line.

-A, --archived                  Include archived repositories

--archived-only                 Only list archived repositories

--array                         Output an array of JSON objects

-F, --forks                     Include forks

--forks-only                    Only list forks

-J, --json                      Output a JSON object for each repository.  The
                                JSON objects are separated by newlines but are
                                otherwise not grouped.  The result is not valid
                                JSON (unless there's only one repository), but
                                it can be processed with a tool like jq_.

-L, --language NAME             Only list repositories with the given
                                programming language as their primary language.

                                The language name must be spelled out
                                completely (i.e., "Python", not "Py"), but case
                                is not significant.

--private-only                  Only list private repositories

                                This option can only be given when listing
                                repositories for the authenticated user, i.e.,
                                when no usernames are given on the command
                                line.

--public-only                   Only list public repositories.

                                This option can only be given when listing
                                repositories for the authenticated user, i.e.,
                                when no usernames are given on the command
                                line.

-R, --reverse                   Reverse the sort order

-S, --sort-by <created|updated|pushed|full_name>
                                Sort the repositories for each
                                user/organization based on the given attribute.
                                [default: ``full_name``]

                                Note that sorting only applies on a
                                per-user/organization basis.  If multiple users
                                or organizations are specified on the command
                                line, the repositories for each individual
                                owner are sorted, but repositories from
                                different owners are not merged together.

-t, --topic TOPIC               Only list repositories with the given topic
                                (case insensitive).  This option can be given
                                multiple times to only list repositories with
                                all of the specified topics.

-T, --exclude-topic TOPIC       Only list repositories without the given topic
                                (case insensitive).  This option can be given
                                multiple times.

--no-topics                     Only list repositories without any topics

.. _jq: https://jqlang.github.io/jq/


Authentication
--------------

``repolist`` requires a GitHub access token with appropriate permissions in
order to run.  Specify the token via the ``GH_TOKEN`` or ``GITHUB_TOKEN``
environment variable (possibly in an ``.env`` file), by storing a token with
the ``gh`` or ``hub`` command, or by setting the ``hub.oauthtoken`` Git config
option in your ``~/.gitconfig`` file.
