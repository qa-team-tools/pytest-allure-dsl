# -*- coding: utf-8 -*-

import os

import allure
import pytest
import yaml
from _pytest.config import Config
from allure_commons.types import LabelType, LinkType, AttachmentType
from future.utils import raise_from


def pytest_addoption(parser):
    parser.addoption(
        '--allure-dsl',
        action='store_true',
        default=False,
        help='Parse test doc string and try it as allure report instructions',
    )


@pytest.hookimpl(tryfirst=True)
def pytest_configure(config: Config):
    if config.option.allure_dsl and not config.option.allure_report_dir:
        config.option.allure_report_dir = './.allure'


@pytest.hookimpl(tryfirst=True)
def pytest_collection_modifyitems(session):
    if session.config.option.allure_dsl:
        for item in session.items:
            item.allure_dsl = AllureDSL(item)
            item.allure_dsl.build(item)


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    result = outcome.get_result()

    if call.when == 'setup':
        # rewrite reports from previous runs in case of test rerun.
        item.allure_dsl.reports = {
            call.when: result
        }
    else:
        item.allure_dsl.reports[call.when] = result


@pytest.fixture(scope='function')
def allure_dsl(request):
    """
    Allure DSL instance of test node
    """
    try:
        return request.node.allure_dsl
    except AttributeError:
        return AllureDSL(request.node)


@pytest.fixture(scope='function', autouse=True)
def __allure_dls_pre_post_actions__(request, allure_dsl):
    if request.config.option.allure_dsl:
        with allure_dsl:
            yield


class BaseAllureDSLException(Exception):
    pass


class InvalidInstruction(BaseAllureDSLException):
    pass


class StepIsNotImplemented(InvalidInstruction):
    pass


class StepsWasNotUsed(BaseAllureDSLException):
    pass


class AllureDSL(object):
    __labels__ = {
        LabelType.FEATURE: allure.feature,
        LabelType.STORY: allure.story,
        LabelType.SEVERITY: allure.severity,
        LinkType.ISSUE: allure.issue,
        LinkType.TEST_CASE: allure.testcase,
    }

    __allow_inherit_from_parent__ = (
        LabelType.FEATURE,
        LinkType.ISSUE,
    )

    def __init__(self, node):
        self._node = node
        self._description_load_error = None
        self._instructions = self._yaml_load(self._node.obj.__doc__)
        self._inherit_from_parent()

        self._is_built = False
        self._steps_was_used = set()
        self.reports = {}

    def __enter__(self):
        pass

    def __exit__(self, *args, **kwargs):
        self._add_attachments()
        if 'call' in self.reports:
            if self.reports['call'].passed:
                self._check_steps_was_used()

    def _inherit_from_parent(self):
        if not isinstance(self._instructions, dict):
            self._instructions = {}

        parent_instructions = self._yaml_load(self._node.parent.obj.__doc__)

        if not isinstance(parent_instructions, dict):
            return

        for label in self.__allow_inherit_from_parent__:
            if label in parent_instructions and label not in self._instructions:
                self._instructions[label] = parent_instructions[label]

    def _add_attachments(self):
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
                    file_ext, AttachmentType.TEXT,
                )
                allure.attach.file(path, name=title,
                                   attachment_type=attach_type,
                                   extension=file_ext)

            if content:
                extension = attach.get('type')
                attach_type = file_ext_to_type.get(
                    extension, AttachmentType.TEXT,
                )
                allure.attach(content, name=title,
                              attachment_type=attach_type,
                              extension=extension)

    def _setup_description(self, item):
        item.add_marker(allure.description(self.description))

        if self._node.module.__doc__:
            module_instructions = self._yaml_load(self._node.module.__doc__)

            if isinstance(module_instructions, dict):
                self._node.module.__doc__ = module_instructions.get('description')

    def _build_markers(self):
        for label, value in self.labels:
            mark_decorator = self.__labels__[label](value)
            self._node.add_marker(mark_decorator)

    def _check_steps_was_used(self):
        not_used_steps = set(self.steps.keys()) - self._steps_was_used

        if not_used_steps:
            if hasattr(self._node, 'execution_count'):
                # No need for further rerun_failures
                self._node.execution_count = float('inf')
            raise StepsWasNotUsed(*not_used_steps)

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
        return self._instructions.get(LabelType.FEATURE)

    @property
    def story(self):
        return self._instructions.get(LabelType.STORY)

    @property
    def severity(self):
        return self._instructions.get(LabelType.SEVERITY)

    @property
    def issue(self):
        return self._instructions.get(LinkType.ISSUE)

    @property
    def test_id(self):
        return self._instructions.get(LinkType.TEST_CASE)

    @property
    def attachments(self):
        return self._instructions.get('attachments', [])

    @property
    def description(self):
        return self._instructions.get('description')

    def step(self, key, **kwargs):
        if self._description_load_error:
            raise raise_from(InvalidInstruction('Description has been loaded with error.'),
                             self._description_load_error)
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

        self._steps_was_used.add(key)

        return allure.step(step_name.format(**kwargs))

    def build(self, item):
        if self._is_built:
            return

        self._setup_description(item)
        if isinstance(self._instructions, dict):
            self._build_markers()

        self._is_built = True

    def _yaml_load(self, string):
        try:
            return yaml.load(str(string), Loader=yaml.FullLoader)
        except yaml.YAMLError as e:
            self._description_load_error = e
            return {}
