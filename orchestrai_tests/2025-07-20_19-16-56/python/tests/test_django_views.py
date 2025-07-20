```python
import pytest
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
import json

class TestDjangoViews(TestCase):
    
    def setUp(self