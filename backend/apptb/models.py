# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import datetime
import itertools
import os
import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files import File
from django.core.files.base import ContentFile
from django.db import models, transaction
from django.templatetags.static import static

from apptb.utils import pk8, pk16, format_amount

DEBUG_PDF = False

def format_date(date):
    return '%s-%s-%s' % (
        str(date.day).zfill(2),
        str(date.month).zfill(2),
        str(date.year).zfill(4),
    )

@transaction.atomic
def update_charges_action(modeladmin, request, activities_qs):
    for activity in activities_qs:
        try:
            charge_db = Charge.objects.get(activity = activity)
        except Charge.DoesNotExist:
            charge_db = None
        if activity.hours is not None:
            hours = activity.hours
        else:
            hours = (
                (activity.finished_at - activity.started_at)
                    .total_seconds() / 3600.
            )
        hours = round(hours, 2)
        amount = (float(activity.task.project.hourly_rate)
                    * float(hours))
        amount = round(amount, 2)
        charge = Charge(
            pk = charge_db is not None and charge_db.pk or None,
            activity = activity,
            date = datetime.date.today(),
            amount = amount,
            currency = activity.task.project.currency,
            hourly_rate = activity.task.project.hourly_rate,
            hours = hours,
            created_at = (
                charge_db is not None
                and charge_db.created_at or datetime.datetime.now()),
            updated_at = datetime.datetime.now(),
        )
        charge.save()

def create_invoice_action(modeladmin, request, charges_qs):
    return create_invoice(list(charges_qs))

def recreate_invoice_document_action(modeladmin, request, invoice_qs):
    for invoice in invoice_qs.order_by('number'):
        document_buffer = create_invoice_document(invoice)
        save_document_buffer_and_update_invoice(invoice, document_buffer)

