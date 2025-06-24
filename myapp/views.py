from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Navigation
from .serializers import *
from rest_framework import status
from django.core.cache import cache
from datetime import datetime, timedelta
from django.http import JsonResponse
from django.conf import settings
from django.core.files.storage import default_storage
from django.http import JsonResponse
import os
import requests
from django.utils import timezone
from rest_framework import status as drf_status
from .utils import get_poweron_object
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login,logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404
from io import StringIO
from rest_framework.parsers import MultiPartParser, FormParser
from django.core.files.storage import FileSystemStorage
from urllib.parse import urljoin
from django.core.files.storage import FileSystemStorage
import zipfile
from django.db import DatabaseError
from django.utils.timezone import now
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.utils.timezone import now
from .models import Scheduler
from .serializers import SchedulerSerializer
from django.utils.timezone import localtime

@api_view(['POST'])
def create_navigation(request):
    serializer = NavigationSerializer(data=request.data)
    
    if serializer.is_valid():
        serializer.save()
        return Response({"status": "ok", "message": "Navigation created successfully", "data": serializer.data}, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['PUT'])
def edit_navigation(request, navigation_id):
    """
    Allows authenticated users to update an existing navigation entry.
    """
    try:
        navigation = Navigation.objects.get(id=navigation_id)
    except Navigation.DoesNotExist:
        return Response({"error": "Navigation not found."}, status=status.HTTP_404_NOT_FOUND)

    serializer = NavigationSerializer(navigation, data=request.data, partial=True)

    if serializer.is_valid():
        serializer.save()
        return Response({"status": "ok", "message": "Navigation updated successfully", "data": serializer.data}, status=status.HTTP_200_OK)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['DELETE'])
def delete_all_navigation(request):
    """
    Delete all navigation records.
    """
    Navigation.objects.all().delete()  
    return Response({"status": "ok", "message": "All navigation records deleted successfully"}, status=status.HTTP_204_NO_CONTENT)

@api_view(['GET'])
def list_navigation(request):
    navigations = Navigation.objects.all()
    serializer = NavigationSerializer(navigations, many=True, context={'request': request})  
    return Response({"status": "ok", "message": "Navigation list", "data": serializer.data}, status=status.HTTP_200_OK)


@api_view(['POST'])
def update_base_status(request):
    new_status = request.data.get('status', None)
    print("Incoming status:", new_status, type(new_status))  # Debug print

    if new_status is None:
        return Response({"message": "Status is required"}, status=status.HTTP_400_BAD_REQUEST)

    base_status, created = BaseStatus.objects.get_or_create(id=1)
    base_status.status = new_status
    base_status.last_updated = datetime.now() if new_status else None
    base_status.save()

    return Response({
        "message": "Status updated successfully",
        "status": base_status.status,
        "last_updated": base_status.last_updated
    }, status=status.HTTP_200_OK)

@api_view(['GET'])
def get_base_status(request):
    base_status, created = BaseStatus.objects.get_or_create(id=1)

    # Check if the status is True and last_updated exists
    if base_status.status and base_status.last_updated:
        elapsed_time = (timezone.now() - base_status.last_updated).total_seconds()  # Use timezone.now() here
        if elapsed_time > 15:  # If the status has been True for more than 15 seconds
            base_status.status = False  # Reset status to False
            base_status.last_updated = None  # Reset last_updated to None
            base_status.save()

    # Return the current status, always return status as True/False
    return Response({"status": bool(base_status.status)}, status=drf_status.HTTP_200_OK)


def get_robot_upload_dir(stock_id):
    upload_dir = os.path.join(settings.MEDIA_ROOT, 'stm_files', stock_id)
    os.makedirs(upload_dir, exist_ok=True)
    return upload_dir

