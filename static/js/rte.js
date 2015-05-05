/**
 * Copyright Solocal Group (2015)
 *
 * eureka@solocal.com
 *
 * This software is a computer program whose purpose is to provide a full
 * featured participative innovation solution within your organization.
 *
 * This software is governed by the CeCILL license under French law and
 * abiding by the rules of distribution of free software.  You can  use,
 * modify and/ or redistribute the software under the terms of the CeCILL
 * license as circulated by CEA, CNRS and INRIA at the following URL
 * "http://www.cecill.info".
 *
 * As a counterpart to the access to the source code and  rights to copy,
 * modify and redistribute granted by the license, users are provided only
 * with a limited warranty  and the software's author,  the holder of the
 * economic rights,  and the successive licensors  have only  limited
 * liability.
 *
 * In this respect, the user's attention is drawn to the risks associated
 * with loading,  using,  modifying and/or developing or reproducing the
 * software by the user in light of its specific status of free software,
 * that may mean  that it is complicated to manipulate,  and  that  also
 * therefore means  that it is reserved for developers  and  experienced
 * professionals having in-depth computer knowledge. Users are therefore
 * encouraged to load and test the software's suitability as regards their
 * requirements in conditions enabling the security of their systems and/or
 * data to be ensured and,  more generally, to use and operate it in the
 * same conditions as regards security.
 *
 * The fact that you are presently reading this means that you have had
 * knowledge of the CeCILL license and that you accept its terms.
 */

YAHOO.widget.Toolbar.prototype._colorData = {
    '#000000': 'Black',
    '#ffffff': 'White',
    '#00519e': 'Bleu',
    '#00aec7': 'Bleu clair',
    '#6ab023': 'Vert',
    '#bdcd00': 'Vert clair',
    '#ffdd00': 'Jaune',
    '#f29400': 'Orange',
    '#c50e1f': 'Rouge',
    '#e30054': 'Fuchsia',
    '#d4007a': 'Rose framboise',
    '#ad0074': 'Violet'
};

