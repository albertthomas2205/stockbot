from rest_framework import serializers
from .models import *

class NavigationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Navigation
        fields = ['id', 'name']


class RobotSerializer(serializers.ModelSerializer):
    class Meta:
        model = Robot
        fields = '__all__'


class STCMFileSerializer(serializers.Serializer):
    file = serializers.FileField()


class FullTourSerializer(serializers.ModelSerializer):
    navigations = serializers.SerializerMethodField()

    class Meta:
        model = FullTour
        fields = ['id', 'navigations','tour_date','tour_time','full_tour_name']

    def get_navigations(self, obj):
        # Retrieve navigations in the order stored in JSONField
        navigations = {nav.id: nav for nav in Navigation.objects.filter(id__in=obj.navigations)}
        ordered_navigations = [navigations[nav_id] for nav_id in obj.navigations if nav_id in navigations]
        return NavigationSerializer(ordered_navigations, many=True).data
    


class IPAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = IPAddress
        fields = ['ip_address', 'created_at','stock_id']


class SoundSerializer(serializers.ModelSerializer):
    value = serializers.FloatField(min_value=0, max_value=150)

    class Meta:
        model = Sound
        fields = ['id', 'value']

    def to_internal_value(self, data):
        data = super().to_internal_value(data)
        # Convert float to string before saving
        data['value'] = str(data['value'])
        return data
    


    
class SpeedSerializer(serializers.ModelSerializer):
    value = serializers.FloatField(min_value=0.1, max_value=0.7)

    class Meta:
        model = Speed
        fields = ['id', 'value']

    def to_internal_value(self, data):
        data = super().to_internal_value(data)
        # Convert float to string before saving
        data['value'] = str(data['value'])
        return data
    



class ChargeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Charge
        fields = ['id', 'low_battery_entry', 'back_to_home_entry']


class RobotFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = RobotFile
        fields = ['robot', 'zip_file', 'uploaded_at']


class ChargingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Charging
        fields = ['status']


class NavigationCancelSerializer(serializers.ModelSerializer):
    class Meta:
        model = NavigationCancel
        fields = ['status']



# py dev

class RefreshButtonSerializer(serializers.ModelSerializer):
    class Meta:
        model = RefreshButton
        fields = ['id' , 'status']

class APICredentialSerializer(serializers.ModelSerializer):
    class Meta:
        model = APICredential
        fields = '__all__'

    def create(self, validated_data):
        username = validated_data.get('username')
        APICredential.objects.filter(username=username).delete()
        return super().create(validated_data)

class SchedulerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Scheduler
        fields = '__all__'

class CustomerConnectionDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerConnectionData
        fields = ['customer_url', 'customer_id']

    def create(self, validated_data):
        # Try to update the existing instance or create new if not exists
        instance, created = CustomerConnectionData.objects.update_or_create(
            defaults=validated_data
        )
        return instance

    def update(self, instance, validated_data):
        instance.customer_url = validated_data.get('customer_url', instance.customer_url)
        instance.customer_id = validated_data.get('customer_id', instance.customer_id)
        instance.save()
        return instance
    
class GeneralNotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = GeneralNotification
        fields = ['id', 'title', 'notification', 'created_at', 'seen']
        read_only_fields = ['id', 'created_at']
