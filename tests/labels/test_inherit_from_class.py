class TestLabels:
    """
    feature:
        - class
        - feature
    """

    def test_inheritance(self, allure_dsl):
        """
        feature:
            - method
        """
        assert set(allure_dsl._instructions._features) == {'class', 'feature', 'method'}
