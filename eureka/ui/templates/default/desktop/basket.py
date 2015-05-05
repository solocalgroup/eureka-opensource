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

from nagare import presentation
from nagare.i18n import _, _L

from eureka.domain.services import get_workflow
from eureka.infrastructure import event_management

from eureka.ui.desktop.basket import IdeaBasket


# FIXME: remove duplicated code!
# render_idea_basket_fi and render_idea_basket_fi_dsig are quite the same
# except that the user name is shown in the latter case
# render_idea_basket_di and render_idea_basket_di_dsig are quite the same
# except that the user name is shown in the latter case
# in both case, they do not emit the same event but the events can be merged!

#  FIXME: we may miss translations here
def default_states_labels():
    workflow = get_workflow()
    return [(state, _L(u'You have %d ideas in state ' + state))
            for state in workflow.get_ordered_states()]


# Help Babel's messages extraction
TRANSLATED_STATE_LABELS = (_L('You have %d ideas in state AUTHOR_NORMALIZE_STATE'),
                           _L('You have %d ideas in state DRAFT_STATE'),
                           _L('You have %d ideas in state DSIG_BASKET_STATE'),
                           _L('You have %d ideas in state PROTOTYPE_REFUSED_STATE'),
                           _L('You have %d ideas in state APPROVAL_REFUSED_STATE'),
                           _L('You have %d ideas in state DI_APPROVED_STATE'),
                           _L('You have %d ideas in state PROTOTYPE_STATE'),
                           _L('You have %d ideas in state DI_REFUSED_STATE'),
                           _L('You have %d ideas in state EXTENDED_STATE'),
                           _L('You have %d ideas in state RETURNED_BY_DI_STATE'),
                           _L('You have %d ideas in state SELECT_REFUSED_STATE'),
                           _L('You have %d ideas in state FI_REFUSED_STATE'),
                           _L('You have %d ideas in state PROJECT_STATE'),
                           _L('You have %d ideas in state PROJECT_REFUSED_STATE'),
                           _L('You have %d ideas in state SELECTED_STATE'),
                           _L('You have %d ideas in state DI_APPRAISAL_STATE'),
                           _L('You have %d ideas in state FI_NORMALIZE_STATE'),
                           _L('You have %d ideas in state INITIAL_STATE'))


def fi_states_labels():
    workflow = get_workflow()
    return (
        (workflow.WFStates.FI_NORMALIZE_STATE, _L(u'You have %d ideas to review')),
        (workflow.WFStates.AUTHOR_NORMALIZE_STATE, _L(u'You have sent back %d ideas to innovators')),
        (workflow.WFStates.DI_APPRAISAL_STATE, _L(u'You have sent %d ideas to developers')),
        (workflow.WFStates.FI_REFUSED_STATE, _L(u'You have refused %d ideas')),
    )


def di_states_labels():
    workflow = get_workflow()
    return (
        (workflow.WFStates.DI_APPRAISAL_STATE, _L(u'You have %d ideas to review')),
        (workflow.WFStates.DSIG_BASKET_STATE, _L(u'You have sent %d ideas to DSIG')),
        (workflow.WFStates.DI_REFUSED_STATE, _L(u'You have refused %d ideas')),
        (workflow.WFStates.DI_APPROVED_STATE, _L(u'You have approved %d ideas')),
        (workflow.WFStates.SELECTED_STATE, _L(u'You have %d selected ideas')),
        (workflow.WFStates.PROJECT_STATE, _L(u'You have %d projected ideas')),
        (workflow.WFStates.PROTOTYPE_STATE, _L(u'You have %d prototyped ideas')),
        (workflow.WFStates.EXTENDED_STATE, _L(u'You have %d extended ideas')),
    )


@presentation.render_for(IdeaBasket)
def render_idea_basket(self, h, comp, *args):
    labels = dict(default_states_labels())
    with h.div(class_="state_selector rounded"):
        sorted_ideas = self.get_sorted_ideas()

        if len(sorted_ideas) == 0:
            h << _(u'No submitted idea')
        else:
            with h.ul(class_="ideaBoard"):
                for state, nb in sorted_ideas:
                    label = labels.get(state, None)
                    if label:
                        with h.li(class_='ideas-list'):
                            if self.state_id == state:
                                h << h.a(
                                    '[-] ', label % nb, class_="selected_link"
                                ).action(lambda: event_management._emit_signal(self, "HIDE_IDEAS"))
                                with h.table:
                                    with h.tbody:
                                        with h.tr(class_='filter'):
                                            h << h.td
                                            h << h.td(_('Comments'))
                                            h << h.td(_('Votes'))
                                h << self.pager
                            else:
                                h << h.a(
                                    '[+] ', label % nb
                                ).action(lambda v=state: event_management._emit_signal(self, "VIEW_MY_IDEAS", state=v))

    return h.root


@presentation.render_for(IdeaBasket, model='FI')
def render_idea_basket_fi(self, h, comp, *args):
    labels = dict(fi_states_labels())
    with h.div(class_="state_selector rounded"):
        sorted_ideas = self.get_sorted_ideas()

        if len(sorted_ideas) == 0:
            h << _(u'No idea in basket')
        else:
            with h.ul(class_="ideaBoard"):
                for state, nb in sorted_ideas:
                    label = labels.get(state, None)
                    if label:
                        with h.li(class_='ideas-list'):
                            if self.state_id == state:
                                h << h.a(
                                    '[-] ', label % nb, class_="selected_link"
                                ).action(lambda: event_management._emit_signal(self, "HIDE_IDEAS"))
                                with h.table:
                                    with h.tbody:
                                        with h.tr(class_='filter'):
                                            h << h.td
                                            h << h.td(_('Comments'))
                                            h << h.td(_('Votes'))
                                h << self.pager
                            else:
                                h << h.a(
                                    '[+] ', label % nb
                                ).action(lambda v=state: event_management._emit_signal(self, "VIEW_FI_IDEAS", state=v))

    return h.root


