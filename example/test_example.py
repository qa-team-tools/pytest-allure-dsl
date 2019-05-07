# -*- coding: utf-8 -*-

"""
feature:
  - common feature from module to test functions
  - can be re-writen from test case doc
  - can be simple string
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
        2: By World!
    """
    with allure_dsl.step(1):
        pass

    with allure_dsl.step(2):
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