def create_invoice_document(invoice):
    import cStringIO

    from reportlab.platypus import Table, TableStyle, Paragraph

    from reportlab.lib import colors
    from reportlab.lib.enums import TA_LEFT, TA_CENTER
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.pdfgen import canvas

    out_buffer = cStringIO.StringIO()

    total_amount = sum(l.amount for l in invoice.invoiceline_set.all())
    currencies = set(l.currency for l in invoice.invoiceline_set.all())
    assert len(currencies) == 1
    currency = list(currencies)[0]
    del currencies

    W, H = A4 # Width, Height
    SM = 45 # Side margin
    TM = 45 # Top/bottom margin
    TLX, TLY = (SM, H-TM) # Top left
    TRX, TRY = (W-SM, H-TM) # Top right
    BLX, BLY = (SM, TM) # Bottom left
    BRX, BRY = (W-SM, TM) # Bottom right
    AVW = W-2*SM # Available width
    AVH = H-2*TM # Available height
    RIGHT_SIDE_INFO_X = W/2+10

    c = canvas.Canvas(out_buffer, pagesize=A4)

    if DEBUG_PDF:
        c.rect(BLX, BLY, AVW, AVH)

    issuer_info_text = c.beginText()
    issuer_info_text.setTextOrigin(TLX, TLY-20)
    issuer_info_text.setFont('Helvetica-Bold', 18)
    issuer_info_text.textLine('Giorgos Tzampanakis')
    issuer_info_text.moveCursor(0, -2)

    issuer_info_text.setFont('Helvetica-Bold', 14)
    issuer_info_text.textLine('Computer Programmer')
    issuer_info_text.moveCursor(0, 1)

    issuer_info_text.setFont('Helvetica', 12)
    issuer_info_text.textLines('''
        2 Theotoki, Flat 301
        1055 Nicosia, Cyprus
        Tax ID Code: 08045231L
        +357 96-68-3803
        giorgos.tzampanakis@gmail.com
    ''')
    issuer_info_text.textLine()
    c.drawText(issuer_info_text)

    invoice_info_text = c.beginText()
    invoice_info_text.setTextOrigin(RIGHT_SIDE_INFO_X, TRY-25)

    invoice_info_text.setFont('Helvetica-Bold', 28)
    invoice_info_text.textLine('INVOICE')

    invoice_info_text.setFont('Helvetica-Bold', 14)
    invoice_info_text.textOut('Invoice date: ')
    invoice_info_text.setFont('Helvetica', 14)
    invoice_info_text.textLine(format_date(invoice.date))

    invoice_info_text.setFont('Helvetica-Bold', 14)
    invoice_info_text.textOut('Invoice number: ')
    invoice_info_text.setFont('Helvetica', 14)
    invoice_info_text.textLine(str(invoice.number).zfill(4))

    c.drawText(invoice_info_text)

    x, y = issuer_info_text.getCursor()
    bill_to_info = c.beginText()
    bill_to_info.setTextOrigin(x, y-10)
    bill_to_info.setFont('Helvetica-Bold', 14)
    bill_to_info.textLine('Bill To:')
    for i in xrange(1, 7):
        info = getattr(invoice.client, 'invoice_details_' + str(i), None)
        if info:
            bill_to_info.setFont('Helvetica', 14)
            bill_to_info.textLine(info)
    x, y = bill_to_info.getCursor()
    c.drawText(bill_to_info)

    border_padding = 6
    pay_info_style = ParagraphStyle(
                    'PleasePayStyle',
                    alignment=TA_LEFT,
                    fontName='Helvetica',
                    fontSize=10,
                    borderWidth=1,
                    borderPadding=(4, 6, 14, 6),
                    borderRadius=4,
                    borderColor=colors.black)

    please_pay_text = '''
        <para autoLeading=max>
        <b>PLEASE PAY: &nbsp;</b><font size=24><b>%s</b></font>
        <br/><b>Bank Name:</b> USB BANK
        <br/><b>Name:</b> TZAMPANAKIS GEORGIOS
        <br/><b>Account Number:</b> 152-5-0010422-27017
        <br/><b>IBAN:</b> CY37 0110 0022 1525 0010 4222 7017
        <br/><b>Swift Code:</b> UNVKCY2N
        </para>
    ''' % format_amount(total_amount, currency)
    paragraph = Paragraph(please_pay_text, pay_info_style)
    paragraph.wrapOn(c, TRX - RIGHT_SIDE_INFO_X - border_padding*1.5, 100)
    paragraph.drawOn(c, RIGHT_SIDE_INFO_X, y+28)

    data_header = ['Date', 'Description',
                   'Quantity', 'Unit Price', 'Amount']
    data_footer = ['', '',
                   '', 'Total', format_amount(total_amount, currency)]
    col_widths = [60, 200,
                  70, 60, 50]
    col_widths = [float(n)/sum(col_widths)*AVW for n in col_widths]

    data = [data_header] + [
        [
            format_date(line.date),
            Paragraph(line.description, ParagraphStyle('DescriptionStyle')),
            ' '.join([str(line.quantity), str(line.units)]),
            format_amount(line.unit_price, line.currency),
            format_amount(line.amount, line.currency),
        ]
        for line in invoice.invoiceline_set.order_by('index')
    ] + [data_footer]

    for line in data:
        assert len(data_header) == len(line)
        assert len(col_widths) == len(line)

    table = Table(data, colWidths=col_widths)
    table_style = TableStyle([
        ('FONT', (0,0), (-1,0), 'Helvetica-Bold', 12),
        ('FONT', (0,1), (-1,-1), 'Helvetica', 11),
        ('FONT', (0,-1), (-1,-1), 'Helvetica-Bold', 11),
        ('ALIGN', (0,0), (1,-1), 'LEFT'),
        ('ALIGN', (2,0), (-1,-1), 'RIGHT'),
        ('LINEABOVE', (0,1), (-1,1), 1, colors.black),
        ('LINEABOVE', (0,2), (-1,-2), 1, '#CFCFCF'),
        ('LINEABOVE', (0,-1), (-1,-1), 1, colors.black),
    ])
    table.setStyle(table_style)

    def end_page():
        c.setFont('Helvetica', 11)
        c.drawCentredString(W/2, TM/2+5,
                            'Page %s/%s' % (current_page, total_pages))
        # c.line(BLX, BLY-14, BRX, BRY-14)
        c.showPage()

    y -= 10
    y0 = y
    total_pages = 0
    for run_kind in ['count_pages', 'draw']:
        current_page = 1
        current_table = table
        while True:
            if current_page == 1:
                y = y0 - 4
                available_height_for_table = y - BLY
            else:
                y = TLY
                available_height_for_table = AVH
            parts = current_table.split(AVW, available_height_for_table)
            part_width, part_height = parts[0].wrapOn(c, AVW,
                                                   available_height_for_table)
            if run_kind == 'draw':
                parts[0].drawOn(c, TLX, y - part_height)
                end_page()
            if len(parts) == 1:
                break
            current_table = parts[1]
            current_page += 1
        if run_kind == 'count_pages':
            total_pages = current_page

    c.save()

    return out_buffer.getvalue()

