# Generated by Django 3.1.1 on 2020-11-23 19:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('notes', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='note',
            options={'ordering': ('-created',)},
        ),
        migrations.AlterField(
            model_name='note',
            name='content',
            field=models.TextField(null=True),
        ),
    ]
