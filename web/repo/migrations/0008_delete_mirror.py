from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('repo', '0007_pgpsigningkey_passphrase'),
    ]

    operations = [
        migrations.DeleteModel(
            name='Mirror',
        ),
    ]
