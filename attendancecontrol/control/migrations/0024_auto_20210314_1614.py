# Generated by Django 3.1.7 on 2021-03-14 15:14

from django.db import migrations, models
import django.db.models.deletion
import macaddress.fields


class Migration(migrations.Migration):

    dependencies = [
        ('control', '0023_remove_accesstoken_modified'),
    ]

    operations = [
        migrations.CreateModel(
            name='WifiInfo',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(editable=False)),
                ('modified', models.DateTimeField()),
                ('mac', macaddress.fields.MACAddressField(blank=True, integer=False, max_length=17, null=True)),
                ('mac_burst_interval', models.FloatField(default=0)),
                ('mac_burst_count', models.PositiveIntegerField(default=0)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.RemoveField(
            model_name='student',
            name='mac',
        ),
        migrations.AddField(
            model_name='student',
            name='wifi_info',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='control.wifiinfo'),
        ),
    ]
