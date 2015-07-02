I Quick start
=============

I.1 Stackless Python installation
---------------------------------

Eureka open is a solution that requires a custom Python implementation called `Stackless Python`_ (version 2.7.X). In order to install it, you can do it via the sources via the following commands::

    $ mkdir <STACKLESS_DIR>
    $ wget http://www.stackless.com/binaries/stackless-278-export.tar.bz2
    $ tar xf stackless-278-export.tar.bz2
    $ ./configure --prefix=<STACKLESS_DIR> && make -j3 all && make install

.. _Stackless Python: http://www.stackless.com

I.2 Virtualenv and setuptools install
-------------------------------------

In order to isolate your Eureka project, you can install and use ``virtualenv``. To do so within you fresh Stackless Python, you can execute the following commands::

    $ wget https://bitbucket.org/pypa/setuptools/raw/bootstrap/ez_setup.py -O - | <STACKLESS_DIR>/bin/python
    $ <STACKLESS_DIR>/bin/easy_install virtualenv

Note: you can also find some more details on how to install Stackless Python on `its documentation`_

.. _its documentation: http://www.stackless.com/wiki

I.3 Eureka installation
-----------------------

First, you can create you project folder::

    $ mkdir -p <EUREKA_DIR>

Then, you can create our virtualenv by doing::

    $ cd <EUREKA_DIR>
    $ <STACKLESS_DIR>/bin/virtualenv .

As a pre-requisite, you then need to install `ez_setup` as followed::

    $ <EUREKA_DIR>/bin/easy_install ez_setup

You can finally install Eureka open with ``easy_install``::

    $ easy_install eureka-opensource

Or download the `compressed archive from PyPI`_ or `from Github`_, extract it, and inside it
run::

    $ python setup.py install

.. _compressed archive from PyPI: https://pypi.python.org/pypi/eureka-open
.. _from Github: http://www.github.com/eureka-open

I.5 Database creation
---------------------

By default, Eureka open is using a standard SQLite database for its persistence. So to create the database and its schema, you can use the following `Nagare command`_::

    $ <EUREKA_DIR>/bin/nagare-admin create-db eureka

.. _Nagare command: http://www.nagare.org/trac/wiki/NagareAdmin

I.6 Standalone application startup
----------------------------------

Now that your application has been successfully set up, you can run it in standalone mode using the following command::

    $ <EUREKA_DIR>/bin/nagare-admin serve eureka

And Voilà, you can now access your Eureka by accessing http://127.0.0.1:8080 in your favourite browser.

II Application configuration & customization
============================================

This section covers the main areas you may want to customize within your Eureka instance.

Please note that the below changes are explained in the context of a fresh copy of the code that is not yet installed. If this is already the case, you can still apply these changes but the provided locations will be different. Indeed, please consider the result of the following command as being your ``<EUREKA_DIR>`` onwards or just re-install Eureka after any customization::

    $ <EUREKA_DIR>/bin/python -c "import pkg_resources; print pkg_resources.get_distribution('eureka').location"

II.1 Nagare related configuration
---------------------------------

As Nagare is based upon the Nagare Framework, the default configuration for the application can be found in ``<EUREKA_DIR>/conf/eureka.conf``.

In order to understand how to customize non domain specific parameters such as some basic application settings or the type of database to use, you can refer to `this page`_ to find the needed information.

.. _this page: http://www.nagare.org/trac/wiki/ApplicationConfiguration

II.2 Eureka specific configuration & customization
--------------------------------------------------

In order to customize your application, you can modify the configuration file available at ``<EUREKA_DIR>/conf/eureka.conf`` and adapt it to your taste.
This `EUREKA_DIR` can be found using the following command::

    $ <EUREKA_DIR>/bin/python -c "import pkg_resources; print pkg_resources.get_distribution('eureka').location"

Among the configurable aspects of Eureka can be found:

* ``security``: Security configuration (cookies/password)
* ``points``: Points weighting
* ``mail``: E-mail/recipients
* ``html``: Presentation related optimization
* ``filesystem``: The data directory location
* ``search_engine``: By default uses Whoosh, but can also support Solr
* ``dashboard``: Configuration of satistics to be displayed on your dashboard

Detailed explanations on the aforementioned sections can be found directly within the ``<EUREKA_DIR>/conf/eureka.conf`` configuration file.

Idea domains
^^^^^^^^^^^^

In order to import custom idea domains, you can use the following commands::

    $ cd <EUREKA_DIR>
    $ ./bin/nagare-admin eureka batch <EUREKA_DIR>/eureka/batch/populate_domains -c <CSV_FILEPATH>

The CSV filepath to be given as an argument has to be formatted similarly to what you can see in ``<EUREKA_DIR>/data/fixtures/domains.csv``. Although automatically detected, the recommended delimiters for your CSV are the comma ``,`` or the semicolon ``;``.

Article topics
^^^^^^^^^^^^^^

In order to import custom article topics, you can use the following commands::

    $ cd <EUREKA_DIR>
    $ ./bin/nagare-admin eureka batch <EUREKA_DIR>/eureka/batch/populate_article_topics -c <CSV_FILEPATH>

