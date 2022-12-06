from rest_framework import serializers

class ScoreboardSerializer(serializers.Serializer):
    email = serializers.SerializerMethodField()
    score = serializers.SerializerMethodField()

    def get_email(self, obj):
        return obj[0]

    def get_score(self, obj):
        return obj[1]
