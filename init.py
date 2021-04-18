#!/usr/bin/env python3

__author__ = 'Adrian Geuß'
__contact__ = 'adrian@viagis.app'
__copyright__ = 'Copyright 2021 VIAGIS'
__project__ = 'django-starter'

import re
import shutil
import string
from argparse import ArgumentParser
from enum import Enum
from pathlib import Path
from random import SystemRandom
from sys import stderr
from typing import Optional


class Environment(Enum):
    debug = 'debug'
    staging = 'staging'
    production = 'production'


ENVIRONMENT_OPTIONS = [it for it in Environment]
ENVIRONMENT_OPTIONS_NAMES = '|'.join(it.name for it in ENVIRONMENT_OPTIONS)

SCRIPT_DIR = Path(__file__).absolute().parent
ENV_FILE_NAME = '.env'
SECRET_TXT_FILE_NAME = 'secret.txt'
SETTINGS_LOCAL_FILE_NAME = 'settings_local.py'


def fatal_error(message: str, exit_code: int = 1):
    print(message, file=stderr)
    exit(exit_code)


def find_django_dir() -> Optional[Path]:
    for item in SCRIPT_DIR.iterdir():
        if not item.is_dir() or item.name.startswith('.'):
            continue

        if next(item.glob('manage.py'), None):
            return item

    return None


def find_django_settings_dir(directory: Path) -> Optional[Path]:
    for item in directory.iterdir():
        if not item.is_dir():
            continue

        if next(item.glob('settings.py'), None):
            return item

    return None


def update_env_file(file_path: Path, env: Environment, dry_run: bool = False) -> bool:
    env_re = re.compile(r'ENVIRONMENT=\"(?P<environment>.+)\"')

    processed_lines = []
    with file_path.open() as f:
        lines = f.readlines()

        for line in lines:
            new_line = line
            match = env_re.search(line)
            if match:
                env_name = match.groupdict()['environment']
                if env_name != env.name:
                    start, stop = match.regs[1]
                    new_line = line[:start] + env.name + line[stop:]

            processed_lines.append(new_line)

        updated = lines != processed_lines

    if updated and not dry_run:
        with file_path.open('w') as f:
            f.writelines(processed_lines)

    return updated


def update_secret_txt(file_path: Path, length: int):
    sys_random = SystemRandom()
    with file_path.open('w+') as f:
        letters = string.ascii_letters + string.digits + string.punctuation
        f.write(''.join(sys_random.choices(letters, k=length)))


if __name__ == '__main__':
    parser = ArgumentParser(description='Creates the necessary files for running the project.')
    parser.add_argument('environment', type=str, help=f'Project environment ({ENVIRONMENT_OPTIONS_NAMES})')
    parser.add_argument('-l', '--length', type=int, default=512, help='Length of the generated secret')
    parser.add_argument('-f', '--force', action='store_true', help='Overwrite existing secret.txt')
    args = parser.parse_args()

    secret_length = args.length
    force = args.force
    environment_name = args.environment
    environment: Environment = next((it for it in ENVIRONMENT_OPTIONS if it.name == environment_name), None)
    if environment not in ENVIRONMENT_OPTIONS:
        fatal_error(f'Invalid environment specified! ({ENVIRONMENT_OPTIONS_NAMES})')

    env_file = SCRIPT_DIR.joinpath(ENV_FILE_NAME)

    django_dir = find_django_dir()
    if not django_dir:
        fatal_error('Unable to find django dir.')

    settings_dir = find_django_settings_dir(django_dir)
    if not settings_dir:
        fatal_error('Unable to find django project dir.')

    secret_txt = settings_dir.joinpath(SECRET_TXT_FILE_NAME)
    settings_local = settings_dir.joinpath(SETTINGS_LOCAL_FILE_NAME)

    padding = max(len(str(it.relative_to(SCRIPT_DIR))) for it in [
        env_file,
        secret_txt,
        settings_local,
    ]) + 5

    print(f'{str(env_file.relative_to(SCRIPT_DIR)):<{padding}}', end='')
    if env_file.exists():
        if not env_file.is_file():
            fatal_error(f'{ENV_FILE_NAME} is not a file!')

        if update_env_file(env_file, environment):
            print('UPDATED')
        else:
            print('OK')
    else:
        env_file_sample = SCRIPT_DIR.joinpath('.env.example')
        if not env_file_sample.is_file():
            fatal_error(f'Missing file: {env_file_sample}')

        shutil.copy(env_file_sample, env_file)
        update_env_file(env_file, environment)
        print('CREATED')

    print(f'{str(secret_txt.relative_to(SCRIPT_DIR)):<{padding}}', end='')
    if secret_txt.exists():
        if not secret_txt.is_file():
            fatal_error(f'{SECRET_TXT_FILE_NAME} is not a file!')

        if force:
            update_secret_txt(secret_txt, secret_length)
            print('CREATED')
        else:
            print('OK')
    else:
        secret_txt.touch()
        update_secret_txt(secret_txt, secret_length)
        print('CREATED')

    print(f'{str(settings_local.relative_to(SCRIPT_DIR)):<{padding}}', end='')
    if settings_local.exists():
        if not settings_local.is_file():
            fatal_error(f'{SETTINGS_LOCAL_FILE_NAME} is not a file!')

        print('OK')
    else:
        settings_local_example = settings_dir.joinpath('settings_local.example.py')
        if not settings_local_example.is_file():
            fatal_error(f'Missing file: {settings_local_example}')

        shutil.copy(settings_local_example, settings_local)
        print('CREATED')

    if environment == Environment.debug:
        print(f'{"Git Hooks":<{padding}}', end='')

        project_root = SCRIPT_DIR
        git_hook_dir = project_root.joinpath('.git', 'hooks')
        hook_dir = project_root.joinpath('git-hooks')
        if not git_hook_dir.is_dir():
            git_hook_dir.mkdir()
        if not hook_dir.is_dir():
            fatal_error('Unable to find git hooks in project!')

        created = False
        for script_file in hook_dir.glob('*.sh'):
            dest_file = git_hook_dir.joinpath(script_file.name.replace(script_file.suffix, ''))
            if not dest_file.is_file():
                with script_file.open() as f:
                    script_contents = f.read()

                from os import environ

                script_contents = f"""#!/usr/bin/env bash

export PATH="$PATH:{environ.get('PATH')}"

{script_contents}"""
                with dest_file.open('w+') as f:
                    f.write(script_contents)

                created = True

            permissions = 0o755
            if dest_file.stat().st_mode != permissions:
                dest_file.chmod(permissions)

        print('CREATED' if created else 'OK')
