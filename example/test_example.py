# -*- coding: utf-8 -*-

"""
feature: single-line common feature from module to test functions.

# NOT recommended to set "feature" HERE.
# Use test-functions docstrings instead or other constructions
# Due to nature of allure-python: all content of THIS block will be copied into description of each(!) test
"""


def test_example_1(allure_dsl):
    """
    story: story for example
    description: description for example
    attachments:
        - title: json data
          file: attachments/example.json
    steps:
        1: Hello World!
        activity: living in the world!
        3: Bye World!
    """
    with allure_dsl.step(1):
        pass

    with allure_dsl.step('activity'):
        pass

    with allure_dsl.step(3):
        pass


def test_example_2():
    """
    feature: re-writen feature
    story: story for example
   """
    pass


class TestExample:
    """
    feature: common feature from class to test case methods
    """

    def test_example(self):
        """
        story: story for example
        description: description for example
        attachments:
            - title: request
              type: json
              content: '{"hello": "world"}'
        """
        pass
