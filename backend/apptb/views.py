# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render

from rest_framework import viewsets

import apptb.models as am
import apptb.serializers as as_

class ActivityViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = am.Activity.objects.none().order_by('id')
    serializer_class = as_.ActivitySerializer

    def get_queryset(self):
        client_web_key = self.request.query_params.get('client_web_key')
        client = am.ClientWebKey.objects.get(key = client_web_key).client
        return am.Activity.objects.filter(
            task__project__client = client
        ).order_by('id')
