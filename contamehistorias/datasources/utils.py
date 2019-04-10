# -*- coding: utf-8 -*-
import re

SPECIAL_CHARACTERS_DICT =  dict([
		(u"Ã¡", u"á"), (u"Ã ", u"à"),(u"Ã£", u"ã"), (u'Ã¢',u'â'), (u'Ã',u'Á'),# a
		(u"Ã©", u"é"), (u'Ãª', u'ê'),
		(u"Ã³", u"ó"), (u"Ãµ", u"õ"), (u'Ã´',u'ô'),
		(u"Ãº", u"ú"), (u'Ã', u'Ú'),
		(u'Ã§',u'ç'),
		(u"Ã", u"í")])

def multiple_replace(string):
		pattern = re.compile("|".join([re.escape(k) for k in SPECIAL_CHARACTERS_DICT.keys()]), re.M)
		return pattern.sub(lambda x: SPECIAL_CHARACTERS_DICT[x.group(0)], string)


