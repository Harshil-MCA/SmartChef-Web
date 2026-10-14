from django.test import TestCase

from ai.services import ExternalAIService


class ExternalAIServiceTest(TestCase):
    def test_service_initialization(self):
        service = ExternalAIService()
        self.assertIsInstance(service.is_configured(), bool)
