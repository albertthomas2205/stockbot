"""
URL configuration for stock project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from myapp.views import *
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('navigation/create/', create_navigation, name='create-navigation'),
    path('navigation/edit/<int:navigation_id>/', edit_navigation, name='edit_navigation'),
    path('navigation/list/', list_navigation, name='list-navigation'),
    path("delete-navigation/", delete_all_navigation, name="delete_all_navigation"),

    path('navigation/last-clicked/', get_last_clicked_navigation, name='get_last_clicked_navigation'),
    path('navigation/<int:nav_id>/', get_navigation_by_id, name='get_navigation_by_id'),

    path('base/status/', get_base_status, name='base_status'),
    path('update/base/status/', update_base_status, name='update_base_status'),

    path('upload-stcm/<str:stock_id>/', upload_stcm_file, name='upload-stcm'),
    path('latest-stcm/<str:stock_id>/', get_latest_stcm_file, name='latest-stcm'),
    path('stcm/delete/<str:stock_id>/', delete_stcm_file, name='delete_stcm_file'),

    path('data/create/', robot_create_or_update_view, name='robot-create-update'),
    path('data/list/', robot_list_view, name='robot-list'),

    path('delete-status/', delete_status, name='update_status'),
    path('get_delete_status/', get_delete_status, name='get_status'),

    path('full_tour/create/', create_full_tour, name='create_full_tour'),
    path('full_tour/list/', full_tour_list, name='full_tour_list'),
    path('fulltour/current/', get_current_full_tour, name='get_current_full_tour'),
    path('fulltour/update/<int:pk>/', update_full_tour, name='update_full_tour'),
    path('full-tour/delete/<int:pk>/',delete_full_tour, name='delete_full_tour'),



    path('on/', turn_on, name='turn_on'),
    path('off/', turn_off, name='turn_off'),
    path('status/', check_status, name='check_status'),

    path("update-reboot-status/", update_reboot_status, name="update_reboot_status"),
    path("get-reboot-status/", get_reboot_status, name="get_reboot_status"),


    path('ip-address/save/<str:stock_id>/', save_ip_address,name="save_ip_address"),
    path('ip-address/<str:stock_id>/', get_ip_address,name="ip-address"),

    path('sound/value/', update_or_create_sound, name='update_or_create_speed url'),
    path('current_sound/', get_current_sound_value, name='get_current_speed_value url'),

    path('speed/value/', update_or_create_speed, name='update_or_create_speed url'),
    path('current_speed/', get_current_speed_value, name='get_current_speed_value url'),

    path('charge/update/', create_or_update_charge, name='create_or_update_charge'),
    path('charge/current/', get_current_charge, name='get_current_charge'),

    path("volume/set/<str:stock_id>/<int:volume>/", set_volume, name="set_volume"),
    path("volume/get/<str:stock_id>/", get_volume, name="get_volume"),

    path('login/admin/',superadmin_login, name='superadmin_login'),
    path('logout/', superadmin_logout, name='superadmin_logout'),

    path('upload/zip/', upload_zip_file, name='upload_zip'),
    path('api/list/zip/<str:stock_id>/', list_zip_files, name='list_zip_files'),


    path('charging/get/', get_charging_status, name='get-charging'),
    path('charging/set/', set_charging_status, name='set-charging'),


    path('navigation/get/', get_navigation_cancel_status, name='get-navigation-status'),
    path('navigation/set/', set_navigation_cancel_status, name='set-navigation-status'),


    # py dev

    path('start_stop_button_press/',change_refresh_status,name='start stop button press url'),
    path('fetch_refresh_status/',fetch_refresh_status,name='fetch refresh status url'),

    path('save_auth_cred_from_api/',save_api_credentials,name='save auth cred from api url'),
    path('fetch_api_credentials/',fetch_api_credentials,name='fetch api credentials url'),

    path('api/save-schedulers/', save_schedulers, name='save_schedulers'),
    path('api/schedulers/', list_schedulers, name='list_schedulers'),
    path('api/scheduler/check-now/', check_current_scheduler, name='check_current_scheduler'),

    path('customer-connection/create/update/', create_or_update_customer_connection, name='get-all-customer-connection-create or-update'),
    path('customer-connection/all/', get_customer_connection_data, name='get all customer connection'),

    path('notification/save-notification/', save_notification, name='save_notification'),
    path('notification/seen/<int:pk>/', mark_notification_as_seen, name='mark_notification_as_seen'),
    path('notifications/unseen/', get_unseen_notifications, name='get_unseen_notifications'),


] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)