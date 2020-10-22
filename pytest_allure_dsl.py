# -*- coding: utf-8 -*-

import os
from typing import Union

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
    return request.node.allure_dsl


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


NO_DESCRIPTION = object()


class Instructions:
    _listable_labels__ = [
        LabelType.FEATURE,
        LabelType.STORY,
        LabelType.EPIC,
        LinkType.LINK,
        LinkType.ISSUE,
        LinkType.TEST_CASE,
    ]

    def __init__(self):
        self._features = []
        self._stories = []
        self._epics = []
        self._issues = []
        self._links = []
        self._test_cases = []
        self._severity = None
        self._attachments = []
        self._description = NO_DESCRIPTION
        self._load_errors = []
        self._steps = {}

    def _label(self, label_type: Union[LabelType, LinkType]):
        return {
            LabelType.FEATURE: self._features,
            LabelType.STORY: self._stories,
            LabelType.EPIC: self._epics,
            LabelType.SEVERITY: self._severity,
            LinkType.LINK: self._links,
            LinkType.ISSUE: self._issues,
            LinkType.TEST_CASE: self._test_cases,
        }[label_type]

    def _store_load_error(self, e: Exception):
        self._load_errors.append(e)
        return self

    @property
    def load_errors(self):
        return self._load_errors

    @classmethod
    def from_docstring(cls, docstring: str):
        if not docstring:
            return cls()
        if not isinstance(docstring, str):
            return cls()._store_load_error(ValueError(f'Docstring is not a string, but: {str(docstring)}'))
        try:
            dictionary = yaml.load(docstring, Loader=yaml.FullLoader)
        except yaml.YAMLError as e:
            return cls()._store_load_error(e)
        return cls.from_dictionary(dictionary)

    @staticmethod
    def _extract_listable_labels(dictionary, label_type: LabelType):
        labels = dictionary.get(label_type, [])
        if not isinstance(labels, list):
            labels = [labels]
        for label in labels:
            if not isinstance(label, str):
                raise ValueError(f'{label_type} must be a string, but got: {str(label)}')
        return labels

    @staticmethod
    def _extract_attachments(dictionary):
        attachments = dictionary.get('attachments', [])
        if not isinstance(attachments, list):
            attachments = [attachments]
        for attachment in attachments:
            if not isinstance(attachment, dict):
                raise ValueError(f'Attachment should be a dictionary.')
            if not ('title' in attachment):
                raise ValueError(f'Title is mandatory for an attachments.')
            if not ('content' in attachment or 'file' in attachment):
                raise ValueError(f'Attachment should contains content or file link.')
        return attachments

    @classmethod
    def from_dictionary(cls, dictionary: dict):
        try:
            listable_labels = {
                label_type: cls._extract_listable_labels(dictionary, label_type)
                for label_type in cls._listable_labels__
            }
            severity = dictionary.get(LabelType.SEVERITY)
            attachments = cls._extract_attachments(dictionary)
        except Exception as e:
            return cls()._store_load_error(e)
        instance = cls()
        for label_type, labels in listable_labels.items():
            attribute = instance._label(label_type)
            attribute += labels
        instance._severity = severity
        instance._attachments = attachments
        instance._steps = dictionary.get('steps', {})
        instance._description = dictionary.get('description', NO_DESCRIPTION)
        return instance

    def merge_parent(self, parent):
        if self._load_errors:
            return
        if parent._load_errors:
            self._load_errors += parent._load_errors
            return
        for label_type in self._listable_labels__:
            attribute = self._label(label_type)
            attribute += parent._label(label_type)
        if not self._severity:
            self._severity = parent._severity
        if not (parent._description is NO_DESCRIPTION):
            if self._description is NO_DESCRIPTION:
                self._description = parent._description
            else:
                self._description = '\n'.join([
                    self._description,
                    '***',
                    parent._description
                ])

    @property
    def description(self):
        return self._description

    @property
    def steps(self):
        return self._steps

    @property
    def attachments(self):
        return self._attachments

    @property
    def labels(self):
        label_types = [
            LabelType.FEATURE,
            LabelType.STORY,
            LabelType.EPIC,
            LinkType.LINK,
            LinkType.ISSUE,
            LinkType.TEST_CASE,
        ]
        return {
            label_type: self._label(label_type)
            for label_type in label_types
            if self._label(label_type)
        }

    @property
    def labels_raveled(self):
        for label_type, label in self.labels.items():
            if label_type in self._listable_labels__:
                for _label in label:
                    yield label_type, _label
            else:
                yield label_type, label


class AllureDSL(object):
    _label_to_marker_decorator = {
        LabelType.FEATURE: allure.feature,
        LabelType.STORY: allure.story,
        LabelType.EPIC: allure.epic,
        LabelType.SEVERITY: allure.severity,
        LinkType.ISSUE: allure.issue,
        LinkType.LINK: allure.link,
        LinkType.TEST_CASE: allure.testcase,
    }

    def __init__(self, node):
        self._node = node
        self._instructions: Instructions = None
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
        parent_instructions = Instructions.from_docstring(self._node.parent.obj.__doc__)
        self._instructions.merge_parent(parent_instructions)

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

        for attach in self._instructions.attachments:
            title = attach['title']
            path = attach.get('file')
            content = attach.get('content')

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

    @property
    def description(self):
        description = self._instructions.description
        if description is NO_DESCRIPTION:
            description = ' '
        return description

    def _setup_description(self, item):
        item.add_marker(allure.description(self.description))

    def _build_markers(self):
        for label, value in self._instructions.labels_raveled:
            mark_decorator = self._label_to_marker_decorator[label](value)
            self._node.add_marker(mark_decorator)

    def _check_steps_was_used(self):
        not_used_steps = set(self.steps.keys()) - self._steps_was_used

        if not_used_steps:
            if hasattr(self._node, 'execution_count'):
                # No need for further rerun_failures
                self._node.execution_count = float('inf')
            raise StepsWasNotUsed(*not_used_steps)

    @property
    def steps(self):
        return self._instructions.steps

    def step(self, key, **kwargs):
        if self._instructions.load_errors:
            raise raise_from(InvalidInstruction('Description has been loaded with error.'),
                             self._instructions.load_errors[0])
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

        self._instructions = Instructions.from_docstring(self._node.obj.__doc__)
        self._inherit_from_parent()

        self._setup_description(item)
        self._build_markers()

        self._is_built = True
