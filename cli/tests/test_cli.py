# Copyright 2022 by Open Kilt LLC. All rights reserved.
import unittest
import responses
import json
import logging
from unittest.mock import patch, MagicMock
from openrepo_cli.rest_interface import RestInterface
from openrepo_cli.output_formatter import OutputFormatter
from openrepo_cli.errors import ORUnauthorizedException, ORNon200ResponseException

class TestRestInterface(unittest.TestCase):
    def setUp(self):
        self.base_url = "http://test-server"
        self.api_key = "test-key"
        self.interface = RestInterface(self.base_url, self.api_key)

    @responses.activate
    def test_list_repos_success(self):
        mock_response = {
            "count": 1,
            "next": None,
            "previous": None,
            "results": [
                {
                    "repo_uid": "test-repo",
                    "repo_type": "deb",
                    "package_count": 5,
                    "last_updated": "2022-01-01T00:00:00Z"
                }
            ]
        }
        responses.add(responses.GET, f"{self.base_url}/api/repos/",
                      json=mock_response, status=200)

        result = self.interface.list_repos()
        self.assertEqual(result["results"][0]["repo_uid"], "test-repo")

    @responses.activate
    def test_unauthorized(self):
        responses.add(responses.GET, f"{self.base_url}/api/repos/",
                      status=401)
        with self.assertRaises(ORUnauthorizedException):
            self.interface.list_repos()

    @responses.activate
    def test_repo_create(self):
        from urllib.parse import parse_qs
        mock_response = {"repo_uid": "new-repo", "repo_type": "rpm"}
        responses.add(responses.POST, f"{self.base_url}/api/repos/",
                      json=mock_response, status=201)
        
        result = self.interface.repo_create("new-repo", "rpm", "key-fingerprint")
        self.assertEqual(result["repo_uid"], "new-repo")
        
        # Verify request body (form-encoded)
        self.assertEqual(len(responses.calls), 1)
        body = responses.calls[0].request.body
        if isinstance(body, bytes):
            body = body.decode('utf-8')
        sent_body = parse_qs(body)
        self.assertEqual(sent_body["repo_uid"][0], "new-repo")
        self.assertEqual(sent_body["signing_key"][0], "key-fingerprint")

class TestOutputFormatter(unittest.TestCase):
    def setUp(self):
        self.logger_patcher = patch('openrepo_cli.output_formatter.logger')
        self.mock_logger = self.logger_patcher.start()

    def tearDown(self):
        self.logger_patcher.stop()

    def test_json_output(self):
        formatter = OutputFormatter(output_json=True)
        data = {"key": "value"}
        formatter.print(data, "any_op")
        
        # Verify that logger.info was called with JSON string
        self.assertTrue(self.mock_logger.info.called)
        args, _ = self.mock_logger.info.call_args
        self.assertIn('"key": "value"', args[0])

    def test_properties_output(self):
        formatter = OutputFormatter(output_json=False)
        data = {"repo_uid": "test-repo", "repo_type": "deb"}
        formatter.print(data, "repo_details")
        
        # Verify that a table was printed
        self.assertTrue(self.mock_logger.info.called)
        args, _ = self.mock_logger.info.call_args
        self.assertIn("repo_uid", args[0])
        self.assertIn("test-repo", args[0])

if __name__ == '__main__':
    unittest.main()
