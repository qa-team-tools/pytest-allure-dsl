Pytest Allure DSL Plugin
========================

Installation
------------

```bash
pip install pytest-allure-dsl
```

Enable plugin
-------------

```bash
pytest --allure-dsl
```

Using allure labels and description
-----------------------------------

```python
def test_example():
    """
    feature: test feature string or features list
    story: test story string or story list
    description: test description string
    issue: test issue
    ... and etc allure labels
    """
    pass
```

Using allure steps from dsl
---------------------------

```python
def test_example(allure_dsl):
    """
    steps:
        1: step one
        2:
            name: step two
            my_key: my custom annotation, will not be using for allure report
    """
    with allure_dsl.step(1):
        pass

    with allure_dsl.step(2):
        pass
```

Advantages
----------
Plugin can be using for sync to jira zephyr, kanoah.
For example:
```python
import pytest

@pytest.fixture(scope='function')
def sync_to(client_for_sync, allure_dsl):
    client_for_sync.sync_case(allure_dsl.instructions)
```
