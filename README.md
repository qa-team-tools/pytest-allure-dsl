Pytest Allure DSL Plugin
========================

Installation
------------

```bash
pip install pytest-allure-dsl
```

Enable plugin
-------------

From command line

```bash
pytest -p pytest_allure_dsl --allure-dsl
```

From pytest.ini

```ini
[pytest]
addopts = -p pytest_allure_dsl --allure-dsl
```

From conftest.py

```python
pytest_plugins = ['pytest_allure_dsl']
```

By default allure dir is **./.allure**, you can change it with **--alluredir** option

Using allure labels and description
-----------------------------------

```python
"""
feature:
  - common feature from module to test case functions
  - can be re-writen from test case function docstring
"""


def test_example():
    """
    story: test story string or story list
    description: test description string
    issue: issue for example
    ... and etc allure labels
    """
    pass


class TestExample:
    """
    feature:
      - common feature from class to test case methods
      - can be re-writen from test case method docstring
    """

    def test_example(self):
        """
        story: test story string or story list
        description: test description string
        """
        pass
```

What label can be re-writen
---------------------------

* feature
* issue
* host

Using allure steps from dsl
---------------------------

```python
def test_example(allure_dsl):
    """
    steps:
      1: step one
      2: step two
    """
    with allure_dsl.step(1):
        pass

    with allure_dsl.step(2):
        pass
```

Using allure attachments
------------------------

```python
def test_example_file():
    """
    attachments:
      - title: jsonschema
        file: jsonschemaes/schema.json
    """
    pass


def test_example_content():
    """
    attachments:
      - title: simple text or something
        content: some content
    """


def test_example_content_with_type():
    """
    attachments:
      - title: simple text or something
        type: json
        content: '{"hello": "world"}'
    """
    pass
```

Advantages
----------
You can add custom keys for interpretation.
Plugin can be using for sync to jira zephyr, jira kanoah or another test case storage.
