==========================
Contributing / Report bugs
==========================

Contributions are welcome, and they are greatly appreciated! Every
little bit helps, and credit will always be given.

Note that MinimalModbus is released very infrequently, but your issues are not
forgotten. Do not use GitHub issues for problems getting the Modbus communication
to your instrument to work. For that Stack Overflow is much better, see :ref:`support`.


You can contribute in many ways:

Types of Contributions
----------------------

Help other users
~~~~~~~~~~~~~~~~

It is greatly appreciated if you can help other users to get their Modbus equipment up and running.
Please subscribe ("watch") the tags "modbus" and "minimalmodbus" on Stack Overflow.

Here are the newest minimalmodbus questions on Stack Overflow:
https://stackoverflow.com/questions/tagged/minimalmodbus?tab=Newest


Report Bugs
~~~~~~~~~~~

Report bugs at https://github.com/pyhys/minimalmodbus/issues.

Try to isolate the bug by running in interactive mode (Python interpreter)
with debug mode activated.

Of course it is appreciated if you can spend a few moments trying to locate
the problem, as it might possibly be related to your particular instrument
(and thus difficult to reproduce without it).
The source code is very readable, so is should be straight-forward to work with.

If you are reporting a bug, please include:

* Your operating system name and version.
* Any details about your local setup that might be helpful in troubleshooting.
* Detailed steps to reproduce the bug.
* The output from :meth:`._get_diagnostic_string`.

Fix Bugs
~~~~~~~~

Look through the GitHub issues for bugs. Anything tagged with "bug"
is open to whoever wants to implement it.

Implement Features
~~~~~~~~~~~~~~~~~~

Look through the GitHub issues for features. Anything tagged with "enhancement"
is open to whoever wants to implement it.

Write Documentation
~~~~~~~~~~~~~~~~~~~
MinimalModbus could always use more documentation, whether as part of the
official MinimalModbus docs, in docstrings, or even on the web in blog posts,
articles, and such.

Submit Feedback
~~~~~~~~~~~~~~~
The best way to send feedback is to file an issue at https://github.com/pyhys/minimalmodbus/issues.

If you are proposing a feature:

* Explain in detail how it would work.
* Keep the scope as narrow as possible, to make it easier to implement.
* Remember that this is a volunteer-driven project, and that contributions
  are welcome :)

Get Started!
------------

Ready to contribute? Here's how to set up `minimalmodbus` for local development.

1. Fork the `minimalmodbus` repo on GitHub.
2. Clone your fork locally::

    $ git clone git@github.com:your_name_here/minimalmodbus.git

3. Install your local copy into a virtualenv. Assuming you have virtualenvwrapper installed, this is how you set up your fork for local development::

    $ mkvirtualenv minimalmodbus
    $ cd minimalmodbus/
    $ python setup.py develop

4. Create a branch for local development::

    $ git checkout -b name-of-your-bugfix-or-feature

   Now you can make your changes locally.

5. When you're done making changes, check that your changes pass flake8 and the
   tests, including testing other Python versions with tox::

    $ flake8 minimalmodbus tests
    $ python setup.py test
    $ tox

   To get flake8 and tox, just pip install them into your virtualenv.

6. Commit your changes and push your branch to GitHub::

    $ git add .
    $ git commit -m "Your detailed description of your changes."
    $ git push origin name-of-your-bugfix-or-feature

7. Submit a pull request through the GitHub website.

Pull Request Guidelines
-----------------------

Before you submit a pull request, check that it meets these guidelines:

1. The pull request should include tests.
2. If the pull request adds functionality, the docs should be updated. Put
   your new functionality into a function with a docstring, and add the
   feature to the list in README.rst.
3. The pull request should work for Python 2.7, 3.5, 3.6, and 3.7. Check
   https://travis-ci.org/pyhys/minimalmodbus/pull_requests
   and make sure that the tests pass for all supported Python versions.

