from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('repo', '0002_default_superuser'),
    ]

    operations = [
        migrations.AlterField(
            model_name='repository',
            name='promote_to',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='repo.repository', unique=True),
        ),
    ]
