# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import unicode_literals

import pytest

from poetry.poetry import Poetry
from poetry.utils._compat import PY2
from poetry.utils._compat import Path
from poetry.utils.toml_file import TomlFile


fixtures_dir = Path(__file__).parent / "fixtures"


def test_poetry():
    poetry = Poetry.create(str(fixtures_dir / "sample_project"))

    package = poetry.package

    assert package.name == "my-package"
    assert package.version.text == "1.2.3"
    assert package.description == "Some description."
    assert package.authors == ["Sébastien Eustace <sebastien@eustace.io>"]
    assert package.license.id == "MIT"
    assert (
        package.readme.relative_to(fixtures_dir).as_posix()
        == "sample_project/README.rst"
    )
    assert package.homepage == "https://poetry.eustace.io"
    assert package.repository_url == "https://github.com/sdispater/poetry"
    assert package.keywords == ["packaging", "dependency", "poetry"]

    assert package.python_versions == "~2.7 || ^3.6"
    assert str(package.python_constraint) == ">=2.7,<2.8 || >=3.6,<4.0"

    dependencies = {}
    for dep in package.requires:
        dependencies[dep.name] = dep

    cleo = dependencies["cleo"]
    assert cleo.pretty_constraint == "^0.6"
    assert not cleo.is_optional()

    pendulum = dependencies["pendulum"]
    assert pendulum.pretty_constraint == "branch 2.0"
    assert pendulum.is_vcs()
    assert pendulum.vcs == "git"
    assert pendulum.branch == "2.0"
    assert pendulum.source == "https://github.com/sdispater/pendulum.git"
    assert pendulum.allows_prereleases()

    requests = dependencies["requests"]
    assert requests.pretty_constraint == "^2.18"
    assert not requests.is_vcs()
    assert not requests.allows_prereleases()
    assert requests.is_optional()
    assert requests.extras == ["security"]

    pathlib2 = dependencies["pathlib2"]
    assert pathlib2.pretty_constraint == "^2.2"
    assert pathlib2.python_versions == "~2.7"
    assert not pathlib2.is_optional()

    demo = dependencies["demo"]
    assert demo.is_file()
    assert not demo.is_vcs()
    assert demo.name == "demo"
    assert demo.pretty_constraint == "*"

    demo = dependencies["my-package"]
    assert not demo.is_file()
    assert demo.is_directory()
    assert not demo.is_vcs()
    assert demo.name == "my-package"
    assert demo.pretty_constraint == "*"

    simple_project = dependencies["simple-project"]
    assert not simple_project.is_file()
    assert simple_project.is_directory()
    assert not simple_project.is_vcs()
    assert simple_project.name == "simple-project"
    assert simple_project.pretty_constraint == "*"

    functools32 = dependencies["functools32"]
    assert functools32.name == "functools32"
    assert functools32.pretty_constraint == "^3.2.3"
    assert (
        str(functools32.marker)
        == 'python_version ~= "2.7" and sys_platform == "win32" or python_version in "3.4 3.5"'
    )

    assert "db" in package.extras

    classifiers = package.classifiers

    assert classifiers == [
        "Topic :: Software Development :: Build Tools",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ]

    assert package.all_classifiers == [
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Topic :: Software Development :: Build Tools",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ]


def test_poetry_with_packages_and_includes():
    poetry = Poetry.create(
        str(fixtures_dir.parent / "masonry" / "builders" / "fixtures" / "with-include")
    )

    package = poetry.package

    assert package.packages == [
        {"include": "extra_dir/**/*.py"},
        {"include": "extra_dir/**/*.py"},
        {"include": "my_module.py"},
        {"include": "package_with_include"},
        {"include": "tests", "format": "sdist"},
        {"include": "for_wheel_only", "format": ["wheel"]},
    ]

    assert package.include == ["extra_dir/vcs_excluded.txt", "notes.txt"]


def test_poetry_with_multi_constraints_dependency():
    poetry = Poetry.create(
        str(fixtures_dir / "project_with_multi_constraints_dependency")
    )

    package = poetry.package

    assert len(package.requires) == 2


def test_poetry_with_default_source():
    poetry = Poetry.create(fixtures_dir / "with_default_source")

    assert 1 == len(poetry.pool.repositories)


def test_poetry_with_two_default_sources():
    with pytest.raises(ValueError) as e:
        Poetry.create(fixtures_dir / "with_two_default_sources")

    assert "Only one repository can be the default" == str(e.value)


def test_check():
    complete = TomlFile(fixtures_dir / "complete.toml")
    content = complete.read()["tool"]["poetry"]

    assert Poetry.check(content) == {"errors": [], "warnings": []}


def test_check_fails():
    complete = TomlFile(fixtures_dir / "complete.toml")
    content = complete.read()["tool"]["poetry"]
    content["this key is not in the schema"] = ""

    if PY2:
        expected = (
            "Additional properties are not allowed "
            "(u'this key is not in the schema' was unexpected)"
        )
    else:
        expected = (
            "Additional properties are not allowed "
            "('this key is not in the schema' was unexpected)"
        )

    assert Poetry.check(content) == {"errors": [expected], "warnings": []}


def test_create_fails_on_invalid_configuration():
    with pytest.raises(RuntimeError) as e:
        Poetry.create(
            Path(__file__).parent / "fixtures" / "invalid_pyproject" / "pyproject.toml"
        )

    if PY2:
        expected = """\
The Poetry configuration is invalid:
  - u'description' is a required property
"""
    else:
        expected = """\
The Poetry configuration is invalid:
  - 'description' is a required property
"""
    assert expected == str(e.value)
