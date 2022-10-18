Contributing
============

If you have a new idea for a feature, or find a bug, come have a chat or write to me (Damon)! 
Maybe the feature already exists or I can think of a quick way to fix the bug.
Otherwise, read on for some sensible information from the original qcodes developers.
If you are familiar with github, it should be pretty clear what you should do.
If you are not, let's discuss the best way forward. I don't think every new student 
should be forced to learn github. The second-most important thing is that we make the
changes as quickly and robustly as possible so you can get the results you need
as soon as possible.

The most important thing is of course:
**please do not mess with a working version of qcodes on one of the measurement computers!!**

.. contents::

New code and testing
~~~~~~~~~~~~~~~~~~~~
-  Fork the repo into your github account
-  Make a branch within this repo to make your changes

Commit Message Format
^^^^^^^^^^^^^^^^^^^^^

A useful git repo starts with great commits. This is not optional, and
it may seem daunting at first but you'll soon get the hang of it and
will find out that it helps with developing good software. Nobody will
get shot/tortured if the guidelines are not followed but you'll have to
fix your commits.

Each commit message consists of a **header**, a **body** and a
**footer**. The header has a special format that includes a **type** and
a **subject**:

::

    <type>: <subject>
    <BLANK LINE>
    <body>
    <BLANK LINE>
    <footer>

Limit the subject line to 50 characters. This is mandatory, github will
truncate otherwise making the commit hard to read. No line may exceed
100 characters. This makes it easier to read the message on GitHub as
well as in various git tools.

Type


Must be one of the following:

-  **feat**: A new feature
-  **fix**: A bug fix
-  **docs**: Documentation only changes
-  **style**: Changes that do not affect the meaning of the code
   (white-space, formatting, missing semi-colons, etc)
-  **refactor**: A code change that neither fixes a bug nor adds a
   feature
-  **perf**: A code change that improves performance
-  **test**: Adding missing tests
-  **chore**: Changes to the build process or auxiliary tools and
   libraries such as documentation generation

Subject


The subject contains succinct description of the change:

-  use the imperative, present tense: "change" not "changed" nor
   "changes"
-  capitalize first letter
-  no dot (.) at the end

Body


Just as in the **subject**, use the imperative, present tense: "change"
not "changed" nor "changes"The body should include the motivation for
the change and contrast this with previous behavior.

Footer


The footer should contain any information about **Breaking Changes** and
is also the place to reference GitHub issues that this commit
**Closes**.

You are allowed to skip both body and footer only and only if your
header is indeed enough to understandable 10 years after.

A note on committing and pushing (if you are not really familiar with git).
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

A good commit is really important (for you writing it in the first
place). If you need a loving guide all the time you commit, see
`here <http://codeinthehole.com/writing/a-useful-template-for-commit-messages/>`__.
Do not push! Unless you are sure about your commits. If you have a typo
in your commit message, do not push. If you added more files/changes
that the commit says, do not push. In general everything is fixable if
you don't push. The reason is that on your local machine you can always
re-write history and make everything look nice, once pushed is just
harder to go back. If in doubt, ask and help will be given. Nobody was
born familiar with git, and everybody makes mistakes.

-  Write your new feature or fix. Be sure it doesn't break any existing
   tests, and please write tests that cover your feature as well, or if
   you are fixing a bug, write a test that would have failed before your
   fix. Our goal is 100% test coverage, and although we are not there,
   we should always strive to increase our coverage with each new
   feature. Please be aware also that 100% test coverage does NOT
   necessarily mean 100% logic coverage. If (as is often the case in
   Python) a single line of code can behave differently for different
   inputs, coverage in itself will not ensure that this is tested.

-  Write the docs, following the other documentation files (.rst) in the
   repo.

NOTE(giulioungaretti): maybe running test locally should be simplified,
and then unit testing should be run on pull-request, using CI. Maybe
simplify to a one command that says: if there's enough cover, and all
good or fail and where it fails.

-  We should have a *few* high-level "integration" tests, but simple
   unit tests (that just depend on code in one module) are more valuable
   for several reasons:
-  If complex tests fail it's more difficult to tell why
-  When features change it is likely that more tests will need to change
-  Unit tests can cover many scenarios much faster than integration
   tests.
-  If you're having difficulty making unit tests, first consider whether
   your code could be restructured to make it less dependent on other
   modules. Often, however, extra techniques are needed to break down a
   complex test into simpler ones. @alexcjohnson or @giulioungaretti are
   happy to help with this. Two ideas that are useful here:
