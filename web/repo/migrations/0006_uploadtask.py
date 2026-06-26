from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('repo', '0005_alter_package_unique_together'),
        ('repo', '0002a_unique_promote_to'),
    ]

    operations = [
        migrations.CreateModel(
            name='UploadTask',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('status', models.CharField(default='uploading', max_length=20)),
                ('filename', models.CharField(max_length=65536)),
                ('filesize', models.BigIntegerField(default=0)),
                ('overwrite', models.BooleanField(default=False)),
                ('stored_path', models.CharField(max_length=65536)),
                ('sha512', models.CharField(blank=True, max_length=512)),
                ('error_message', models.TextField(blank=True)),
                ('result_data', models.JSONField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('completed_at', models.DateTimeField(blank=True, null=True)),
                ('repo', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='repo.repository')),
            ],
        ),
    ]
