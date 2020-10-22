"""
feature: module feature
"""
from pytest_allure_dsl import AllureDSL


def test_single_label(allure_dsl: AllureDSL):
    """
    feature: one
    """
    assert set(allure_dsl._instructions._features) == {'module feature', 'one'}


def test_multiple_label(allure_dsl: AllureDSL):
    """
    feature:
        - one
        - two
    """
    assert set(allure_dsl._instructions._features) == {'module feature', 'one', 'two'}


def test_the_same_label(allure_dsl: AllureDSL):
    """
    feature: module feature
    """
    assert allure_dsl._instructions._features == ['module feature', 'module feature']
