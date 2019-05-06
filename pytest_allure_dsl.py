# -*- coding: utf-8 -*-

from functools import wraps

import yaml
from yaml.loader import Loader as FullLoader
import pytest
from _pytest.mark import MarkInfo, Mark
from allure.constants import Label
from allure.pytest_plugin import MASTER_HELPER, LazyInitStepContext


def pytest_addoption(parser):
    parser.addoption(
        '--allure-dsl',
        action='store_true',
        default=False,
        help='Parse test doc string and try it as allure report instructions',
    )


def pytest_collection_modifyitems(session, config, items):
    if config.getoption('--allure-dsl'):
        for item in items:
            AllureDSL(item).apply()


@pytest.fixture(scope='function')
def allure_dsl(request):
    return AllureDSL(request.node)


class AllureDSL(object):

    def __init__(self, node):
        self._node = node
        self._instructions = yaml.load(str(self._node.obj.__doc__), Loader=FullLoader)

    @property
    def node(self):
        return self._node

    @property
    def instructions(self):
        return self._instructions

    @property
    def steps(self):
        if isinstance(self._instructions, dict):
            return self._instructions.get('steps', {})

        return {}

    def step(self, key, name=None):
        if name is not None:
            return LazyInitStepContext(MASTER_HELPER, name)

        step = self.steps[key]

        if isinstance(step, dict):
            step_name = step['name']
        else:
            step_name = step

        return LazyInitStepContext(MASTER_HELPER, step_name)

    def apply(self):
        if getattr(self._node, '__allure_dsl_class__', None):
            return

        setattr(self._node, '__allure_dsl_class__', self.__class__)

        def apply_description(string):
            def wrapper(func):
                @wraps(func)
                def wrapped(*args, **kwargs):
                    MASTER_HELPER.description(string)
                    return func(*args, **kwargs)

                return wrapped
            return wrapper

        if self._node.obj.__doc__:
            if isinstance(self._instructions, dict):
                exclude = ('steps', 'description')

                for label, value in ((k, v) for k, v in self._instructions.items() if k not in exclude):
                    name = '{}.{}'.format(Label.DEFAULT, label)
                    args = (value,) if isinstance(value, str) else tuple(value)

                    mark = Mark(name=name, args=args, kwargs={})
                    mark_info = MarkInfo(marks=[mark])

                    self._node.own_markers.append(mark)
                    self._node.keywords[name] = mark_info

                    if 'pytestmark' not in self._node.keywords:
                        self._node.keywords['pytestmark'] = []

                    self._node.keywords['pytestmark'].append(mark)

                    description = self._instructions.get('description', None)

                    if description is not None:
                        self._node.obj = apply_description(description)(self._node.obj)
            else:
                self._node.obj = apply_description(self._node.obj.__doc__)(self._node.obj)
