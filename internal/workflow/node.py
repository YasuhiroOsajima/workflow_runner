#!/usr/bin/env python3
"""
Node object for job_template information..
"""

from internal.playbook import parser


class SwitchJobResult:
    """ Check methods state keyword."""

    success_keyword = {'success'}
    failed_keyword = {'failed'}
    always_keyword = {'always'}

    @classmethod
    def is_success(cls, state: str):
        """ `state` is success """
        return state in cls.success_keyword

    @classmethod
    def is_failed(cls, state: str):
        """ `state` is failed """
        return state in cls.failed_keyword

    @classmethod
    def is_always(cls, state: str):
        """ `state` is always """
        return state in cls.always_keyword

    @classmethod
    def is_result_keyword(cls, state):
        """ `state` is in result keyword """
        result_keywords: set = (cls.success_keyword |
                                cls.failed_keyword |
                                cls.always_keyword)
        return state in result_keywords


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
        self.after_extra_vars_failed = {}

    def _set_job_extra_vars_run(self, parent=None,
                                extra_vars_arg: dict = None):
        extra_vars_dict = {}

        if parent:
            extra_vars_dict.update(parent.after_extra_vars)
        else:
            # Top level node case.
            if extra_vars_arg:
                # If `extra_vars` are given by command line args.
                extra_vars_dict.update(extra_vars_arg)

        # `extra_vars` at start of job_template executing.
        self.before_extra_vars = extra_vars_dict

    def _set_job_extra_vars_dry_run(self, parent=None,
                                    extra_vars_arg: dict = None,
                                    case_type: str = None):
        extra_vars_dict = {}

        if parent:
            if SwitchJobResult.is_success(case_type):
                extra_vars_dict.update(parent.after_extra_vars)
            else:
                # `failed` and `always` situation
                # doesn't include `set_stats` vars.
                extra_vars_dict.update(parent.after_extra_vars_failed)
        else:
            # Top level node case.
            if extra_vars_arg:
                # If `extra_vars` are given by command line args.
                extra_vars_dict.update(extra_vars_arg)

        # `extra_vars` at start of job_template executing.
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
        self.after_extra_vars_failed.update(self.before_extra_vars)

        self.after_extra_vars.update(self.define_stats)

    def prepare_job_node_run(self, parent_node=None,
                             extra_vars_arg: dict = None):
        """ This method is always called for top job_template """

        self._set_job_extra_vars_run(parent=parent_node,
                                     extra_vars_arg=extra_vars_arg)
        self._set_define_vars()
        # Non top job_template node's `self.before_extra_vars`
        # will be replaced to parent's after extra_vars
        # in ahead of job running process.
        # And `self.after_extra_vars` will be set at after job running process.

    def prepare_job_node_dry_run(self, parent_node=None,
                                 extra_vars_arg: dict = None,
                                 case_type: str = None):
        """
        Set job_template node's all of data for dry run.
        This method takes `extra_vars_arg` or `parent_node`.
        """

        self._set_job_extra_vars_dry_run(parent=parent_node,
                                         extra_vars_arg=extra_vars_arg,
                                         case_type=case_type)
        self._set_define_vars()
        self._set_dry_run_after_extra_vars()

    def prepare_job_node(self, dry_run: bool, parent_node=None,
                         extra_vars_arg: dict = None, case_type: str = None):
        """ This method is always called for top job_template """

        if dry_run:
            self.prepare_job_node_dry_run(parent_node, extra_vars_arg, case_type)
        else:
            self.prepare_job_node_run(parent_node, extra_vars_arg)

    def set_before_extra_vars(self, parent_node):
        """ setter for Node's `before_extra_vars` """
        parent_after_extra_vars: dict = parent_node.after_extra_vars
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
