from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("vendor_app", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="vendorprofile",
            name="user_id",
            field=models.UUIDField(null=True, blank=True, db_index=True),
        ),
    ]

