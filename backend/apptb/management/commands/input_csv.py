import argparse, re, string

from django.db import transaction
from django.core.management.base import BaseCommand, CommandError
import apptb.models as am

class Command(BaseCommand):
    help = 'Input a CSV as pasted by Google Docs'

    def add_arguments(self, parser):
        parser.add_argument('infile', type=argparse.FileType('rb'))

    @transaction.atomic
    def handle(self, *args, **options):
        fo = options['infile']

        project = am.Project.objects.get(code = 'billing')

        tasks_created = 0
        activities_created = 0

        for line in fo:
            line = line.strip()
            date, hours, desc = string.split(line, maxsplit=2)
            found_tasks = am.Task.objects.filter(
                short_desc = desc
            )
            if len(found_tasks) > 1:
                raise Exception
            if len(found_tasks) == 1:
                task = found_tasks[0]
            if len(found_tasks) == 0:
                task = am.Task.objects.create(
                    short_desc = desc,
                    date = date,
                    project = project,
                )
                tasks_created += 1

            activity = am.Activity.objects.create(
                task = task,
                description = desc,
                started_at = date,
                hours = hours
            )
            activities_created += 1

        print 'Tasks created: %s' % tasks_created
        print 'Activities created: %s' % activities_created
