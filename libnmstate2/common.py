# The default_property() is modified based on libstoragemgmt project with
#   File:       libstoragemgmt/python_binding/lsm/_common.py
#   License:    LGPL 2.1+
#   Author:     Tony Asleson <tasleson@redhat.com>
# Copyright (C) 2011-2014 Red Hat, Inc.

from collections.abc import Sequence


def default_property(name, default, doc=None):
    """
    Creates the get/set properties for the given name.  It assumes that the
    actual attribute is '_' + name

    TODO: Expand this with domain validation to ensure the values are correct.
    """
    attribute_name = "_" + name

    def getter(self):
        value = getattr(self, attribute_name)
        if value is None:
            return default
        else:
            return value

    def setter(self, value):
        setattr(self, attribute_name, value)

    prop = property(getter, setter, None, doc)

    def decorator(cls):
        setattr(cls, name, prop)
        return cls

    return decorator


def _key_name_to_pri_prop_name(key_name):
    """
    Get the private property name for specific key name.
    """
    prop_name = f"{key_name.replace('-', '_')}"
    if key_name.startswith('_'):
        return prop_name
    return f"_{prop_name}"


def _key_name_to_pub_prop_name(key_name):
    """
    Get the public property name for specific key name.
    """
    return key_name.replace("-", "_")


class BaseState:
    KEYS = []

    SUB_CONFIG_NAME = None
    SUB_CONFIG_KEYS = []

    def __init__(self):
        for key in self.KEYS + self.SUB_CONFIG_KEYS:
            prop_name = _key_name_to_pri_prop_name(key)
            setattr(self, prop_name, None)
            # For property value, None means not defined.

    def load(self, info):
        for key in self.KEYS + self.SUB_CONFIG_KEYS:
            prop_name = _key_name_to_pub_prop_name(key)
            if key in info:
                value = info[key]
            elif key in info.get(self.SUB_CONFIG_NAME, {}):
                value = info[self.SUB_CONFIG_NAME][key]
            else:
                continue
            setattr(self, prop_name, value)

    def to_dict(self):
        """
        Return information in dictionary without undefined properties, with
        metadata.
        """
        info = {}
        for key in self.KEYS + self.SUB_CONFIG_KEYS:
            prop_name = _key_name_to_pri_prop_name(key)
            value = getattr(self, prop_name)
            if value is not None:
                if key in self.SUB_CONFIG_KEYS:
                    try:
                        # Create the sub config here to make sure sub config
                        # added after self.KEYS, since Python 3.7, dict() will
                        # preserve the key order by its adding order.
                        info[self.SUB_CONFIG_NAME][key] = BaseState._serialize(
                            value
                        )
                    except KeyError:
                        info[self.SUB_CONFIG_NAME] = {
                            key: BaseState._serialize(value)
                        }
                else:
                    info[key] = BaseState._serialize(value)

        self._clean_up_info(info)
        return info

    def to_dict_full(self):
        """
        Return information in dictionary with undefined properties set to
        default value and metadata removed.
        """
        info = {}
        for key in self.KEYS + self.SUB_CONFIG_KEYS:
            if key.startswith('_'):
                continue
            prop_name = _key_name_to_pub_prop_name(key)
            value = getattr(self, prop_name)
            if key in self.SUB_CONFIG_KEYS:
                try:
                    # Initial in loop just to make sure sub config added
                    # after self.KEYS, since Python 3.7, dict() will
                    # preserve the key order by its adding order.
                    info[self.SUB_CONFIG_NAME][key] = BaseState._serialize(
                        value
                    )
                except KeyError:
                    info[self.SUB_CONFIG_NAME] = {
                        key: BaseState._serialize(value)
                    }
            else:
                info[key] = BaseState._serialize(value)
        self._clean_up_info(info)
        return info

    @staticmethod
    def _serialize(value):
        if isinstance(value, BaseState):
            return value.to_dict()
        elif isinstance(value, list):
            return [BaseState._serialize(v) for v in value]
        else:
            return value

    def _clean_up_info(self, info):
        return info

    def __str__(self):
        return f"{self.__class__.__name__}: {self.to_dict()}"

    def __repr__(self):
        return self.__str__()

    def merge(self, other):
        self_info = self.to_dict()
        other_info = other.to_dict()
        for key in self.KEYS + self.SUB_CONFIG_KEYS:
            prop_name = _key_name_to_pri_prop_name(key)
            value = getattr(other, prop_name)
            if value and not getattr(self, prop_name):
                setattr(self, prop_name, value)
