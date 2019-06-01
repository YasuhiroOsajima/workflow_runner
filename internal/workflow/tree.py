#!/usr/bin/env python3
"""
Tree structure generator for workflow parser.
"""

import glob
import pathlib

from internal.playbook import parser

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


class Node:
    """
    workflow job_template node in workflow tree.
    """

    def __init__(self, node_id: int, node_name: str, playbook_path: str):
        self.node_id = node_id
        self.node_name = node_name
        self.playbook_path = playbook_path

        # child job_template list.
        self.success = []
        self.failed = []
        self.always = []

        # extra_vars at this job_template stage.
        self.before_extra_vars = {}
        self.define_stats = {}
        self.define_fact = {}
        self.define_vars_header = set()
        self.after_extra_vars = {}

    def _set_job_extra_vars(self, extra_vars_arg: dict = None, parent=None):
        extra_vars_dict = {}

        if parent:
            extra_vars_dict.update(parent.after_extra_vars)
        else:
            if extra_vars_arg:
                extra_vars_dict.update(extra_vars_arg)

        self.before_extra_vars = extra_vars_dict

    def _set_define_vars(self):
        defined: dict = parser.get_defined_variable_keys(self.playbook_path)
        stats: list = defined['set_stats']
        fact: dict = defined['set_fact']
        self.define_vars_header: set = defined['vars']
        # `fact` is dictionary to contain defined variables.
        # These dict's keys mean defined task timing in the playbook.
        # And the values mean defined variables name.

        if stats:
            self.define_stats = {key: None for key in stats}

        if [v_key for v_key in fact.values() if v_key]:
            self.define_fact = fact

    def _set_dry_run_after_extra_vars(self):
        self.after_extra_vars.update(self.before_extra_vars)
        self.after_extra_vars.update(self.define_stats)

    def prepare_job_node(self, extra_vars_arg: dict = None,
                         parent_node=None):
        """ This method is always called for top job_template """

        self._set_job_extra_vars(extra_vars_arg, parent_node)
        self._set_define_vars()
        # Non top job_template node's `self.before_extra_vars`
        # will be replaced to parent's after extra_vars
        # in ahead of job running process.
        # And `self.after_extra_vars` will be set at after job running process.

    def prepare_job_node_dry_run(self, extra_vars_arg: dict = None,
                                 parent_node=None):
        """ Set job_template node's all of data for dry run. """

        self._set_job_extra_vars(extra_vars_arg, parent_node)
        self._set_define_vars()
        self._set_dry_run_after_extra_vars()

    def set_before_extra_vars(self, parent_after_extra_vars: dict):
        """ setter for Node's `before_extra_vars` """
        self.before_extra_vars = parent_after_extra_vars

    def set_after_extra_vars(self, after_extra_vars: dict):
        """ setter for Node's `after_extra_vars` """
        self.after_extra_vars = after_extra_vars

    def add_parent_success(self, parent):
        """ Add target Node to parent Node's `success` child list. """
        parent.success.append(self)

    def add_parent_failed(self, parent):
        """ Add target Node to parent Node's `failed` child list. """
        parent.failed.append(self)

    def add_parent_always(self, parent):
        """ Add target Node to parent Node's `always` child list. """
        parent.always.append(self)


def generate_workflow_tree(workflow: list, dry_run: bool,
                           extra_vars_arg: dict) -> Node:
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

    top_node: Node = parse_job_dict(initial_job_template, stack, node_id,
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
    """
    Create each job's Node and chain to it's parent Node.
    """

    # nested workflow yaml is an future issue.
    ## execute_available = {'job_template', 'workflow'}
    execute_available = {'job_template'}
    success_keyword = {'success'}
    failed_keyword = {'failed'}
    always_keyword = {'always'}

    top_node = None
    node_id += 1

    # Get this job's executable keyword. Maybe `job_template`.
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
    node = Node(node_id, job_template_name, playbook_path)
    if node_id == 1:
        top_node = node

        if dry_run:
            node.prepare_job_node_dry_run(extra_vars_arg=extra_vars_arg)
        else:
            node.prepare_job_node(extra_vars_arg=extra_vars_arg)
    else:
        parent_node: Node = stack[-1]

        if dry_run:
            node.prepare_job_node_dry_run(parent_node=parent_node)
        else:
            node.prepare_job_node(parent_node=parent_node)

        if child_type in success_keyword:
            node.add_parent_success(parent_node)
        elif child_type in failed_keyword:
            node.add_parent_failed(parent_node)
        elif child_type in always_keyword:
            node.add_parent_failed(parent_node)
        else:
            raise ParseFailed("Invalid keyword specified: `{}`"
                              .format(child_type))

    stack.append(node)
    for state, child_list in job_dict.items():
        if state in success_keyword | failed_keyword | always_keyword:
            for child_dict in child_list:
                parse_job_dict(child_dict, stack, node_id, child_type=state,
                               dry_run=dry_run)

    stack.pop()

    return top_node