The CSV filepath to be given as an argument has to be formatted similarly to what you can see in ``<EUREKA_DIR>/data/fixtures/article_topics.csv``. Although automatically detected, the recommended delimiters for your CSV are the comma ``,`` or the semicolon ``;``.

Event based point weighting
^^^^^^^^^^^^^^^^^^^^^^^^^^^

In order to customize the number of points awarded to a given user following the below events, you can override the default values by adding a ``[points]`` section within you configuration file and add the following entries:

* ``first_connection``: Allocated upon first ever connection
* ``first_connection_of_the_day``: Allocated upon first connection of the day
* ``vote``: Allocated whenever voting. Limited to 3 times a day
* ``add_comment``: Allocated whenever making a comment. Limited to twice a day
* ``publish_idea``: Allocated once publishing an idea. Equally divided among every co-author
* ``publish_challenge_first_idea``: Awarded to the author(s) publishing the first idea of a challenge. Also equally divided among every author
* ``approval``: Awarded to the author(s) whenever its idea gets approved. Also equally divided among every author
* ``change_avatar``: Given to a user everytime he changes his avatar
* ``select_idea``: Awarded to the author(s) whenever its idea gets selected. Also equally divided among every author
* ``send_project_idea``: ...
* ``send_prototype_idea``: ...

II.3 Customized translations
----------------------------

In order to internationalize your Eureka you may want to change the default translations. The translations files, located within the ``data/locale`` folder (with `*.po` extensions) of the project have to be compiled after any modification.

Based on `Babel`_, you can compile these translation files using the following command::

    $ <EUREKA_DIR>/bin/pybabel compile -d $EUREKA_DIR/data/locale

If you want further details on how to compile handle internationalization using `Babel`_, you can refer to `this Babel documentation`_.

.. _Babel: http://babel.pocoo.org/
.. _this Babel documentation: http://babel.pocoo.org/docs/

User status levels
^^^^^^^^^^^^^^^^^^

In order to customize the labels for the different user levels, you can edit them in the ``message.po`` located within the following path for the ``<LANG>`` language::

    ``<EUREKA_DIR>/data/locale/<LANG>/LC_MESSAGES/messages.po``

Their related message ID (i.e. ``msgid`` within the file) are:

* ``status_level0`` which is by default translated as `Inactive` in english
* ``status_level1`` which is by default translated as `Pioneer` in english
* ``status_level2`` which is by default translated as `Explorer` in english
* ``status_level3`` which is by default translated as `Discoverer` in english
* ``status_level4`` which is by default translated as `Visionary` in english
* ``status_level5`` which is by default translated as `Brilliant` in english

Please note that these translations will then need to be re-compiled using the aforementioned batch command in section I.3.

Idea state labels
^^^^^^^^^^^^^^^^^
If you want to customize the idea state labels, you do so by editing the ``<EUREKA_DIR>/data/locale/<LANG>/LC_MESSAGES/messages.po`` files by changing the message IDs (i.e. ``msgid``) ending with ``_STATE`` (e.g. ``PROTOTYPE_STATE``)

Please note that these translations will then need to be re-compiled using the aforementioned batch command in section I.3.

II.3 Publisher configuration
----------------------------

If you are interested in deploying Eureka into a production server, you can use the publishers supported by `Nagare`_ as described in the its `documentation`_.

Among the supported Web servers can be found:

* `Nginx`_
* `Apache Web Server`_
* `Lighttpd`_

These web serve can serve your Eureka application via their FastCGI module.

To help you write your web server configuration, Nagare provides `create-rules command`_ that will generate the rules needed to serve your Eureka instance.

.. _Nagare: http://www.nagare.org
.. _documentation: http://www.nagare.org/trac/wiki/ApplicationDeployment
.. _Nginx: http://nginx.org/
.. _Apache Web Server: http://httpd.apache.org/
.. _Lighttpd: http://www.lighttpd.net/
.. _create-rules command: http://www.nagare.org/trac/wiki/NagareAdmin

III Contribute
==============

III.1 Development mode
----------------------

In order to install Eureka in development mode, you can simply type::

    $ <EUREKA_DIR>/bin/easy_install --editable --build-directory <EUREKA_DIR> eureka-open

III.2 Contributing
------------------

Contributions in the form of pull requests are always welcome. To do so, these can be done through either via `our Github repository`_ or `the Bitbucket one`_.

So do not hesitate to fork the main repository and make pull requests!

.. _our Github repository: https://github.com/solocalgroup/eureka-opensource
.. _the Bitbucket one: https://bitbucket.org/solocalgroup/eureka-opensource

III.3 Coding style
------------------

Use PEP-8 as a coding standard. Ignored PEP8 errors can be found in the ``setup.cfg`` file within the ``[pep8]`` section.

III.4 Testing
-------------

Contributions covered by tests are encouraged to help us raise the stability of Eureka.

We use `nose`_ to run our tests.

.. _nose: https://nose.readthedocs.org/en/latest/
