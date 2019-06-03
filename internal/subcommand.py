#!/usr/bin/env python3
"""
routing sub command process.
"""

from datetime import datetime, timezone
import os
import pathlib
import re

import texttable as ttb

from internal.workflow import parser as w_parser
from internal.workflow import runner as w_run

DEFAULT_DIR = '/tmp/workflow_runner'


def _prepare_work_directory(dir_path='') -> str:
    if not dir_path:
        dir_path = DEFAULT_DIR

    if not os.path.exists(dir_path):
        os.mkdir(dir_path)

    return dir_path


def _get_tty_width():
    tty_size = os.popen('stty size 2> /dev/null', 'r').read().split()
    if len(tty_size) != 2:
        return 0
    _, width = tty_size
    return int(width)


def _print_job_results(results: [w_run.JobRecord]):
    table = ttb.Texttable(max_width=_get_tty_width())

    table.set_deco(ttb.Texttable.HEADER |
                   ttb.Texttable.VLINES |
                   ttb.Texttable.BORDER)
    table.set_chars(['=',  # horizontal
                     ' ',  # vertical
                     ' ',  # corner
                     '='])  # header

    headers = ["id", "name", "type", "status", "created", "elapsed"]
    table.header(headers)
    table.set_cols_dtype(['t' for _ in headers])
    table.set_cols_align(['l' for _ in headers])

    for res in results:
        record = [res.job_id,
                  res.job_template_name,
                  res.type,
                  res.status,
                  res.get_created_time(),
                  res.get_elapsed()]
        table.add_row(record)

    print()
    print('------ Job results ------')
    job_results: str = \
        re.sub('^ ', '',
               table.draw().replace('\n ', '\n').replace('\r ', '\r'))
    print(job_results)
    print()


def _print_workflow_result(workflow_file: str, workflow_start: str,
                           workflow_status: str):
    table = ttb.Texttable(max_width=_get_tty_width())

    table.set_deco(ttb.Texttable.HEADER |
                   ttb.Texttable.VLINES |
                   ttb.Texttable.BORDER)
    table.set_chars(['=',  # horizontal
                     ' ',  # vertical
                     ' ',  # corner
                     '='])  # header

    headers = ["workflow_job_template", "created", "status"]
    table.header(headers)
    table.set_cols_dtype(['t' for _ in headers])
    table.set_cols_align(['l' for _ in headers])

    workflow_name: str = pathlib.Path(workflow_file).name
    table.add_row([workflow_name, workflow_start, workflow_status])

    print('------ Workflow process ended ------')
    workflow_results: str = \
        re.sub('^ ', '',
               table.draw().replace('\n ', '\n').replace('\r ', '\r'))
    print(workflow_results)
    print()


def _print_result(workflow_file: str, workflow_start: str,
                  workflow_status: str, job_results: [w_run.JobRecord]):
    _print_job_results(job_results)
    _print_workflow_result(workflow_file, workflow_start, workflow_status)


def execute(dry_run: bool, workflow_file: str, inventory_file: str,
            auth_extra_vars: str, extra_vars: dict):
    """
    Run sub command with switching 'dry_run' option.
    """

    work_dir: str = _prepare_work_directory()

    workflow_node: w_parser.WorkflowNode = w_parser.parse(workflow_file,
                                                          dry_run, extra_vars)
    workflow = w_run.WorkflowRunner(inventory_file)

    if dry_run:
        print()
        print('Check all variables are defined at running each job_template.')
        print('------')

        workflow.dry_run(workflow_node)

        print("Dry run complete.")
    else:
        workflow_start: str = \
            datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")

        job_result: [w_run.JobRecord] = workflow.run(workflow_node,
                                                     auth_extra_vars,
                                                     work_dir)

        workflow_status: str = job_result[-1].status
        _print_result(workflow_file, workflow_start, workflow_status,
                      job_result)
