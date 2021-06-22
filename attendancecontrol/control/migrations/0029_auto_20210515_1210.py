# Generated by Django 3.1.7 on 2021-05-15 10:10

from django.db import migrations, models
import macaddress.fields


class Migration(migrations.Migration):

    dependencies = [
        ('control', '0028_auto_20210515_1037'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='proberequest',
            options={'managed': True},
        ),
        migrations.AlterField(
            model_name='proberequest',
            name='id',
            field=models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='proberequest',
            name='mac',
            field=macaddress.fields.MACAddressField(blank=True, integer=False, max_length=17, null=True),
        ),
    ]