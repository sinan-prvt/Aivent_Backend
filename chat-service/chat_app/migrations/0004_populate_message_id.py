import uuid
from django.db import migrations, models


def populate_message_ids(apps, schema_editor):
    ChatMessage = apps.get_model("chat_app", "ChatMessage")
    for msg in ChatMessage.objects.filter(message_id__isnull=True):
        msg.message_id = uuid.uuid4()
        msg.save(update_fields=["message_id"])


class Migration(migrations.Migration):

    dependencies = [
        ("chat_app", "0003_chatmessage_message_id"),
    ]

    operations = [
        migrations.RunPython(populate_message_ids),

        migrations.AlterField(
            model_name="chatmessage",
            name="message_id",
            field=models.UUIDField(unique=True, db_index=True),
        ),
    ]
