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

from eureka.domain.models import UserGroup


AllUnitsGroups = (
    UserGroup(u"Direction Amélioration Performance", (
        (u'PagesJaunes', u'Dir. Amelioration Performance', None, None),
    )),
    UserGroup(u"Direction Financière PJ SA et PJG", (
        (u'PagesJaunes', u'Dir. Financiere', None, None),
        (u'PagesJaunes', u'Pagesjaunes Groupe', u'Holding Direction Financiere', None),
        (u'PagesJaunes', u'Mediannuaire', u'Mediannuair Direction Financiere', None),
    )),
    UserGroup(u"Direction Systèmes d'Informations", (
        (u'PagesJaunes', u'Dir. Systemes Dir. Informations', None, None),
    )),
    UserGroup(u"Direction Commerciale", (
        (u'PagesJaunes', u'Dir. Commerciale Admin Agences Fdv', None, None),
        (u'PagesJaunes', u'Dir. Commerciale Equipes Fdv', None, None),
        (u'PagesJaunes', u'Dir. Commerciale Televente', None, None),
        (u'PagesJaunes', u'Dir. Commerciale Direction', None, None),
    )),
    UserGroup(u"Direction Grands Comptes", (
        (u'PagesJaunes', u'Dir. Grands Comptes Groupe', None, None),
    )),
    UserGroup(u"Direction Production Annonceurs", (
        (u'PagesJaunes', u'Dir. Production', None, None),
    )),
    UserGroup(u"Direction Marketing Annonceurs", (
        (u'PagesJaunes', u'Dir. Marketing Annonceurs', None, None),
    )),
    UserGroup(u"PJMS", (
        (u'PJMS', None, None, None),
    )),
    UserGroup(u"Direction Services en Mobilité", (
        (u'PagesJaunes', u'Dir. Services En Mobilite', None, None),
    )),
    UserGroup(u"Direction PagesJaunes.fr", (
        (u'PagesJaunes', u'Dir. Pagesjaunes.Fr', None, None),
    )),
    UserGroup(u"Direction Innovation (Pôle Internet)", (
        (u'PagesJaunes', u'Dir. Innovation', u'Dir. Innovation', None),
        (u'PagesJaunes', u'Pagesjaunes Groupe', u'Holding Pole Internet', None),
    )),
    UserGroup(u"Nouvelles activités internet", (
        (u'PagesJaunes', u'Dir. Nouvelles Activites Internet', None, None),
    )),
    UserGroup(u"KELTRAVO", (
        (u'Keltravo', None, None, None),
    )),
    UserGroup(u"MAPPY", (
        (u'Mappy', None, None, None),
    )),
    UserGroup(u"Pôle Annuaires Imprimés", (
        (u'PagesJaunes', u'Dir. Annuaires Imprimes', None, None),
    )),
    UserGroup(u"Direction Stratégie et Communication Groupe", (
        (u'PagesJaunes', u'Dir. Strategie', None, None),
        (u'PagesJaunes', u'Pagesjaunes Groupe', u'Holding Dir Strategie Et Comm', None),
        (u'PagesJaunes', u'Mediannuaire', u'Mediannuaire Strategie Et Comm', None),
        (u'PagesJaunes', u'Pagesjaunes Groupe', u'Holding Direction Communication', None),
    )),
    UserGroup(u"Direction Ressources Humaines PJ SA et PJG", (
        (u'PagesJaunes', u'Dir. Ressources Humaines', None, None),
        (u'PagesJaunes', u'Pagesjaunes Groupe', u'Holding Direction Ress Humaines', None),
    )),
    UserGroup(u"Direction Juridique et Immobilier", (
        (u'PagesJaunes', u'Daji Juridique', None, None),
        (u'PagesJaunes', u'Di Immobilier', None, None),
        (u'PagesJaunes', u'Pagesjaunes Groupe', u'Holding Direction Juridique', None),
    )),
    UserGroup(u"Comex", (), (
        u'jpremy',
        u'jbillot',
        u'pgarcia',
        u'mgerow',
    )),
    UserGroup(u"EDITUS", (
        (u'Editus', None, None, None),
    )),
    UserGroup(u"AdNet", (
        (u'PagesJaunes', u'Dir. Adnet', None, None),
    )),
    UserGroup(u"HORIZON MEDIA", (
        (u'Horyzon Media', None, None, None),
    )),
)