@api_view(['POST'])
def upload_stcm_file(request, stock_id):
    """Upload or replace .stcm file for a robot_id"""
    serializer = STCMFileSerializer(data=request.data)
    
    if serializer.is_valid():
        file = serializer.validated_data['file']
        
        if not file.name.endswith('.stcm'):
            return Response({"error": "Only .stcm files are allowed"}, status=status.HTTP_400_BAD_REQUEST)

        # Construct path for this robot
        robot_dir = os.path.join(settings.MEDIA_ROOT, 'stm_files', stock_id)

        # If folder exists, delete existing .stcm files (replace case)
        if os.path.exists(robot_dir):
            for existing_file in os.listdir(robot_dir):
                if existing_file.endswith('.stcm'):
                    os.remove(os.path.join(robot_dir, existing_file))
        else:
            # If folder does not exist, create it (new file for new robot_id)
            os.makedirs(robot_dir, exist_ok=True)

        # Save the new file
        file_path = os.path.join(robot_dir, file.name)
        with open(file_path, 'wb+') as destination:
            for chunk in file.chunks():
                destination.write(chunk)

        return Response({
            "message": "File uploaded successfully",
            "robot_id": stock_id,
            "file_name": file.name
        }, status=status.HTTP_201_CREATED)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def get_latest_stcm_file(request, stock_id):
    """Get the latest uploaded .stcm file for a robot_id"""
    try:
        upload_dir = get_robot_upload_dir(stock_id)
        files = [f for f in os.listdir(upload_dir) if f.endswith('.stcm')]

        if not files:
            return Response({"message": "No .stcm files found"}, status=status.HTTP_404_NOT_FOUND)

        latest_file = files[0]
        file_url = request.build_absolute_uri(f"/stm_files/{stock_id}/{latest_file}")

        return Response({
            "latest_file": latest_file,
            "robot_id": stock_id,
            "file_url": file_url
        })

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['DELETE'])
def delete_stcm_file(request, stock_id):
    """Delete uploaded .stcm file for a robot_id"""
    try:
        upload_dir = get_robot_upload_dir(stock_id) 
        files = [f for f in os.listdir(upload_dir) if f.endswith('.stcm')]

        if not files:
            return Response({"message": "No .stcm files to delete"}, status=status.HTTP_404_NOT_FOUND)

        file_to_delete = os.path.join(upload_dir, files[0])
        os.remove(file_to_delete)
        local_store["status"] = True

        return Response({"message": "File deleted", "robot_id": stock_id}, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
def robot_create_or_update_view(request):
    try:
        if not request.data:
            return Response({"status": "error", "message": "No data provided."}, status=status.HTTP_400_BAD_REQUEST)

        # Get stock_id from the root key (e.g., "SB3")
        stock_id, robot_data = next(iter(request.data.items()))
        robot_data["stock_id"] = stock_id  # Add stock_id to the data

        # Try to find robot by stock_id
        robot = Robot.objects.filter(stock_id=stock_id).first()
        if robot:
            serializer = RobotSerializer(robot, data=robot_data)
        else:
            serializer = RobotSerializer(data=robot_data)

        if serializer.is_valid():
            serializer.save()
            return Response({
                "status": "ok",
                "message": "Robot saved successfully",
                "data": serializer.data
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                "status": "error",
                "message": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        return Response({
            "status": "error",
            "message": str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def robot_list_view(request):
    robot = Robot.objects.first()
    if robot:
        serializer = RobotSerializer(robot)
        return Response({
            "status": "ok",
            "message":"data retrieved successfully",
            "data": serializer.data
        }, status=status.HTTP_200_OK)
    else:
        return Response({
            "status": "error",
            "message": "No robot found"
        }, status=status.HTTP_404_NOT_FOUND)
    


@api_view(['GET'])
def get_navigation_by_id(request, nav_id):
    """
    Retrieve a specific navigation item's ID and name when clicked,
    and store it as last clicked in DB.
    """
    try:
        navigation = Navigation.objects.get(id=nav_id)
    except Navigation.DoesNotExist:
        return Response({"error": "Navigation not found."}, status=status.HTTP_404_NOT_FOUND)

    # Use update_or_create to avoid NULL errors
    LastClickedNavigation.objects.update_or_create(
        id=1,  # Force single-row overwrite
        defaults={
            "navigation_id": navigation.id,
            "navigation_name": navigation.name,
        }
    )

    return Response({
        "status": "ok",
        "message": "Navigation retrieved and saved successfully",
        "data": {
            "id": navigation.id,
            "name": navigation.name
        }
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
def get_last_clicked_navigation(request):
    """
    Get the last clicked navigation from DB if not expired (30 seconds limit).
    """
    try:
        last_clicked = LastClickedNavigation.objects.get(id=1)
    except LastClickedNavigation.DoesNotExist:
        return Response({"error": "No navigation has been clicked yet."}, status=status.HTTP_404_NOT_FOUND)

    now = timezone.now()
    if now - last_clicked.updated_at > timedelta(seconds=30):
        return Response({"error": "Last clicked navigation has expired."}, status=status.HTTP_404_NOT_FOUND)

    return Response({
        "status": "ok",
        "message": "Last clicked navigation retrieved successfully",
        "data": {
            "id": last_clicked.navigation_id,
            "name": last_clicked.navigation_name,
            "updated_at": last_clicked.updated_at
        }
    }, status=status.HTTP_200_OK)


local_store = {"status": False}  # Default status is False

@api_view(['POST'])
def delete_status(request):
    """Update the status (only one status is stored at a time)."""
    new_status = request.data.get('status', False)  # Expecting {"status": true/false}
    
    local_store["status"] = new_status  # Overwrite the stored status

    return Response({"message": "Status updated", "status": local_store["status"]}, status=status.HTTP_200_OK)


@api_view(['GET'])
def get_delete_status(request):
    """Retrieve the current status."""
    return Response({"status": local_store["status"]}, status=status.HTTP_200_OK)


@api_view(['POST'])
def create_full_tour(request):
    import json

    navigations = request.data.get('navigations', [])
    full_tour_name = request.data.get('full_tour_name')  # <-- Fetch full_tour_name
    tour_date = request.data.get('tour_date')
    tour_time = request.data.get('tour_time')

    if isinstance(navigations, str):
        try:
            navigations = json.loads(navigations)
        except json.JSONDecodeError:
            return Response({"error": "Invalid JSON format for navigations."}, status=status.HTTP_400_BAD_REQUEST)

    if not isinstance(navigations, list):
        return Response({"error": "Navigations must be a list of IDs."}, status=status.HTTP_400_BAD_REQUEST)

    if not tour_date or not tour_time:
        return Response({"error": "tour_date and tour_time are required."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        tour_date = datetime.strptime(tour_date, "%Y-%m-%d").date()
        tour_time = datetime.strptime(tour_time, "%H:%M:%S").time()
    except ValueError:
        return Response({"error": "Invalid date or time format."}, status=status.HTTP_400_BAD_REQUEST)

    # ✅ Check for duplicate date + time
    if FullTour.objects.filter(tour_date=tour_date, tour_time=tour_time).exists():
        return Response({
            "status": "failed",
            "message": "A tour with the same date and time already exists."
        }, status=status.HTTP_400_BAD_REQUEST)

    # ✅ Now also save full_tour_name
    full_tour = FullTour.objects.create(
        full_tour_name=full_tour_name,
        navigations=navigations,
        tour_date=tour_date,
        tour_time=tour_time
    )

    serializer = FullTourSerializer(full_tour)
    return Response({
        "status": "ok",
        "message": "Full tour created successfully",
        "data": serializer.data
    }, status=status.HTTP_201_CREATED)

# @api_view(['GET'])
# def get_current_full_tour(request):
#     now = datetime.now()
#     adjusted_now = now + timedelta(hours=5)  # Subtract 5 hours from current time
   
#     today = adjusted_now.date()
   

#     # Get all tours scheduled for the adjusted date
#     today_tours = FullTour.objects.filter(tour_date=today)

#     for full_tour in today_tours:
#         tour_datetime = datetime.combine(full_tour.tour_date, full_tour.tour_time)
#         window_end = tour_datetime + timedelta(minutes=1)

#         if tour_datetime <= adjusted_now <= window_end:
#             serializer = FullTourSerializer(full_tour)
#             return Response(serializer.data, status=status.HTTP_200_OK)

#     return Response({"message": "No current tour in the time window."}, status=status.HTTP_400_BAD_REQUEST)


import traceback
@api_view(['GET'])
def get_current_full_tour(request):
    try:
        now = datetime.now()
        # adjusted_now = now + timedelta(hours=5)  # Adjust time

        today = now

        # Get all tours scheduled for the adjusted date
        today_tours = FullTour.objects.filter(tour_date=today)

        for full_tour in today_tours:
            tour_datetime = datetime.combine(full_tour.tour_date, full_tour.tour_time)
            window_end = tour_datetime + timedelta(minutes=1)

            if tour_datetime <=  window_end:
                serializer = FullTourSerializer(full_tour)
                return Response(serializer.data, status=status.HTTP_200_OK)
        error_message = traceback.format_exc()
        return Response({"message": f"No current tour in the time window.{error_message}"}, status=status.HTTP_404_NOT_FOUND)

    except DatabaseError as db_err:
        return Response({"error": "Database error", "details": str(db_err)},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    except Exception as e:
        return Response({"error": "Unexpected error", "details": str(e)},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR)





@api_view(['GET'])
def full_tour_list(request):
    full_tours = FullTour.objects.all().order_by('-tour_date', '-tour_time')  # Optional ordering (latest first)

    serializer = FullTourSerializer(full_tours, many=True)
    return Response({"status": "ok", "data": serializer.data}, status=status.HTTP_200_OK)


@api_view(['PUT', 'PATCH'])
def update_full_tour(request, pk):
    import json
    try:
        full_tour = FullTour.objects.get(pk=pk)
    except FullTour.DoesNotExist:
        return Response({"error": "Full tour not found."}, status=status.HTTP_404_NOT_FOUND)

    navigations = request.data.get('navigations', full_tour.navigations)
    if isinstance(navigations, str):
        try:
            navigations = json.loads(navigations)
        except json.JSONDecodeError:
            return Response({"error": "Invalid JSON format for navigations."}, status=status.HTTP_400_BAD_REQUEST)

    tour_date = request.data.get('tour_date', full_tour.tour_date)
    tour_time = request.data.get('tour_time', full_tour.tour_time)

    try:
        if isinstance(tour_date, str):
            tour_date = datetime.strptime(tour_date, "%Y-%m-%d").date()
        if isinstance(tour_time, str):
            tour_time = datetime.strptime(tour_time, "%H:%M:%S").time()
    except ValueError:
        return Response({"error": "Invalid date or time format."}, status=status.HTTP_400_BAD_REQUEST)

    # ✅ Check for duplicates excluding the current tour
    if FullTour.objects.exclude(pk=pk).filter(tour_date=tour_date, tour_time=tour_time).exists():
        return Response({
            "status": "failed",
            "message": "Another tour with the same date and time already exists."
        }, status=status.HTTP_400_BAD_REQUEST)

    # ✅ Update tour
    full_tour.navigations = navigations
    full_tour.tour_date = tour_date
    full_tour.tour_time = tour_time
    full_tour.save()

    serializer = FullTourSerializer(full_tour)
    return Response({
        "status": "ok",
        "message": "Full tour updated successfully",
        "data": serializer.data
    }, status=status.HTTP_200_OK)

@api_view(['DELETE'])
def delete_full_tour(request, pk):
    try:
        full_tour = FullTour.objects.get(pk=pk)
    except FullTour.DoesNotExist:
        return Response({"error": "Full tour not found."}, status=status.HTTP_404_NOT_FOUND)

    full_tour.delete()
    return Response({
        "status": "ok",
        "message": "Full tour deleted successfully"
    }, status=status.HTTP_204_NO_CONTENT)




@api_view(['POST'])
def turn_on(request):
    poweron = get_poweron_object()
    if not poweron.status:  # Only turn on if it's currently off
        poweron.status = True
        poweron.save()
    return Response({"message": "Robot turned ON", "status": poweron.status})

@api_view(['POST'])
def turn_off(request):
    poweron = get_poweron_object()
    if poweron.status:  # Only turn off if it's currently on
        poweron.status = False
        poweron.save()
    return Response({"message": "Robot turned OFF", "status": poweron.status})

@api_view(['GET'])
def check_status(request):
    poweron = get_poweron_object()
    return Response({"status": "ON" if poweron.status else "OFF"})



@api_view(['POST'])
def update_reboot_status(request):
    new_status = request.data.get("status")

    if not isinstance(new_status, bool):
        return Response({"error": "Invalid status value. Must be true or false."}, status=status.HTTP_400_BAD_REQUEST)

    reboot, _ = RebootStatus.objects.get_or_create(id=1)
    reboot.status = new_status
    reboot.save()

    return Response({"message": "Reboot status updated", "status": reboot.status}, status=status.HTTP_200_OK)

@api_view(['GET'])
def get_reboot_status(request):
    reboot, _ = RebootStatus.objects.get_or_create(id=1)
    return Response({"status": reboot.status}, status=status.HTTP_200_OK)


@api_view(['POST'])
def save_ip_address(request, stock_id):
    ip = request.data.get("ip_address")

    if not ip:
        return Response({"error": "IP address is required."}, status=status.HTTP_400_BAD_REQUEST)

    # Optional: Delete existing entries for the same stock_id
    IPAddress.objects.filter(stock_id=stock_id).delete()

    ip_obj = IPAddress.objects.create(ip_address=ip, stock_id=stock_id)
    serializer = IPAddressSerializer(ip_obj)

    return Response({"message": "IP address saved.", "data": serializer.data}, status=status.HTTP_201_CREATED)


@api_view(['GET'])
def get_ip_address(request, stock_id):
    try:
        ip_obj = IPAddress.objects.filter(stock_id=stock_id).latest('created_at')
        serializer = IPAddressSerializer(ip_obj)
        return Response({"data": serializer.data}, status=status.HTTP_200_OK)
    except IPAddress.DoesNotExist:
        return Response({"message": "No IP address found for this stock ID."}, status=status.HTTP_404_NOT_FOUND)
    


@api_view(['POST'])
def update_or_create_sound(request):
    sound, created = Sound.objects.get_or_create(id=1)  # Keep one record only

    serializer = SoundSerializer(instance=sound, data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response({
            "status": "ok",
            "message": "Sound value updated" if not created else "Sound created",
            "data": serializer.data
        }, status=status.HTTP_200_OK)

    return Response({
        "status": "error",
        "message": serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def get_current_sound_value(request):
    try:
        sound = Sound.objects.first()  # Get the only sound object
        if sound:
            serializer = SoundSerializer(sound)
            return Response({
                "status": "ok",
                "data": serializer.data
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                "status": "error",
                "message": "No sound value found."
            }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            "status": "error",
            "message": str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    






@api_view(['POST'])
def update_or_create_speed(request):
    sound, created = Speed.objects.get_or_create(id=1)  # Keep one record only

    serializer = SpeedSerializer(instance=sound, data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response({
            "status": "ok",
            "message": "Speed value updated" if not created else "Speed created",
            "data": serializer.data
        }, status=status.HTTP_200_OK)

    return Response({
        "status": "error",
        "message": serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def get_current_speed_value(request):
    try:
        sound = Speed.objects.first()  # Get the only sound object
        if sound:
            serializer = SpeedSerializer(sound)
            return Response({
                "status": "ok",
                "data": serializer.data
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                "status": "error",
                "message": "No speed value found."
            }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            "status": "error",
            "message": str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)






    


@api_view(['POST'])
def create_or_update_charge(request):
    # Always fetch the one existing object or create it
    charge_obj, created = Charge.objects.get_or_create(id=1)

    serializer = ChargeSerializer(charge_obj, data=request.data, partial=True)
    
    if serializer.is_valid():
        serializer.save()
        return Response({
            "status": "ok",
            "message": "Charge updated successfully" if not created else "Charge created successfully",
            "data": serializer.data
        }, status=status.HTTP_200_OK)
    
    return Response({
        "status": "error",
        "message": serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def create_or_update_charge(request):
    charge_obj, created = Charge.objects.get_or_create(id=1)

    serializer = ChargeSerializer(charge_obj, data=request.data, partial=True)
    
    if serializer.is_valid():
        serializer.save()
        return Response({
            "status": "ok",
            "message": "Charge updated successfully" if not created else "Charge created successfully",
            "data": serializer.data
        }, status=status.HTTP_200_OK)
    
    return Response({
        "status": "error",
        "message": serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def get_current_charge(request):
    try:
        charge = Charge.objects.last()  # Get the latest one
        if not charge:
            return Response({"message": "No charge data found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = ChargeSerializer(charge)
        return Response({
            "status": "ok",
            "data": serializer.data
        }, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({
            "status": "error",
            "message": str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    

boat_volumes = {}

def set_volume(request, stock_id, volume):
    """
    Set the volume for a specific robot.
    Only the last updated volume is stored.
    """
    try:
        volume = int(volume)  # Ensure volume is an integer

        if 0 <= volume <= 150:
            boat_volumes[stock_id] = volume  # Store only the latest volume
            return JsonResponse({"message": "Volume updated", "stock_id": stock_id, "current_volume": volume})
        else:
            return JsonResponse({"error": "Volume must be between 0 and 150"}, status=400)

    except ValueError:
        return JsonResponse({"error": "Invalid volume input. Volume must be an integer."}, status=400)

def get_volume(request, stock_id):
    """
    Get the last updated volume of the robot.
    If no volume was set, return a default of 50.
    """
    volume = boat_volumes.get(stock_id, 105)  # Return default volume if not set
    return JsonResponse({"robo_id": stock_id, "current_volume": volume})


def superadmin_login(request):
    if request.user.is_authenticated:
       
        if request.user.is_superuser:
            return redirect('upload_zip')  
        else:
            return HttpResponseForbidden("You are not authorized to view this page.")
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None and user.is_superuser:
            login(request, user)
            return redirect('upload_zip')  
        else:
            messages.error(request, 'Invalid credentials or you are not a superadmin.')
    
    return render(request, 'superadmin_login.html')

def superadmin_logout(request):
    logout(request)  # Logs out the user
    return redirect('superadmin_login') 


@login_required
def upload_zip_file(request):
    if request.method == 'POST':
        robot_id = request.POST.get('robot')  
        zip_file = request.FILES.get('zip_file')

        if not robot_id or not zip_file:
            return render(request, 'upload.html', {
                'error': 'Robot and ZIP file are required!',
                'robots': Robot.objects.all()
            })

        try:
            robot = Robot.objects.get(id=robot_id)
        except Robot.DoesNotExist:
            return render(request, 'upload.html', {
                'error': 'Invalid robot selection.',
                'robots': Robot.objects.all()
            })

        folder_name = robot.stock_id or f"robot_{robot.id}"

        if not zip_file.name.endswith('.zip'):
            return render(request, 'upload.html', {
                'error': 'Only ZIP files are allowed.',
                'robots': Robot.objects.all()
            })

        upload_dir = os.path.join(settings.MEDIA_ROOT, 'robot_files', folder_name)
        os.makedirs(upload_dir, exist_ok=True)

        # Remove existing zip files
        for file in os.listdir(upload_dir):
            file_path = os.path.join(upload_dir, file)
            if os.path.isfile(file_path) and file.endswith('.zip'):
                os.remove(file_path)

        fs = FileSystemStorage(location=upload_dir)
        zip_filename = fs.save(zip_file.name, zip_file)

        robot_file = RobotFile(
            robot=robot,
            zip_file=f'robot_files/{folder_name}/{zip_filename}'
        )
        robot_file.save()

        return render(request, 'upload.html', {
            'success': 'ZIP file uploaded successfully!',
            'robots': Robot.objects.all()
        })

    return render(request, 'upload.html', {'robots': Robot.objects.all()})

#get zip file path
@api_view(['GET'])
def list_zip_files(request, stock_id):
    try:
        robot = Robot.objects.get(stock_id=stock_id)
    except Robot.DoesNotExist:
        return Response({"error": "Robot with given stock_id not found"}, status=404)

    robot_files = RobotFile.objects.filter(robot=robot).order_by('-uploaded_at')
    if not robot_files.exists():
        return Response({"error": "No files found for this robot"}, status=404)

    latest_file = robot_files.first()
    zip_file_url = request.build_absolute_uri(latest_file.zip_file.url)
    file_data = {
        "zip_file_url": zip_file_url,
        "robot_id": latest_file.robot.id,
        "stock_id": latest_file.robot.stock_id,
        "uploaded_at": latest_file.uploaded_at
    }
    return Response(file_data)



@api_view(['GET'])
def get_charging_status(request):
    charging = Charging.objects.first()
    if charging:
        serializer = ChargingSerializer(charging)
        return Response(serializer.data)
    return Response({'status': None}, status=drf_status.HTTP_200_OK)

@api_view(['POST'])
def set_charging_status(request):
    status_value = request.data.get('status')

    if not isinstance(status_value, bool):
        return Response({'error': 'status must be true or false'}, status=drf_status.HTTP_400_BAD_REQUEST)

    Charging.objects.all().delete()  # ensure only one object
    serializer = ChargingSerializer(data={'status': status_value})
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=drf_status.HTTP_201_CREATED)
    return Response(serializer.errors, status=drf_status.HTTP_400_BAD_REQUEST)



@api_view(['GET'])
def get_navigation_cancel_status(request):
    obj = NavigationCancel.objects.first()
    if obj:
        serializer = NavigationCancelSerializer(obj)
        return Response(serializer.data)
    return Response({'status': False}, status=drf_status.HTTP_200_OK)

@api_view(['POST'])
def set_navigation_cancel_status(request):
    status_value = request.data.get('status')

    if not isinstance(status_value, bool):
        return Response({'error': 'Status must be true or false'}, status=drf_status.HTTP_400_BAD_REQUEST)

    # Delete all existing objects to ensure only one
    NavigationCancel.objects.all().delete()

    # Create new one
    serializer = NavigationCancelSerializer(data={'status': status_value})
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=drf_status.HTTP_201_CREATED)
    return Response(serializer.errors, status=drf_status.HTTP_400_BAD_REQUEST)








# P dev
@api_view(['POST'])
def change_refresh_status(request):
    try:
        # Extract the 'status' value from the request data
        status_value = request.data.get('status')

        if status_value is None:
            return Response({
                "status": "error",
                "message": "Missing 'status' value in request."
            }, status=status.HTTP_400_BAD_REQUEST)

        # If only one RefreshButton instance is expected
        obj, created = RefreshButton.objects.get_or_create(id=1)  # or use a different condition
        obj.status = status_value
        obj.save()

        local_store["status"] = status_value

        # Serialize and return the updated object
        serializer = RefreshButtonSerializer(obj)
        return Response({
            "status": "ok",
            "updated_data": serializer.data
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({
            "status": "error",
            "message": str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
@api_view(['GET'])
def fetch_refresh_status(request):
    try:
        obj = RefreshButton.objects.filter(id=1).first()

        if obj is None:
            return Response({
                "status": "error",
                "message": "RefreshButton not found."
            }, status=status.HTTP_404_NOT_FOUND)

        serializer = RefreshButtonSerializer(obj)
        return Response({
            "status": "ok",
            "data": serializer.data
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({
            "status": "error",
            "message": str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
@api_view(['POST'])
def save_api_credentials(request):
    try:
        serializer = APICredentialSerializer(data=request.data)

        if serializer.is_valid():
            credential = serializer.save()
            return Response({
                "status": "ok",
                "data": APICredentialSerializer(credential).data
            }, status=status.HTTP_200_OK)

        return Response({
            "status": "error",
            "message": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        return Response({
            "status": "error",
            "message": str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def fetch_api_credentials(request):
    try:
        credentials = APICredential.objects.all().order_by('-created_at')
        serializer = APICredentialSerializer(credentials, many=True)
        return Response({
            "status": "ok",
            "data": serializer.data
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({
            "status": "error",
            "message": str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
@api_view(['POST']) 
def save_schedulers(request):
    try:
        # ✅ Check if "status" is True in request data
        if not request.data.get("status", False):
            return Response({
                "status": "error",
                "message": "Invalid or false status in request"
            }, status=status.HTTP_400_BAD_REQUEST)

        data_list = request.data.get('dataSet', {}).get('data', [])

        # Delete all existing records first
        Scheduler.objects.all().delete()

        saved = []
        for item in data_list:
            obj = Scheduler.objects.create(
                scheduler_id=item['schedulerID'],
                scheduler_name=item['schedulerName'],
                scheduler_date=item['schedulerDate'],
                scheduler_time=item['schedulerTime'],
                all_day=item['allDay'].strip(),
                modified=item['modified'].strip(),
            )
            saved.append(obj)

        serializer = SchedulerSerializer(saved, many=True)
        return Response({
            "status": "ok",
            "data": serializer.data
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        return Response({
            "status": "error",
            "message": str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    # try:
    #     data_list = request.data.get('dataSet', {}).get('data', [])

    #     # Delete all existing records first
    #     Scheduler.objects.all().delete()

    #     saved = []
    #     for item in data_list:
    #         obj = Scheduler.objects.create(
    #             scheduler_id=item['schedulerID'],
    #             scheduler_name=item['schedulerName'],
    #             scheduler_date=item['schedulerDate'],
    #             scheduler_time=item['schedulerTime'],
    #             all_day=item['allDay'].strip(),
    #             modified=item['modified'].strip(),
    #         )
    #         saved.append(obj)

    #     serializer = SchedulerSerializer(saved, many=True)
    #     return Response({
    #         "status": "ok",
    #         "data": serializer.data
    #     }, status=status.HTTP_201_CREATED)

    # except Exception as e:
    #     return Response({
    #         "status": "error",
    #         "message": str(e)
    #     }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def list_schedulers(request):
    try:
        schedulers = Scheduler.objects.all().order_by('scheduler_date', 'scheduler_time')
        serializer = SchedulerSerializer(schedulers, many=True)
        return Response({
            "status": "ok",
            "data": serializer.data
        }, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({
            "status": "error",
            "message": str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
def check_current_scheduler(request):
    try:
        # Get current local datetime
        local_now = timezone.localtime(timezone.now())
        local_today = local_now.date()
        current_time = local_now.time().replace(second=0, microsecond=0)

        # Get all tours scheduled for today in local time
        today_tours = Scheduler.objects.filter(
            scheduler_date__year=local_today.year,
            scheduler_date__month=local_today.month,
            scheduler_date__day=local_today.day,
            scheduler_time__gte=current_time
        )

        now_hour = current_time.hour
        now_minute = current_time.minute

        # Check if any tours are scheduled for the current time (same hour and minute)
        matching_now_tours = today_tours.filter(
            scheduler_time__hour=now_hour,
            scheduler_time__minute=now_minute,
            notified = False
        )

        credentials = APICredential.objects.first()
        if not credentials:
            return Response({
                "status": "error",
                'status_bool': False,
                "message": "No creadentials available.",
            }, status=status.HTTP_404_NOT_FOUND)
        access_token = credentials.access_token

        if matching_now_tours.exists():
            customer_Data = CustomerConnectionData.objects.first()
            location_details_url = f"{customer_Data.customer_url}api/StockBot/GetScheduleStockBotLocations" if customer_Data.customer_url else "https://stockbotapi.technowavegroup.com/api/StockBot/GetScheduleStockBotLocations"
            scheduler_id = matching_now_tours.first().scheduler_id
            cust_id = customer_Data.customer_id if customer_Data.customer_id else "00"
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            params = {
                "CustID": cust_id,
                "SchedulerID": scheduler_id,
                "DeviceID": settings.ROBOT_GLOBAL_ID,
            }
            response = requests.get(location_details_url, headers=headers, params=params)
            response.raise_for_status()
            json_data = response.json()

            if json_data.get("status") is True:
                matching_now_tours.update(notified=True)
                response_data = {
                    "message": "Tours scheduled for the current time found.",
                    "tour_data": json_data,
                    "SchedulerID": scheduler_id
                }
                print("Sending response:", response_data)
                return Response(response_data, status=status.HTTP_200_OK)
            else:
                return Response({
                    "message": "No locations found.",
                    "now": str(local_now),
                    "SchedulerID": scheduler_id
                }, status=status.HTTP_404_NOT_FOUND)
        else :
            return Response({
                "message": "No tours scheduled for the rest of today.",
                "now": str(local_now),
            }, status=status.HTTP_404_NOT_FOUND)

    except DatabaseError as db_err:
        error = traceback.format_exc()
        return Response({
            "error": "Database error",
            "details": str(db_err),
            "trace": error
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    except Exception as e:
        return Response({
            "error": "Unexpected error",
            "details": str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
def create_or_update_customer_connection(request):
    data = request.data

    # Either get the only object or None
    instance = CustomerConnectionData.objects.first()

    if instance:
        serializer = CustomerConnectionDataSerializer(instance, data=data)
    else:
        serializer = CustomerConnectionDataSerializer(data=data)

    if serializer.is_valid():
        serializer.save()
        return Response({
            "status": "success",
            "message": "Customer connection data saved.",
            "data": serializer.data
        }, status=status.HTTP_200_OK)

    return Response({
        "status": "error",
        "message": "Invalid data",
        "errors": serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
def get_customer_connection_data(request):
    instance = CustomerConnectionData.objects.first()

    if instance:
        serializer = CustomerConnectionDataSerializer(instance)
        return Response({
            "status": "success",
            "message": "Customer connection data fetched.",
            "data": serializer.data
        }, status=status.HTTP_200_OK)
    else:
        return Response({
            "status": "error",
            "message": "No customer connection data found."
        }, status=status.HTTP_404_NOT_FOUND)
    
@api_view(['POST'])
def save_notification(request):
    try:
        data = request.data.copy()
        notification_field = data.get("notification")
        if isinstance(notification_field, str):
            data["notification"] = f"{notification_field}"
        elif isinstance(notification_field, dict):
            scheduler_data = notification_field.get("dataSet", {}).get("data", [])
            if scheduler_data:
                location_dict = {
                    item.get("location"): item.get("location")
                    for item in scheduler_data if item.get("location")
                }
                location_string = ",".join([f"{v}" for k, v in location_dict.items()])
                data["notification"] = location_string
        else:
            return Response({
                "status": "error",
                "message": "Invalid notification format."
            }, status=400)
        serializer = GeneralNotificationSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response({
                "status": "success",
                "message": "Notification created successfully.",
                "data": serializer.data
            }, status=201)
        else:
            return Response({
                "status": "error",
                "message": "Invalid data.",
                "errors": serializer.errors
            }, status=400)
    except Exception as e:
        error = traceback.format_exc()
        return Response({
            "status": "error",
            "message": str(e),
            "error_trace": error
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
def mark_notification_as_seen(request, pk):
    try:
        notification = GeneralNotification.objects.get(pk=pk)
    except GeneralNotification.DoesNotExist:
        return Response({
            "status": "error",
            "message": f"Notification with id {pk} does not exist."
        }, status=status.HTTP_404_NOT_FOUND)

    notification.seen = True
    notification.save()

    serializer = GeneralNotificationSerializer(notification)

    return Response({
        "status": "success",
        "message": "Notification marked as seen.",
        "data": serializer.data
    }, status=status.HTTP_200_OK)

@api_view(['GET'])
def get_unseen_notifications(request):
    unseen_notifications = GeneralNotification.objects.filter(seen=False).order_by('-created_at')
    serializer = GeneralNotificationSerializer(unseen_notifications, many=True)

    return Response({
        "status": "success",
        "message": "Unseen notifications fetched successfully.",
        "data": serializer.data
    }, status=status.HTTP_200_OK)

@api_view(['GET'])
def get_all_notifications(request):
    unseen_notifications = GeneralNotification.objects.order_by('-created_at')
    serializer = GeneralNotificationSerializer(unseen_notifications, many=True)

    return Response({
        "status": "success",
        "message": "Unseen notifications fetched successfully.",
        "data": serializer.data
    }, status=status.HTTP_200_OK)