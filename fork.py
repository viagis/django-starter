#!/usr/bin/env python3

__author__ = 'Adrian Geuß'
__contact__ = 'adrian@viagis.app'
__copyright__ = 'Copyright 2021 VIAGIS'
__project__ = 'django-starter'

import re
import shutil
from argparse import ArgumentParser
from dataclasses import dataclass
from pathlib import Path
from subprocess import run
from sys import stderr
from typing import List, Pattern, Iterable

SCRIPT_DIR = Path(__file__).absolute().parent
IGNORED_DIRECTORY_PATTERNS = {
    re.compile(r'\.venv'),
    re.compile(r'\.git'),
}
IGNORED_FILE_PATTERNS = {
    re.compile(r'.*\.pyc$'),
    re.compile(r'.*\.mo$'),
    re.compile(r'\.DS_Store'),
}
TP = 30


@dataclass
class ReSub:
    pattern: Pattern[str]
    replacement: str


def fatal_error(message: str, exit_code: int = 1):
    print(message, file=stderr)
    exit(exit_code)


def rename_dir(source_path: Path, target_path: Path, dir_title: str) -> Path:
    print(f'{f"Renaming {dir_title}:":<{TP}} -> {str(target_path.relative_to(SCRIPT_DIR.parent)):>3}')
    new_path = source_path
    if source_path.is_dir():
        if not dry_run:
            source_path.rename(target_path)
            new_path = target_path
    else:
        fatal_error(f'Unable to find directory: {source_path}')

    return new_path


def replace_in_dir(dir_path: Path, subs: Iterable[ReSub]) -> List[Path]:
    adjusted_files = []
    for item in dir_path.iterdir():
        if item.is_dir():
            if any(it.match(item.name) for it in IGNORED_DIRECTORY_PATTERNS):
                continue

            adjusted_files += replace_in_dir(item, subs)
        elif item.is_file():
            if any(it.match(item.name) for it in IGNORED_FILE_PATTERNS):
                continue

            updated_lines = []
            total_replacements = 0
            try:
                with item.open() as f:
                    for line in f.readlines():
                        updated_line = line
                        for sub in subs:
                            updated_line, count = sub.pattern.subn(sub.replacement, updated_line)
                            total_replacements += count

                        updated_lines.append(updated_line)
            except UnicodeDecodeError:
                print(f'Unable to read: {item}', file=stderr)
                continue

            if total_replacements:
                adjusted_files.append(item)

                if not dry_run:
                    with item.open('w') as f:
                        f.writelines(updated_lines)

    return adjusted_files


if __name__ == '__main__':
    parser = ArgumentParser(description='Transforms the starter project into a new django project with custom name.')
    parser.add_argument('-n', '--dry-run', action='store_true')
    parser.add_argument('--name', type=str, help='Project name')
    parser.add_argument('-d', '--destination', type=Path, default=SCRIPT_DIR.parent,
                        help='Path to the destination directory the fork should be created in')
    args = parser.parse_args()
    dry_run = args.dry_run
    destination_dir: Path = args.destination

    if not destination_dir.is_dir():
        fatal_error(f'Destination directory does not exist: {destination_dir}')

    project_name = args.name
    if isinstance(project_name, str):
        project_name = project_name.strip()

    while not project_name:
        project_name = input('Enter project name: ').strip()

    django_project_name = re.sub(r'\s|-', '_', project_name).lower()

    # Replace directory names
    project_root = destination_dir.joinpath(project_name)
    django_root = project_root.joinpath(django_project_name)
    django_project_dir = django_root.joinpath(django_project_name)

    # Copy project to destination
    if project_root.is_dir():
        fatal_error(f'Project root already exists: {project_root}')

    if not dry_run:
        shutil.copytree(SCRIPT_DIR, project_root, ignore=shutil.ignore_patterns('.git', '.venv'), symlinks=True)

    django_root = rename_dir(project_root.joinpath('django_starter'), django_root, 'Django Root')
    django_project_dir = rename_dir(django_root.joinpath('django_starter'), django_project_dir, 'Django Project Dir')

    # Replace project name and directory references in files (django-starter, django_starter)
    print(f'{"Rewriting project files":<{TP}}', end='')
    updated_files = set(replace_in_dir(project_root, [
        ReSub(re.compile('django-starter'), project_name),
        ReSub(re.compile('django_starter'), django_project_name),
        ReSub(re.compile('Django Starter'), project_name),
    ]))
    print(f'({len(updated_files)})')

    if not dry_run:
        run(['git', 'init', '-b', 'main'], cwd=project_root)

    if not dry_run:
        run(['git', 'add', '-A'], cwd=project_root)
        run(['git', 'commit', '-m', '"Initial commit."'], cwd=project_root)

    print('Setting project up for development')
    setup_script = project_root.joinpath('init.py')
    if not dry_run:
        run(['python3', str(setup_script), 'debug'], cwd=project_root)

    print('To setup your poetry virtual environment run:\n'
          'poetry env use ~/.pyenv/versions/3.7.3/bin/python\n'
          'poetry install --no-root')
