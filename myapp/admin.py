from django.contrib import admin
from .models import *

# Register the models to make them available in the admin interface
admin.site.register(Navigation)
admin.site.register(FullTour)
admin.site.register(Robot)
admin.site.register(LastClickedNavigation)
admin.site.register(BaseStatus)
admin.site.register(PowerOn)
admin.site.register(RebootStatus)
admin.site.register(IPAddress)
admin.site.register(Sound)
admin.site.register(Speed)
admin.site.register(Charge)
admin.site.register(RobotFile)
admin.site.register(Charging)
admin.site.register(NavigationCancel)
admin.site.register(RefreshButton)
admin.site.register(APICredential)
admin.site.register(Scheduler)
admin.site.register(GeneralNotification)
