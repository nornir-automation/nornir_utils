.. image:: https://img.shields.io/badge/docs-passing-green.svg
   :target: https://nornir.tech/nornir_utils/
   :alt: Documentation

.. image:: https://github.com/nornir-automation/nornir_utils/workflows/test_nornir_utils/badge.svg
   :target: https://github.com/nornir-automation/nornir_utils/actions?query=workflow%3Atest_nornir_utils
   :alt: test_nornir_utils

nornir_utils
============

Collection of simple plugins for `nornir <github.com/nornir-automation/nornir/>`_

Installation
------------

.. code::

    pip install nornir_utils

Plugins
-------

Inventory
_________

* **YAMLInventory** - Create an inventory from yaml files

Functions
_________

* **print_result** - Formats nicely and prints results on stdout.
* **print_title** - Formats nicely a title and prints it on stdout.
* **print_stat** - Prints results statistic on stdout.
* **write_result** - Writes results to file.
* **write_results** - Writes results to files.

Processors
__________

* **PrintResult** - Formats nicely and prints results on stdout as soon as they are made available.

Tasks
_____

Data:

* **echo_data** - Dummy task that echoes the data passed to it.
* **load_json** - Load a JSON file.
* **load_yaml** - Load a YAML file.

Files:

* **write_file** - Writes content to files
