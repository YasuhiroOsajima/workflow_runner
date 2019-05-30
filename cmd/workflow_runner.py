#!/usr/bin/env python3
"""
$ python3 workflow_runner.py 'workflow file path'
"""

import argparse

from internal import auth_info as aui
from internal import subcommand as com


def _arg_parse() -> dict:
    usage = ("""
  Ansible workflow runner on local command line.

  Please use this command as follows:
    $ python3 %(prog)s `workflow file path` -i `inventory file path` (--ask-pass or --private-key `file path`)

  If you want to check settings correctness, you can use `dry_run` mode.
    $ python3 %(prog)s `workflow file path` -i `inventory file path` --dry_run
  
""")

    parser = argparse.ArgumentParser(usage=usage, add_help=True)

    parser.add_argument('workflow_file',
                        type=str,
                        help='target workflow file path.')
    parser.add_argument('-i', '--inventory_file',
                        type=str,
                        help='target inventory file path.')

    parser.add_argument('-u', '--user',
                        type=str,
                        help="ansible's `ansible_ssh_user` option. "
                             "Default is current user.")
    parser.add_argument('--port',
                        type=int,
                        help="ansible's `ansible_port` option. "
                             "Default is `22`.")
    parser.add_argument('--become-user',
                        type=str,
                        help="ansible's `ansible_become_user` option. "
                             "Default is `root`.")
    parser.add_argument('-K', '--ask-become-pass',
                        action='store_true',
                        help="ansible's `ansible_become_pass` option.")

    auth_method = parser.add_mutually_exclusive_group(required=True)
    auth_method.add_argument('-k', '--ask-pass',
                             action='store_true',
                             help='Password for running ansible playbook. '
                                  'Please specify `--ask-pass` '
                                  'or `--private-key`')
    auth_method.add_argument('--private-key',
                             type=str,
                             help='Private key file path '
                                  'for running ansible playbook. '
                                  'Please specify `--ask-pass` '
                                  'or `--private-key`')
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

    return {'dry_run': args.dry_run,
            'workflow_file': args.workflow_file,
            'inventory_file': args.inventory_file,
            'auth_extra_vars': auth_extra_vars}


def main():
    """
    Run workflow.
    """

    args: dict = _arg_parse()
    dry_run: bool = args['dry_run']
    workflow_file: str = args['workflow_file']
    inventory_file: str = args['inventory_file']
    auth_extra_vars: str = args['auth_extra_vars']

    com.execute(dry_run, workflow_file, inventory_file, auth_extra_vars)


if __name__ == '__main__':
    main()
