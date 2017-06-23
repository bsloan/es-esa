from datetime import datetime
from contextlib import contextmanager
from fabric.api import *

env.user = "ubuntu"
env.deployment = "{0}-{1}".format(env.version, datetime.now().strftime("%Y-%m-%d-%H-%M-%S"))
env.project_root = "/opt/es-esa/{0}".format(env.deployment)
env.activate = "source {0}/venv/bin/activate".format(env.project_root)
env.version = env.branch

@contextmanager
def virtualenv():
    with cd(env.project_root):
        with prefix(env.activate):
            yield


def install_code(branch):
    puts("Installing code ...")
    with cd(env.project_root):
        run("git clone -b {0} https://github.com/bsloan/es-esa.git".format(branch))


def setup_virtualenv():
    puts("Creating virtualenv ...")
    with cd(env.project_root):
        run("virtualenv --prompt='(es-esa-web)' venv")
    with virtualenv():
        run("pip install --upgrade pip")
        run("pip install -r {0}/es-esa/requirements.txt".format(env.project_root))


@task
def install_system_dependencies():
    puts("Installing pip, virtualenv, git ...")
    sudo("apt-get purge python-pip")
    run("curl https://bootstrap.pypa.io/get-pip.py | sudo python")
    sudo("apt-get install python-dev build-essential")
    sudo("pip install --upgrade pip")
    sudo("pip install --upgrade virtualenv")
    sudo("apt-get install git")


@task
def web():
    puts("Deploying API ...")

    run("sudo mkdir -p {0}".format(env.project_root))
    run("sudo chown {0} {1}".format(env.user, env.project_root))

    install_code(env.branch)
    setup_virtualenv()


@task
def restart_api():
    pass  # TODO: stop the API process (if it's already running) and start it up again