/* Custom localized editor */
function EurekaEditor(el, height, galleryURL, popupBlockerMessage, translations) {
    // install the translations
    for (var key in translations) {
        this[key] = translations[key];
    }
    var toolbarLabels = ['STR_SPIN_LABEL', 'STR_SPIN_UP', 'STR_SPIN_DOWN', 'STR_COLLAPSE', 'STR_EXPAND'];
    for (var i=0; i<toolbarLabels.length; ++i) {
        var label = toolbarLabels[i];
        YAHOO.widget.Toolbar.prototype[label] = translations[label];
    }

    // default toolbar
    this._defaultToolbar = {
        collapse: true,
        draggable: false,
        buttonType: 'advanced',
        buttons: [
            {
                group: 'parastyle', label: this.STR_PARA_STYLE,
                buttons: [
                    {
                        type: 'select', label: this.STR_PARA_STYLE_NORMAL, value: 'heading', disabled: true,
                        menu: [
                            { text: this.STR_PARA_STYLE_NORMAL, value: 'none', checked: true },
                            { text: this.STR_PARA_STYLE_HEADING1, value: 'h1' },
                            { text: this.STR_PARA_STYLE_HEADING2, value: 'h2' },
                            { text: this.STR_PARA_STYLE_HEADING3, value: 'h3' },
                            { text: this.STR_PARA_STYLE_HEADING4, value: 'h4' },
                            { text: this.STR_PARA_STYLE_HEADING5, value: 'h5' },
                            { text: this.STR_PARA_STYLE_HEADING6, value: 'h6' }
                        ]
                    },
                    {
                        type: 'spin', label: '13', value: 'fontsize', range: [ 9, 75 ], disabled: true
                    }
                ]
            },
            { type: 'separator' },
            {
                group: 'textstyle', label: this.STR_TEXT_STYLE,
                buttons: [
                    { type: 'push', label: this.STR_TEXT_STYLE_BOLD, value: 'bold' },
                    { type: 'push', label: this.STR_TEXT_STYLE_ITALIC, value: 'italic' },
                    { type: 'separator' },
                    { type: 'color', label: this.STR_TEXT_STYLE_COLOR, value: 'forecolor', disabled: true },
                    { type: 'separator' },
                    { type: 'push', label: this.STR_TEXT_STYLE_REMOVE_FORMATTING, value: 'removeformat', disabled: true }
                ]
            },
            { type: 'separator' },
            {
                group: 'alignment', label: this.STR_ALIGNMENT,
                buttons: [
                    { type: 'push', label: this.STR_ALIGNMENT_LEFT, value: 'justifyleft' },
                    { type: 'push', label: this.STR_ALIGNMENT_CENTER, value: 'justifycenter' },
                    { type: 'push', label: this.STR_ALIGNMENT_RIGHT, value: 'justifyright' },
                    { type: 'push', label: this.STR_ALIGNMENT_JUSTIFY, value: 'justifyfull' }
                ]
            },
            { type: 'separator' },
            {
                group: 'indentlist', label: this.STR_INDENTATION_AND_LISTS,
                buttons: [
                    { type: 'push', label: this.STR_INDENT, value: 'indent', disabled: true },
                    { type: 'push', label: this.STR_OUTDENT, value: 'outdent', disabled: true },
                    { type: 'push', label: this.STR_UNORDERED_LIST, value: 'insertunorderedlist' },
                    { type: 'push', label: this.STR_ORDERED_LIST, value: 'insertorderedlist' }
                ]
            },
            { type: 'separator' },
            { group: 'insertitem', label: this.STR_INSERT_ITEM,
                buttons: [
                    { type: 'push', label: this.STR_LINK, value: 'createlink', disabled: true },
                    { type: 'push', label: this.STR_IMAGE, value: 'insertimage' }
                    //{ type: 'push', label: 'Edit HTML Code', value: 'editcode' }
                ]
            }
        ]
    };

    // default image toolbar
    this._defaultImageToolbarConfig = {
        buttonType: this._defaultToolbar.buttonType,
        buttons: [
            { group: 'textflow', label: this.STR_IMAGE_TEXTFLOW + ':',
                buttons: [
                    { type: 'push', label: this.STR_IMAGE_TEXTFLOW_LEFT, value: 'left' },
                    { type: 'push', label: this.STR_IMAGE_TEXTFLOW_INLINE, value: 'inline' },
                    { type: 'push', label: this.STR_IMAGE_TEXTFLOW_BLOCK, value: 'block' },
                    { type: 'push', label: this.STR_IMAGE_TEXTFLOW_RIGHT, value: 'right' }
                ]
            },
            { type: 'separator' },
            { group: 'padding', label: this.STR_IMAGE_PADDING + ':',
                buttons: [
                    { type: 'spin', label: '0', value: 'padding', range: [0, 50] }
                ]
            },
            { type: 'separator' },
            { group: 'border', label: this.STR_IMAGE_BORDER + ':',
                buttons: [
                    { type: 'select', label: this.STR_IMAGE_BORDER_SIZE, value: 'bordersize',
                        menu: [
                            { text: this.STR_NONE, value: '0', checked: true },
                            { text: '1px', value: '1' },
                            { text: '2px', value: '2' },
                            { text: '3px', value: '3' },
                            { text: '4px', value: '4' },
                            { text: '5px', value: '5' }
                        ]
                    },
                    { type: 'select', label: this.STR_IMAGE_BORDER_TYPE, value: 'bordertype', disabled: true,
                        menu: [
                            { text: this.STR_IMAGE_BORDER_TYPE_SOLID, value: 'solid', checked: true },
                            { text: this.STR_IMAGE_BORDER_TYPE_DASHED, value: 'dashed' },
                            { text: this.STR_IMAGE_BORDER_TYPE_DOTTED, value: 'dotted' }
                        ]
                    },
                    { type: 'color', label: this.STR_IMAGE_BORDER_COLOR, value: 'bordercolor', disabled: true }
                ]
            }
        ]
    };

    // call base constructor
    var editorConfig = {
        handleSubmit: true,
        width: '100%',
        height: '' + (height || 300) + 'px'
    }
    EurekaEditor.superclass.constructor.call(this, el, editorConfig);

    /*var showCode = false;*/
    this.on('toolbarLoaded', function() {
        /*
        this.toolbar.on('editcodeClick', function() {
          var ta = this.get('element');
          var iframe = this.get('iframe').get('element');

          if (showCode) {
            showCode = false;
            this.toolbar.set('disabled', false);
            this.setEditorHTML(ta.value);
            if (!this.browser.ie) {
              this._setDesignMode('on');
            }

            YAHOO.util.Dom.removeClass(iframe, 'hidden');
            YAHOO.util.Dom.addClass(ta, 'hidden');
            this.show();
            this._focusWindow();
          }
          else {
            showCode = true;
            this.cleanHTML();
            YAHOO.util.Dom.addClass(iframe, 'hidden');
            YAHOO.util.Dom.removeClass(ta, 'hidden');
            this.toolbar.set('disabled', true);
            this.toolbar.getButtonByValue('editcode').set('disabled', false);
            this.toolbar.selectButton('editcode');
            this.dompath.innerHTML = 'Editing HTML Code';
            this.hide();
          }
          return false;
        }, this, true);
        */

        /*
        this.on('cleanHTML', function(ev) {
          this.get('element').value = ev.html;
        }, this, true);
        */

        /* displays the gallery in insert mode */
        /* FIXME: move this functionality out of the RTE and pass a callback to the RTE */
        this.toolbar.on('insertimageClick', function() {
            var _sel = this._getSelectedElement();

            // if the selected element is an image, do the normal thing so they can manipulate the image
            if (_sel && _sel.tagName && (_sel.tagName.toLowerCase() == 'img')) {
                // let the other listeners be notified
            }
            else {
                win = window.open(galleryURL, 'image_browser', 'width=420,height=700,toolbar=0,scrollbars=1,scrollable=1,status=0,location=0');
                if (!win) {
                    alert(popupBlockerMessage);
                }
                else {
                    return false; // let the other listeners be notified
                }
            }
        }, this, true);
    }, this, true);

    // IE6: change the image alignment to use the float style instead of align
    var float_hook_installed = false;

    // FIXME: we should connect to the window afterRender event instead, since
    //        the default image toolbar is created there
    this.on('afterOpenWindow', function(args) {
        if (args.win.name == 'insertimage') {
            if (float_hook_installed) {
                return true;
            }

            this._defaultImageToolbar.on("buttonClick", function(V) {
                var T = V.button.value, S = this._defaultImageToolbar.editor_el;
                if (V.button.menucmd) {
                      T = V.button.menucmd;
                }

                // updates the float style and the display and align properties
                // Note: we do not provide a width for the float even when when
                //       the image is not resized in the editor (which sets
                //       its widht/height styles), but it works flawlessly
                //       under all browsers, including IE6
                switch (T) {
                    case "right":
                    case "left":
                        S.style.cssFloat = T;   // standard
                        S.style.styleFloat = T; // IE
                        S.style.display = "block";
                        S.align = "";
                        break;
                    case "inline":
                    case "block":
                        S.style.cssFloat = "none";   // standard
                        S.style.styleFloat = "none"; // IE
                        break;
                }
            }, this, true);

            float_hook_installed = true;

            return true;
        }
    }, this, true);
}


