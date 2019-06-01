#!/usr/bin/env python3
"""
$ python3 workflow_runner.py 'workflow file path'
"""

import argparse
import json
import sys

import yaml

from internal import auth_info as aui
from internal import subcommand as com


def _parse_extra_vars(extra_vars: str) -> dict:
    def _is_json(text: str) -> bool:
        try:
            json.loads(text)
        except json.JSONDecodeError:
            return False
        except ValueError:
            return False

        return True

    if not extra_vars:
        extra_vars_arg: dict = {}

    elif extra_vars.startswith('@'):
        with open(extra_vars[1:], 'r') as evf:
            extra_vars_arg: dict = yaml.load(stream=evf, Loader=yaml.SafeLoader)

    elif _is_json(extra_vars):
        extra_vars_arg: dict = json.loads(extra_vars)

    else:
        extra_vars_arg: dict = yaml.load(extra_vars, Loader=yaml.SafeLoader)
        if not isinstance(extra_vars_arg, dict):
            print()
            print('<< Invalid argument. >>')
            print('Specified `extra_vars` format is invalid.')
            sys.exit(2)

    return extra_vars_arg


def _arg_parse() -> dict:
    usage = ("""
  Ansible workflow runner on local command line.

  Please use this command as follows:
    $ python3 %(prog)s `workflow file path`\
 -i `inventory file path`\
 (--ask-pass or --private-key `file path`)\
 [-e '@extra-vars_file_path']

  If you want to check settings correctness, you can use `dry_run` mode.
    $ python3 %(prog)s `workflow file path`\
 -i `inventory file path`\
 --dry_run\
 [-e '@extra-vars_file_path']
  
""")

    parser = argparse.ArgumentParser(usage=usage, add_help=True)

    parser.add_argument('workflow_file',
                        type=str,
                        help='Target workflow file path.')
    parser.add_argument('-i', '--inventory_file',
                        type=str,
                        help='Target inventory file path.')

    parser.add_argument('-u', '--user',
                        type=str,
                        help="Ansible's `ansible_ssh_user` option. "
                             "Default is current user.")
    parser.add_argument('--port',
                        type=int,
                        help="Ansible's `ansible_port` option. "
                             "Default is `22`.")
    parser.add_argument('--become-user',
                        type=str,
                        help="Ansible's `ansible_become_user` option. "
                             "Default is `root`.")
    parser.add_argument('-K', '--ask-become-pass',
                        action='store_true',
                        help="Ansible's `ansible_become_pass` option.")
    parser.add_argument('-e', '--extra-vars',
                        type=str,
                        help="Ansible's extra_vars option. "
                             "Default is `None`.")

    auth_method = parser.add_mutually_exclusive_group(required=True)
    auth_method.add_argument('-k', '--ask-pass',
                             action='store_true',
                             help='Password auth enable '
                                  'for ansible remote login. '
                                  'Please specify this or `--private-key`.')
    auth_method.add_argument('--private-key',
                             type=str,
                             help='Private key file path '
                                  'for ansible remote login. '
                                  'Please specify this or `--ask-pass`.')
    auth_method.add_argument('--dry_run',
                             action='store_true',
                             help='Run with `dry_run` mode.')

    args = parser.parse_args()

    auth_info: aui.AuthInfo = aui.AuthInfo(args.ask_pass,
                                           args.private_key,
                                           args.user,
                                           args.port,
                                           args.become_user,
                                           args.ask_become_pass)
    auth_extra_vars: str = auth_info.generate_auth_extra_vars()

    extra_vars: str = args.extra_vars
    extra_vars_dict: dict = _parse_extra_vars(extra_vars)

    return {'dry_run': args.dry_run,
            'workflow_file': args.workflow_file,
            'inventory_file': args.inventory_file,
            'extra_vars': extra_vars_dict,
            'auth_extra_vars': auth_extra_vars}


def main():
    """
    Run workflow.
    """

    args: dict = _arg_parse()
    dry_run: bool = args['dry_run']
    workflow_file: str = args['workflow_file']
    inventory_file: str = args['inventory_file']
    extra_vars: dict = args['extra_vars']
    auth_extra_vars: str = args['auth_extra_vars']

    com.execute(dry_run, workflow_file, inventory_file, auth_extra_vars,
                extra_vars)


if __name__ == '__main__':
    main()
