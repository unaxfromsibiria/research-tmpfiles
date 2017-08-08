# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2017-08-08 13:10
from __future__ import unicode_literals

import django.contrib.gis.db.models.fields
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='BaseEvent',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('event_type', models.SmallIntegerField(default=0, verbose_name='Event type')),
                ('time_start', models.DateTimeField(verbose_name='Event time begin')),
                ('time_end', models.DateTimeField(verbose_name='Event time end')),
                ('uid', models.UUIDField(verbose_name='User or device ID')),
                ('location', django.contrib.gis.db.models.fields.PointField(geography=True, null=True, srid=4326, verbose_name='Location of this event')),
            ],
            options={
                'verbose_name': 'Base event',
                'db_table': 'bioevent_activity_base',
            },
        ),
        migrations.CreateModel(
            name='MovementEventModel',
            fields=[
                ('baseevent_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='activity.BaseEvent')),
                ('step_count', models.IntegerField(default=0, verbose_name='Count of steps')),
            ],
            options={
                'verbose_name': 'Movement',
                'db_table': 'bioevent_activity_movement',
            },
            bases=('activity.baseevent',),
        ),
        migrations.CreateModel(
            name='SleepEventModel',
            fields=[
                ('baseevent_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='activity.BaseEvent')),
            ],
            options={
                'verbose_name': 'Sleep',
                'db_table': 'bioevent_activity_sleep',
            },
            bases=('activity.baseevent',),
        ),
    ]
