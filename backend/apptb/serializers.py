from rest_framework import serializers, viewsets

import apptb.models as am

class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = am.Task
        fields = '__all__'

class ActivitySerializer(serializers.ModelSerializer):
    task = TaskSerializer(read_only=True)
    class Meta:
        model = am.Activity
        fields = '__all__'