SalesDepartmentGroups = (
    # Directions
    UserGroup(u"DC/Directions supports transverses", (
        (u'PagesJaunes', u'Dir. Commerciale Direction', None, None),
    )),

    # Forces de vente
    UserGroup(u"Agence Ajaccio", (
        (u'PagesJaunes', u'Dir. Commerciale * Fdv', None, u'Ajaccio*'),
    )),
    UserGroup(u"Agence Bordeaux", (
        (u'PagesJaunes', u'Dir. Commerciale * Fdv', None, u'Bordeaux*'),
    )),
    UserGroup(u"Agence Boulogne", (
        (u'PagesJaunes', u'Dir. Commerciale * Fdv', None, u'Boulogne*'),
    )),
    UserGroup(u"Agence Dijon", (
        (u'PagesJaunes', u'Dir. Commerciale * Fdv', None, u'Dijon*'),
    )),
    UserGroup(u"Agence Grenoble", (
        (u'PagesJaunes', u'Dir. Commerciale * Fdv', None, u'Grenoble*'),
    )),
    UserGroup(u"Agence Issy Les Moulineaux", (
        (u'PagesJaunes', u'Dir. Commerciale * Fdv', None, u'Issy Les Moulineaux*'),
    )),
    UserGroup(u"Agence Lille", (
        (u'PagesJaunes', u'Dir. Commerciale * Fdv', None, u'Lille*'),
    )),
    UserGroup(u"Agence Lyon", (
        (u'PagesJaunes', u'Dir. Commerciale * Fdv', None, u'Lyon*'),
    )),
    UserGroup(u"Agence Marseille", (
        (u'PagesJaunes', u'Dir. Commerciale * Fdv', None, u'Marseille*'),
    )),
    UserGroup(u"Agence Montpellier", (
        (u'PagesJaunes', u'Dir. Commerciale * Fdv', None, u'Montpellier*'),
    )),
    UserGroup(u"Agence Nancy", (
        (u'PagesJaunes', u'Dir. Commerciale * Fdv', None, u'Nancy*'),
    )),
    UserGroup(u"Agence Nantes", (
        (u'PagesJaunes', u'Dir. Commerciale * Fdv', None, u'Nantes*'),
    )),
    UserGroup(u"Agence Nice", (
        (u'PagesJaunes', u'Dir. Commerciale * Fdv', None, u'Nice*'),
    )),
    UserGroup(u"Agence Orléans", (
        (u'PagesJaunes', u'Dir. Commerciale * Fdv', None, u'Orleans*'),
    )),
    UserGroup(u"Agence Paris Nord", (
        (u'PagesJaunes', u'Dir. Commerciale * Fdv', None, u'Paris Nord*'),
    )),
    UserGroup(u"Agence Paris Ouest", (
        (u'PagesJaunes', u'Dir. Commerciale * Fdv', None, u'Paris Ouest*'),
    )),
    UserGroup(u"Agence Paris Sud", (
        (u'PagesJaunes', u'Dir. Commerciale * Fdv', None, u'Paris Sud*'),
    )),
    UserGroup(u"Agence Poitiers", (
        (u'PagesJaunes', u'Dir. Commerciale * Fdv', None, u'Poitiers*'),
    )),
    UserGroup(u"Agence Rennes", (
        (u'PagesJaunes', u'Dir. Commerciale * Fdv', None, u'Rennes*'),
    )),
    UserGroup(u"Agence Rouen", (
        (u'PagesJaunes', u'Dir. Commerciale * Fdv', None, u'Rouen*'),
    )),
    UserGroup(u"Agence Sèvres", (
        (u'PagesJaunes', u'Dir. Commerciale * Fdv', None, u'Sevres*'),
    )),
    UserGroup(u"Agence Strasbourg", (
        (u'PagesJaunes', u'Dir. Commerciale * Fdv', None, u'Strasbourg*'),
    )),
    UserGroup(u"Agence Toulouse", (
        (u'PagesJaunes', u'Dir. Commerciale * Fdv', None, u'Toulouse*'),
    )),

    # Télévente
    UserGroup(u"Télévente Eysines", (
        (u'PagesJaunes', u'Dir. Commerciale Televente', None, u'Eysines*'),
    )),
    UserGroup(u"Télévente Lille", (
        (u'PagesJaunes', u'Dir. Commerciale Televente', None, u'Lille*'),
    )),
    UserGroup(u"Télévente Lyon", (
        (u'PagesJaunes', u'Dir. Commerciale Televente', None, u'Lyon*'),
    )),
    UserGroup(u"Télévente Marseille", (
        (u'PagesJaunes', u'Dir. Commerciale Televente', None, u'Marseille*'),
    )),
    UserGroup(u"Télévente Nancy", (
        (u'PagesJaunes', u'Dir. Commerciale Televente', None, u'Nancy*'),
    )),
    UserGroup(u"Télévente Rennes", (
        (u'PagesJaunes', u'Dir. Commerciale Televente', None, u'Rennes*'),
    )),
    UserGroup(u"Télévente Sèvres", (
        (u'PagesJaunes', u'Dir. Commerciale Televente', None, u'Sevres*'),
    )),
    UserGroup(u"Télévente Toulouse", (
        (u'PagesJaunes', u'Dir. Commerciale Televente', None, u'Toulouse*'),
    )),
)


def get_user_groups_categories():
    return ((u'Entités', AllUnitsGroups),
            (u'DC', SalesDepartmentGroups),)
