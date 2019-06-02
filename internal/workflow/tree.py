#!/usr/bin/env python3
"""
Tree structure generator for workflow parser.
"""

import glob
import pathlib

from internal.workflow import node

# resource file path from project top directory.
JOB_TEMPLATE_DIR = 'resource_files/job_template'


class ParseFailed(Exception):
    """
    Parsing workflow structure failed.
    """

    def __init__(self, message):
        super(ParseFailed, self).__init__()
        self.message = message

    def __str__(self):
        return repr(self.message)


def generate_workflow_tree(workflow: list, dry_run: bool,
                           extra_vars_arg: dict) -> node.Node:
    """
    arg 'workflow' ->
    [
        {
            "job_template": "sample_job1",
            "success": [
                {
                    "job_template": "sample_job2",
                    "success": [
                        {
                            "job_template": "sample_job3"
                        }
                    ]
                }
            ]
        }
    ]
    """

    stack = []
    node_id = 0
    initial_job_template: dict = workflow[0]

    top_node: node.Node = parse_job_dict(initial_job_template, stack, node_id,
                                         child_type=None, dry_run=dry_run,
                                         extra_vars_arg=extra_vars_arg)
    if not top_node:
        raise ParseFailed('Top level job_template not found '
                          'in target workflow file.')

    return top_node


def _get_playbook_file_path(job_template_name: str) -> str:
    top_dir: pathlib.PosixPath = \
        pathlib.Path(__file__).resolve().parent.parent.parent
    job_template_dir_path = \
        str(top_dir / "{}/**/{}.y*".format(JOB_TEMPLATE_DIR,
                                           job_template_name))
    match: list = glob.glob(job_template_dir_path, recursive=True)
    if not match:
        raise ParseFailed("Job_template file not found "
                          "by resource files directory. "
                          "job_template: `{}`".format(job_template_name))

    playbook_path: str = match[0]
    return playbook_path


def parse_job_dict(job_dict: dict, stack: list, node_id: int,
                   child_type: str = None, dry_run: bool = False,
                   extra_vars_arg: dict = None):
    """ Create each job's Node and chain to it's parent Node."""

    top_node = None
    node_id += 1

    # Get this job stage's executable keyword. Maybe `job_template`.
    # nested workflow yaml is an future issue.
    # execute_available = {'job_template', 'workflow'}
    execute_available = {'job_template'}

    executable_keywords = execute_available & set(job_dict.keys())
    if len(executable_keywords) != 1:
        raise ParseFailed("Invalid executable_keywords: `{}`"
                          .format(executable_keywords))

    keyword: str = list(executable_keywords)[0]

    # Get this stage's job_template name.
    # Currently, nested workflow is not supported.
    job_template_name: str = \
        job_dict[keyword]  # Target job's `job_template` playbook name.
    playbook_path: str = _get_playbook_file_path(job_template_name)

    # Parse and prepare job_template.
    # And go to next stage by Depth first search.
    _node = node.Node(node_id, job_template_name, playbook_path)
    if node_id == 1:
        top_node = _node
        _node.prepare_job_node(dry_run, extra_vars_arg=extra_vars_arg)
    else:
        parent_node: node.Node = stack[-1]
        _node.prepare_job_node(dry_run, parent_node=parent_node,
                               case_type=child_type)

        if node.SwitchJobResult.is_success(child_type):
            _node.add_parent_success(parent_node)
        elif node.SwitchJobResult.is_failed(child_type):
            _node.add_parent_failed(parent_node)
        elif node.SwitchJobResult.is_always(child_type):
            _node.add_parent_always(parent_node)
        else:
            raise ParseFailed("Invalid keyword specified: `{}`"
                              .format(child_type))

    # Move forward to each result next job stage.
    stack.append(_node)
    for state, child_list in job_dict.items():
        if node.SwitchJobResult.is_result_keyword(state):
            for child_dict in child_list:
                parse_job_dict(child_dict, stack, node_id, child_type=state,
                               dry_run=dry_run)

    stack.pop()

    return top_node
