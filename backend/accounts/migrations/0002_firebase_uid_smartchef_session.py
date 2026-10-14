from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):
    dependencies = [("accounts", "0001_initial")]

    operations = [
        migrations.AddField(
            model_name="user",
            name="firebase_uid",
            field=models.CharField(blank=True, max_length=128, null=True, unique=True),
        ),
        migrations.CreateModel(
            name="SmartChefSession",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("session_id", models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ("platform", models.CharField(choices=[("flutter", "Flutter"), ("web", "Web")], max_length=16)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("last_seen", models.DateTimeField(auto_now=True)),
                ("expires_at", models.DateTimeField()),
                ("user", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="smartchef_session", to="accounts.user")),
            ],
            options={"ordering": ["-last_seen"]},
        ),
    ]
