# -*- coding: utf-8 -*-
# =-
# Copyright Solocal Group (2015)
#
# eureka@solocal.com
#
# This software is a computer program whose purpose is to provide a full
# featured participative innovation solution within your organization.
#
# This software is governed by the CeCILL license under French law and
# abiding by the rules of distribution of free software.  You can  use,
# modify and/ or redistribute the software under the terms of the CeCILL
# license as circulated by CEA, CNRS and INRIA at the following URL
# "http://www.cecill.info".
#
# As a counterpart to the access to the source code and  rights to copy,
# modify and redistribute granted by the license, users are provided only
# with a limited warranty  and the software's author,  the holder of the
# economic rights,  and the successive licensors  have only  limited
# liability.
#
# In this respect, the user's attention is drawn to the risks associated
# with loading,  using,  modifying and/or developing or reproducing the
# software by the user in light of its specific status of free software,
# that may mean  that it is complicated to manipulate,  and  that  also
# therefore means  that it is reserved for developers  and  experienced
# professionals having in-depth computer knowledge. Users are therefore
# encouraged to load and test the software's suitability as regards their
# requirements in conditions enabling the security of their systems and/or
# data to be ensured and,  more generally, to use and operate it in the
# same conditions as regards security.
#
# The fact that you are presently reading this means that you have had
# knowledge of the CeCILL license and that you accept its terms.
# =-

import csv
import os
import tarfile
import time
from contextlib import contextmanager
from functools import wraps
from optparse import OptionParser
from urlparse import urlparse

import eureka
import nagare
import posixpath
from configobj import ConfigObj
from fabric.api import (
    cd, env, execute, hosts, lcd, local, put, run, settings, sudo, task
)
from fabric.contrib import files
from eureka.domain import populate
from eureka.domain.populate import get_or_create_organization
from eureka.pkg import resource_filename
from eureka.infrastructure.unicode_csv import UnicodeDictReader
from nagare import database
from nagare.admin.db import read_options
from nagare.admin.serve import publisher_options_spec
from nagare.admin.util import read_application
from settings import demo, integration, localhost

root_dir = resource_filename('')


@task
def int():
    execute(integration)


def _get_config_filepath():
    return os.path.join(root_dir, 'etc', 'eureka.cfg')


@contextmanager
def dbcontext():
    for (database_settings, _) in read_options(
            True, [_get_config_filepath()], ValueError):
        database.set_metadata(*database_settings)
        with database.session.begin():
            yield


@contextmanager
def load_config(filepath):
    _, app, _, conf = read_application(filepath, ValueError)
    spec = ConfigObj({'DEFAULT': {'name': 'eureka'}})
    conf = ConfigObj(
        filepath,
        configspec=publisher_options_spec,
        interpolation='Template'
    )
    conf.merge(spec)
    yield conf


@task
def runserver():
    """Starts the server in standalone mode"""
    with lcd(root_dir):
        local('./bin/nagare-admin serve eureka')


# ================


