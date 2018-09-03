#
# Copyright 2018 Red Hat, Inc.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#

import pytest

from lib.compat import mock

from libnmstate import nm


@pytest.fixture
def NM_mock():
    with mock.patch.object(nm.wired.nmclient, 'NM') as m:
        yield m


def test_create_setting_None(NM_mock):
    setting = nm.wired.create_setting({}, None)
    assert setting is None


def test_create_setting_duplicate(NM_mock):
    base_profile = mock.MagicMock()

    setting = nm.wired.create_setting({'ethernet': {'speed': 1000}},
                                      base_profile)
    assert setting == \
        base_profile.get_setting_wired.return_value.duplicate.return_value


def test_create_setting_mtu(NM_mock):
    setting = nm.wired.create_setting({'mtu': 1500}, None)
    assert setting == NM_mock.SettingWired.new.return_value
    setting.set_property.assert_called_with(NM_mock.SETTING_WIRED_MTU, 1500)


def test_create_setting_auto_negotiation_False(NM_mock):
    setting = nm.wired.create_setting(
        {'ethernet': {'auto-negotiation': False}}, None)
    assert setting == NM_mock.SettingWired.new.return_value
    setting.set_property.assert_called_with(
        NM_mock.SETTING_WIRED_AUTO_NEGOTIATE, False)


def test_create_setting_auto_negotiation_True(NM_mock):
    setting = nm.wired.create_setting({'ethernet':
                                      {'auto-negotiation': True}}, None)
    assert setting == NM_mock.SettingWired.new.return_value
    setting.set_property.assert_called_with(
        NM_mock.SETTING_WIRED_AUTO_NEGOTIATE, True)


def test_create_setting_speed_duplex(NM_mock):
    setting = nm.wired.create_setting({'ethernet': {'speed': 1000,
                                                    'duplex': 'full'}},
                                      None)
    assert setting == NM_mock.SettingWired.new.return_value
    setting.set_property.assert_has_calls([
        mock.call(NM_mock.SETTING_WIRED_SPEED, 1000),
        mock.call(NM_mock.SETTING_WIRED_DUPLEX, 'full')],
        any_order=True)