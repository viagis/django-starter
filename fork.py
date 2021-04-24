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
from subprocess import run, DEVNULL, PIPE
from sys import stderr
from typing import List, Pattern, Iterable, Optional

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
TP = 40


@dataclass
class ReSub:
    pattern: Pattern[str]
    replacement: str


def fatal_error(message: Optional[str] = None, exit_code: int = 1):
    print(message, file=stderr)
    exit(exit_code)


def rename_dir(source_path: Path, target_path: Path, dir_title: str) -> Path:
    print(f'{f"Renaming {dir_title}":<{TP}}-> {str(target_path.relative_to(SCRIPT_DIR.parent)):>3}')
    new_path = source_path
    if source_path.is_dir():
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

                with item.open('w') as f:
                    f.writelines(updated_lines)

    return adjusted_files


def run_command(args: List[str], **kwargs):
    result = run(args, stdout=None if verbose else DEVNULL, **kwargs)
    if result.returncode != 0:
        fatal_error()


if __name__ == '__main__':
    parser = ArgumentParser(description='Transforms the starter project into a new django project with custom name.')
    parser.add_argument('--project', type=str, help='Project name')
    parser.add_argument('--django-project', type=str, help='Django Project name')
    parser.add_argument('-d', '--destination', type=Path, default=SCRIPT_DIR.parent,
                        help='Path to the destination directory where the fork should be created in')
    parser.add_argument('-v', '--verbose', action='store_true')
    args = parser.parse_args()
    destination_dir: Path = args.destination
    verbose = args.verbose

    if not destination_dir.is_dir():
        fatal_error(f'Destination directory does not exist: {destination_dir}')

    project_name = args.project
    if isinstance(project_name, str):
        project_name = project_name.strip()

    while not project_name:
        project_name = input('Enter project name: ').strip()

    django_project_name = args.django_project or project_name
    django_project_name = re.sub(r'\s|-', '_', django_project_name).lower()

    # Replace directory names
    project_root = destination_dir.joinpath(project_name)
    django_root = project_root.joinpath(django_project_name)
    django_project_dir = django_root.joinpath(django_project_name)

    if project_root.is_dir():
        fatal_error(f'Project root already exists: {project_root}')

    # Copy project to destination
    shutil.copytree(SCRIPT_DIR, project_root, ignore=shutil.ignore_patterns(
        '.git', '.venv', 'fork.py', '*.mo'
    ), symlinks=True)

    # Rename django directories
    django_root = rename_dir(project_root.joinpath('django_starter'), django_root, 'Django Root')
    django_project_dir = rename_dir(django_root.joinpath('django_starter'), django_project_dir, 'Django Project Dir')

    # Replace project name and directory references in files (django-starter, django_starter)
    print(f'{"Rewriting project files":<{TP}}', end='', flush=True)
    updated_files = set(replace_in_dir(project_root, [
        ReSub(re.compile('django-starter'), project_name),
        ReSub(re.compile('django_starter'), django_project_name),
        ReSub(re.compile('Django Starter'), project_name),
    ]))
    print(len(updated_files))

    # Rename Intellij .iml file
    idea_dir = project_root.joinpath('.idea')
    idea_dir.joinpath('django-starter.iml').rename(idea_dir.joinpath(f'{project_name}.iml'))

    print(f'{"Initializing Git repository":<{TP}}', end='', flush=True)
    version_number_re = re.compile(r'([0-9]+\.[0-9]+\.?[0-9]+)')
    result = run(['git', '--version'], cwd=project_root, stdout=PIPE)
    if result.returncode != 0:
        fatal_error('Unable to get git version.')
    match = version_number_re.search(result.stdout.decode())
    if not match:
        fatal_error('Unable to get git version.')

    git_version = match.group(1)
    run_command(['git', 'init'] + (['-b', 'main'] if git_version >= '2.28' else []), cwd=project_root)
    run_command(['git', 'add', '-A'], cwd=project_root)
    run_command(['git', 'commit', '-m', '"Initial commit."'], cwd=project_root)
    print('OK', flush=True)

    print(f'{"Setting up project for development":<{TP}}', end='', flush=True)
    setup_script = project_root.joinpath('init.py')
    run_command(['python3', str(setup_script), 'debug'], cwd=project_root)
    print('OK')

    print()
    print('Next setup your poetry virtual environment with:\n'
          'poetry env use ~/.pyenv/versions/3.7.3/bin/python\n'
          'poetry install --no-root')
    print()
    print('Build the project before running the server with:\n'
          'poetry run task build')
