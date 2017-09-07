# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf import settings
from django.contrib import admin
from django.utils.html import format_html

import apptb.models

class ActivityAdmin(admin.ModelAdmin):
    actions = [apptb.models.update_charges_action]

class ChargeAdmin(admin.ModelAdmin):
    actions = [apptb.models.create_invoice_action]
    list_filter = [
        'date',
    ]

class InvoiceAdmin(admin.ModelAdmin):

    def invoice_download_link(self, invoice):
        return format_html(
            '<a href="{}">{}</a>',
            settings.STATIC_URL + 'invoice_documents/' + invoice.filename,
            invoice.filename)

    actions = [apptb.models.recreate_invoice_document_action]
    list_display = ['__unicode__', 'invoice_download_link', 'client', 'date']

admin.site.register(apptb.models.Client)
admin.site.register(apptb.models.Project)
admin.site.register(apptb.models.Task)
admin.site.register(apptb.models.Activity, ActivityAdmin)
admin.site.register(apptb.models.Charge, ChargeAdmin)
admin.site.register(apptb.models.RecvPayment)
admin.site.register(apptb.models.Invoice, InvoiceAdmin)
admin.site.register(apptb.models.ClientWebKey)
