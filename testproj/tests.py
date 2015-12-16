# -*- coding: utf-8 -*-

"""Serializer integration tests."""

from __future__ import unicode_literals

from django.test import TestCase

import six

from .models import Country
from .serializers import CountryTranslatedSerializer, AutoSharedModelCountryTranslatedSerializer, \
    ExplicitSerializerCountryTranslatedSerializer
from parler_rest.utils import create_translated_fields_serializer


class CountryTranslatedSerializerTestCase(TestCase):

    def setUp(self):
        self.instance = Country.objects.create(
            country_code='ES', name="Spain",
            url="http://en.wikipedia.org/wiki/Spain"
        )
        self.instance.set_current_language('es')
        self.instance.name = "España"
        self.instance.url = "http://es.wikipedia.org/wiki/Spain"
        self.instance.save()

    def tearDown(self):
        # Delete our instance to make sure that no language data is cached
        self.instance.delete()

    def test_translations_serialization(self):
        expected = {
            'pk': self.instance.pk,
            'country_code': 'ES',
            'translations': {
                'en': {
                    'name': "Spain",
                    'url': "http://en.wikipedia.org/wiki/Spain"
                },
                'es': {
                    'name': "España",
                    'url': "http://es.wikipedia.org/wiki/España"
                },
            }
        }
        serializer = CountryTranslatedSerializer(self.instance)
        six.assertCountEqual(self, serializer.data, expected)

    def test_translations_validation(self):
        data = {
            'country_code': 'FR',
            'translations': {
                'en': {
                    'name': "France",
                    'url': "http://en.wikipedia.org/wiki/France"
                },
                'es': {
                    'name': "Francia",
                    'url': "http://es.wikipedia.org/wiki/Francia"
                },
            }
        }
        serializer = CountryTranslatedSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        six.assertCountEqual(self, serializer.validated_data['translations'], data['translations'])

    def test_translated_fields_validation(self):
        data = {
            'country_code': 'FR',
            'translations': {
                'en': {
                    'url': "http://en.wikipedia.org/wiki/France"
                },
                'es': {
                    'name': "Francia",
                    'url': "es.wikipedia.org/wiki/Francia"
                },
            }
        }
        serializer = CountryTranslatedSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('translations', serializer.errors)
        six.assertCountEqual(self, serializer.errors['translations'], ('en', 'es'))
        self.assertIn('name', serializer.errors['translations']['en'])
        self.assertIn('url', serializer.errors['translations']['es'])

    def test_tranlations_saving_on_create(self):
        data = {
            'country_code': 'FR',
            'translations': {
                'en': {
                    'name': "France",
                    'url': "http://en.wikipedia.org/wiki/France"
                },
                'es': {
                    'name': "Francia",
                    'url': "http://es.wikipedia.org/wiki/Francia"
                },
            }
        }
        serializer = CountryTranslatedSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        instance = serializer.save()
        instance = Country.objects.get(pk=instance.pk)
        instance.set_current_language('en')
        self.assertEqual(instance.name, "France")
        self.assertEqual(instance.url, "http://en.wikipedia.org/wiki/France")
        instance.set_current_language('es')
        self.assertEqual(instance.name, "Francia")
        self.assertEqual(instance.url, "http://es.wikipedia.org/wiki/Francia")

    def test_translations_saving_on_update(self):
        data = {
            'country_code': 'ES',
            'translations': {
                'en': {
                    'name': "Spain",
                    'url': "http://en.wikipedia.org/wiki/Spain"
                },
                'es': {
                    'name': "Hispania",
                    'url': "http://es.wikipedia.org/wiki/Hispania"
                },
                'fr': {
                    'name': "Espagne",
                    'url': "http://fr.wikipedia.org/wiki/Espagne"
                }
            }
        }
        serializer = CountryTranslatedSerializer(self.instance, data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        instance = serializer.save()
        instance = Country.objects.get(pk=instance.pk)
        instance.set_current_language('en')
        self.assertEqual(instance.name, "Spain")
        self.assertEqual(instance.url, "http://en.wikipedia.org/wiki/Spain")
        instance.set_current_language('es')
        self.assertEqual(instance.name, "Hispania")
        self.assertEqual(instance.url, "http://es.wikipedia.org/wiki/Hispania")
        instance.set_current_language('fr')
        self.assertEqual(instance.name, "Espagne")
        self.assertEqual(instance.url, "http://fr.wikipedia.org/wiki/Espagne")


    def test_auto_shared_model(self):
        s = AutoSharedModelCountryTranslatedSerializer(self.instance)
        assert s.data["translations"]


    def test_explicit_serializer(self):
        country = self.instance
        s = ExplicitSerializerCountryTranslatedSerializer(country)
        assert s.data["xl"]["en"]["name"] == "Spain"
        assert not "url" in s.data["xl"]["en"]
        assert s.data["xl"]["es"]["name"] == "España"
        assert not "url" in s.data["xl"]["es"]
        s = ExplicitSerializerCountryTranslatedSerializer(country, partial=True, data={
            "xl": {"fi": {"name": "Espanja"}}
        })
        assert s.is_valid()
        country = s.save()
        country.set_current_language("en")
        assert country.name == "Spain"
        country.set_current_language("fi")
        assert country.name == "Espanja"


    def test_deserialization_data_types(self):
        country = self.instance
        s = CountryTranslatedSerializer(country, data={"translations": "this is not a dict"}, partial=True)
        assert not s.is_valid()

class UtilsTestCase(TestCase):

    def test_serializer_creation(self):
        sx = create_translated_fields_serializer(Country)()
        assert sx.fields["name"]
        assert sx.fields["url"]
        assert sx.fields["language_code"]

