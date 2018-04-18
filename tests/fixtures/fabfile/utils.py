# coding: utf-8

import os

from fabric.api import task, abort, sudo, run, puts, local, settings
from fabric.state import env
from fabric.contrib.files import exists

@task
def sudo_hostname():
    puts("sudo hostname for [%(host_string)s]" % env)
    sudo('hostname')

@task
def sudo_ls():
    puts("sudo ls for [%(host_string)s]" % env)
    sudo('ls -lta')

@task
def run_hostname():
    puts("run hostname for [%(host_string)s]" % env)
    run('hostname')

@task
def run_ls():
    puts("run ls for [%(host_string)s]" % env)
    run('ls -lta')

@task
def local_hostname():
    puts("local hostname")
    local('hostname')

@task
def local_ls():
    puts("local ls")
    local('ls -lta')
