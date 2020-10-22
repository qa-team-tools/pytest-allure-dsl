def test_description(allure_dsl):
    """
    description: a test
    """
    assert allure_dsl.description == 'a test'


def test_empty_description(allure_dsl):
    """
    :param allure_dsl:
    :return:
    """
    assert allure_dsl.description == ' '
