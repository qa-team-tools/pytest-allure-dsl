# -*- coding: utf-8 -*-

"""
feature: single-line common feature from module to test functions.
"""
import allure
import pytest


# @pytest.mark.wip
@allure.feature('unambigous feature.')
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
        2: Cook {dish} and fry {second_dish}
        3: Long good bye
        3-1: bye-bye!
    """
    with allure_dsl.step(1):
        pass

    with allure_dsl.step('activity'):
        pass

    with allure_dsl.step(2, dish='soup', second_dish='sausages'):
        pass

    with allure_dsl.step(3):
        with allure_dsl.step('3-1'):
            pass


def test_example_2():
    """
    feature: re-writen feature
    story: story for example
    """
    pass


def test_example_3():
    """
    feature: re-writen feature
    story: story for example
    issue: issue (other label type in new allure)
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
