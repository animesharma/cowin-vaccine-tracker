import requests
import argparse
import re
import sys
import json
import smtplib
from email.mime.text import MIMEText
from random import randint
from time import sleep, strftime
from concurrent.futures import ThreadPoolExecutor, as_completed

class CowinVaccineTracker:
    def __init__(self):
        self.base_url = "https://cdn-api.co-vin.in/api"
        self.parser = argparse.ArgumentParser()
        self.define_arguments(self.parser)

    def define_arguments(self, parser):
        parser.add_argument("--pin", 
                            dest="pin",
                            nargs="*",
                            required=True,
                            help="PIN Code (6 digits) to find vaccine centers")
        parser.add_argument("--age",
                            dest="min_age",
                            type=int,
                            choices=[18, 45],
                            help="Minimum Age Limit - 18 or 45")
        parser.add_argument("--vaccine",
                            dest="vaccine",
                            choices=["COVAXIN", "COVISHIELD"],
                            help="Preferred Vaccine: COVAXIN or COVISHIELD. Shows any available by default")
        parser.add_argument("--recipient", 
                            dest="recipient",
                            help="Email address to notify vaccine availability")
        parser.add_argument("--loop",
                            dest="loop",
                            action="store_true",
                            help="Specify option to run script on a loop")
    @staticmethod
    def terminate(error):
        print("Error: " + error)
        sys.exit(-1)

    def validate_input(self, args):
        for pin in args.pin:
            if not re.fullmatch(r"^\d\d\d\d\d\d$", pin):
                self.terminate("Invalid PIN Code")
        if args.recipient and not re.fullmatch(r"[^@]+@[^@]+\.[^@]+", args.recipient):
            self.terminate("Invalid recipient email address")

    def get_vaccine_centers_by_pin(self, pin, date):
        api_endpoint = "/v2/appointment/sessions/public/calendarByPin"
        parameters = {
            "pincode": pin,
            "date": date
        }
        response = requests.get(url=self.base_url + api_endpoint, params=parameters, headers={"User-Agent": "PostmanRuntime/8"})
        if response.ok:
            return response.json().get("centers")
        else:
            self.terminate("Unable to reach CoWin servers, please try again later.")

    @staticmethod
    def filter_centers_by_attribute(vaccine_centers, attribute, value):
        filtered_centers = []
        for center in vaccine_centers:
            filtered_sessions = []
            for session in center.get("sessions"):
                if session.get(attribute) == value and session.get("available_capacity") > 0:
                    filtered_sessions.append(session)
            if filtered_sessions:
                center["sessions"] = filtered_sessions
                filtered_centers.append(center)
        return filtered_centers

    @staticmethod
    def send_email_notification(recipient, content):
        email_config = json.loads("./config/email_config.json")
        sender = email_config.get("sender_email")
        message = MIMEText(content)
        message["Subject"] = "Vaccine Availability Notification"
        message["From"] = sender
        message["To"] = recipient
        with smtplib.SMTP_SSL(email_config.get("smtp_url"), email_config.get("smtp_port")) as mail_server:
            mail_server.login(sender, email_config.get("password"))
            mail_server.sendmail(sender, recipient, message.as_string())

    @staticmethod
    def create_formatted_message(centers):
        message_body = "Available Vaccine Centers:\n\n"
        for index, center in enumerate(centers):
            message_body += "Center " + str(index + 1) + ": " + center.get("name") + " - " + \
                            center.get("address") + " - " + center.get("district_name") + " - " + \
                            center.get("state_name") + " - " + str(center.get("pincode")) + "\n\n"

            for index, session in enumerate(center.get("sessions")):   
                message_body += "Session " + str(index + 1) + ":\n\n"         
                message_body += "\tDate: " + session.get("date") + "\n"
                message_body += "\tAvailable Capacity: " + str(session.get("available_capacity")) + "\n"
                message_body += "\tMinimum Age Limit: " + str(session.get("min_age_limit")) + "\n"
                message_body += "\tVaccine: " + session.get("vaccine") + "\n"
                message_body += "\tFee Type: " + center.get("fee_type") + "\n\n"
        message_body += "Book your slot now at: https://selfregistration.cowin.gov.in/\n\n"
        return message_body

if __name__ == "__main__":
    tracker = CowinVaccineTracker()
    args = tracker.parser.parse_args()
    tracker.validate_input(args)
    while(True):
        with ThreadPoolExecutor() as executor:
            future_centers = {executor.submit(tracker.get_vaccine_centers_by_pin, pin, strftime("%d-%m-%Y")): pin for pin in args.pin}
            for future in as_completed(future_centers):
                pin = future_centers[future]
                try:
                    vaccine_centers = tracker.filter_centers_by_attribute(future.result(), None, None)
                    if(args.min_age):
                        vaccine_centers = tracker.filter_centers_by_attribute(vaccine_centers, "min_age_limit", args.min_age)
                    if(args.vaccine):
                        vaccine_centers = tracker.filter_centers_by_attribute(vaccine_centers, "vaccine", args.vaccine.upper())
                    if vaccine_centers: 
                        message_body = tracker.create_formatted_message(vaccine_centers)
                        print(message_body)
                        if args.recipient:
                            tracker.send_email_notification(args.recipient, message_body)
                except Exception as exc:
                    print('%r generated an exception: %s' % (pin, exc))
        if not args.loop:
            break
        wait_time = randint(45, 90)
        sleep(wait_time)
       