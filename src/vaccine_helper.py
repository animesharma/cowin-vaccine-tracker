"""Module containing helper functions for cowin-vaccine-tracker"""
import sys
import json
import hashlib
import smtplib
from email.mime.text import MIMEText
import requests

class VaccineHelper:
    """Class containing helper functions"""
    def __init__(self):
        """Constructor"""
        self.base_url = "https://cdn-api.co-vin.in/api"
        self.sent_email_checksums = set()

    @staticmethod
    def terminate(error):
        """Function to display an error message and exit the program"""
        print("Error: " + error)
        sys.exit(-1)

    def get_vaccine_centers(self, api_endpoint, parameters):
        """Function to fetch vaccine centers from CoWin Servers"""
        response = requests.get(url=self.base_url + api_endpoint, params=parameters, \
                                headers={"User-Agent": "PostmanRuntime/8"})
        if response.ok:
            return response.json().get("centers")
        self.terminate("Unable to reach CoWin servers, please try again later.")

    @staticmethod
    def filter_centers_by_attribute(vaccine_centers, attribute, operand, value):
        """Function to filter vaccine centers based on a given attribute"""
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
    def calculate_checksum(message_body):
        """Function to calulate the BLAKE2b checksum of a string"""
        return hashlib.blake2b(message_body.encode("utf-8"), digest_size=24).hexdigest()

    def create_formatted_message(self, centers):
        """Function to create a formatted message with details about available vaccine appointments"""
        message_body = "Available Vaccine Centers:\n\n"
        for center_index, center in enumerate(centers):
            message_body += "Center " + str(center_index + 1) + ": " + center.get("name") + " - " + \
                            center.get("address") + " - " + center.get("district_name") + " - " + \
                            center.get("state_name") + " - " + str(center.get("pincode")) + "\n\n"
            for session_index, session in enumerate(center.get("sessions")):
                message_body += "Session " + str(session_index + 1) + ":\n\n"
                message_body += "\tDate: " + session.get("date") + "\n"
                message_body += "\tAvailable First Dose Capacity: " + str(session.get("available_capacity_dose1")) + "\n"
                message_body += "\tAvailable Second Dose Capacity: " + str(session.get("available_capacity_dose2")) + "\n"
                message_body += "\tMinimum Age Limit: " + str(session.get("min_age_limit")) + "\n"
                message_body += "\tVaccine: " + session.get("vaccine") + "\n"
                message_body += "\tFee Type: " + center.get("fee_type") + "\n\n"
        message_body += "Book your slot now at: https://selfregistration.cowin.gov.in/\n\n"
        checksum = self.calculate_checksum(message_body)
        return message_body, checksum

    def send_email_notification(self, recipient, content):
        """Function to send a vaccine availability notification email"""
        try:
            with open("./config/email_credentials.json") as config_file:
                email_config = json.load(config_file)
        except FileNotFoundError:
            self.terminate("Could not access email configuration file")
        sender = email_config.get("sender_email")
        message = MIMEText(content)
        message["Subject"] = "Vaccine Availability Notification"
        message["From"] = sender
        message["To"] = recipient
        with smtplib.SMTP_SSL(email_config.get("smtp_url"), email_config.get("smtp_port")) as mail_server:
            mail_server.login(sender, email_config.get("password"))
            mail_server.sendmail(sender, recipient, message.as_string())
