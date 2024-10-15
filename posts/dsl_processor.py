from django_elasticsearch_dsl.signals import CelerySignalProcessor as CSP

from django_elasticsearch_dsl.registries import registry
from django.db import models
from django.apps import apps
from django.dispatch import Signal
from django.core.exceptions import ObjectDoesNotExist
from importlib import import_module
from commons.celery import shared_task


class CelerySignalProcessor(CSP):
    def get_info(self, instance):
        pk = instance.pk
        app_label = instance._meta.app_label
        model_name: str = instance.__class__.__name__
        return pk, app_label, model_name

    @staticmethod
    def get_instance(pk, app_label, model_name):
        return apps.get_model(app_label, model_name).objects.first()

    def handle_save(self, sender, instance, **kwargs):
        pk, app_label, model_name = self.get_info(instance)
        if app_label.startswith("django_celery"):
            return

        self.registry_update_task.delay(pk, app_label, model_name)
        self.registry_update_related_task.delay(pk, app_label, model_name)

    def handle_pre_delete(self, sender, instance, **kwargs):
        pk, app_label, model_name = self.get_info(instance)
        if app_label.startswith("django_celery"):
            return

        self.prepare_registry_delete_related_task.delay(pk, app_label, model_name).get()

    def handle_delete(self, sender, instance, **kwargs):
        pk, app_label, model_name = self.get_info(instance)
        if app_label.startswith("django_celery"):
            return

        self.prepare_registry_delete_task.delay(pk, app_label, model_name).get()

    @shared_task()
    def prepare_registry_delete_related_task(pk, app_label, model_name):
        instance = CelerySignalProcessor.get_instance(pk, app_label, model_name)
        if not instance:
            return
        action = "index"
        for doc in registry._get_related_doc(instance):
            doc_instance = doc(related_instance_to_ignore=instance)
            try:
                related = doc_instance.get_instances_from_related(instance)
            except ObjectDoesNotExist:
                related = None
            if related is not None:
                doc_instance.update(related)
                if isinstance(related, models.Model):
                    object_list = [related]
                else:
                    object_list = related
                bulk_data = (list(doc_instance._get_actions(object_list, action)),)
                CelerySignalProcessor.registry_delete_task.delay(
                    doc_instance.__class__.__name__, bulk_data
                )

    @shared_task()
    def prepare_registry_delete_task(pk, app_label, model_name):
        instance = CelerySignalProcessor.get_instance(pk, app_label, model_name)
        if not instance:
            return
        action = "delete"
        for doc in registry._get_related_doc(instance):
            doc_instance = doc(related_instance_to_ignore=instance)
            try:
                related = doc_instance.get_instances_from_related(instance)
            except ObjectDoesNotExist:
                related = None
            if related is not None:
                doc_instance.update(related)
                if isinstance(related, models.Model):
                    object_list = [related]
                else:
                    object_list = related
                bulk_data = (list(doc_instance.get_actions(object_list, action)),)
                CelerySignalProcessor.registry_delete_task.delay(
                    doc_instance.__class__.__name__, bulk_data
                )

    @shared_task()
    def registry_delete_task(doc_label, data):
        doc_instance = import_module(doc_label)
        parallel = True
        doc_instance._bulk(data, parallel=parallel)

    @shared_task()
    def registry_update_task(pk, app_label, model_name):
        """Handle the update on the registry as a Celery task."""
        try:
            model = apps.get_model(app_label, model_name)
        except LookupError:
            pass
        else:
            registry.update(model.objects.get(pk=pk))

    @shared_task()
    def registry_update_related_task(pk, app_label, model_name):
        """Handle the related update on the registry as a Celery task."""
        try:
            model = apps.get_model(app_label, model_name)
        except LookupError:
            pass
        else:
            registry.update_related(model.objects.get(pk=pk))
