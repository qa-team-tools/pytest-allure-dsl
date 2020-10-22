"""
description: module
"""


def test_description(allure_dsl):
    """
    description: function
    """
    assert allure_dsl.description == """function
***
module"""
