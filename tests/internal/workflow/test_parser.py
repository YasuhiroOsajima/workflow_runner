#!/usr/bin/env python3
"""
Unit test for workflow parser.
"""

import unittest

from internal.workflow import tree


class TestWorkFlowParser(unittest.TestCase):
    def test_workflow_parse(self):
        workflow = [{'job_template': 'sample_job1',
                     'success': [{'job_template': 'sample_job2'}],
                     'always': [{'job_template': 'sample_job3'}]}]
        dry_run = True
        extra_vars_arg = {'sample_vars': 'sample'}

        top_node = tree.generate_workflow_tree(workflow, dry_run,
                                               extra_vars_arg)
        correct = 1
        self.assertEqual(top_node.node_id, correct)


if __name__ == '__main__':
    unittest.main()
