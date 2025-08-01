from collections.abc import Iterable
from enum import Enum
from typing import Self

from django.core.serializers.json import DjangoJSONEncoder
from django.db import models


class EnumEncoder(DjangoJSONEncoder):
    def default(self, obj):
        if isinstance(obj, Enum):
            return obj.value
        return super().default(obj)


class Validator(models.Model):
    public_key = models.TextField(unique=True)
    active = models.BooleanField()
    debug = models.BooleanField(default=False)

    def __str__(self):
        return f"hotkey: {self.public_key}"


class ValidatorBlacklist(models.Model):
    validator = models.OneToOneField(Validator, on_delete=models.CASCADE)

    class Meta:
        verbose_name = "Blacklisted Validator"
        verbose_name_plural = "Blacklisted Validators"

    def __str__(self):
        return f"hotkey: {self.validator.public_key}"


class AcceptedJob(models.Model):
    class Status(models.TextChoices):
        WAITING_FOR_EXECUTOR = "WAITING_FOR_EXECUTOR"
        WAITING_FOR_PAYLOAD = "WAITING_FOR_PAYLOAD"
        RUNNING = "RUNNING"
        FINISHED = "FINISHED"
        FAILED = "FAILED"
        REJECTED = "REJECTED"

        @classmethod
        def end_states(cls) -> set["AcceptedJob.Status"]:
            """
            Determines which job statuses mean that the job will not be updated anymore.
            """
            return {cls.FINISHED, cls.FAILED, cls.REJECTED}

        def is_in_progress(self) -> bool:
            """
            Check if the job is in progress (has not completed or failed yet).
            """
            return self not in AcceptedJob.Status.end_states()

        def is_successful(self) -> bool:
            """Check if the job has finished successfully."""
            return self == self.FINISHED

        def is_failed(self) -> bool:
            """Check if the job has failed."""
            return self in (self.FAILED, self.REJECTED)

        def is_active(self) -> bool:
            """
            Check if the job is in an active state.
            """
            return self in {
                self.WAITING_FOR_EXECUTOR,
                self.WAITING_FOR_PAYLOAD,
                self.RUNNING,
            }

    validator = models.ForeignKey(Validator, on_delete=models.CASCADE)
    job_uuid = models.UUIDField()
    executor_token = models.CharField(max_length=73)
    status = models.CharField(choices=Status.choices, max_length=255)
    initial_job_details = models.JSONField(encoder=EnumEncoder)
    full_job_details = models.JSONField(encoder=EnumEncoder, null=True)
    exit_status = models.PositiveSmallIntegerField(null=True)
    stdout = models.TextField(blank=True, default="")
    stderr = models.TextField(blank=True, default="")
    error_type = models.TextField(null=True, default=None)
    error_detail = models.TextField(null=True, default=None)
    result_reported_to_validator = models.DateTimeField(null=True)
    time_took = models.DurationField(null=True)
    score = models.FloatField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    executor_address = models.TextField(null=True)
    artifacts = models.JSONField(encoder=EnumEncoder, null=True)
    upload_results = models.JSONField(null=True)

    def __str__(self):
        return (
            f"uuid: {self.job_uuid} - validator hotkey: {self.validator.public_key} - {self.status}"
        )

    @classmethod
    async def get_for_validator(cls, validator: Validator) -> dict[str, Self]:
        return {
            str(job.job_uuid): job
            async for job in cls.objects.filter(
                validator=validator,
                status__in=[
                    cls.Status.WAITING_FOR_EXECUTOR.value,
                    cls.Status.WAITING_FOR_PAYLOAD.value,
                    cls.Status.RUNNING.value,
                ],
            )
        }

    @classmethod
    async def get_not_reported(cls, validator: Validator) -> Iterable[Self]:
        return [
            job
            async for job in cls.objects.filter(
                validator=validator,
                status__in=[cls.Status.FINISHED.value, cls.Status.FAILED.value],
                result_reported_to_validator__isnull=True,
            )
        ]


class ClusterMiner(models.Model):
    hotkey = models.CharField(max_length=48, primary_key=True)
    block = models.BigIntegerField(null=True)

    def __str__(self):
        return f"hotkey: {self.hotkey}"
