# Generated by Django 5.0.2 on 2024-03-06 01:25

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0008_alter_relationship_child_alter_relationship_parent'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='access',
            unique_together={('object', 'verb', 'property', 'rule', 'permission', 'type', 'accessor', 'group', 'weight')},
        ),
    ]
