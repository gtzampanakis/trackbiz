# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render

from rest_framework import viewsets

import apptb.models as am
import apptb.serializers as as_

class ActivityViewSet(viewsets.ModelViewSet):
    queryset = am.Activity.objects.all().order_by('id')
    serializer_class = as_.ActivitySerializer
