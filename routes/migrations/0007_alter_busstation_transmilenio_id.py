# Generated by Django 4.0.1 on 2022-02-27 02:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('routes', '0006_alter_busstation_code'),
    ]

    operations = [
        migrations.AlterField(
            model_name='busstation',
            name='transmilenio_id',
            field=models.IntegerField(default=None, unique=True),
            preserve_default=False,
        ),
    ]