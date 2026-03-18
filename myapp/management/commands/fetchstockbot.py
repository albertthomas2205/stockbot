from django.core.management.base import BaseCommand
import requests
from myapp.models import Scheduler , APICredential , CustomerConnectionData
from myapp.serializers import SchedulerSerializer , APICredentialSerializer
from django.utils.dateparse import parse_datetime, parse_time
from django.conf import settings

class Command(BaseCommand):
    help = "Fetches stock bot schedule details from external API and saves to DB"

    def handle(self, *args, **kwargs):
        customer_Data = CustomerConnectionData.objects.first()
        # API endpoints
        schedule_url = f"{customer_Data.customer_url}api/StockBot/GetStockBotSchedules" if customer_Data.customer_url else "https://stockbotapi.technowavegroup.com/api/StockBot/GetStockBotSchedules"
        cust_id = customer_Data.customer_id if customer_Data.customer_id else "00"
        # scheduler_id_stat = 1
        try:
            credentials = APICredential.objects.first()
            if not credentials:
                self.stderr.write("Credentials not available.")
            access_token = credentials.access_token
            # Step 2: Get schedule data
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            params = {
                "CustID": cust_id,
                "DeviceID": settings.ROBOT_GLOBAL_ID,
                # "SchedulerID": scheduler_id_stat
            }
            response = requests.get(schedule_url, headers=headers, params=params)
            response.raise_for_status()
            json_data = response.json()

            if json_data.get("status") is True:
                schedules = json_data.get("dataSet", {}).get("data", [])
                self.stdout.write(f"Fetched {len(schedules)} schedules")

                for item in schedules:
                    scheduler_id = item.get("schedulerID")
                    scheduler_name = item.get("schedulerName")
                    scheduler_date = parse_datetime(item.get("schedulerDate"))
                    scheduler_time = parse_time(item.get("schedulerTime"))
                    all_day = item.get("allDay")
                    modified = item.get("modified")

                    obj, created = Scheduler.objects.update_or_create(
                        scheduler_id=scheduler_id,
                        defaults={
                            "scheduler_name": scheduler_name,
                            "scheduler_date": scheduler_date,
                            "scheduler_time": scheduler_time,
                            "all_day": all_day,
                            "modified": modified,
                            "notified": False,
                        }
                    )
                    action = "Created" if created else "Updated"
                    self.stdout.write(f"{action}: {obj}")

            else:
                self.stderr.write("Schedule API returned status=False")

        except Exception as e:
            self.stderr.write(f"Error: {str(access_token)}")
            self.stderr.write(f"Error exception printed: {str(e)}")

# tail -f /home/jetson/fetchstockbot.log
# * * * * * /usr/bin/python3 /home/jetson/WAre/stock/manage.py fetchstockbot >> /home/jetson/fetchstockbot.log 2>&1

# * * * * * /usr/bin/python3 /home/jetson/WAre/stock/manage.py fetchstockbot >> /home/jetson/fetchstockbot.log 2>&1
# * * * * * cd /home/jetson/WAre/stock && /usr/bin/python3 manage.py fetchstockbot >> /home/jetson/fetchstockbot.log 2>&1


