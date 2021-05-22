import sys
import requests
import json
import smtplib
from email.mime.text import MIMEText

class VaccineHelper:

    def __init__(self):
        self.base_url = "https://cdn-api.co-vin.in/api"

    @staticmethod
    def terminate(error):
        print("Error: " + error)
        sys.exit(-1)

    def get_vaccine_centers(self, api_endpoint, parameters):
        response = requests.get(url=self.base_url + api_endpoint, params=parameters, headers={"User-Agent": "PostmanRuntime/8"})
        if response.ok:
            return response.json().get("centers")
        else:
            self.terminate("Unable to reach CoWin servers, please try again later.")

    @staticmethod
    def filter_centers_by_attribute(vaccine_centers, attribute, operand, value):
        filtered_centers = []
        for center in vaccine_centers:
            filtered_sessions = []
            for session in center.get("sessions"):
                if operand == "equals":
                    if session.get(attribute) == value:
                        filtered_sessions.append(session)
                elif operand == "greater":
                    if session.get(attribute) > value:
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
