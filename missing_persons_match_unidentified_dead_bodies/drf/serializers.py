from rest_framework import serializers

from missing_persons_match_unidentified_dead_bodies.backend.models import Report


class ReportSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(required=False, allow_blank=True, max_length=100)
    age = serializers.IntegerField()
    height = serializers.IntegerField(required=False)
    description = serializers.CharField()

    def create(self, validated_data):
        """
        Create and return a new `Snippet` instance, given the validated data.
        """
        return Report.objects.create(**validated_data)

    def update(self, instance, validated_data):
        """
        Update and return an existing `Snippet` instance, given the validated data.
        """
        instance.name = validated_data.get("name", instance.name)
        instance.age = validated_data.get("age", instance.age)
        instance.height = validated_data.get("height", instance.height)
        instance.description = validated_data.get("description", instance.description)
        instance.save()
        return instance
