"""
This is the core logic for the XBlock MUFI: XBlock for transcribing manuscripts using MUFI font.
"""
import os

import pkg_resources

from django.template.context import Context
from django.template.loader import get_template
from xblock.core import XBlock
from xblock.fields import Scope
from xblock.fields import String
from xblock.fragment import Fragment
from .mixins import EnforceDueDates


class XblockMufi(EnforceDueDates, XBlock):
    """
    Icon of the XBlock. Values : [other (default), video, problem]
    """
    icon_class = 'problem'

    @staticmethod
    def workbench_scenarios():
        """
        Gather scenarios to be displayed in the workbench
        """
        return [
            ('XBlock MUFI',
             """
                <sequence_demo>
                    <xblockmufi />
                </sequence_demo>
             """),
        ]

    """
    Fields
    """
    DEFAULT_FIELDS = [
        'parent',
        'tags',
    ]
    
    display_name = String(
        default='XBlock MUFI',
        scope=Scope.settings,
        help="This is the XBlock's name",
    )

    student_answer = String(
        default='',
        scope=Scope.user_state,
        help="This is the student's answer to the question",
    )

    your_answer_label = String(
        default='Your Answer:',
        scope=Scope.settings,
        help="Label for the text area containing the student's answer",
    )

    our_answer_label = String(
        default='Our Answer:',
        scope=Scope.settings,
        help="Label for the 'expert' answer",
    )

    answer_string = String(
        default='',
        scope=Scope.settings,
        help="The 'expert' answer.",
    )

    """
    Main functions
    """
    def student_view(self, context={}):
        """
        Build the fragment for the default student view
        """
        context.update(
            {
                'display_name': self.display_name,
                'student_answer': self.student_answer,
                'is_past_due': self.is_past_due(),
                'button_display_class': self._get_button_display_class(),
                'your_answer_label': self.your_answer_label,
                'our_answer_label': self.our_answer_label,
                'answer_string': self.answer_string,
            }
        )
        template = get_template('view.html')
        fragment = self.build_fragment(
            template,
            context,
            paths_css=[
                'view.less.min.css',
                'library/font-awesome.min.css',
            ],
            paths_js=[
                'view.js.min.js',
            ],
            fragment_js='XblockMufiView',
        )
        return fragment

    def studio_view(self, context={}):
        """
        Build the fragment for the edit/studio view

        Implementation is optional.
        """
        context.update(
            {
                'display_name': self.display_name,
                'your_answer_label': self.your_answer_label,
                'our_answer_label': self.our_answer_label,
                'answer_string': self.answer_string,
            }
        )
        template = get_template('edit.html')
        fragment = self.build_fragment(
            template,
            context,
            paths_css=[
                'edit.less.min.css',
                'library/font-awesome.min.css',
            ],
            paths_js=[
                'edit.js.min.js',
            ],
            fragment_js='XblockMufiEdit',
        )
        return fragment

    @XBlock.json_handler
    def studio_view_save(self, data, suffix=''):
        """
        Save XBlock fields

        Returns: the new field values
        """

        self.display_name = data['display_name']
        self.your_answer_label = data['your_answer_label']
        self.our_answer_label = data['our_answer_label']
        self.answer_string = data['answer_string']
        
        return {
            'display_name': self.display_name,
            'your_answer_label': self.your_answer_label,
            'our_answer_label': self.our_answer_label,
            'answer_string': self.answer_string,
        }

    def get_resource_url(self, path):
        """
        Retrieve a public URL for the file path
        """
        path = os.path.join('public', path)
        resource_url = self.runtime.local_resource_url(self, path)
        return resource_url

    def build_fragment(
        self,
        template,
        context_dict,
        paths_css=[],
        paths_js=[],
        fragment_js=None,
    ):
        """
        Assemble the HTML, JS, and CSS for an XBlock fragment
        """

        context = Context(context_dict)
        fragment = Fragment(template.render(context))
        for path in paths_css:
            url = self.get_resource_url(path)
            fragment.add_css_url(url)
        for path in paths_js:
            url = self.get_resource_url(path)
            fragment.add_javascript_url(url)
        if fragment_js:
            fragment.initialize_js(fragment_js)
        return fragment

    @XBlock.json_handler
    def student_submit(self, data, suffix=''):
        """
        Save student answer
        """
        if self.is_past_due():
            success_value = False
        else:
            success_value = True
            self.student_answer = data['answer']
        return {
            'success': success_value,
            'button_display_class': self._get_button_display_class(),
        }

    @XBlock.json_handler
    def publish_event(self, data, suffix=''):
        try:
            event_type = data.pop('event_type')
        except KeyError:
            return {'result': 'error', 'message': 'Missing event_type in JSON data'}

        data['user_id'] = self.scope_ids.user_id
        data['component_id'] = self._get_unique_id()
        self.runtime.publish(self, event_type, data)

        return {'result': 'success'}

    """
    Util functions
    """
    def load_resource(self, resource_path):
        """
        Gets the content of a resource
        """
        resource_content = pkg_resources.resource_string(__name__, resource_path)
        return unicode(resource_content)

    def render_template(self, template_path, context={}):
        """
        Evaluate a template by resource path, applying the provided context
        """
        template_str = self.load_resource(template_path)
        return Template(template_str).render(Context(context))

    def resource_string(self, path):
        """Handy helper for getting resources from our kit."""
        data = pkg_resources.resource_string(__name__, path)
        return data.decode('utf8')

    def _get_unique_id(self):
        try:
            unique_id = self.location.name
        except AttributeError:
            # workaround for xblock workbench
            unique_id = 'workbench-workaround-id'
        return unique_id

    def _get_button_display_class(self):
        """
        Returns the css class for the submit button
        """
        result = ''
        if self.is_past_due():
            result = 'nodisplay'
        return result
