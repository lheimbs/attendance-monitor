# Generated by Django 3.1.7 on 2021-03-03 09:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('control', '0009_auto_20210301_1730'),
    ]

    operations = [
        migrations.AddConstraint(
            model_name='weekday',
            constraint=models.CheckConstraint(check=models.Q(day__in=[('MON', 'Monday'), ('TUE', 'Tuesday'), ('WED', 'Wednesday'), ('THU', 'Thursday'), ('FRI', 'Friday'), ('SAT', 'Saturday'), ('SUN', 'Sunday')]), name='control_weekday_day_valid'),
        ),
    ]