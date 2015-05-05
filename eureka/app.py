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

from __future__ import absolute_import

import sys
import os
from datetime import timedelta

import configobj
import pkg_resources
import webob
from eureka.domain import services
from eureka.infrastructure import filesystem, mail, urls, users
from eureka.infrastructure.password_policy import PasswordPolicy
from eureka.infrastructure.security import get_current_user, SecurityManager
from eureka.infrastructure.timings import timeit
from eureka.infrastructure.tools import redirect_to
from eureka.infrastructure.workflow import voucher
from eureka.pkg import available_locales
from eureka.ui.desktop.shell import Shell as DesktopShell
from eureka.ui.desktop.staticcontent.comp import InternalServerError
from nagare import component, config, i18n, log, presentation, wsgi
from nagare.i18n import _L
from nagare.namespaces import xhtml5
from webob.exc import HTTPInternalServerError


class MainTask(component.Task):

    def __init__(self, shell, configuration):
        self.configuration = configuration
        self.shell = shell

    def go(self, comp):
        comp.call(self.shell(self.configuration))


@presentation.init_for(MainTask)
def init_shell(self, url, comp, *args):
    o = self.shell(self.configuration)
    component.call_wrapper(lambda: comp.call(o))
    comp.init(url, *args)


class BaseApplication(wsgi.WSGIApp):
    APPLICATION_SPEC = {
        'application': {
            'as_root': 'boolean(default=False)',
            'template': 'string(default="default")',
            'workflow': 'string(default="default")',
            'workflow_menu': 'string(default="default")',
        },
        'mobile_version': {
            'enabled': 'boolean(default=False)',
        },
        'administration': {
            'board_export': 'boolean(default=False)',
            'stats_url': 'string(default=None)',
        },
        'dashboard': {
            'tabs': {
                'ideas': 'string_list(default=list())',
                'users': 'string_list(default=list())',
            },
            'chart': {
                'chart_width': 'integer(default=752, min=0)',
                'panel_chart_width': 'integer(default=420, min=0)',
            }
        },
        'users': users.spec,
        'points': voucher.spec,
        'mail': mail.Mailer.spec,
        'security': {
            'cookie': {
                'max_age': 'integer(default=None)',
                'secure': 'boolean(default=False)',
            },
            'autoconnection': {
                'token_timeout': 'integer(default=60)',
            },
            'password': {
                'min_length': 'integer(1, 255, default=6)',
                'nb_cases': 'integer(1, 4, default=1)',
                'default_password': 'string(default=None)',
                'expiration_delay': 'integer(default=None)'
            },
        },
        'html': {
            'use_combined_css': 'boolean(default=False)',
            'use_combined_js': 'boolean(default=False)',
        },
        'filesystem': filesystem.FSService.spec,
        'misc': {
            'attachments_max_size': 'integer(default=500)'
        },
        'search_engine': {'type': 'string(default="dummy")'}
    }

    def __init__(self, root_factory):
        super(BaseApplication, self).__init__(root_factory)
        self.domain = None
        self.search_engine = None
        self.application_path = None
        self.as_root = False
        self.configuration = None

    def prompt_info(self, config_filename):
        sys.stderr.write("************************************************************\n")
        sys.stderr.write("    Welcome to Eureka Open!\n")
        sys.stderr.write("    Your Eureka configuration file is located at:\n")
        sys.stderr.write("        {}\n".format(config_filename))
        sys.stderr.write("************************************************************\n")

    @property
    def log(self):
        return log.get_logger('.' + __name__)

    def _validate_config(self, conf, config_filename, error):
        """
        Validates the INI configuration of the application
        :param conf: The parsed ConfigObj object
        :param config_filename: The config filepath
        :returns:
        """
        base_conf = configobj.ConfigObj(
            conf, configspec=configobj.ConfigObj(self.APPLICATION_SPEC)
        )
        config.validate(config_filename, base_conf, error)

        # Complete application config spec with search engine spec
        search_engine_factory = self.load_entry_point(
            'eureka.search_engine',
            base_conf['search_engine']['type']
        )
        self.APPLICATION_SPEC['search_engine'].update(search_engine_factory.SPEC)

        # Revalidate the entire config and initialize the application
        conf = configobj.ConfigObj(
            conf,
            configspec=configobj.ConfigObj(self.APPLICATION_SPEC))
        config.validate(config_filename, conf, error)

        return dict(conf), search_engine_factory

    def set_config(self, config_filename, conf, error):
        """Read the configuration parameters

        In:
          -  ``config_filename`` -- the path to the configuration file
          - ``conf`` -- the ``ConfigObj`` object, created
                          from the configuration file
          - ``error`` -- the function to call in case of configuration errors
        """
        super(BaseApplication, self).set_config(config_filename, conf, error)
        # Configuration validation
        conf, search_engine_factory = self._validate_config(
            conf, config_filename, error)

        self.search_engine = search_engine_factory(
            **conf.get('search_engine', {}))
        services.set_search_engine(self.search_engine)

        # read the application settings
        self.application_path = conf['application']['path']
        self.as_root = conf['application']['as_root']

        # read the security settings in order to configure the security manager
        self.security = self._create_security_manager(conf['security'])
        del conf['security']

        mail.set_mailer(mail.Mailer(**conf['mail']))
        del conf['mail']

        users.set_default_users(conf['users'])

        # add the platform to the configuration
        conf['misc']['platform'] = self.PLATFORM

        self.configuration = conf

        self.load_entry_point('eureka.templates',
                              conf['application']['template'])
        workflow = self.load_entry_point('eureka.workflow',
                                         conf['application']['workflow'])
        self.load_entry_point('eureka.workflow_menu',
                              conf['application']['workflow_menu'])

        services.set_workflow(workflow.workflow)
        del conf['application']

        filesystem.set_fs_service(filesystem.FSService(**conf['filesystem']))
        del conf['filesystem']

        voucher.configure(conf['points'])

        self.prompt_info(config_filename)

    def load_entry_point(self, entry_point, name):
        entry_point = [
            entry for entry in pkg_resources.iter_entry_points(entry_point)
            if entry.name == name
        ][0]
        return entry_point.load()

    def _create_security_manager(self, security_settings):
        cookie_settings = security_settings['cookie']
        autoconnection_settings = security_settings['autoconnection']
        password_settings = security_settings['password']
        return SecurityManager(
            platform=self.PLATFORM,
            cookie_max_age=cookie_settings['max_age'],
            secure_cookie=cookie_settings['secure'],
            autoconnection_token_timeout=autoconnection_settings[
                'token_timeout'],
            password_policy=self._create_password_policy(password_settings)
        )

    def _create_password_policy(self, password_settings):
        min_length = password_settings['min_length']
        nb_cases = password_settings['nb_cases']
        default_password = password_settings['default_password']
        expiration_delay = password_settings['expiration_delay']
        if default_password:
            default_password = unicode(default_password)

        return PasswordPolicy(
            min_length,
            nb_cases,
            default_password,
            expiration_delay
        )

    def set_databases(self, databases):
        # the database settings must be of the correct types
        for (__, uri, __, conf) in databases:
            if uri.startswith('mysql:'):
                conf['pool_recycle'] = int(conf.get('pool_recycle', '3600'))

        # calls the default implementation
        super(BaseApplication, self).set_databases(databases)

    def set_publisher(self, publisher):
        # call base implementation
        super(BaseApplication, self).set_publisher(publisher)

        if self.as_root:
            publisher.register_application(
                self.application_path, "", self, self)

    def create_root(self, *args, **kw):
        """Create the application root component and wrap it into a Task.
        Permissions can be check in objects initializers and don't have to
        be called in rendering methods.

        Return:
          - the root component
        """
        return component.Component(MainTask(self.root_factory,
                                            self.configuration))

    def set_base_url(self, base_url):
        urls.set_url_service(urls.URLService(base_url))

    def _install_locale(self, request):
        current_user = get_current_user()
        language = current_user.locale if current_user\
            else request.cookies.get('language')
        if language:
            locale = i18n.Locale(language, domain=self.domain)
        else:
            locales = [(lang,) for lang, __ in available_locales]
            default_locale = (available_locales[0][0], None)
            locale = i18n.NegotiatedLocale(request, locales, default_locale,
                                           domain=self.domain)

        self.set_locale(locale)

    def _save_locale(self, response):
        language = i18n.get_locale().language
        response.set_cookie('language', language, max_age=timedelta(days=365))

        current_user = get_current_user()
        if current_user:
            current_user.locale = language

    def start_request(self, root, request, response):
        # remember the application's base URL
        self.set_base_url(request.application_url)

        # Disable the browser's cache.
        #   The reason is that, when we render asynchronous components, the
        #   current state is overwritten, but when we hit the back button,
        #   the browser retrieves the HTML of the first version of the state
        #   from its cache, and thus callbacks are broken because the
        #   state has changed in-between.
        response.cache_expires(0)

        # call the default implementation:
        #   install the default locale and perform other initializations
        super(BaseApplication, self).start_request(root, request, response)

        # set the locale for the current request
        self._install_locale(request)

        # eventually initialize the root component for the next request
        if hasattr(root(), 'on_start_request'):
            root().on_start_request(root, request, response)

    def _phase1(self, request, response, callbacks):
        # callbacks processing
        result = super(BaseApplication, self)._phase1(
            request, response, callbacks)

        # save the locale setting (it may have changed during phase1)
        self._save_locale(response)

        return result

    def on_exception(self, request, response):
        """Called when an unhandled exception is raised
        (*not* called for HTTPException)"""
        # log some information about the request and the exception
        msg = (u"An error occurred while processing the following request:\n"
               u"url=%r\n"
               u"headers=%r\n"
               u"params=%r\n") % (request.url,
                                  dict(request.headers),
                                  dict(request.params))
        self.log.exception(msg)
        super(BaseApplication, self).on_exception(request, response)  # raise

    @timeit('request')
    def __call__(self, environ, start_response):
        try:
            return super(BaseApplication, self).__call__(environ, start_response)
        except:
            return InternalServerError()(environ, start_response)


def merge_spec(d1, d2):
    spec = configobj.ConfigObj(d1)
    spec.merge(d2)
    return dict(spec)


class DesktopApplication(BaseApplication):
    PLATFORM = u'Eureka Desktop'
    _L(u'Eureka Desktop')  # associated translation

    renderer_factory = xhtml5.Renderer

    APPLICATION_SPEC = merge_spec(BaseApplication.APPLICATION_SPEC, {
        'misc': {
            'tutorial_video_url': 'string(default=None)',
            'tutorial_splash_url': 'string(default=None)',
        }
    })

    shell_factory = DesktopShell

    def __init__(self):
        super(DesktopApplication, self).__init__(self.shell_factory)


desktop_app = DesktopApplication()
