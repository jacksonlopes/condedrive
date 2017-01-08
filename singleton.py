# -*- coding: utf-8 -*-
"""Singleton class.

__author__ = Jackson Lopes
__email__  = jacksonlopes@gmail.com
"""
# thanks http://blog.thedigitalcatonline.com/blog/2014/09/01/python-3-oop-part-5-metaclasses/#.V8dFlFbR_Ho
class Singleton(type):
    """Singleton class."""

    instance = None
    def __call__(cls, *args, **kw):
        if not cls.instance:
            cls.instance = super(Singleton, cls).__call__(*args, **kw)
        return cls.instance

