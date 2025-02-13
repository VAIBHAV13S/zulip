# Generated by Django 5.0.9 on 2024-12-23 10:03

from datetime import timedelta

from django.db import migrations, transaction
from django.db.backends.base.schema import BaseDatabaseSchemaEditor
from django.db.migrations.state import StateApps
from django.utils.timezone import now as timezone_now


def check_update_all_channels_active_status(
    apps: StateApps, schema_editor: BaseDatabaseSchemaEditor
) -> None:
    Channel = apps.get_model("zerver", "Stream")
    Message = apps.get_model("zerver", "Message")
    Realm = apps.get_model("zerver", "Realm")
    Recipient = apps.get_model("zerver", "Recipient")

    Recipient.STREAM = 2
    Channel.LAST_ACTIVITY_DAYS_BEFORE_FOR_ACTIVE = 180

    date_days_ago = timezone_now() - timedelta(days=Channel.LAST_ACTIVITY_DAYS_BEFORE_FOR_ACTIVE)

    for realm in Realm.objects.filter(deactivated=False):
        with transaction.atomic(durable=True):
            active_channel_ids = (
                Message.objects.filter(
                    date_sent__gte=date_days_ago,
                    recipient__type=Recipient.STREAM,
                    realm=realm,
                )
                .values_list("recipient__type_id", flat=True)
                .distinct()
            )

            channels_to_mark_inactive_queryset = Channel.objects.filter(
                is_recently_active=True, realm=realm
            ).exclude(id__in=active_channel_ids)
            channels_to_mark_inactive_queryset.update(is_recently_active=False)


class Migration(migrations.Migration):
    atomic = False

    dependencies = [
        ("zerver", "0643_realm_scheduled_deletion_date"),
    ]

    operations = [
        migrations.RunPython(
            check_update_all_channels_active_status,
            elidable=True,
            reverse_code=migrations.RunPython.noop,
        )
    ]