@presentation.render_for(IdeaBasket, model='FI_DSIG')
def render_idea_basket_fi_dsig(self, h, comp, *args):
    labels = dict(fi_states_labels())
    with h.div(class_="state_selector rounded"):
        sorted_ideas = self.get_sorted_ideas()

        u = self.user
        h << h.h2(_(u"Basket of %s") % u.fullname)

        if len(sorted_ideas) == 0:
            h << _(u'No idea in basket')
        else:
            with h.ul(class_="ideaBoard"):
                for state, nb in sorted_ideas:
                    label = labels.get(state, None)
                    if label:
                        with h.li(class_='ideas-list'):
                            if self.state_id == state:
                                h << h.a(
                                    '[-] ', label % nb, class_="selected_link"
                                ).action(lambda: event_management._emit_signal(self, "HIDE_IDEAS"))
                                with h.table:
                                    with h.tbody:
                                        with h.tr(class_='filter'):
                                            h << h.td
                                            h << h.td(_('Comments'))
                                            h << h.td(_('Votes'))
                                h << self.pager
                            else:
                                h << h.a(
                                    '[+] ', label % nb
                                ).action(lambda v=state: event_management._emit_signal(self, "VIEW_FI_DSIG_IDEAS", state=v, user_uid=self.user_uid))

    return h.root


@presentation.render_for(IdeaBasket, model='DI')
def render_idea_basket_di(self, h, comp, *args):
    labels = dict(di_states_labels())
    with h.div(class_="state_selector rounded"):
        sorted_ideas = self.get_sorted_ideas()

        if len(sorted_ideas) == 0:
            h << _(u'No idea in basket')
        else:
            with h.ul(class_="ideaBoard"):
                for state, nb in sorted_ideas:
                    label = labels.get(state, None)
                    if label:
                        with h.li(class_='ideas-list'):
                            if self.state_id == state:
                                h << h.a(
                                    '[-] ', label % nb, class_="selected_link"
                                ).action(lambda: event_management._emit_signal(self, "HIDE_IDEAS"))
                                with h.table:
                                    with h.tbody:
                                        with h.tr(class_='filter'):
                                            h << h.td
                                            h << h.td(_('Comments'))
                                            h << h.td(_('Votes'))
                                h << self.pager
                            else:
                                h << h.a(
                                    '[+] ', label % nb
                                ).action(lambda v=state: event_management._emit_signal(self, "VIEW_DI_IDEAS", state=v))

    return h.root


@presentation.render_for(IdeaBasket, model='DI_DSIG')
def render_idea_basket_di_dsig(self, h, comp, *args):
    labels = dict(di_states_labels()[:4])
    with h.div(class_="state_selector rounded"):
        sorted_ideas = self.get_sorted_ideas()

        u = self.user
        h << h.h2(_(u"Basket of %s") % u.fullname)

        if len(sorted_ideas) == 0:
            h << _(u'No idea in basket')
        else:
            with h.ul(class_="ideaBoard"):
                for state, nb in sorted_ideas:
                    label = labels.get(state, None)
                    if label:
                        with h.li(class_='ideas-list'):
                            if self.state_id == state:
                                h << h.a(
                                    '[-] ', label % nb, class_="selected_link"
                                ).action(lambda: event_management._emit_signal(self, "HIDE_IDEAS"))
                                with h.table:
                                    with h.tbody:
                                        with h.tr(class_='filter'):
                                            h << h.td
                                            h << h.td(_('Comments'))
                                            h << h.td(_('Votes'))
                                h << self.pager
                            else:
                                h << h.a(
                                    '[+] ', label % nb
                                ).action(lambda v=state: event_management._emit_signal(self, "VIEW_DI_DSIG_IDEAS", state=v, user_uid=self.user_uid))

    return h.root


@presentation.render_for(IdeaBasket, model='DSIG')
def render_idea_basket_dsig(self, h, comp, *args):
    labels = dict(default_states_labels())
    with h.div(class_="state_selector rounded"):
        sorted_ideas = self.get_sorted_ideas()

        if len(sorted_ideas) == 0:
            h << _(u'No idea in basket')
        else:
            with h.ul(class_="ideaBoard"):
                for state, nb in sorted_ideas:
                    label = labels.get(state, None)
                    if label:
                        with h.li(class_='ideas-list'):
                            if self.state_id == state:
                                h << h.a(
                                    '[-] ', label % nb, class_="selected_link"
                                ).action(lambda: event_management._emit_signal(self, "HIDE_IDEAS"))
                                with h.table:
                                    with h.tbody:
                                        with h.tr(class_='filter'):
                                            h << h.td
                                            h << h.td(_('Comments'))
                                            h << h.td(_('Votes'))
                                h << self.pager
                            else:
                                h << h.a(
                                    '[+] ', label % nb
                                ).action(lambda v=state: event_management._emit_signal(self, "VIEW_DSIG_IDEAS", state=v))

    return h.root