-  Patching, one of the most useful parts of the
   `unittest.mock <https://docs.python.org/3/library/unittest.mock.html>`__
   library. This lets you specify exactly how other functions/objects
   should behave when they're called by the code you are testing.

-  Supporting files / data: Lets say you have a test of data acquisition
   and analysis. You can break that up into an acquisition test and an
   analysis by saving the intermediate state, namely the data file, in
   the test directory. Use it to compare to the output of the
   acquisition test, and as the input for the analysis test.

-  We have not yet settled on a framework for testing real hardware.
   Stay tuned, or post any ideas you have as issues!

Coding Style
~~~~~~~~~~~~

NOTE(giulioungaretti): is this enough ?

-  Try to make your code self-documenting. Python is generally quite
   amenable to that, but some things that can help are:

-  Use clearly-named variables
-  Only use "one-liners" like list comprehensions if they really fit on
   one line.
-  Comments should be for describing *why* you are doing something. If
   you feel you need a comment to explain *what* you are doing, the code
   could probably be rewritten more clearly.
-  If you *do* need a multiline statement, use implicit continuation
   (inside parentheses or brackets) and implicit string literal
   concatenation rather than backslash continuation
-  Format non-trivial comments using your GitHub nick and one of these
   prefixes:

   -  TODO( theBrain ): Take over the world!
   -  NOTE( pinky ): Well, that's a good idea.

-  Docstrings are required for classes, attributes, methods, and
   functions (if public i.e no leading underscore). Because docstrings
   (and comments) *are not code*, pay special attention to them when
   modifying code: an incorrect comment or docstring is worse than none
   at all! Docstrings should utilize the `google
   style <http://google.github.io/styleguide/pyguide.html?showone=Comments#Comments>`__
   in order to make them read well, regardless of whether they are
   viewed through help() or on Read the Docs. See `the falcon
   framework <https://github.com/falconry/falcon>`__ for best practices
   examples.

-  Use `PEP8 <http://legacy.python.org/dev/peps/pep-0008/>`__ style. Not
   only is this style good for readability in an absolute sense, but
   consistent styling helps us all read each other's code.
-  There is a command-line tool (``pip install pep8``) you can run after
   writing code to validate its style.
-  A lot of editors have plugins that will check this for you
   automatically as you type. Sublime Text for example has
   sublimelinter-pep8 and the even more powerful sublimelinter-flake8.
   For Emacs, the elpy package is strongly recommended (https://github.com/jorgenschaefer/elpy).
-  BUT: do not change someone else's code to make it pep8-compliant
   unless that code is fully tested.
-  BUT: remove all trailing spaces.
-  BUT: do not mix tabs and indentation for any reason.

-  JavaScript: The `Airbnb style
   guide <https://github.com/airbnb/javascript>`__ is quite good. If we
   start writing a lot more JavaScript we can go into more detail.

Pull requests
~~~~~~~~~~~~~

-  Push your branch back to github and make a pull request (PR). If you
   visit the repo `home page <ht://github.com/qdev-dk/Qcodes>`__ soon
   after pushing to a branch, github will automatically ask you if you
   want to make a PR and help you with it.

-  Naming matters; try to come up with a nice header:

   -  fix(dataformatter): Decouple foo from bar
   -  feature: Add logviewer

-  The template will help you write nice pull requests <3 !

-  Try to keep PRs small and focused on a single task. Frequent small
   PRs are much easier to review, and easier for others to work around,
   than large ones that touch the whole code base.

-  tag AT LEAST ONE person in the description of the PR (a tag is
   ``@username``) who you would like to have look at your work. Of
   course everyone is welcome and encouraged to chime in.

-  It's OK (in fact encouraged) to open a pull request when you still
   have some work to do. Just make a checklist
   (``- [ ] take over the world``) to let others know what more to
   expect in the near future.

-  There are a number of emoji that have specific meanings within our
   github conversations. The most important one is :dancer: which means
   "approved" - typically one of the core contributors should give the
   dancer. Ideally this person was also tagged when you opened the PR.

-  Delete your branch once you have merged (using the helpful button
   provided by github after the merge) to keep the repository clean.
   Then on your own computer, after you merge and pull the merged master
   down, you can call ``git branch --merged`` to list branches that can
   be safely deleted, then ``git branch -d <branch-name>`` to delete it.
