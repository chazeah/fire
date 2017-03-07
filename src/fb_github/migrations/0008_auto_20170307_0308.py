# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-03-07 03:08
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('fb_github', '0007_auto_20170302_2254'),
    ]

    operations = [
        migrations.AddField(
            model_name='repository',
            name='initial_issue',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='fb_github.Issue'),
        ),
        migrations.AlterField(
            model_name='issue',
            name='msg',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='fb_emails.IncomingMessage'),
        ),
    ]
