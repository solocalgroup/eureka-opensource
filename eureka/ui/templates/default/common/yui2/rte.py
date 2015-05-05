# -*- coding: utf-8 -*-
# =-
# Copyright Solocal Group (2015)
#
# eureka@solocal.com
#
# This software is a computer program whose purpose is to provide a full
# featured participative innovation solution within your organization.
#
# This software is governed by the CeCILL license under French law and
# abiding by the rules of distribution of free software.  You can  use,
# modify and/ or redistribute the software under the terms of the CeCILL
# license as circulated by CEA, CNRS and INRIA at the following URL
# "http://www.cecill.info".
#
# As a counterpart to the access to the source code and  rights to copy,
# modify and redistribute granted by the license, users are provided only
# with a limited warranty  and the software's author,  the holder of the
# economic rights,  and the successive licensors  have only  limited
# liability.
#
# In this respect, the user's attention is drawn to the risks associated
# with loading,  using,  modifying and/or developing or reproducing the
# software by the user in light of its specific status of free software,
# that may mean  that it is complicated to manipulate,  and  that  also
# therefore means  that it is reserved for developers  and  experienced
# professionals having in-depth computer knowledge. Users are therefore
# encouraged to load and test the software's suitability as regards their
# requirements in conditions enabling the security of their systems and/or
# data to be ensured and,  more generally, to use and operate it in the
# same conditions as regards security.
#
# The fact that you are presently reading this means that you have had
# knowledge of the CeCILL license and that you accept its terms.
# =-

import json

from nagare import presentation
from nagare.i18n import _


from eureka.ui.common.yui2 import RichTextEditor, RichTextEditorInsertImageCallback


