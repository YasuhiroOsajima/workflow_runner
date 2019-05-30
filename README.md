# Ansible workflow runner

## What is this.
Ansible workflow runner on local command line.  
This tool is to run workflow template without Ansible AWX server.  

Please use this command as follows:
```
$ python3 workflow_runner.py `workflow file path` -i `inventory file path` (--ask-pass or --private-key `file path`)
```

If you want to check settings correctness, you can use `dry_run` mode.
```
$ python3 workflow_runner.py `workflow file path` -i `inventory file path` --dry_run
```

positional arguments:
  workflow_file         target workflow file path.

optional arguments:
  -h, --help            show this help message and exit
  -i INVENTORY_FILE, --inventory_file INVENTORY_FILE
                        target inventory file path.
  -u USER, --user USER  ansible's `ansible_ssh_user` option. Default is
                        current user.
  --port PORT           ansible's `ansible_port` option. Default is `22`.
  --become-user BECOME_USER
                        ansible's `ansible_become_user` option. Default is
                        `root`.
  -K, --ask-become-pass
                        ansible's `ansible_become_pass` option.
  -k, --ask-pass        Password for running ansible playbook. Please specify
                        `--ask-pass` or `--private-key`
  --private-key PRIVATE_KEY
                        Private key file path for running ansible playbook.
                        Please specify `--ask-pass` or `--private-key`
  --dry_run             Run with `dry_run` mode.


## Setup
```
$ pip3 install requirements.txt
$ pip3 install -e .
```

## Attention
- job_template names in workflow YAML file have to be same as job_template YAML file name which without '.yml'.
- YAML structure of workflow file have to be following Ansible AWX style:
  ```
  - job_template: sample_job1
    success:
      - job_template: sample_job2
        success:
          - job_template: sample_job3
  ```
  
  You can not use other type style like this:
  ```
  - failure_nodes:
  - inventory_source: 42
  job_template: 45
  success_nodes:
  - always_nodes:
    - job_template: 55
      success_nodes:
      - job_template: 44
    project: 40
  ```
  
## Issue
- all style workflow support.
- not supported workflow in workflow yet.
- not supported cover roles in job_template yet.
- simultaneous multi job execution if parallel case wrote in workflow.