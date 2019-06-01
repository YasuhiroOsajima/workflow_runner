#!/usr/bin/env python3
"""
Parse playbook structure and extract local variables.
"""

import yaml


def get_defined_variable_keys(playbook_path: str) -> dict:
    """ Extract local defined variables in target playbook. """

    set_stats = []
    set_fact = {}

    with open(playbook_path, 'r') as pbf:
        playbook: dict = yaml.load(stream=pbf, Loader=yaml.SafeLoader)[0]

        if 'vars' in playbook:
            defined_on_vars_header: set = set(playbook['vars'].keys())
        else:
            defined_on_vars_header = set()

        tasks: list = playbook['tasks']
        for idx, task in enumerate(tasks):
            if 'set_stats' in task:
                for stats_name in task['set_stats']['data'].keys():
                    set_stats.append(stats_name)

            defined_fact = set()
            if 'set_fact' in task:
                for fact_name in task['set_fact'].keys():
                    defined_fact.add(fact_name)

            set_fact[idx]: set = defined_fact

    return {'set_stats': set_stats, 'set_fact': set_fact,
            'vars': defined_on_vars_header}


def _is_variable(value) -> bool:
    """ argument is `str` type or `bool` type. """
    value_str: str = str(value)
    return '{{' in value_str and '.' not in value_str


def _get_variable_name(value: str) -> set:
    necessary = set()
    for sp_word in value.split('{{ '):
        if ' }}' in sp_word:
            necessary.add(sp_word.split(' }}')[0])

    return necessary


def _parse_task_dick(task_dict: dict, necessary: set) -> set:
    for val in task_dict.values():
        if isinstance(val, dict):
            necessary = necessary | _parse_task_dick(val, necessary)
        elif isinstance(val, str):
            if _is_variable(val):
                necessary = necessary | _get_variable_name(val)
        else:
            pass

    return necessary


def get_necessary_variable_keys(playbook_path: str) -> tuple:
    """
    Search and collect necessary variable keys in playbook.
    """

    with open(playbook_path, 'r') as pbp:
        playbook: dict = yaml.load(stream=pbp, Loader=yaml.SafeLoader)

    necessary_keys_at_started = set()
    necessary_keys_in_tasks = {}
    playbook_dict: dict = playbook[0]
    for key, sub_dict in playbook_dict.items():
        if key in ('vars', 'environment'):
            for value in sub_dict.values():
                if _is_variable(value):
                    necessary_keys_at_started = \
                        necessary_keys_at_started | _get_variable_name(value)

        if 'tasks' in key:
            # `tasks` is list of task dictionary.

            for idx, task_dict in enumerate(sub_dict):
                necessary_in_task = set()
                necessary_keys_in_tasks[idx] = \
                    _parse_task_dick(task_dict, necessary_in_task)

    return necessary_keys_at_started, necessary_keys_in_tasks
