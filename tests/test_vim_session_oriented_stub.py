# VMware vSphere Python SDK tests
#
# Copyright (c) 2017-2024 Broadcom. All Rights Reserved.
# The term "Broadcom" refers to Broadcom Inc. and/or its subsidiaries.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import copy
from unittest.mock import Mock

import tests

from pyVim import connect
from pyVmomi import SessionOrientedStub, vim


class SoapAdapterTests(tests.VCRTestBase):
    def test_invoke_method_login_session_exception(self):
        def login_fail(*args, **kwargs):
            raise vim_session.SESSION_EXCEPTIONS[0]()

        stub = connect.SoapStubAdapter()
        vim_session = connect.VimSessionOrientedStub(stub, login_fail)
        self.assertRaises(vim.fault.NotAuthenticated, vim_session.InvokeAccessor, "mo", "info")

    def test_deepcopy_preserves_session_stub(self):
        for stub_type in (SessionOrientedStub, connect.VimSessionOrientedStub):
            with self.subTest(stub_type=stub_type):
                login = Mock()
                soap_stub = connect.SoapStubAdapter()
                session = stub_type(soap_stub, login)
                session.state = session.STATE_AUTHENTICATED

                self.assertIs(copy.deepcopy(session), session)
                self.assertIs(session.soapStub, soap_stub)
                self.assertEqual(session.state, session.STATE_AUTHENTICATED)
                login.assert_not_called()

    def test_deepcopy_managed_object_retains_session(self):
        login = Mock()
        session = connect.VimSessionOrientedStub(
            connect.SoapStubAdapter(), login)
        original = vim.ServiceInstance("ServiceInstance", session)

        copied = copy.deepcopy(original)

        self.assertIsNot(copied, original)
        self.assertEqual(copied._moId, original._moId)
        self.assertIs(copied._stub, session)
        login.assert_not_called()

    def test_deepcopy_data_object_retains_shared_session(self):
        login = Mock()
        session = connect.VimSessionOrientedStub(
            connect.SoapStubAdapter(), login)
        original = vim.ServiceContent(
            rootFolder=vim.Folder("group-d1", session),
            sessionManager=vim.SessionManager("SessionManager", session))

        copied = copy.deepcopy(original)

        self.assertIsNot(copied, original)
        self.assertIsNot(copied.rootFolder, original.rootFolder)
        self.assertIs(copied.rootFolder._stub, session)
        self.assertIs(copied.sessionManager._stub, session)
        copied.rootFolder = vim.Folder("group-d2", session)
        self.assertEqual(original.rootFolder._moId, "group-d1")
        login.assert_not_called()
