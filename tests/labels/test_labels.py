from pytest_allure_dsl import AllureDSL


def test_own_feature(allure_dsl: AllureDSL):
    """
    feature: own
    """
    assert ['own'] == allure_dsl._instructions._features


def test_multiple_features(allure_dsl: AllureDSL):
    """
    feature:
        - first
        - second
    """
    assert set(allure_dsl._instructions._features) == {'first', 'second'}


def test_the_same_feature(allure_dsl):
    """
    feature:
        - the same
        - the same
    """
    assert allure_dsl._instructions._features == ['the same', 'the same']