YAHOO.lang.extend(EurekaEditor, YAHOO.widget.Editor, {});


/* Setup the Rich Text Editor */
function setupRichTextEditor(editorId, height, maxChars, galleryURL, popupBlockerMessage, translations) {
    var editor = new EurekaEditor(editorId, height, galleryURL, popupBlockerMessage, translations);
    editor.render();

    // setup the character counter
    if (maxChars) {
        setupCharacterCounter(editor, maxChars);
    }

    return editor;
}

/* Setup the character counter */
function setupCharacterCounter(editor, maxChars) {
    var count = function() {
        var text = stripHTMLTags(editor.cleanHTML());
        var counterEl = YAHOO.util.Dom.get('count-' + editor.get("id"));
        var count = text.length;
        if (count > maxChars) {
            counterEl.innerHTML = '<span class="overflow">' + count + '</span>';
        }
        else {
            counterEl.innerHTML = count;
        }
    };
    editor.on('editorContentLoaded', count)
    editor.on('editorKeyUp', count);
    editor.on('editorKeyPress', count);
    editor.on('editorMouseUp', count);
}

/* Strip the HTML tags from a string */
function stripHTMLTags(text) {
    var regex = /<\S[^><]*>/g;
    return text.replace(regex, '');
}

/* Insert an image in the Editor */
function insertImageInEditor(editorId, imageURL) {
    var editor = window.opener.YAHOO.widget.EditorInfo.getEditorById(editorId);
    editor._focusWindow();
    editor.execCommand('insertimage', imageURL);
    window.close();
}