def save_document_buffer_and_update_invoice(invoice, document_buffer):
    filename=('invoice'
              + '_' + invoice.client.code
              + '_' + str(invoice.number).zfill(4) + '.pdf')
    path = os.path.join(settings.INVOICE_DOCUMENTS_DIR, filename)
    if not os.path.exists(os.path.dirname(path)):
        os.makedirs(os.path.dirname(path), 0775)
    with open(path, 'wb') as fobj:
        fobj.write(document_buffer)
    invoice.filename = filename
    invoice.save(update_fields=['filename'])

@transaction.atomic
def create_invoice(charges):
    clients = set()
    for charge in charges:
        clients.add(charge.activity.task.project.client)
    if len(clients) > 1:
        raise ValidationError('More than one clients in the charges passed')

    try:
        last_number = Invoice.objects.latest('number').number
    except Invoice.DoesNotExist as e:
        last_number = 0

    client = list(clients)[0]
    number = last_number + 1

    invoice = Invoice(
        number=number,
        date=datetime.date.today(),
        client=client,
    )

    for charge in charges:
        assert charge.invoice_line is None

    charges = sorted(charges,
                     key=lambda c: (
                            c.activity.task.date,
                            c.activity.task.short_desc,
                            c.activity.task.pk,
                            c.activity.started_at,
                            c.activity.pk))

    for ci, c in enumerate(charges, 1):

        line = InvoiceLine(
            invoice=invoice,
            index=ci,
            date=c.activity.started_at.date(),
            description=c.activity.task.short_desc,
            quantity=c.hours,
            units='hours',
            amount=c.amount,
            currency=c.currency,
        )
        line.unit_price = line.amount / line.quantity

        line.save()

        c.invoice_line = line
        c.save()

    # document creation

    invoice.save() # Necessary in order to associate the lines with the invoice
    document_buffer = create_invoice_document(invoice)
    save_document_buffer_and_update_invoice(invoice, document_buffer)