def dest_env_initialized(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        assert env.hosts
        assert env.user
        assert env.application_dir
        return func(*args, **kwargs)
    return wrapper


@task
def deploy_integration():
    """Install application on integration platform"""
    execute(integration)
    execute(stop)
    execute(install)
    execute(start)


@task
def deploy_demo():
    """Install application on demo platform"""
    execute(demo)
    execute(stop)
    execute(install)
    execute(setup_demo_config)
    execute(start)


@task
def deploy_localhost():
    """Install application on local machine"""
    execute(localhost)
    execute(stop)
    execute(install)
    execute(start)


@hosts('localhost')
def distrib():
    """Create the application distrib"""
    with lcd(os.path.dirname(root_dir)):
        local('./sh/fetch-downloads.sh')
        archive = local('./sh/create-distrib.sh',
                        capture=True).splitlines()[-1]
        env.archive = archive


@task
@dest_env_initialized
def stop():
    """Stops the application"""
    with settings(warn_only=True):
        with cd(env.application_dir):
            eureka_egg_dir = run(
                './bin/python -c "import pkg_resources; '
                'print pkg_resources.get_distribution(\'eureka\').location"')
            run('./bin/supervisorctl -c '
                '{eureka_egg_dir}/etc/supervisord.conf shutdown'.format(
                    eureka_egg_dir=eureka_egg_dir))


@task
@dest_env_initialized
def start():
    """Starts the application"""
    with settings(warn_only=True):
        if files.exists('/usr/bin/systemctl'):
            sudo('sudo systemctl restart httpd')
        elif files.exists('/etc/init.d/apache2'):
            sudo('sudo /etc/init.d/apache2 restart')
        elif files.exists('/etc/init.d/httpd'):
            sudo('/etc/init.d/httpd restart')

    with cd(env.application_dir):
        eureka_egg_dir = run(
            './bin/python -c "import pkg_resources; '
            'print pkg_resources.get_distribution(\'eureka\').location"')
        run('./bin/supervisord -c '
            '{eureka_egg_dir}/etc/supervisord.conf'.format(
                eureka_egg_dir=eureka_egg_dir))
        time.sleep(3)
        run("./bin/supervisorctl -c {eureka_egg_dir}/etc/supervisord.conf "
            "start eureka mailrelay".format(eureka_egg_dir=eureka_egg_dir))


@dest_env_initialized
def install():
    """Install the application"""

    # === Stackless Install === #

    if not files.exists(env.application_dir):
        run("mkdir -p {}".format(env.application_dir))

    if not run("ls stackless.tar.bz2 2>/dev/null || cat /dev/null"):
        run("wget http://www.stackless.com/binaries/"
            "stackless-278-export.tar.bz2 -O stackless.tar.bz2")

    if not files.exists("projects/stackless/"):
        run("tar xf stackless.tar.bz2")

        with cd("stackless-278-export"):
            run("./configure --prefix=$HOME/projects/stackless/ "
                "&& make -j3 all && make install")

    # === Setuptools & virtualenv install === #

    if not files.exists(os.path.join(env.application_dir, "bin")):
        setuptools_url = (
            "https://bitbucket.org/pypa/setuptools/raw/bootstrap/ez_setup.py"
        )
        with cd(env.application_dir):
            stackless_dir = "$HOME/projects/stackless"
            spython = "{}/bin/python".format(stackless_dir)
            if not files.exists(posixpath.join(stackless_dir, 'bin/easy_install')):
                run("wget {url} -O - | {python}".format(
                    url=setuptools_url, python=spython))
                run("rm -f setuptools*")
            # Virtualenv installation
            run("{stackless_dir}/bin/easy_install virtualenv".format(
                stackless_dir=stackless_dir))
            run("{stackless_dir}/bin/virtualenv .".format(
                stackless_dir=stackless_dir))

    # === Eureka standalone install === #

    with cd(env.application_dir):
        run("rm -rf pj-eureka-open*")
        eureka_url = "http://hg.net-ng.com/pj-eureka-open/archive/{}.tar.gz".format(env.hg_version)
        local("wget {url} --user={user} --password={pwd} -O /tmp/xeureka.tar.gz".format(url=eureka_url, user=env.hg_user, pwd=env.hg_pwd))
        put('/tmp/xeureka.tar.gz', '/tmp/eureka.tar.gz')
        run("tar -xf /tmp/eureka.tar.gz")
        with cd("pj-eureka-open*"):
            run("../bin/easy_install ez_setup")
            run("../bin/easy_install .")

    # === Non-standalone deployment === #

    with cd(env.application_dir):
        eureka_egg_dir = run((
            '{}/bin/python -c "import pkg_resources; '
            'print pkg_resources.get_distribution(\'eureka\').location"'
        ).format(env.application_dir))
        run('rm -f src')
        run('rm -f etc')
        run('rm -f data')
        run('ln -s {} src'.format(eureka_egg_dir))
        run("mkdir -p {}/etc".format(eureka_egg_dir))
        run('ln -s {}/etc etc'.format(eureka_egg_dir))
        run('ln -s {}/data data'.format(eureka_egg_dir))
        run('ln -s {}/conf/eureka.cfg etc/eureka.cfg'.format(eureka_egg_dir))
        run("mkdir -p run")  # Supevisord socket location
        run("mkdir -p sh")  # Scripts are located here
        run(
            ('./bin/nagare-admin batch eureka '
             '{eureka_egg_dir}/contrib/batch/generate_httpd_config.py -n '
             '{server_name} -a {alias_server_name} -H {fcgi_host} -p {fcgi_port} '
             '> {output}').format(
                eureka_egg_dir=eureka_egg_dir,
                server_name=env.server_name[env.host],
                alias_server_name=env.server_alias.get(env.host, ''),
                fcgi_host=env.fcgi_host,
                fcgi_port=env.fcgi_port,
                output="{}/etc/httpd.conf".format(eureka_egg_dir),
            )
        )
        run(
            ("./bin/nagare-admin batch eureka "
             "{eureka_egg_dir}/contrib/batch/generate_publisher_config.py "
             "-H {fcgi_host} -P {fcgi_port} "
             "-m {memcached_host} -p {memcached_port} "
             "> {output}").format(
                eureka_egg_dir=eureka_egg_dir,
                fcgi_host=env.fcgi_host,
                fcgi_port=env.fcgi_port,
                memcached_host=env.memcached_host,
                memcached_port=env.memcached_port,
                output="{}/etc/fastcgi.conf".format(eureka_egg_dir),
            )
        )

        run(
            ("./bin/nagare-admin batch eureka "
             "{eureka_egg_dir}/contrib/batch/generate_supervisord_config.py "
             "'{mailrelay_user}' '{mailrelay_password}'"
             "> {output}").format(eureka_egg_dir=eureka_egg_dir,
                                  output="{}/etc/supervisord.conf".format(eureka_egg_dir),
                                  mailrelay_password=env.mailrelay_password,
                                  mailrelay_user=env.mailrelay_user))

        run(
            ("./bin/nagare-admin batch eureka "
             "{eureka_egg_dir}/contrib/batch/generate_build_backup_script.py "
             "> {output}").format(
                eureka_egg_dir=eureka_egg_dir,
                output="{}/sh/build_backup.sh".format(env.application_dir),
            )
        )

        run(
            ("./bin/nagare-admin batch eureka "
             "{eureka_egg_dir}/contrib/batch/generate_restore_snapshot_script.py "
             "> {output}").format(
                eureka_egg_dir=eureka_egg_dir,
                output="{}/sh/restore_snapshot.sh".format(env.application_dir),
            )
        )

        run('chmod u+x {}/sh/*'.format(env.application_dir))

    # Must adapt configuration depending on Apache version
    # See http://httpd.apache.org/docs/trunk/en/upgrading.html
    apache_config = os.path.join(env.application_dir, 'etc/httpd.conf')
    if files.exists(apache_config):
        out = run('apachectl -v 2>/dev/null || /usr/sbin/apachectl -v')
        if 'Apache/2.2' in out:
            # Apache 2.2
            files.comment(apache_config, '^\s*Require .*')
            files.uncomment(apache_config, '^\s*Order .*')
            files.uncomment(apache_config, '^\s*Allow .*')
        else:
            # Assume Apache 2.4
            files.uncomment(apache_config, '^\s*Require .*')
            files.comment(apache_config, '^\s*Order .*')
            files.comment(apache_config, '^\s*Allow .*')


@dest_env_initialized
def setup_demo_config():
    """
    Modifies the Eureka instance to comply with the demo instance requirements
    --> Memcached + FastCGI + SSL/HTTPS
    """
    assert env.hosts

    with cd(env.application_dir):
        eureka_egg_dir = run(
            './bin/python -c "import pkg_resources; '
            'print pkg_resources.get_distribution(\'eureka\').location"')
        # ==== HTTPD config ==== #
        apache_config = os.path.join(eureka_egg_dir, 'etc', 'httpd.conf')

        # HTTPS instead of HTTP
        files.sed(
            filename=apache_config,
            before='<VirtualHost \*:80>',
            after='<VirtualHost \*:443>',
        )
        # Enable SSL (for HTTPS)
        files.uncomment(apache_config, 'SSLEngine .*')

        with cd('{}/contrib'.format(eureka_egg_dir)):
            # Deactivate password change
            run('patch --forward "../eureka/domain/models.py" < demo/models_no_pwd_change.diff')
            # Restore snapshot every night
            run('crontab -l | {{ grep -v "restore_snapshot" ; echo "0 0 * * * {}/sh/restore_snapshot.sh"; }} | crontab -'.format(env.application_dir))

        # Restore snapshot
        run('./sh/restore_snapshot.sh')

# === APPLICATION BACKUP Commands === #

@task
def create_backup(backup_folder=''):
    """Creates a MySQL DB snapshot (contains DROP TABLE statements)"""
    _python = local("which python", capture=True)
    eureka_egg_dir = local((
        '{python} -c "import pkg_resources; '
        'print pkg_resources.get_distribution(\'eureka\').location"'
    ).format(python=_python), capture=True)

    with lcd(eureka_egg_dir):
        with load_config("conf/eureka.cfg") as conf:
            apache_servername = local(
                "cat {}/etc/httpd.conf | grep ServerName".format(eureka_egg_dir),
                capture=True).split(' ', 1)[-1]
            data_dir = local(
                "cat {}/etc/httpd.conf | grep DocumentRoot".format(eureka_egg_dir),
                capture=True).split(' ', 1)[-1]

            db_uri = urlparse(conf['database']['uri'])
            if db_uri.scheme.lower() != 'sqlite':
                raise ValueError("Unsupported database {}".format(db_uri.scheme))
            db_name = db_uri.path.split(posixpath.sep, 1)[-1]

            with open("contrib/demo/build_backup.sh") as script_file:
                script_template = script_file.read()
                local(script_template.format(
                    apache_servername=apache_servername,
                    data_dir=data_dir,
                    db_name=db_name,
                ))


@task
def restore_backup(backup_filepath):
    """Restores a SQLite application backup"""
    data_dir = local("cat etc/httpd.conf | grep DocumentRoot",
                     capture=True).split(' ', 1)[-1]
    server_name = local("cat etc/httpd.conf | grep ServerName",
                        capture=True).split(' ', 1)[-1]

    with lcd(data_dir):
        data_folders = [
            "articles-thumbnails", "attachments", "gallery",
            "improvements", "profile-photo", "profile-thumbnails"]

        # Cleans up the data folders
        for data_folder in data_folders:
            if os.path.exists(os.path.join(data_dir, data_folder)):
                local("rm -rf {folder}/*".format(folder=data_folder))
            else:
                local("mkdir {folder}".format(folder=data_folder))

    _stem, _ = os.path.splitext(os.path.basename(backup_filepath))
    tmp_folder = '/tmp/{}'.format(_stem)

    # Restores the backup data
    with tarfile.open(backup_filepath, 'r:gz') as tfile:
        tfile.extractall(path=tmp_folder)

    data_tarball_filename = "{}-data.tgz".format(server_name)
    data_tarball_filepath = os.path.join(tmp_folder, data_tarball_filename)
    with tarfile.open(data_tarball_filepath, 'r:gz') as tfile:
        tfile.extractall(data_dir)

    # Restore Database data
    db_filename = "{}.db".format(server_name)
    sql_filepath = os.path.join(tmp_folder, sql_filename)

    with load_config(_get_config_filepath()) as conf:
        db_config = urlparse(conf['database']['uri'])
        db_name = db_config.path.split(posixpath.sep, 1)[-1]
        local("rm {db_name}".format(db_name=db_name))
        local("cp {db_filepath} > {db_name}".format(
            db_filepath=db_filename,
            db_name=db_name,
        ))

        # local(("mysql -u{username} -p{password} "
        #       "-h{host} eureka < {sql_dump}").format(
        #     username=db_config.username,
        #     password=db_config.password,
        #     host=db_config.hostname,
        #     db_name=db_config.path.split(posixpath.sep, 1)[-1],
        #     sql_dump=sql_filepath,
        # ))
