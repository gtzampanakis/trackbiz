# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from decimal import Decimal as D
import datetime, random

from django.test import TestCase

import apptb.models as am

random.seed('apptb.tests')

class Tester(TestCase):

    def setUp(self):
        self.client = am.Client.objects.create(
            code='CLIENT1', name='Client1',
            invoice_details_1 = 'Great Company Ltd.',
            invoice_details_2 = '25 Nice Road',
            invoice_details_3 = '1824 Great City')
        self.project = am.Project.objects.create(
            client=self.client, code='PROJECT1',
            name='Project1', hourly_rate=30,
            currency='EUR')
        self.N_TASKS = 18
        self.tasks = []
        for i in xrange(1, self.N_TASKS+1):
            self.tasks.append(am.Task.objects.create(
                project=self.project,
                date=datetime.date.today() + datetime.timedelta(days=i),
                short_desc='Task %s' % str(i).zfill(5),
                long_desc='long desc'))

    def test_charges_creation_1(self):
        for i in xrange(self.N_TASKS):
            am.Activity.objects.create(
                task=self.tasks[i],
                started_at=datetime.datetime.now(),
                hours=round(random.random()*5.2, 2))
            am.Activity.objects.create(
                task=self.tasks[i],
                started_at=datetime.datetime.now(),
                hours=round(random.random()*8.4, 2))
        am.update_charges_action(None, None, am.Activity.objects.all())
        
        for _ in xrange(2): # To test that charges are re-created.
            for chargei, charge in enumerate(am.Charge.objects.all(), 1):
                self.assertEqual(charge.hours,
                                 charge.activity.hours)
                self.assertEqual(charge.amount,
                                 charge.hours * charge.hourly_rate)
            self.assertEqual(chargei, am.Activity.objects.count())

    def test_invoice_creation(self):
        self.test_charges_creation_1()
        am.create_invoice(list(am.Charge.objects.all()))

        self.assertEqual(am.Invoice.objects.count(), 1)
        self.assertEqual(am.InvoiceLine.objects.count(),
                         am.Activity.objects.count())

        for charge in am.Charge.objects.all():
            self.assertIsNotNone(charge.invoice_line)
        for line in am.InvoiceLine.objects.all():
            self.assertEqual(line.amount,
                             sum(c.amount for c in am.Charge.objects.filter(
                                    invoice_line=line)))

        # AssertionError given because charges have already been invoiced.
        self.assertRaises(AssertionError, am.create_invoice, [charge])