@presentation.render_for(RichTextEditor)
def render_rich_text_editor(self, h, comp, *args):
    # FIXME: replace this big dictionary by a buttons structure instead
    translations = dict(
        STR_SPIN_LABEL=_(u'Spin Button with value {VALUE}. Use Control Shift Up Arrow and Control Shift Down arrow keys to increase or decrease the value.'),
        STR_SPIN_UP=_(u'Click to increase the value of this input'),
        STR_SPIN_DOWN=_(u'Click to decrease the value of this input'),
        STR_COLLAPSE=_(u'Collapse'),
        STR_EXPAND=_(u'Expand'),
        STR_BEFORE_EDITOR=_(u'This text field can contain stylized text and graphics. To cycle through all formatting options, use the keyboard shortcut Control + Shift + T to place focus on the toolbar and navigate between option heading names. <h4>Common formatting keyboard shortcuts:</h4><ul><li>Control Shift B sets text to bold</li> <li>Control Shift I sets text to italic</li> <li>Control Shift U underlines text</li> <li>Control Shift [ aligns text left</li> <li>Control Shift | centers text</li> <li>Control Shift ] aligns text right</li> <li>Control Shift L adds an HTML link</li> <li>To exit this text editor use the keyboard shortcut Control + Shift + ESC.</li></ul>'),
        STR_LEAVE_EDITOR=_(u'You have left the Rich Text Editor.'),
        STR_TITLE=_(u'Rich Text Area.'),
        STR_CLOSE_WINDOW=_(u'Close Window'),
        STR_CLOSE_WINDOW_NOTE=_(u'To close this window use the Control + Shift + W key'),
        STR_IMAGE_HERE=_(u'Image URL Here'),
        STR_IMAGE_URL=_(u'Image URL'),
        STR_IMAGE_PROP_TITLE=_(u'Image Options'),
        STR_IMAGE_TITLE=_(u'Description'),
        STR_IMAGE_SIZE=_(u'Size'),
        STR_IMAGE_ORIG_SIZE=_(u'Original Size'),
        STR_IMAGE_COPY=u'<span class="tip"><span class="icon icon-info"></span><strong>%s</strong>%s</span>' % (_(u'Note:'), _(u'To move this image just highlight it, cut, and paste where ever you\'d like.')),
        STR_IMAGE_PADDING=_(u'Padding'),
        STR_IMAGE_BORDER=_(u'Border'),
        STR_IMAGE_BORDER_SIZE=_(u'Border Size'),
        STR_IMAGE_BORDER_TYPE=_(u'Border Type'),
        STR_IMAGE_BORDER_TYPE_SOLID=_(u'Solid'),
        STR_IMAGE_BORDER_TYPE_DASHED=_(u'Dashed'),
        STR_IMAGE_BORDER_TYPE_DOTTED=_(u'Dotted'),
        STR_IMAGE_BORDER_COLOR=_(u'Border Color'),
        STR_IMAGE_TEXTFLOW=_(u'Text Flow'),
        STR_IMAGE_TEXTFLOW_LEFT=_(u'Left'),
        STR_IMAGE_TEXTFLOW_INLINE=_(u'Inline'),
        STR_IMAGE_TEXTFLOW_BLOCK=_(u'Block'),
        STR_IMAGE_TEXTFLOW_RIGHT=_(u'Right'),
        STR_LINK_URL=_(u'Link URL'),
        STR_LINK_PROP_TITLE=_(u'Link Options'),
        STR_LINK_PROP_REMOVE=_(u'Remove link from text'),
        STR_LINK_NEW_WINDOW=_(u'Open in a new window.'),
        STR_LINK_TITLE=_(u'Description'),
        STR_LOCAL_FILE_WARNING=u'<span class="tip"><span class="icon icon-warn"></span><strong>%s</strong>%s</span>' % (_(u'Note:'), _(u'This image/link points to a file on your computer and will not be accessible to others on the internet.')),
        STR_PARA_STYLE=_(u'Paragraph style'),
        STR_PARA_STYLE_NORMAL=_(u'Normal'),
        STR_PARA_STYLE_HEADING1=_(u'Heading 1'),
        STR_PARA_STYLE_HEADING2=_(u'Heading 2'),
        STR_PARA_STYLE_HEADING3=_(u'Heading 3'),
        STR_PARA_STYLE_HEADING4=_(u'Heading 4'),
        STR_PARA_STYLE_HEADING5=_(u'Heading 5'),
        STR_PARA_STYLE_HEADING6=_(u'Heading 6'),
        STR_TEXT_STYLE=_(u'Text Style'),
        STR_TEXT_STYLE_BOLD=_(u'Bold CTRL + SHIFT + B'),
        STR_TEXT_STYLE_ITALIC=_(u'Italic CTRL + SHIFT + I'),
        STR_TEXT_STYLE_COLOR=_(u'Text Color'),
        STR_TEXT_STYLE_REMOVE_FORMATTING=_(u'Remove the formatting'),
        STR_ALIGNMENT=_(u'Text Alignment'),
        STR_ALIGNMENT_LEFT=_(u'Left CTRL + SHIFT + ['),
        STR_ALIGNMENT_CENTER=_(u'Center CTRL + SHIFT + |'),
        STR_ALIGNMENT_RIGHT=_(u'Right CTRL + SHIFT + ]'),
        STR_ALIGNMENT_JUSTIFY=_(u'Justify'),
        STR_INDENTATION_AND_LISTS=_(u'Indentation and lists'),
        STR_INDENT=_(u'Indent'),
        STR_OUTDENT=_(u'Outdent'),
        STR_UNORDERED_LIST=_(u'Create an Unordered List'),
        STR_ORDERED_LIST=_(u'Create an Ordered List'),
        STR_INSERT_ITEM=_(u'Insert Item'),
        STR_LINK=_(u'Link CTRL + SHIFT + L'),
        STR_IMAGE=_(u'Image')
    )
    # translations are common to all RTE instances
    h << h.head.javascript('rte_translations',
                           "var RTETranslations = %s;" % json.dumps(translations))

    # show editor code
    error_msg = _(u'You must whitelist this site from your popup blocker in order to use this feature.')
    mapping = dict(
        editor_id=json.dumps(self.id),
        height=json.dumps(self.height),
        max_chars=json.dumps(self.max_chars),
        gallery_url=json.dumps(self.gallery_url),
        popup_error_msg=json.dumps(error_msg)
    )
    js = '''
    setupRichTextEditor(%(editor_id)s, %(height)s, %(max_chars)s, %(gallery_url)s, %(popup_error_msg)s, RTETranslations);
    ''' % mapping

    # html
    with h.div(class_='rich-text-editor'):
        h << h.textarea(self.property() or '',
                        id=self.id).action(self.property)
        h << h.script(js, type='text/javascript')

    if self.max_chars:
        with h.div(class_="counter"):
            h << h.span(class_="count",
                        id="count-%s" % self.id)
            h << " / "
            h << self.max_chars << " " << _("characters")

    if self.property.error:
        h << h.div(self.property.error, class_='nagare-error-message')

    return h.root


@presentation.render_for(RichTextEditorInsertImageCallback)
def render_rich_text_editor_insert_image_callback(self, h, comp, *args):
    js = '''function %(callback_name)s(url) { insertImageInEditor('%(editor_id)s', url); }'''
    mapping = {
        'editor_id': self.id,
        'callback_name': self.callback_name,
    }

    h << h.script(js % mapping, type='text/javascript')

    return h.root
