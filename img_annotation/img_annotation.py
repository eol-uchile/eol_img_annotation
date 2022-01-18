import pkg_resources
import six
import json
import six.moves.urllib.error
import six.moves.urllib.parse
import six.moves.urllib.request

import logging
import requests
import xmltodict
from six import text_type
from xblock.core import XBlock
from xblock.fields import Integer, Scope, String, Dict, Float, Boolean, List, DateTime, JSONField
from xblock.fragment import Fragment
from xblockutils.studio_editable import StudioEditableXBlockMixin
from xblockutils.resources import ResourceLoader
from django.template import Context, Template
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey
from django.http import Http404, HttpResponse
from django.urls import reverse

logger = logging.getLogger(__name__)
loader = ResourceLoader(__name__)
# Make '_' a no-op so we can scrape strings

XBLOCK_TYPE = "img_annotation"

def _(text): return text


def reify(meth):
    """
    Decorator which caches value so it is only computed once.
    Keyword arguments:
    inst
    """
    def getter(inst):
        """
        Set value to meth name in dict and returns value.
        """
        value = meth(inst)
        inst.__dict__[meth.__name__] = value
        return value
    return property(getter)


class ImgAnnotationXBlock(StudioEditableXBlockMixin, XBlock):

    display_name = String(
        display_name="Display Name",
        help="Display name for this module",
        default="Imagen Annotation",
        scope=Scope.settings,
    )
    header_text = String(
        display_name="Encabezado",
        help="Encabezado del problema",
        default="",
        scope=Scope.settings,
    )
    image_url = String(
        display_name="Imagen Url",
        help="Url de la imagen para visualizar en el componente",
        default="",
        scope=Scope.settings,
    )
    puntajemax = Integer(
        display_name='Puntaje Máximo',
        help='Entero que representa puntaje máximo',
        default=1,
        values={'min': 0},
        scope=Scope.settings,
    )
    has_author_view = True
    has_score = True
    editable_fields = ('display_name', 'image_url', 'header_text', 'puntajemax')

    def resource_string(self, path):
        """Handy helper for getting resources from our kit."""
        data = pkg_resources.resource_string(__name__, path)
        return data.decode("utf8")

    @reify
    def block_course_id(self):
        """
        Return the course_id of the block.
        """
        return six.text_type(self.course_id)

    @reify
    def block_id(self):
        """
        Return the usage_id of the block.
        """
        return six.text_type(self.scope_ids.usage_id)

    def is_course_staff(self):
        # pylint: disable=no-member
        """
        Check if user is course staff.
        """
        return getattr(self.xmodule_runtime, 'user_is_staff', False)

    def is_instructor(self):
        # pylint: disable=no-member
        """
        Check if user role is instructor.
        """
        return self.xmodule_runtime.get_user_role() == 'instructor'

    def is_instructor(self):
        # pylint: disable=no-member
        """
        Check if user role is instructor.
        """
        return self.xmodule_runtime.get_user_role() == 'instructor'

    def show_staff_grading_interface(self):
        """
        Return if current user is staff and not in studio.
        """
        in_studio_preview = self.scope_ids.user_id is None
        return (self.is_course_staff() or self.is_instructor()) and not in_studio_preview
    
    def get_annotations(self, student_id, role):
        """
        Return annotations by student_id
        """
        from .models import ImgAnnotationModel
        
        annotations = ImgAnnotationModel.objects.filter(
            user__id=student_id,
            course_key=self.course_id,
            usage_key=self.location,
            role=role
        ).values('annotation_id', 'body', 'target')

        return [{'id': x['annotation_id'], 'body': json.loads(x['body']), 'target': x['target']} for x in annotations]

    def max_score(self):
        return self.puntajemax

    def get_annotations_author(self):
        """
        Return annotations by student_id, author view
        """
        from .models import ImgAnnotationModel
        
        annotations = ImgAnnotationModel.objects.filter(
            course_key=self.course_id,
            usage_key=self.location,
            role='staff'
        ).values('annotation_id', 'body', 'target')

        return [{'id': x['annotation_id'], 'body': json.loads(x['body']), 'target': x['target']} for x in annotations]

    def delete_annotation(self, student_id, annotation_id):
        """
        delete annotation by annotation id and student id
        """
        try:
            from .models import ImgAnnotationModel
            aux = ImgAnnotationModel.objects.filter(
                annotation_id=annotation_id,
                user__id=student_id,
                course_key=self.course_id,
                usage_key=self.location
            )
            if aux:
                aux.delete()
                return True
            else:
                return False
        except Exception as e:
            logger.error('ImgAnnotation Error delete_annotation: {}'.format(str(e)))
            return False

    def get_or_create_imgannotation_model(self, student_id, annotation_id, role):
        """
        Get or Create img annotation model
        """
        # pylint: disable=no-member
        from .models import ImgAnnotationModel
        annotation, created = ImgAnnotationModel.objects.get_or_create(
            course_key=self.course_id,
            usage_key=self.location,
            user_id=student_id,
            annotation_id=annotation_id,
            defaults={
                'role': role
            }
        )
        if created:
            logger.info(
                "Created imagen annotation id: %s [course: %s] [student: %s]",
                annotation.annotation_id,
                annotation.course_key,
                annotation.user.username
            )
        return annotation

    def get_or_create_student_module(self, student_id):
        """
        Gets or creates a StudentModule for the given user for this block
        Returns:
            StudentModule: A StudentModule object
        """
        # pylint: disable=no-member
        from lms.djangoapps.courseware.models import StudentModule
        student_module, created = StudentModule.objects.get_or_create(
            course_id=self.course_id,
            module_state_key=self.location,
            student_id=student_id,
            defaults={
                'state': '{}',
                'module_type': self.category,
            }
        )
        if created:
            logger.info(
                "Created student module %s [course: %s] [student: %s]",
                student_module.module_state_key,
                student_module.course_id,
                student_module.student.username
            )
        return student_module

    def get_comment(self, student_id):
        """
        Return student's comments
        """
        try:
            from lms.djangoapps.courseware.models import StudentModule
            student_module = StudentModule.objects.get(
                student_id=student_id,
                course_id=self.course_id,
                module_state_key=self.location
            )
        except StudentModule.DoesNotExist:
            student_module = None

        if student_module:
            return json.loads(student_module.state)
        return {}

    def get_score(self, student_id=None):
        """
        Return student's current score.
        """
        from submissions import api as submissions_api
        anonymous_user_id = self.get_anonymous_id(student_id)
        score = submissions_api.get_score(
            self.get_student_item_dict(anonymous_user_id)
        )
        if score:
            return score['points_earned']
        else:
            return None

    def get_anonymous_id(self, student_id=None):
        """
            Return anonymous id
        """
        from common.djangoapps.student.models import anonymous_id_for_user
        from django.contrib.auth.models import User

        course_key = self.course_id
        return anonymous_id_for_user(User.objects.get(id=student_id), course_key)

    def get_student_item_dict(self, student_id=None):
        # pylint: disable=no-member
        """
        Returns dict required by the submissions app for creating and
        retrieving submissions for a particular student.
        """
        if student_id is None:
            student_id = self.xmodule_runtime.anonymous_student_id
        return {
            "student_id": student_id,
            "course_id": self.block_course_id,
            "item_id": self.block_id,
            "item_type": XBLOCK_TYPE,
        }

    def author_view(self, context=None):
        from django.contrib.auth.models import User
        annotations = self.get_annotations_author()
        image_data = self.get_data_dzi()
        context = {
            'xblock': self, 
            'location': str(self.location).split('@')[-1],
            'annotation_author': [x['id'] for x in annotations],
            'have_data': len(image_data) > 0,
            }
        user = User.objects.get(id=self.scope_ids.user_id)
        settings = {
            'annotation': annotations,
            'location': str(self.location).split('@')[-1],
            'username': user.username,
            'image_data': image_data,
            'osd_resources': self.runtime.local_resource_url(
                self,
                "static/images/"),
        }
        template = self.render_template(
            'static/html/author_view.html', context)
        frag = Fragment(template)
        frag.add_css(self.resource_string("static/css/annotorious.min.css"))
        frag.add_css(self.resource_string("static/css/img_annotation.css"))
        frag.add_javascript(self.resource_string("static/js/src/img_annotation_author.js"))
        frag.initialize_js('ImgAnnotationAuthorXBlock', json_args=settings)
        return frag

    def studio_view(self, context):
        """
        Render a form for editing this XBlock
        """
        fragment = Fragment()

        context = {
            'xblock': self,
            'location': str(self.location).split('@')[-1],
        }
        fragment.content = loader.render_django_template(
            'static/html/studio_view.html', context)
        fragment.add_css(self.resource_string("static/css/img_annotation.css"))
        fragment.add_javascript(self.resource_string(
            "static/js/src/img_annotation_studio.js"))
        fragment.initialize_js('ImgAnnotationStudioXBlock')
        return fragment

    def student_view(self, context=None):
        context, settings = self.get_context_settings()
        template = self.render_template(
            'static/html/img_annotation.html', context)
        frag = Fragment(template)
        frag.add_css(self.resource_string("static/css/img_annotation.css"))
        frag.add_css(self.resource_string("static/css/annotorious.min.css"))
        frag.add_javascript(self.resource_string("static/img_annotation/openseadragon.2.4.2.min.js"))
        frag.add_javascript(self.resource_string("static/img_annotation/openseadragon-annotorious.min.js"))
        frag.add_javascript(self.resource_string("static/img_annotation/annotorious-toolbar.min.js"))
        frag.add_javascript(self.resource_string("static/js/src/img_annotation.js"))
        frag.initialize_js('ImgAnnotationXBlock', json_args=settings)
        return frag

    def get_data_dzi(self):
        """
            Get xml data from dzi link
        """
        if self.image_url != '':
            try:
                response = requests.get(self.image_url)
                if response.status_code == 200:
                    data = xmltodict.parse(response.text)
                    dzi_format ={
                        'Image': {
                            'xmlns': data['Image']['@xmlns'],
                            'Url': self.image_url[:-4] + '_files/',
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
                else:
                    logger.error('ImgAnnotation Error - Error to get dzi image, status_code: {}, block_id: {}'.format(response.status_code, str(self.location)))
            except Exception as e:
                logger.error('ImgAnnotation Error - Invalid Url of dzi image or invalid xml params, block_id: {}, error: {}'.format(str(self.location), str(e)))
        return {}

    def get_context_settings(self):
        """
            Return context and settings by the user role
        """
        from django.contrib.auth.models import User
        image_data = self.get_data_dzi()
        context = {
            'xblock': self,
            'location': str(self.location).split('@')[-1],
            'list_annotation_student': [],
            'have_data': len(image_data) > 0,
            'is_course_staff': False
        }
        user = User.objects.get(id=self.scope_ids.user_id)
        settings = {
            'location': str(self.location).split('@')[-1],
            'username': user.username,
            'image_data': image_data,
            'puntajemax' : self.puntajemax,
            'is_course_staff': False,
            'osd_resources': self.runtime.local_resource_url(
                self,
                "static/images/"),
        }
        if self.show_staff_grading_interface():
            context['is_course_staff'] = True
            settings['is_course_staff'] = True
            settings['list_student'] = []
            from submissions import api as submissions_api
            enrolled_students = User.objects.filter(
                courseenrollment__course_id=self.course_id,
                courseenrollment__is_active=1
            ).order_by('username').values('id')
            filter_all_sub = {}
            all_submission = list(
                submissions_api.get_all_course_submission_information(
                    self.course_id, XBLOCK_TYPE))
            for student_item, submission, score in all_submission:
                if self.block_id == student_item['item_id']:
                    filter_all_sub[student_item['student_id']
                                   ] = score['points_earned']
            calificado = 0
            for a in enrolled_students:
                anonymous_id = self.get_anonymous_id(a['id'])
                if anonymous_id in filter_all_sub:
                    if filter_all_sub[anonymous_id] is not None and filter_all_sub[anonymous_id] >= 0:
                        calificado = calificado + 1
                    else:
                        settings['list_student'].append(a['id'])
                else:
                    settings['list_student'].append(a['id'])
            context['calificado'] = calificado
            context['total_student'] = len(enrolled_students)
        else:
            settings['score'] = ''
            context['score'] = ''
            context['comentario'] = ''
            aux_pun = self.get_score(self.scope_ids.user_id)
            if aux_pun is not None and aux_pun >= 0:
                context['score'] = aux_pun
                settings['score'] = aux_pun
            state = self.get_comment(self.scope_ids.user_id)
            if 'comment' in state:
                context['comentario'] = state['comment']
            settings['annotation'] = self.get_annotations(self.scope_ids.user_id, 'student')
            context['list_annotation_student'] = [x['id'] for x in settings['annotation']]
        settings['annotation_staff'] = self.get_annotations_author()
        settings['list_annotation_staff'] = [x['id'] for x in settings['annotation_staff']]
        context['list_annotation_staff'] = settings['list_annotation_staff']
        return context, settings

    def get_submission(self, student_id=None):
        """
        Get student's most recent submission.
        """
        from submissions import api as submissions_api
        submissions = submissions_api.get_submissions(
            self.get_student_item_dict(student_id)
        )
        if submissions:
            # If I understand docs correctly, most recent submission should
            # be first
            return submissions[0]

    def validar_datos(self, data):
        """
            Verify if data is valid
        """
        return 'puntaje' in data and 'student_id' in data and 'comentario' in data and str(
            data.get('puntaje')).lstrip('+').isdigit() and int(
            data.get('puntaje')) >= 0 and int(
            data.get('puntaje')) <= self.puntajemax

    @XBlock.json_handler
    def studio_submit(self, data, suffix=''):
        """
        Called when submitting the form in Studio.
        """
        try:
            if data.get('puntajemax').lstrip('+').isdigit() and int(data.get('puntajemax')) >= 0:
                self.puntajemax = int(data.get('puntajemax')) or 1
                self.display_name = data.get('display_name') or ""
                self.image_url = data.get('image_url') or ""
                self.header_text = data.get('header_text') or ""
                return {'result': 'success'}
            else:
                return {'result': 'error'}
        except Exception as e:
            logger.error('ImgAnnotation Error in studio_submit, block_id: {}, data: {}, error: {}'.format(self.block_id, data, str(e)))
            return {'result': 'error'}

    @XBlock.json_handler
    def save_anno_xblock(self, data, suffix=''):
        """
        Save annotation from author view
        """
        try:
            if not self.show_staff_grading_interface():
                logger.error('ImgAnnotation - Usuario sin Permisos - user_id: {}'.format(self.scope_ids.user_id))
                return { 'text': 'user is not course staff', 'result': 'error'}
            json_annotation = data.get('annotation')
            target = json_annotation.get('target')
            annotation = self.get_or_create_imgannotation_model(self.scope_ids.user_id, json_annotation.get('id'), 'staff')
            annotation.body = json.dumps(json_annotation.get('body'))
            annotation.target = target['selector']['value']
            annotation.save()
            return {'result': 'success'}
        except Exception as e:
            logger.error('ImgAnnotation Error in save_anno_xblock, block_id: {}, data: {}, error: {}'.format(self.block_id, data, str(e)))
            return {'result': 'error'}

    @XBlock.json_handler
    def savestudentannotations(self, data, suffix=''):
        """
            Save annotations in student view
        """
        try:
            json_annotation = data.get('annotation')
            target = json_annotation.get('target')
            annotation = self.get_or_create_imgannotation_model(self.scope_ids.user_id, json_annotation.get('id'), 'student')
            annotation.body = json.dumps(json_annotation.get('body'))
            annotation.target = target['selector']['value']
            annotation.save()
            return {'result': 'success'}
        except Exception as e:
            logger.error('ImgAnnotation Error in savestudentannotations, block_id: {}, data: {}, error: {}'.format(self.block_id, data, str(e)))
            return {'result': 'error'}

    @XBlock.json_handler
    def removestudentannotations(self, data, suffix=''):
        """
            Delete annotations
        """
        try:
            id_annotation = data.get('id')
            if id_annotation is None:
                return {'result': 'error'}
            deleted = self.delete_annotation(self.scope_ids.user_id, id_annotation)
            if deleted:
                return {'result': 'success'}
            else:
                return {'result': 'error'}
        except Exception as e:
            logger.error('ImgAnnotation Error in removestudentannotations, block_id: {}, data: {}, error: {}'.format(self.block_id, data, str(e)))
            return {'result': 'error'}

    @XBlock.json_handler
    def updatestudentannotations(self, data, suffix=''):
        """
            Update annotations author view and student view
        """
        try:
            json_annotation = data.get('annotation')
            annotation = self.get_or_create_imgannotation_model(self.scope_ids.user_id, json_annotation.get('id'), 'student')
            annotation.body = json.dumps(json_annotation['body'])
            annotation.target = json_annotation['target']['selector']['value']
            annotation.save()
            return {'result': 'success'}
        except Exception as e:
            logger.error('ImgAnnotation Error in updatestudentannotations, block_id: {}, data: {}, error: {}'.format(self.block_id, data, str(e)))
            return {'result': 'error'}

    @XBlock.json_handler
    def updatestudentannotationsstaff(self, data, suffix=''):
        """
            Update annotations student view staff
        """
        try:
            json_annotation = data.get('annotation')
            student_id = data.get('student_id')
            annotation = self.get_or_create_imgannotation_model(student_id, json_annotation.get('id'), 'student')
            annotation.body = json.dumps(json_annotation['body'])
            annotation.save()
            return {'result': 'success'}
        except Exception as e:
            logger.error('ImgAnnotation Error in updatestudentannotations, block_id: {}, data: {}, error: {}'.format(self.block_id, data, str(e)))
            return {'result': 'error'}

    @XBlock.json_handler
    def get_student_data(self, data, suffix=''):
        """
            Return a list of students with their id, username and score
        """
        if not self.show_staff_grading_interface():
            logger.error('ImgAnnotation - Usuario sin Permisos - user_id: {}'.format(self.scope_ids.user_id))
            return { 'text': 'user is not course staff', 'result': 'error'}
        from django.contrib.auth.models import User
        from submissions import api as submissions_api
        course_key = self.course_id
        enrolled_students = User.objects.filter(
            courseenrollment__course_id=course_key,
            courseenrollment__is_active=1
        ).order_by('username').values('id', 'username')
        filter_all_sub = {}
        all_submission = list(
            submissions_api.get_all_course_submission_information(
                self.course_id, XBLOCK_TYPE))
        for student_item, submission, score in all_submission:
            if self.block_id == student_item['item_id']:
                filter_all_sub[student_item['student_id']] = score['points_earned']
        lista_alumnos = []
        for a in enrolled_students:
            puntaje = ''
            anonymous_id = self.get_anonymous_id(a['id'])
            if anonymous_id in filter_all_sub:
                if filter_all_sub[anonymous_id] is not None and filter_all_sub[anonymous_id] >= 0:
                    puntaje = filter_all_sub[anonymous_id]
            lista_alumnos.append({'id': a['id'],
                                  'username': a['username'],
                                  'score': puntaje})
        return {
            'result': 'success',
            'lista_alumnos': lista_alumnos}

    @XBlock.json_handler
    def save_data_student(self, data, suffix=''):
        """
            Save score and comment
        """
        try:
            from django.contrib.auth.models import User
            valida = self.validar_datos(data)
            if self.show_staff_grading_interface() and valida:
                calificado = True
                student_module = self.get_or_create_student_module(data.get('student_id'))
                state = json.loads(student_module.state)
                score = int(data.get('puntaje'))
                state['comment'] = data.get('comentario')
                state['student_score'] = score
                student_module.state = json.dumps(state)
                student_module.save()
                
                from common.djangoapps.student.models import anonymous_id_for_user
                from submissions import api as submissions_api
                
                course_key = self.course_id
                anonymous_user_id = anonymous_id_for_user(User.objects.get(id=int(data.get('student_id'))), course_key)
                student_item = self.get_student_item_dict(anonymous_user_id)

                submission = self.get_submission(anonymous_user_id)
                if submission:
                    submissions_api.set_score(
                        submission['uuid'], score, self.puntajemax)
                else:
                    calificado = False
                    submission = submissions_api.create_submission(
                        student_item, 'any answer')
                    submissions_api.set_score(
                        submission['uuid'], score, self.puntajemax)

                return {
                    'result': 'success',
                    'calificado': calificado}
            else:
                return {'result': 'error'}
        except Exception as e:
            logger.error('ImgAnnotation Error in save_data_student, block_id: {}, data: {}, error: {}'.format(self.block_id, data, str(e)))
            return {'result': 'error'}

    @XBlock.json_handler
    def get_student_annotation(self, data, suffix=''):
        """
            Return all user's annotations   
        """
        try:
            if self.show_staff_grading_interface():
                from django.contrib.auth.models import User
                student_id = data.get('id')
                username = User.objects.get(id=int(student_id))
                annotations = self.get_annotations(int(student_id), 'student')
                aux_pun = self.get_score(int(student_id))
                score = ''
                if aux_pun is not None and aux_pun >= 0:
                    score = aux_pun
                state = self.get_comment(int(student_id))
                comment = ''
                if 'comment' in state:
                    comment = state['comment']
                return {'result': 'success', 'annotation': annotations, 'score': score, 'comment': comment, 'username': username.username}
            else:
                return {'result': 'error'}
        except Exception as e:
            logger.error('ImgAnnotation Error in get_student_annotation, block_id: {}, data: {}, error: {}'.format(self.block_id, data, str(e)))
            return {'result': 'error'}

    def render_template(self, template_path, context):
        template_str = self.resource_string(template_path)
        template = Template(template_str)
        return template.render(Context(context))

    # workbench while developing your XBlock.
    @staticmethod
    def workbench_scenarios():
        """A canned scenario for display in the workbench."""
        return [
            ("ImgAnnotationXBlock",
             """<img_annotation/>
             """),
            ("Multiple ImgAnnotationXBlock",
             """<vertical_demo>
                <img_annotation/>
                <img_annotation/>
                <img_annotation/>
                </vertical_demo>
             """),
        ]

