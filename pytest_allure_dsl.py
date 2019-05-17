# -*- coding: utf-8 -*-

import os

import yaml
from yaml.error import YAMLError
from yaml.loader import Loader as FullLoader
import pytest
from _pytest.mark import MarkInfo, Mark
from allure.constants import Label, AttachmentType
from allure.pytest_plugin import MASTER_HELPER, LazyInitStepContext


def pytest_addoption(parser):
    parser.addoption(
        '--allure-dsl',
        action='store_true',
        default=False,
        help='Parse test doc string and try it as allure report instructions',
    )


@pytest.hookimpl(tryfirst=True)
def pytest_configure(config):
    if config.option.allure_dsl and not config.option.allurereportdir:
        config.option.allurereportdir = './.allure'


@pytest.hookimpl(tryfirst=True)
def pytest_collection_modifyitems(session):
    if session.config.option.allure_dsl:
        for item in session.items:
            item.allure_dsl = AllureDSL(item)
            item.allure_dsl.build()


@pytest.fixture(scope='function')
def allure_dsl(request):
    """
    Allure DSL instance of test node
    """
    return request.node.allure_dsl


@pytest.fixture('function', autouse=True)
def __allure_dls_pre_post_actions__(request, allure_dsl):
    if request.config.option.allure_dsl:
        MASTER_HELPER.description(allure_dsl.description)

        try:
            yield
        finally:
            if request.config.option.allure_dsl:
                allure_dsl.add_attachments()


def _yaml_load(string):
    try:
        return yaml.load(str(string), Loader=FullLoader)
    except YAMLError:
        return {}


class BaseAllureDSLException(Exception):
    pass


class InvalidInstruction(BaseAllureDSLException):
    pass


class StepIsNotImplemented(InvalidInstruction):
    pass


class AllureDSL(object):

    __labels__ = (
        Label.FEATURE,
        Label.STORY,
        Label.SEVERITY,
        Label.ISSUE,
        Label.TESTCASE,
        Label.THREAD,
        Label.HOST,
        Label.FRAMEWORK,
        Label.LANGUAGE,
    )

    __allow_inherit_from_parent__ = (
        Label.FEATURE,
        Label.ISSUE,
        Label.THREAD,
        Label.HOST,
        Label.FRAMEWORK,
        Label.LANGUAGE,
    )

    def __init__(self, node):
        self._node = node
        self._instructions = _yaml_load(self._node.obj.__doc__)
        self._inherit_from_parent()

        self._is_built = False

    def _inherit_from_parent(self):
        if not isinstance(self._instructions, dict):
            self._instructions = {}

        parent_instructions = _yaml_load(self._node.parent.obj.__doc__)

        if not isinstance(parent_instructions, dict):
            return

        for label in self.__allow_inherit_from_parent__:
            if label in parent_instructions and label not in self._instructions:
                self._instructions[label] = parent_instructions[label]

    def _build_markers(self):
        for label, value in self.labels:
            name = '{}.{}'.format(Label.DEFAULT, label)
            args = (value,) if isinstance(value, str) else tuple(value)

            mark = Mark(name=name, args=args, kwargs={})
            mark_info = MarkInfo(marks=[mark])

            self._node.own_markers.append(mark)
            self._node.keywords[name] = mark_info

            if 'pytestmark' not in self._node.keywords:
                self._node.keywords['pytestmark'] = []

            self._node.keywords['pytestmark'].append(mark)

    @property
    def instructions(self):
        return self._instructions

    @property
    def steps(self):
        if isinstance(self._instructions, dict):
            return self._instructions.get('steps', {})

        return {}

    @property
    def labels(self):
        return ((k, v) for k, v in self._instructions.items() if k in self.__labels__)

    @property
    def feature(self):
        return self._instructions.get(Label.FEATURE)

    @property
    def story(self):
        return self._instructions.get(Label.STORY)

    @property
    def severity(self):
        return self._instructions.get(Label.SEVERITY)

    @property
    def issue(self):
        return self._instructions.get(Label.ISSUE)

    @property
    def test_id(self):
        return self._instructions.get(Label.TESTCASE)

    @property
    def thread(self):
        return self._instructions.get(Label.THREAD)

    @property
    def host(self):
        return self._instructions.get(Label.HOST)

    @property
    def framework(self):
        return self._instructions.get(Label.FRAMEWORK)

    @property
    def language(self):
        return self._instructions.get(Label.LANGUAGE)

    @property
    def attachments(self):
        return self._instructions.get('attachments', [])

    @property
    def description(self):
        return self._instructions.get('description')

    def step(self, key, title=None):
        if title is not None:
            if key not in self.steps:
                raise StepIsNotImplemented(key)

            return LazyInitStepContext(MASTER_HELPER, title)

        try:
            step = self.steps[key]
        except KeyError:
            raise StepIsNotImplemented(key)

        if isinstance(step, dict):
            try:
                step_name = step['title']
            except KeyError:
                raise InvalidInstruction(
                    'Key "title" is required option for step',
                )
        else:
            step_name = step

        return LazyInitStepContext(MASTER_HELPER, step_name)

    def add_attachments(self):
        file_ext_to_type = {
            'txt': AttachmentType.TEXT,
            'json': AttachmentType.JSON,
            'jpg': AttachmentType.JPG,
            'jpeg': AttachmentType.JPG,
            'png': AttachmentType.PNG,
            'html': AttachmentType.HTML,
            'htm': AttachmentType.HTML,
            'xml': AttachmentType.XML,
        }

        for attach in self.attachments:
            if not isinstance(attach, dict):
                raise InvalidInstruction('Attach must be dictionary')

            try:
                title = attach['title']
            except KeyError:
                raise InvalidInstruction('"title" is required option for attach')

            path = attach.get('file')
            content = attach.get('content')

            if not path and not content:
                raise InvalidInstruction('"file" or "content" is required option for attach')

            if path and os.path.exists(path):
                file_ext = path.split('.')[-1]
                attach_type = file_ext_to_type.get(
                    file_ext, AttachmentType.OTHER,
                )
                with open(path, 'rb') as fp:
                    MASTER_HELPER.attach(title, fp.read(), type=attach_type)

            if content:
                attach_type = file_ext_to_type.get(
                    attach.get('type'), AttachmentType.TEXT,
                )
                MASTER_HELPER.attach(title, content, type=attach_type)

    def build(self):
        if self._is_built:
            return

        if isinstance(self._instructions, dict):
            self._build_markers()

        self._is_built = True
