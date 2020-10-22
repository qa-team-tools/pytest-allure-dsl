"""
feature: module
"""
import pytest


class TestClass:
    """
    feature: class
    """

    @pytest.mark.xfail(reason='recursive inheritance has not been implemented yet.')
    def test_func(self, allure_dsl):
        """
        feature: method
        """
        assert set(allure_dsl._instructions._features) == {'module', 'class', 'method'}
