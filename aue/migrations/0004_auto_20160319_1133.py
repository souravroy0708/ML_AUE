# -*- coding: utf-8 -*-
# Generated by Django 1.9.1 on 2016-03-19 06:03
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('aue', '0003_enquirydetails_url'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='enquirydetails',
            unique_together=set([('parent_url', 'child_url', 'url')]),
        ),
    ]
