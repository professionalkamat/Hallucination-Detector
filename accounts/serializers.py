from django.contrib.auth.models import User
from rest_framework import serializers


class RegisterSerializer(serializers.ModelSerializer):
    name = serializers.CharField(
        write_only=True,
        max_length=100
    )
    password = serializers.CharField(
        write_only=True,
    )
    email = serializers.EmailField(
        required=True
    )

    class Meta:
        model = User
        fields = [
            "username",
            "name",
            "email",
            "password"
        ]

    def validate_username(self, value):
        if User.objects.filter(
            username__iexact=value
        ).exists():
            raise serializers.ValidationError(
                "Username already exists."
            )
        return value

    def validate_email(self, value):
        if User.objects.filter(
            email__iexact=value
        ).exists():
            raise serializers.ValidationError(
                "An account with this email already exists."
            )
        return value


    def create(self, validated_data):
        name = validated_data.pop("name")
        user = User(
            username=validated_data["username"],
            email=validated_data["email"],
            first_name=name
        )
        user.set_password(
            validated_data["password"]
        )
        user.save()
        return user

class UserSerializer(serializers.ModelSerializer):
    name = serializers.CharField(
        source="first_name"
    )
    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "name"
        ]