#!/usr/bin/env python3

__author__ = 'Adrian Geuß'
__contact__ = 'adrian@viagis.app'
__copyright__ = 'Copyright 2021 VIAGIS'
__project__ = 'django-starter'

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Optional, List

from fabric import Connection, Config
from invoke import UnexpectedExit, run

from django_starter.enums import Environment

ENVIRONMENT_OPTIONS = [Environment.staging, Environment.production]
ENVIRONMENT_OPTIONS_NAMES = '|'.join(it.name for it in ENVIRONMENT_OPTIONS)

SCRIPT_DIR = Path(__file__).absolute().parent
PROJECT_ROOT = SCRIPT_DIR.parent
DJANGO_DIR = PROJECT_ROOT.joinpath('django')


@dataclass
class DeploymentConfig:
    hostname: str
    project_root: str
    django_root: str

    def connection(self, config: Optional[Config] = None) -> Connection:
        return Connection(self.hostname, config=config)


def fatal_error(message: str, stop: bool = True):
    print(message, file=sys.stderr)
    if stop:
        exit(1)


def get_config(env: Environment) -> DeploymentConfig:
    config_file_path = Path(DJANGO_DIR.joinpath(f'deploy_{env.name}.json'))
    if not config_file_path.exists():
        fatal_error(f'Config file missing for environment: {config_file_path.relative_to(DJANGO_DIR)}')

    with config_file_path.open('r') as f:
        data = json.load(f)

    return DeploymentConfig(
        hostname=data['hostName'],
        project_root=data['projectDir'],
        django_root=data['djangoDir'])


# Fabric Functions

def disk_free(connection: Connection) -> str:
    command = 'df -h / | tail -n1 | awk "{print $5}"'
    return connection.run(command, hide=True).stdout.strip()


def path_exists(connection: Connection, path: str) -> bool:
    try:
        return connection.run(f'ls "{path}"', hide=True).ok
    except UnexpectedExit:
        return False


def sync_paths(connection: Connection, files: List[Path], source_dir: Path, remote_dir: str, dry_run: bool):
    for path in files:
        remote_path = f'{remote_dir}/{path.relative_to(source_dir)}'
        print(f'{path} -> {remote_path}')
        if not dry_run:
            # Does not create subdirectories automatically -.-
            connection.put(path, remote=remote_path)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Django Deployment Script')
    parser.add_argument('environment', type=str, help=f'Target environment ({ENVIRONMENT_OPTIONS_NAMES})')
    parser.add_argument('-n', '--dry-run', action='store_true')
    parser.add_argument('-v', '--verbose', action='store_true')
    args = parser.parse_args()

    environment_name = args.environment
    environment: Environment = next((it for it in ENVIRONMENT_OPTIONS if it.name == environment_name), None)
    if environment not in ENVIRONMENT_OPTIONS:
        fatal_error(f'Invalid environment specified! ({ENVIRONMENT_OPTIONS_NAMES})')
    dry_run_mode = args.dry_run
    verbose = args.verbose

    print(f'Loading config for: {environment.value}')
    dc = get_config(environment)
    print(f'Host: {dc.hostname}')
    print(f'Project: {dc.project_root}')
    print(f'Django: {dc.django_root}')
    c = dc.connection()

    # Pre Checks
    # print(f'Disk space on target system: {disk_free(c)}')
    if not path_exists(c, dc.project_root):
        fatal_error(f'VHost root does not exist at: {dc.project_root}')
    if not path_exists(c, dc.django_root):
        if dry_run_mode:
            fatal_error(f'Django root does not exist at: {dc.django_root}', stop=False)
        else:
            if not c.run(f'mkdir "{dc.django_root}"').ok:
                fatal_error(f'Django root does not exist at: {dc.django_root}')

    if not dry_run_mode:
        print()
        choice = input(f'Continue deployment to {c.host}? (Y/n) ')
        if choice.lower() == 'n':
            fatal_error('Deployment aborted.')

    # Deployment
    print('Starting Deployment.')
    print('Syncing Files...')
    git_tracked_path = run(f'cd {PROJECT_ROOT} && git ls-files', hide=True).stdout
    file_paths = [PROJECT_ROOT.joinpath(it) for it in git_tracked_path.split('\n') if it.strip()]
    api_doc_files = [it for it in DJANGO_DIR.glob('api_*.html')]
    assert api_doc_files, 'Missing compiled api doc files!'
    file_paths += api_doc_files
    invalid_paths = [str(it) for it in file_paths if not it.exists()]
    if invalid_paths:
        invalid_paths_formatted = '\n'.join(invalid_paths)
        fatal_error(f'Some paths are invalid:\n{invalid_paths_formatted}')

    file_paths = sorted([it.relative_to(PROJECT_ROOT) for it in file_paths])
    with NamedTemporaryFile() as whitelist_file:
        whitelist_file.write('\n'.join(str(it) for it in file_paths).encode())
        whitelist_file.seek(0)
        exclude_file = PROJECT_ROOT.joinpath(".rsync", "exclude")

        if verbose:
            print(f'--file-from={whitelist_file.name}')
            whitelist_file_content = whitelist_file.read()
            print(whitelist_file_content.decode())
            whitelist_file.seek(0)

            print(f'--exclude-from={exclude_file}')
            with exclude_file.open('r') as f:
                print(f.read())

        rsync_args = [f'--files-from={whitelist_file.name}']
        rsync_args += [f'--exclude-from={exclude_file}']
        rsync_command = f'rsync -avh{"n" if dry_run_mode else ""} ' \
                        f'{" ".join(rsync_args)} {PROJECT_ROOT} {dc.hostname}:{dc.project_root}'

        if verbose:
            print(rsync_command)
        c.local(rsync_command)

        ssh_command = f'ssh -A {dc.hostname} "bash --login -c \\"' \
                      f'cd {dc.project_root}' \
                      ' && poetry install --no-dev && poetry check -q' \
                      ' && cd django' \
                      ' && poetry run python manage.py migrate' \
                      ' && poetry run python manage.py compilemessages' \
                      ' && poetry run python manage.py collectstatic --noinput' \
                      ' && touch django_starter/wsgi.py || (echo \'touch failed\' && exit 1)' \
                      '\\""'
        if verbose:
            print(ssh_command)

        if not dry_run_mode:
            c.local(ssh_command)
        print('Finished Deployment.')