class Client(models.Model):
    id = models.CharField(max_length=8, primary_key=True,
                          default=pk8, editable=False)
    code = models.CharField(max_length=16, unique=True)
    name = models.CharField(max_length=256)
    invoice_details_1 = models.CharField(max_length=256, null=True, blank=True)
    invoice_details_2 = models.CharField(max_length=256, null=True, blank=True)
    invoice_details_3 = models.CharField(max_length=256, null=True, blank=True)
    invoice_details_4 = models.CharField(max_length=256, null=True, blank=True)
    invoice_details_5 = models.CharField(max_length=256, null=True, blank=True)
    invoice_details_6 = models.CharField(max_length=256, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['code']
        verbose_name = 'Client'
        verbose_name_plural = 'Clients'

    def __unicode__(self):
        return unicode(self.code)

class ClientWebKey(models.Model):
    id = models.CharField(max_length=8, primary_key=True,
                          default=pk8, editable=False)
    client = models.ForeignKey('Client')
    key = models.CharField(max_length=16, unique=True, default=pk16)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['client', 'id']
        verbose_name = 'Client Web Key'
        verbose_name_plural = 'Client Web Keys'

    def __unicode__(self):
        return unicode(self.client) + '-' + self.key


class Project(models.Model):
    id = models.CharField(max_length=8, primary_key=True,
                          default=pk8, editable=False)
    client = models.ForeignKey('Client')
    code = models.CharField(max_length=16, unique=True)
    name = models.CharField(max_length=256)
    hourly_rate = models.DecimalField(max_digits=5, decimal_places=2)
    currency = models.CharField(max_length=3)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['code']
        verbose_name = 'Project'
        verbose_name_plural = 'Projects'

    def __unicode__(self):
        return unicode(self.code)

class Task(models.Model):
    id = models.CharField(max_length=8, primary_key=True,
                          default=pk8, editable=False)
    project = models.ForeignKey('Project')
    date = models.DateField()
    short_desc = models.CharField(max_length=128)
    long_desc = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at', 'project', 'date', 'short_desc']
        verbose_name = 'Task'
        verbose_name_plural = 'Tasks'

    def __unicode__(self):
        return unicode(self.short_desc)


class Activity(models.Model):
    id = models.CharField(max_length=8, primary_key=True,
                          default=pk8, editable=False)
    task = models.ForeignKey('Task')
    description = models.TextField(null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    hours = models.DecimalField(max_digits=6, decimal_places=3,
                                null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at', 'task', 'started_at']
        verbose_name = 'Activity'
        verbose_name_plural = 'Activities'

    def clean(self):
        if (
                self.finished_at is not None
            and self.hours is not None
        ):
            raise ValidationError(
                'Only one of finished_at, hours can be defined')

    def __unicode__(self):
        return '%s - %s - %s - %s' % (
            self.task,
            self.started_at and self.started_at.date(),
            self.finished_at and self.finished_at.date(),
            self.hours)

class Charge(models.Model):
    id = models.CharField(max_length=8, primary_key=True,
                          default=pk8, editable=False)
    activity = models.OneToOneField('Activity')
    invoice_line = models.ForeignKey('InvoiceLine', null=True,
                                     on_delete=models.SET_NULL)
    date = models.DateField()
    hours = models.DecimalField(max_digits=6, decimal_places=3,
                                null=True, blank=True)
    hourly_rate = models.DecimalField(max_digits=5, decimal_places=2)
    amount = models.DecimalField(max_digits=20, decimal_places=2)
    currency = models.CharField(max_length=3)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date', 'activity']
        verbose_name = 'Charge'
        verbose_name_plural = 'Charges'

    def __unicode__(self):
        return '%s' % self.activity

class RecvPayment(models.Model):
    id = models.CharField(max_length=8, primary_key=True,
                          default=pk8, editable=False)
    client = models.ForeignKey('Client')
    date = models.DateField()
    amount = models.DecimalField(max_digits=20, decimal_places=2)
    currency = models.CharField(max_length=3)
    external_id = models.CharField(max_length=128,
                                   null=True, blank=True, unique=True)
    external_id_desc = models.CharField(max_length=256,
                                        null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['date', 'client']
        verbose_name = 'Received Payment'
        verbose_name_plural = 'Received Payments'

    def __unicode__(self):
        return unicode(self.id)

class Invoice(models.Model):
    id = models.CharField(max_length=8, primary_key=True,
                          default=pk8, editable=False)
    number = models.IntegerField(unique=True)
    date = models.DateField()
    client = models.ForeignKey('Client')
    filename = models.CharField(max_length=128, null=True, editable=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['number']
        verbose_name = 'Invoice'
        verbose_name_plural = 'Invoices'

    def __unicode__(self):
        return unicode(self.number).zfill(4)

class InvoiceLine(models.Model):
    id = models.CharField(max_length=8, primary_key=True,
                          default=pk8, editable=False)
    invoice = models.ForeignKey('Invoice')
    index = models.IntegerField()
    date = models.DateField()
    description = models.CharField(max_length=128)
    quantity = models.DecimalField(max_digits=5, decimal_places=2)
    units = models.CharField(max_length=32)
    unit_price = models.DecimalField(max_digits=20, decimal_places=2)
    amount = models.DecimalField(max_digits=20, decimal_places=2)
    currency = models.CharField(max_length=3)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['invoice', 'index']
        verbose_name = 'Invoice Line'
        verbose_name_plural = 'Invoice Lines'

    def __unicode__(self):
        return unicode(self.id)

