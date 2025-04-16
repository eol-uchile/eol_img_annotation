"""
Module To Test EolImgAnnotation XBlock
"""

# Python Standard Libraries
import json
import logging
from collections import namedtuple

# Installed packages (via pip)
import xmltodict
from common.djangoapps.util.testing import UrlResetMixin
from mock import Mock, patch


# Edx dependencies
from common.djangoapps.student.tests.factories import UserFactory, CourseEnrollmentFactory
from xblock.field_data import DictFieldData
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory


# Internal project dependencies
from .img_annotation import ImgAnnotationXBlock
from .models import ImgAnnotationModel

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

    def xml_to_dict(self, xml):
        data = xmltodict.parse(xml)
        dzi_format ={
            'Image': {
                'xmlns': data['Image']['@xmlns'],
                'Url': 'https://test.image.cl/image_files/',
                'Format': data['Image']['@Format'], 
                'Overlap': data['Image']['@Overlap'], 
                'TileSize': data['Image']['@TileSize'],
                'Size': {
                    'Height': data['Image']['Size']['@Height'],
                    'Width': data['Image']['Size']['@Width']
                }
            }
        }
        return dzi_format

    def setUp(self):
        super(ImgAnnotationXBlockTestCase, self).setUp()
        """
        Creates an xblock
        """
        self.course = CourseFactory.create(org='foo', course='baz', run='bar')
        self.xml_data = '<?xml version="1.0" encoding="UTF-8"?>\n<Image xmlns="http://schemas.microsoft.com/deepzoom/2008"\n  Format="jpeg"\n  Overlap="1"\n  TileSize="256"\n  >\n  <Size \n    Height="32256"\n    Width="65536"\n  />\n</Image>\n' 
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
        self.rectangle_ovelay = {
            'type': 'highlighted_overlay',
            'position_x': 0.3,
            'position_y': 0.4,
            'width': 0.1,
            'height': 0.1
        }
        self.arrow_overlay = {
            'type': 'fixed_size_overlay',
            'position_x': 0.5,
            'position_y': 0.6
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
            Verify submit studio edits when fail
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
        """
            Test create annotations in author view
        """
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

    @patch('img_annotation.img_annotation.ImgAnnotationXBlock.is_instructor')
    def test_author_create_annotation_instructor(self, is_instructor):
        """
            Test create annotations in author view when user is instructor
        """
        request = TestRequest()
        request.method = 'POST'
        self.xblock.scope_ids.user_id = self.staff_user.id
        self.xblock.xmodule_runtime.user_is_staff = False
        is_instructor.return_value = True
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
        """
            Test create annotations in author view when no exists data in post
        """
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
        """
            Test create annotations in author view, when user dont have permission
        """
        request = TestRequest()
        request.method = 'POST'
        self.xblock.scope_ids.user_id = self.student.id
        self.xblock.xmodule_runtime.user_is_staff = False
        data = json.dumps({'annotation': self.annotation})
        request.body = data.encode()
        response = self.xblock.save_anno_xblock(request)
        data_response = json.loads(response._app_iter[0].decode())
        self.assertEqual(data_response['result'], 'error')
        expected = self.xblock.get_annotations(self.staff_user.id, 'staff')
        self.assertEqual(len(expected), 0)

    def test_update_annotation(self):
        """
            Test update annotations
        """
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

    def test_get_annotation(self):
        """
            Test get annotations
        """
        anno = ImgAnnotationModel.objects.create(
            annotation_id = "#123-456-789",
            user = self.staff_user,
            role = 'staff',
            body = 'asdasdsa',
            course_key = self.course.id,
            usage_key = self.xblock.location,
            target = 'test target'
        )
        anno2 = ImgAnnotationModel.objects.create(
            annotation_id = "#333-456-789",
            user = self.student,
            role = 'student',
            body = json.dumps(self.annotation['body']),
            course_key = self.course.id,
            usage_key = self.xblock.location,
            target = 'test target'
        )
        response = self.xblock.get_annotations_author()
        self.assertEqual(len(response), 1)
        self.assertEqual(response[0]['id'], anno.annotation_id)
        self.assertEqual(response[0]['target'], anno.target)
        self.assertEqual(response[0]['body'], '')
        response = self.xblock.get_annotations(self.student.id, 'student')
        self.assertEqual(len(response), 1)
        self.assertEqual(response[0]['id'], anno2.annotation_id)
        self.assertEqual(response[0]['target'], anno2.target)
        self.assertEqual(response[0]['body'], self.annotation['body'])

    def test_update_annotation_staff(self):
        """
            Test update annotations, when user is staff
        """
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
        """
            Test update annotations, when user is staff, when no exists data in post
        """
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
        """
            Test update annotations when no exists data in post
        """
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
        """
            Test delete annotations
        """
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
        """
            Test delete annotations, id annotation no exists in post data
        """
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
        """
            Test delete annotations, when annotation no exists 
        """
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
            Verify context and settings in student_view staff user
        """
        expected_context = {
            'list_annotation_student': [],
            'is_course_staff': True,
            'calificado': 0,
            'total_student': 2,
            'list_annotation_staff':[],
            'have_data': False
        }
        expected_settings = {
            'username': self.staff_user.username,
            'puntajemax' : 1,
            'is_course_staff': True,
            'list_annotation_staff': [],
            'annotation_staff': [],
            'image_data': {}
        }
        self.xblock.xmodule_runtime.user_is_staff = True
        self.xblock.scope_ids.user_id = self.staff_user.id
        context, settings = self.xblock.get_context_settings()
        for key in expected_context:
            self.assertEqual(expected_context[key], context[key])
        for key in expected_settings:
            self.assertEqual(expected_settings[key], settings[key])

    @patch('requests.get')
    def test_student_view_staff_with_image_url(self, get):
        """
            Verify context and settings in student_view staff user
        """
        get.side_effect = [namedtuple("Request", ["status_code", "text"])(200, self.xml_data)]
        expected_context = {
            'list_annotation_student': [],
            'is_course_staff': True,
            'calificado': 0,
            'total_student': 2,
            'list_annotation_staff':[],
            'have_data': True
        }
        expected_settings = {
            'username': self.staff_user.username,
            'puntajemax' : 1,
            'is_course_staff': True,
            'list_annotation_staff': [],
            'annotation_staff': [],
            'image_data': self.xml_to_dict(self.xml_data)
        }
        self.xblock.image_url = 'https://test.image.cl/image.dzi'
        self.xblock.xmodule_runtime.user_is_staff = True
        self.xblock.scope_ids.user_id = self.staff_user.id
        context, settings = self.xblock.get_context_settings()
        for key in expected_context:
            self.assertEqual(expected_context[key], context[key])
        for key in expected_settings:
            self.assertEqual(expected_settings[key], settings[key])

    @patch('requests.get')
    def test_student_view_staff_wrong_image_data(self, get):
        """
            Verify context and settings in student_view staff user
        """
        get.side_effect = [namedtuple("Request", ["status_code", "text"])(200, 'asdsadsadas')]
        expected_context = {
            'list_annotation_student': [],
            'is_course_staff': True,
            'calificado': 0,
            'total_student': 2,
            'list_annotation_staff':[],
            'have_data': False
        }
        expected_settings = {
            'username': self.staff_user.username,
            'puntajemax' : 1,
            'is_course_staff': True,
            'list_annotation_staff': [],
            'annotation_staff': [],
            'image_data': {}
        }
        self.xblock.image_url = 'https://test.image.cl/image.dzi'
        self.xblock.xmodule_runtime.user_is_staff = True
        self.xblock.scope_ids.user_id = self.staff_user.id
        context, settings = self.xblock.get_context_settings()
        for key in expected_context:
            self.assertEqual(expected_context[key], context[key])
        for key in expected_settings:
            self.assertEqual(expected_settings[key], settings[key])

    @patch('requests.get')
    def test_student_view_staff_wrong_image_data_2(self, get):
        """
            Verify context and settings in student_view staff user
        """
        aux = '<?xml version="1.0" encoding="UTF-8"?>\n<Video xmlns="http://schemas.microsoft.com/deepzoom/2008"\n  Format="jpeg"\n  Overlap="1"\n  TileSize="256"\n  >\n  <Size \n    Height="32256"\n    Width="65536"\n  />\n</Video>\n' 
        get.side_effect = [namedtuple("Request", ["status_code", "text"])(200, aux)]
        expected_context = {
            'list_annotation_student': [],
            'is_course_staff': True,
            'calificado': 0,
            'total_student': 2,
            'list_annotation_staff':[],
            'have_data': False
        }
        expected_settings = {
            'username': self.staff_user.username,
            'puntajemax' : 1,
            'is_course_staff': True,
            'list_annotation_staff': [],
            'annotation_staff': [],
            'image_data': {}
        }
        self.xblock.image_url = 'https://test.image.cl/image.dzi'
        self.xblock.xmodule_runtime.user_is_staff = True
        self.xblock.scope_ids.user_id = self.staff_user.id
        context, settings = self.xblock.get_context_settings()
        for key in expected_context:
            self.assertEqual(expected_context[key], context[key])
        for key in expected_settings:
            self.assertEqual(expected_settings[key], settings[key])

    @patch('requests.get')
    def test_student_view_staff_wrong_request_image(self, get):
        """
            Verify context and settings in student_view staff user
        """
        get.side_effect = [namedtuple("Request", ["status_code", "text"])(403, self.xml_data)]
        expected_context = {
            'list_annotation_student': [],
            'is_course_staff': True,
            'calificado': 0,
            'total_student': 2,
            'list_annotation_staff':[],
            'have_data': False
        }
        expected_settings = {
            'username': self.staff_user.username,
            'puntajemax' : 1,
            'is_course_staff': True,
            'list_annotation_staff': [],
            'annotation_staff': [],
            'image_data': {}
        }
        self.xblock.image_url = 'https://test.image.cl/image.dzi'
        self.xblock.xmodule_runtime.user_is_staff = True
        self.xblock.scope_ids.user_id = self.staff_user.id
        context, settings = self.xblock.get_context_settings()
        for key in expected_context:
            self.assertEqual(expected_context[key], context[key])
        for key in expected_settings:
            self.assertEqual(expected_settings[key], settings[key])

    def test_student_view_student(self):
        """
            Verify context and settings in student_view student user
        """
        expected_context = {
            'list_annotation_student': [],
            'is_course_staff': False,
            'score': '',
            'comentario': '',
            'list_annotation_staff':[],
            'have_data': False
        }
        expected_settings = {
            'username': self.student.username,
            'puntajemax' : 1,
            'is_course_staff': False,
            'list_annotation_staff': [],
            'annotation_staff': [],
            'annotation':[],
            'image_data': {}
        }
        self.xblock.xmodule_runtime.user_is_staff = False
        self.xblock.scope_ids.user_id = self.student.id
        context, settings = self.xblock.get_context_settings()
        for key in expected_context:
            self.assertEqual(expected_context[key], context[key])
        for key in expected_settings:
            self.assertEqual(expected_settings[key], settings[key])

    def test_student_create_annotation(self):
        """
            Test create annotation, student user
        """
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
        """
            Test create annotation, student user, when annotation data mp exists in post data
        """
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
        """
            Test create annotation, anonymous user
        """
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
        """
            Verify the student data of get_student_data()
        """
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
        """
            Verify the student data of get_student_data(), when user have score
        """
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
        """
            Verify the student data of get_student_data(), when user dont have permission
        """
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
        """
            test save user score and comment
        """
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
        """
            test save user score and comment, when score is minimum
        """
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
        """
            test save user score and comment, when score is float
        """
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
        """
            test save user score and comment, when score is not a number
        """
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
        """
            test save user score and comment, when score is maximum
        """
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
        """
            test save user score and comment, when score is less than the minimum
        """
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
        """
            test save user score and comment, when user dont have permission
        """
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
        """
            Test get student annotations, score and comment
        """
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
        """
            Test get student annotations, score and comment, when already have data
        """
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
        """
            Test get student annotations, score and comment, when user dont have permission
        """
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
        """
            Test get student annotations, score and comment, when id student is None
        """
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

    def test_author_create_rect_overlay(self):
        """
            Test create rectangle overlay in author view
        """
        request = TestRequest()
        request.method = 'POST'
        self.xblock.scope_ids.user_id = self.staff_user.id
        self.xblock.xmodule_runtime.user_is_staff = True
        data = json.dumps({
            'overlay': self.rectangle_ovelay})
        request.body = data.encode()
        response = self.xblock.save_overlay_xblock(request)
        data_response = json.loads(response._app_iter[0].decode())
        self.assertEqual(data_response['result'], 'success')
        expected = self.xblock.get_overlays()
        self.assertEqual(len(expected), 1)
        self.assertEqual(expected[0]['type'], self.rectangle_ovelay['type'])
        self.assertEqual(float(expected[0]['position_x']), self.rectangle_ovelay['position_x'])
        self.assertEqual(float(expected[0]['position_y']), self.rectangle_ovelay['position_y'])
        self.assertEqual(float(expected[0]['width']), self.rectangle_ovelay['width'])
        self.assertEqual(float(expected[0]['height']), self.rectangle_ovelay['height'])

    def test_author_create_arrow_overlay(self):
        """
            Test create arrow overlay in author view
        """
        request = TestRequest()
        request.method = 'POST'
        self.xblock.scope_ids.user_id = self.staff_user.id
        self.xblock.xmodule_runtime.user_is_staff = True
        data = json.dumps({
            'overlay': self.arrow_overlay})
        request.body = data.encode()
        response = self.xblock.save_overlay_xblock(request)
        data_response = json.loads(response._app_iter[0].decode())
        self.assertEqual(data_response['result'], 'success')
        expected = self.xblock.get_overlays()
        self.assertEqual(len(expected), 1)
        self.assertEqual(expected[0]['type'], self.arrow_overlay['type'])
        self.assertEqual(float(expected[0]['position_x']), self.arrow_overlay['position_x'])
        self.assertEqual(float(expected[0]['position_y']), self.arrow_overlay['position_y'])

    def test_author_create_overlay_error(self):
        """
            Test create arrow overlay in author view error 
        """
        request = TestRequest()
        request.method = 'POST'
        self.xblock.scope_ids.user_id = self.staff_user.id
        self.xblock.xmodule_runtime.user_is_staff = True
        data = json.dumps({
            'overlay': {
                'type': 'error_overlay', 
                "position_x": '1',
                "position_y": 'y'}})
        request.body = data.encode()
        response = self.xblock.save_overlay_xblock(request)
        data_response = json.loads(response._app_iter[0].decode())
        self.assertEqual(data_response['result'], 'error')
        expected = self.xblock.get_overlays()

    def test_delete_overlays(self):
        """
            Test delete overlays
        """
        request = TestRequest()
        request.method = 'POST'
        self.xblock.scope_ids.user_id = self.staff_user.id
        self.xblock.xmodule_runtime.user_is_staff = True
        data = json.dumps({
            'overlay': self.arrow_overlay})
        request.body = data.encode()
        response = self.xblock.save_overlay_xblock(request)
        data_response = json.loads(response._app_iter[0].decode())
        self.assertEqual(data_response['result'], 'success')
        expected = self.xblock.get_overlays()
        delete_request = TestRequest()
        delete_request.method = 'POST'
        delete_id = json.dumps({
            'id': expected[0]['id']})
        delete_request.body = delete_id.encode()
        response_delete = self.xblock.delete_overlay_xblock(delete_request)
        data_response_delete = json.loads(response_delete._app_iter[0].decode())
        self.assertEqual(data_response_delete['result'], 'success')

    def test_delete_overlays_error(self):
        """
            Test delete overlays error
        """
        request = TestRequest()
        request.method = 'POST'
        self.xblock.scope_ids.user_id = self.staff_user.id
        self.xblock.xmodule_runtime.user_is_staff = True
        data = json.dumps({
            'overlay': self.arrow_overlay})
        request.body = data.encode()
        response = self.xblock.save_overlay_xblock(request)
        data_response = json.loads(response._app_iter[0].decode())
        self.assertEqual(data_response['result'], 'success')
        expected = self.xblock.get_overlays()
        delete_request = TestRequest()
        delete_request.method = 'POST'
        delete_id = json.dumps({
            'id': 501})
        delete_request.body = delete_id.encode()
        response_delete = self.xblock.delete_overlay_xblock(delete_request)
        data_response_delete = json.loads(response_delete._app_iter[0].decode())
        self.assertEqual(data_response_delete['result'], 'overlay not found')
        self.assertEqual(data_response_delete['overlay_id'], 501)
