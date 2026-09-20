# Lessons for the engineer in this repository

<!--
One line per lesson, specific to this repository, stated as a rule with the
reason attached. Hard cap of 40 non-blank lines, enforced by the guard.

Past the cap, rewrite rather than append: merge two lessons that say the same
thing, drop the one that has stopped being relevant, tighten what survives.

Delete any lesson that has graduated into a test, a lint rule, or a type.
-->

- This run's sandbox refuses `python3` execution beyond `python3 --version` (`pip3 --version`, `python3 -m pip`, `python3 -m venv`, and running any `.py` file all return "This command requires approval" with nobody to grant it) - do not spend turns retrying variations; install/test commands cannot be verified locally here and must be documented as unverified, for the real CI run to confirm.
