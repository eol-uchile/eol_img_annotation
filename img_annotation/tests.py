"""
Module To Test EolImgAnnotation XBlock
"""

from django.test import TestCase, Client
from mock import MagicMock, Mock, patch
from django.contrib.auth.models import User
from common.djangoapps.util.testing import UrlResetMixin
from opaque_keys.edx.locations import Location
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory
from common.djangoapps.student.roles import CourseStaffRole
from django.test.client import RequestFactory
from opaque_keys.edx.locations import SlashSeparatedCourseKey
from common.djangoapps.student.tests.factories import UserFactory, CourseEnrollmentFactory
from lms.djangoapps.courseware.tests.factories import StudentModuleFactory
from xblock.field_data import DictFieldData
from opaque_keys.edx.locator import CourseLocator
from .img_annotation import ImgAnnotationXBlock
from .models import ImgAnnotationModel

import json
import unittest
import logging
import mock

log = logging.getLogger(__name__)


class TestRequest(object):
    # pylint: disable=too-few-public-methods
    """
    Module helper for @json_handler
    """
    method = None
    body = None
    success = None


class ImgAnnotationXBlockTestCase(UrlResetMixin, ModuleStoreTestCase):
    # pylint: disable=too-many-instance-attributes, too-many-public-methods
    """
    A complete suite of unit tests for the EolImgAnnotation XBlock
    """

    def make_an_xblock(cls, **kw):
        """
        Helper method that creates a EolImgAnnotation XBlock
        """

        course = cls.course
        runtime = Mock(
            course_id=course.id,
            user_is_staff=False,
            service=Mock(
                return_value=Mock(_catalog={}),
            ),
        )
        scope_ids = Mock()
        field_data = DictFieldData(kw)
        xblock = ImgAnnotationXBlock(runtime, field_data, scope_ids)
        xblock.xmodule_runtime = runtime
        xblock.location = course.location
        xblock.course_id = course.id
        xblock.category = 'img_annotation'
        return xblock

    def setUp(self):
        super(ImgAnnotationXBlockTestCase, self).setUp()
        """
        Creates an xblock
        """
        self.course = CourseFactory.create(org='foo', course='baz', run='bar')

        self.xblock = self.make_an_xblock()
        self.annotation = {
            "type": "Annotation",
            "body": [{"type": "TextualBody", "purpose": "highlighting", "value": "GREEN", "creator": {"id": "Luchin101", "name": "Luchin101"}, "created": "2021-11-18T19:21:20.739Z"}, {"type": "TextualBody", "value": "adasdsadsad", "purpose": "commenting", "creator": {"id": "Luchin101", "name": "Luchin101"}, "created": "2021-11-18T19:21:22.300Z", "modified": "2021-11-18T19:21:23.010Z"}],
            "target": {
                "selector": {
                    "type": "FragmentSelector",
                    "conformsTo": "http://www.w3.org/TR/media-frags/",
                    "value": "target"
                }
            },
            "@context": "http://www.w3.org/ns/anno.jsonld",
            "id": "#123-456-789"
        }

        with patch('common.djangoapps.student.models.cc.User.save'):
            # Create the student
            self.student = UserFactory(
                username='student',
                password='test',
                email='student@edx.org')
            # Enroll the student in the course
            CourseEnrollmentFactory(
                user=self.student, course_id=self.course.id)

            # Create staff user
            self.staff_user = UserFactory(
                username='staff_user',
                password='test',
                email='staff@edx.org')
            CourseEnrollmentFactory(
                user=self.staff_user,
                course_id=self.course.id)
            CourseStaffRole(self.course.id).add_users(self.staff_user)

    def test_validate_field_data(self):
        """
            Verify if default xblock is created correctly
        """
        self.assertEqual(self.xblock.display_name, 'Imagen Annotation')
        self.assertEqual(self.xblock.puntajemax, 1)
        self.assertEqual(self.xblock.header_text, "")
        self.assertEqual(self.xblock.image_url, "")

    def test_edit_block_studio(self):
        """
            Verify submit studio edits is working
        """
        request = TestRequest()
        request.method = 'POST'
        self.xblock.xmodule_runtime.user_is_staff = True
        data = json.dumps({
            'display_name': 'testname', 
            "puntajemax": '10',
            "header_text":'text test',
            "image_url": "this is a url"})
        request.body = data.encode()
        response = self.xblock.studio_submit(request)
        self.assertEqual(self.xblock.display_name, 'testname')
        self.assertEqual(self.xblock.puntajemax, 10)
        self.assertEqual(self.xblock.header_text, 'text test',)
        self.assertEqual(self.xblock.image_url, "this is a url")

    def test_edit_block_studio_error(self):
        """
            Verify submit studio edits is working
        """
        request = TestRequest()
        request.method = 'POST'
        self.xblock.xmodule_runtime.user_is_staff = True
        data = json.dumps({
            'display_name': 'testname', 
            "puntajemax": 'asd',
            "header_text":'text test',
            "image_url": "this is a url"})
        request.body = data.encode()
        response = self.xblock.studio_submit(request)
        data_response = json.loads(response._app_iter[0].decode())
        self.assertEqual(data_response['result'], 'error')

    def test_author_create_annotation(self):
        request = TestRequest()
        request.method = 'POST'
        self.xblock.scope_ids.user_id = self.staff_user.id
        self.xblock.xmodule_runtime.user_is_staff = True
        data = json.dumps({
            'annotation': self.annotation})
        request.body = data.encode()
        response = self.xblock.save_anno_xblock(request)
        data_response = json.loads(response._app_iter[0].decode())
        self.assertEqual(data_response['result'], 'success')
        expected = self.xblock.get_annotations(self.staff_user.id, 'staff')
        self.assertEqual(len(expected), 1)
        self.assertEqual(expected[0]['id'], self.annotation['id'])
        self.assertEqual(expected[0]['target'], self.annotation['target']['selector']['value'])
        self.assertEqual(expected[0]['body'], self.annotation['body'])

    def test_author_create_annotation_error(self):
        request = TestRequest()
        request.method = 'POST'
        self.xblock.scope_ids.user_id = self.staff_user.id
        self.xblock.xmodule_runtime.user_is_staff = True
        data = json.dumps({'annotation': {}})
        request.body = data.encode()
        response = self.xblock.save_anno_xblock(request)
        data_response = json.loads(response._app_iter[0].decode())
        self.assertEqual(data_response['result'], 'error')
        expected = self.xblock.get_annotations(self.staff_user.id, 'staff')
        self.assertEqual(len(expected), 0)
    
    def test_author_create_annotation_error_user(self):
        request = TestRequest()
        request.method = 'POST'
        self.xblock.scope_ids.user_id = self.student.id
        self.xblock.xmodule_runtime.user_is_staff = False
        data = json.dumps({'annotation': {}})
        request.body = data.encode()
        response = self.xblock.save_anno_xblock(request)
        data_response = json.loads(response._app_iter[0].decode())
        self.assertEqual(data_response['result'], 'error')
        expected = self.xblock.get_annotations(self.staff_user.id, 'staff')
        self.assertEqual(len(expected), 0)

    def test_update_annotation(self):
        anno = ImgAnnotationModel.objects.create(
            annotation_id = "#123-456-789",
            user = self.staff_user,
            role = 'staff',
            body = '[]',
            course_key = self.course.id,
            usage_key = self.xblock.location,
            target = 'test target'
        )
        request = TestRequest()
        request.method = 'POST'
        self.xblock.scope_ids.user_id = self.staff_user.id
        self.xblock.xmodule_runtime.user_is_staff = True
        data = json.dumps({
            'annotation': self.annotation})
        request.body = data.encode()
        response = self.xblock.updatestudentannotations(request)
        data_response = json.loads(response._app_iter[0].decode())
        self.assertEqual(data_response['result'], 'success')
        expected = self.xblock.get_annotations(self.staff_user.id, 'staff')
        self.assertEqual(len(expected), 1)
        self.assertEqual(expected[0]['id'], self.annotation['id'])
        self.assertEqual(expected[0]['target'], self.annotation['target']['selector']['value'])
        self.assertEqual(expected[0]['body'], self.annotation['body'])

    def test_update_annotation_staff(self):
        anno = ImgAnnotationModel.objects.create(
            annotation_id = "#123-456-789",
            user = self.student,
            role = 'student',
            body = '[]',
            course_key = self.course.id,
            usage_key = self.xblock.location,
            target = 'test target'
        )
        request = TestRequest()
        request.method = 'POST'
        self.xblock.scope_ids.user_id = self.staff_user.id
        self.xblock.xmodule_runtime.user_is_staff = True
        data = json.dumps({
            'annotation': self.annotation,
            'student_id': self.student.id
            })
        request.body = data.encode()
        response = self.xblock.updatestudentannotationsstaff(request)
        data_response = json.loads(response._app_iter[0].decode())
        self.assertEqual(data_response['result'], 'success')
        expected = self.xblock.get_annotations(self.student.id, 'student')
        self.assertEqual(len(expected), 1)
        self.assertEqual(expected[0]['id'], self.annotation['id'])
        self.assertEqual(expected[0]['target'], anno.target)
        self.assertEqual(expected[0]['body'], self.annotation['body'])

    def test_update_annotation_staff_error(self):
        anno = ImgAnnotationModel.objects.create(
            annotation_id = "#123-456-789",
            user = self.student,
            role = 'student',
            body = '[]',
            course_key = self.course.id,
            usage_key = self.xblock.location,
            target = 'test target'
        )
        request = TestRequest()
        request.method = 'POST'
        self.xblock.scope_ids.user_id = self.staff_user.id
        self.xblock.xmodule_runtime.user_is_staff = True
        data = json.dumps({})
        request.body = data.encode()
        response = self.xblock.updatestudentannotationsstaff(request)
        data_response = json.loads(response._app_iter[0].decode())
        self.assertEqual(data_response['result'], 'error')
        expected = self.xblock.get_annotations(self.student.id, 'student')
        self.assertEqual(len(expected), 1)
        self.assertEqual(expected[0]['id'], anno.annotation_id)
        self.assertEqual(expected[0]['target'], anno.target)
        self.assertEqual(expected[0]['body'], [])

    def test_update_annotation_error(self):
        request = TestRequest()
        request.method = 'POST'
        self.xblock.scope_ids.user_id = self.staff_user.id
        self.xblock.xmodule_runtime.user_is_staff = True
        data = json.dumps({'annotation': {}})
        request.body = data.encode()
        response = self.xblock.updatestudentannotations(request)
        data_response = json.loads(response._app_iter[0].decode())
        self.assertEqual(data_response['result'], 'error')
        expected = self.xblock.get_annotations(self.staff_user.id, 'staff')
        self.assertEqual(len(expected), 0)

    def test_delete_annotation(self):
        anno = ImgAnnotationModel.objects.create(
            annotation_id = self.annotation['id'],
            user = self.staff_user,
            role = 'staff',
            body = '[]',
            course_key = self.course.id,
            usage_key = self.xblock.location,
            target = 'test target'
        )
        request = TestRequest()
        request.method = 'POST'
        self.xblock.scope_ids.user_id = self.staff_user.id
        self.xblock.xmodule_runtime.user_is_staff = True
        data = json.dumps({
            'id': self.annotation['id']})
        request.body = data.encode()
        expected = self.xblock.get_annotations(self.staff_user.id, 'staff')
        self.assertEqual(len(expected), 1)
        response = self.xblock.removestudentannotations(request)
        data_response = json.loads(response._app_iter[0].decode())
        self.assertEqual(data_response['result'], 'success')
        expected = self.xblock.get_annotations(self.staff_user.id, 'staff')
        self.assertEqual(len(expected), 0)

    def test_delete_annotation_error(self):
        anno = ImgAnnotationModel.objects.create(
            annotation_id = '#789-456',
            user = self.staff_user,
            role = 'staff',
            body = '[]',
            course_key = self.course.id,
            usage_key = self.xblock.location,
            target = 'test target'
        )
        request = TestRequest()
        request.method = 'POST'
        self.xblock.scope_ids.user_id = self.staff_user.id
        self.xblock.xmodule_runtime.user_is_staff = True
        data = json.dumps({
            'asd': self.annotation['id']})
        request.body = data.encode()
        expected = self.xblock.get_annotations(self.staff_user.id, 'staff')
        self.assertEqual(len(expected), 1)
        response = self.xblock.removestudentannotations(request)
        data_response = json.loads(response._app_iter[0].decode())
        self.assertEqual(data_response['result'], 'error')
        expected = self.xblock.get_annotations(self.staff_user.id, 'staff')
        self.assertEqual(len(expected), 1)

    def test_delete_annotation_error_2(self):
        anno = ImgAnnotationModel.objects.create(
            annotation_id = '#789-456',
            user = self.staff_user,
            role = 'staff',
            body = '[]',
            course_key = self.course.id,
            usage_key = self.xblock.location,
            target = 'test target'
        )
        request = TestRequest()
        request.method = 'POST'
        self.xblock.scope_ids.user_id = self.staff_user.id
        self.xblock.xmodule_runtime.user_is_staff = True
        data = json.dumps({
            'id': self.annotation['id']})
        request.body = data.encode()
        expected = self.xblock.get_annotations(self.staff_user.id, 'staff')
        self.assertEqual(len(expected), 1)
        response = self.xblock.removestudentannotations(request)
        data_response = json.loads(response._app_iter[0].decode())
        self.assertEqual(data_response['result'], 'error')
        expected = self.xblock.get_annotations(self.staff_user.id, 'staff')
        self.assertEqual(len(expected), 1)

    def test_student_view_staff(self):
        """
            Verify context in student_view staff user
        """
        expected_context = {
            'list_annotation_student': [],
            'is_course_staff': True,
            'calificado': 0,
            'total_student': 2,
            'list_annotation_staff':[]
        }
        expected_settings = {
            'username': self.staff_user.username,
            'image_url': '',
            'puntajemax' : 1,
            'is_course_staff': True,
            'list_annotation_staff': [],
            'annotation_staff': []
        }
        self.xblock.xmodule_runtime.user_is_staff = True
        self.xblock.scope_ids.user_id = self.staff_user.id
        context, settings = self.xblock.get_context_settings()
        for key in expected_context:
            self.assertEqual(expected_context[key], context[key])
        for key in expected_settings:
            self.assertEqual(expected_settings[key], settings[key])

    def test_student_view_student(self):
        """
            Verify context in student_view student user
        """
        expected_context = {
            'list_annotation_student': [],
            'is_course_staff': False,
            'score': '',
            'comentario': '',
            'list_annotation_staff':[]
        }
        expected_settings = {
            'username': self.student.username,
            'image_url': '',
            'puntajemax' : 1,
            'is_course_staff': False,
            'list_annotation_staff': [],
            'annotation_staff': [],
            'annotation':[]
        }
        self.xblock.xmodule_runtime.user_is_staff = False
        self.xblock.scope_ids.user_id = self.student.id
        context, settings = self.xblock.get_context_settings()
        for key in expected_context:
            self.assertEqual(expected_context[key], context[key])
        for key in expected_settings:
            self.assertEqual(expected_settings[key], settings[key])

    def test_student_create_annotation(self):
        request = TestRequest()
        request.method = 'POST'
        self.xblock.scope_ids.user_id = self.student.id
        self.xblock.xmodule_runtime.user_is_staff = False
        data = json.dumps({
            'annotation': self.annotation})
        request.body = data.encode()
        response = self.xblock.savestudentannotations(request)
        data_response = json.loads(response._app_iter[0].decode())
        self.assertEqual(data_response['result'], 'success')
        expected = self.xblock.get_annotations(self.student.id, 'student')
        self.assertEqual(len(expected), 1)
        self.assertEqual(expected[0]['id'], self.annotation['id'])
        self.assertEqual(expected[0]['target'], self.annotation['target']['selector']['value'])
        self.assertEqual(expected[0]['body'], self.annotation['body'])

    def test_student_create_annotation_error(self):
        request = TestRequest()
        request.method = 'POST'
        self.xblock.scope_ids.user_id = self.student.id
        self.xblock.xmodule_runtime.user_is_staff = False
        data = json.dumps({'annotation': {}})
        request.body = data.encode()
        response = self.xblock.savestudentannotations(request)
        data_response = json.loads(response._app_iter[0].decode())
        self.assertEqual(data_response['result'], 'error')
        expected = self.xblock.get_annotations(self.student.id, 'student')
        self.assertEqual(len(expected), 0)

    def test_student_create_annotation_error_2(self):
        request = TestRequest()
        request.method = 'POST'
        self.xblock.scope_ids.user_id = None
        self.xblock.xmodule_runtime.user_is_staff = False
        data = json.dumps({'annotation': {}})
        request.body = data.encode()
        response = self.xblock.savestudentannotations(request)
        data_response = json.loads(response._app_iter[0].decode())
        self.assertEqual(data_response['result'], 'error')
        expected = self.xblock.get_annotations(self.student.id, 'student')
        self.assertEqual(len(expected), 0)

    def test_get_student_data(self):
        request = TestRequest()
        request.method = 'POST'
        self.xblock.scope_ids.user_id = self.staff_user.id
        self.xblock.xmodule_runtime.user_is_staff = True
        data = json.dumps({})
        request.body = data.encode()
        response = self.xblock.get_student_data(request)
        data_response = json.loads(response._app_iter[0].decode())
        self.assertEqual(data_response['result'], 'success')
        expected = [
            {
            'id': self.staff_user.id,
            'username': self.staff_user.username,
            'score': ''},
            {
            'id': self.student.id,
            'username': self.student.username,
            'score': ''
            }
        ]
        self.assertEqual(data_response['lista_alumnos'], expected)
    
    @patch('lms.djangoapps.grades.signals.handlers.PROBLEM_WEIGHTED_SCORE_CHANGED.send')
    def test_get_student_data_with_score(self, _):
        request = TestRequest()
        request.method = 'POST'
        self.xblock.scope_ids.user_id = self.staff_user.id
        self.xblock.xmodule_runtime.user_is_staff = True
        
        data = json.dumps({"student_id": self.student.id, "puntaje": 1, "comentario": 'comentario'})
        request.body = data.encode()
        response = self.xblock.save_data_student(request)
        data_response = json.loads(response._app_iter[0].decode())
        self.assertEqual(data_response['result'], 'success')

        data = json.dumps({})
        request.body = data.encode()
        response = self.xblock.get_student_data(request)
        data_response = json.loads(response._app_iter[0].decode())
        self.assertEqual(data_response['result'], 'success')
        expected = [
            {
            'id': self.staff_user.id,
            'username': self.staff_user.username,
            'score': ''},
            {
            'id': self.student.id,
            'username': self.student.username,
            'score': 1
            }
        ]
        self.assertEqual(data_response['lista_alumnos'], expected)

    def test_get_student_data_error(self):
        request = TestRequest()
        request.method = 'POST'
        self.xblock.scope_ids.user_id = self.student.id
        self.xblock.xmodule_runtime.user_is_staff = False
        data = json.dumps({})
        request.body = data.encode()
        response = self.xblock.get_student_data(request)
        data_response = json.loads(response._app_iter[0].decode())
        self.assertEqual(data_response['result'], 'error')

    @patch('lms.djangoapps.grades.signals.handlers.PROBLEM_WEIGHTED_SCORE_CHANGED.send')
    def test_save_data_student(self, _):
        request = TestRequest()
        request.method = 'POST'
        self.xblock.scope_ids.user_id = self.staff_user.id
        self.xblock.xmodule_runtime.user_is_staff = True
        data = json.dumps({"student_id": self.student.id, "puntaje": 1, "comentario": 'comentario'})
        request.body = data.encode()
        response = self.xblock.save_data_student(request)
        data_response = json.loads(response._app_iter[0].decode())
        self.assertEqual(data_response['result'], 'success')
        self.assertEqual(data_response['calificado'], False)
        score = self.xblock.get_score(self.student.id)
        comment = self.xblock.get_comment(self.student.id)
        self.assertEqual(score, 1)
        self.assertEqual(comment['comment'], 'comentario')

    @patch('lms.djangoapps.grades.signals.handlers.PROBLEM_WEIGHTED_SCORE_CHANGED.send')
    def test_save_data_student_min_score(self, _):
        request = TestRequest()
        request.method = 'POST'
        self.xblock.scope_ids.user_id = self.staff_user.id
        self.xblock.xmodule_runtime.user_is_staff = True
        data = json.dumps({"student_id": self.student.id, "puntaje": 0, "comentario": 'comentario'})
        request.body = data.encode()
        response = self.xblock.save_data_student(request)
        data_response = json.loads(response._app_iter[0].decode())
        self.assertEqual(data_response['result'], 'success')
        self.assertEqual(data_response['calificado'], False)
        score = self.xblock.get_score(self.student.id)
        comment = self.xblock.get_comment(self.student.id)
        self.assertEqual(score, 0)
        self.assertEqual(comment['comment'], 'comentario')

    @patch('lms.djangoapps.grades.signals.handlers.PROBLEM_WEIGHTED_SCORE_CHANGED.send')
    def test_save_data_student_error_score(self, _):
        request = TestRequest()
        request.method = 'POST'
        self.xblock.scope_ids.user_id = self.staff_user.id
        self.xblock.xmodule_runtime.user_is_staff = True
        data = json.dumps({"student_id": self.student.id, "puntaje": 0.5, "comentario": 'comentario'})
        request.body = data.encode()
        response = self.xblock.save_data_student(request)
        data_response = json.loads(response._app_iter[0].decode())
        self.assertEqual(data_response['result'], 'error')
    
    @patch('lms.djangoapps.grades.signals.handlers.PROBLEM_WEIGHTED_SCORE_CHANGED.send')
    def test_save_data_student_error_score_2(self, _):
        request = TestRequest()
        request.method = 'POST'
        self.xblock.scope_ids.user_id = self.staff_user.id
        self.xblock.xmodule_runtime.user_is_staff = True
        data = json.dumps({"student_id": self.student.id, "puntaje": 'asd', "comentario": 'comentario'})
        request.body = data.encode()
        response = self.xblock.save_data_student(request)
        data_response = json.loads(response._app_iter[0].decode())
        self.assertEqual(data_response['result'], 'error')
    
    @patch('lms.djangoapps.grades.signals.handlers.PROBLEM_WEIGHTED_SCORE_CHANGED.send')
    def test_save_data_student_error_max_score(self, _):
        request = TestRequest()
        request.method = 'POST'
        self.xblock.scope_ids.user_id = self.staff_user.id
        self.xblock.xmodule_runtime.user_is_staff = True
        data = json.dumps({"student_id": self.student.id, "puntaje": '3', "comentario": 'comentario'})
        request.body = data.encode()
        response = self.xblock.save_data_student(request)
        data_response = json.loads(response._app_iter[0].decode())
        self.assertEqual(data_response['result'], 'error')

    @patch('lms.djangoapps.grades.signals.handlers.PROBLEM_WEIGHTED_SCORE_CHANGED.send')
    def test_save_data_student_error_min_score(self, _):
        request = TestRequest()
        request.method = 'POST'
        self.xblock.scope_ids.user_id = self.staff_user.id
        self.xblock.xmodule_runtime.user_is_staff = True
        data = json.dumps({"student_id": self.student.id, "puntaje": '-1', "comentario": 'comentario'})
        request.body = data.encode()
        response = self.xblock.save_data_student(request)
        data_response = json.loads(response._app_iter[0].decode())
        self.assertEqual(data_response['result'], 'error')

    @patch('lms.djangoapps.grades.signals.handlers.PROBLEM_WEIGHTED_SCORE_CHANGED.send')
    def test_save_data_student_error_user_role(self, _):
        request = TestRequest()
        request.method = 'POST'
        self.xblock.scope_ids.user_id = self.student.id
        self.xblock.xmodule_runtime.user_is_staff = False
        data = json.dumps({"student_id": self.student.id, "puntaje": 1, "comentario": 'comentario'})
        request.body = data.encode()
        response = self.xblock.save_data_student(request)
        data_response = json.loads(response._app_iter[0].decode())
        self.assertEqual(data_response['result'], 'error')
    
    def test_get_student_annotation(self):
        request = TestRequest()
        request.method = 'POST'
        self.xblock.scope_ids.user_id = self.staff_user.id
        self.xblock.xmodule_runtime.user_is_staff = True
        data = json.dumps({"id": self.student.id})
        request.body = data.encode()
        response = self.xblock.get_student_annotation(request)
        data_response = json.loads(response._app_iter[0].decode())
        expected = {'result': 'success', 'annotation': [], 'score': '', 'comment': '', 'username': self.student.username}
        self.assertEqual(data_response, expected)
    
    @patch('lms.djangoapps.grades.signals.handlers.PROBLEM_WEIGHTED_SCORE_CHANGED.send')
    def test_get_student_annotation_with_data(self, _):
        request = TestRequest()
        request.method = 'POST'
        self.xblock.scope_ids.user_id = self.staff_user.id
        self.xblock.xmodule_runtime.user_is_staff = True
        
        data = json.dumps({"student_id": self.student.id, "puntaje": 1, "comentario": 'comentario'})
        request.body = data.encode()
        response = self.xblock.save_data_student(request)
        data_response = json.loads(response._app_iter[0].decode())
        self.assertEqual(data_response['result'], 'success')
        
        data = json.dumps({"id": self.student.id})
        request.body = data.encode()
        response = self.xblock.get_student_annotation(request)
        data_response = json.loads(response._app_iter[0].decode())
        expected = {'result': 'success', 'annotation': [], 'score': 1, 'comment': 'comentario', 'username': self.student.username}
        self.assertEqual(data_response, expected)

    def test_get_student_annotation_wrong_user_role(self):
        request = TestRequest()
        request.method = 'POST'
        self.xblock.scope_ids.user_id = self.student.id
        self.xblock.xmodule_runtime.user_is_staff = False
        data = json.dumps({"id": self.student.id})
        request.body = data.encode()
        response = self.xblock.get_student_annotation(request)
        data_response = json.loads(response._app_iter[0].decode())
        expected = {'result': 'error'}
        self.assertEqual(data_response, expected)
    
    def test_get_student_annotation_wrong_id(self):
        request = TestRequest()
        request.method = 'POST'
        self.xblock.scope_ids.user_id = self.staff_user.id
        self.xblock.xmodule_runtime.user_is_staff = True
        data = json.dumps({"id": None})
        request.body = data.encode()
        response = self.xblock.get_student_annotation(request)
        data_response = json.loads(response._app_iter[0].decode())
        expected = {'result': 'error'}
        self.assertEqual(data_response, expected)
