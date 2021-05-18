import requests
import argparse
import re
import sys
from datetime import datetime
from random import randint
from time import sleep
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
        parser.add_argument("--date", 
                            dest="date",
                            required=True, 
                            help="Date (dd-mm-yyyy) at which appointment is sought")
        parser.add_argument("--age",
                            dest="min_age",
                            type=int,
                            choices=[18, 45],
                            help="Minimum Age Limit - 18 or 45")
        parser.add_argument("--vaccine",
                            dest="vaccine",
                            choices=["COVAXIN", "COVISHIELD"],
                            help="Preferred Vaccine: COVAXIN or COVISHIELD. Shows any available by default")
        parser.add_argument("--loop",
                            dest="loop",
                            action="store_true",
                            help="Specify option to run script on a loop")
    
    def terminate(error):
        print("Error: " + error)
        sys.exit(-1)

    def validate_input(self, args):
        if not args.pin or not args.date:
            self.terminate("Valid date and PIN Code not found")
        for pin in args.pin:
            if not re.match(r"^\d\d\d\d\d\d$", pin):
                self.terminate("Invalid PIN Code")
        try:
            datetime.strptime(args.date, "%d-%m-%Y")
        except ValueError:
            self.terminate("Invalid Date format - use dd-mm-yyyy")

    def get_vaccine_centers_by_pin(self, pin, date):
        api_endpoint = "/v2/appointment/sessions/public/calendarByPin"
        parameters = {
            "pincode": pin,
            "date": date
        }
        response = requests.get(url=self.base_url + api_endpoint, params=parameters, headers={"User-Agent": "PostmanRuntime/8.3.1"})
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
    def display_centers(centers):
        if not centers:
            print("No available slots, please try again later.")
            return
        for center in centers:
            print(center.get("pincode"))
            for session in center.get("sessions"):
                print(center.get("name"), " - ", center.get("address"), " - ", center.get("district_name"), " - ", center.get("state_name"))
                print("Date: ", session.get("date"))
                print("Available Capacity: ", session.get("available_capacity"))
                print("Minimum Age Limit: ", session.get("min_age_limit"))
                print("Vaccine: ", session.get("vaccine"), "\n") 

if __name__ == "__main__":
    tracker = CowinVaccineTracker()
    args = tracker.parser.parse_args()
    tracker.validate_input(args)
    while(True):
        with ThreadPoolExecutor() as executor:
            future_centers = {executor.submit(tracker.get_vaccine_centers_by_pin, pin, args.date): pin for pin in args.pin}
            for future in as_completed(future_centers):
                pin = future_centers[future]
                try:
                    vaccine_centers = future.result()
                    if(args.min_age):
                        vaccine_centers = tracker.filter_centers_by_attribute(vaccine_centers, "min_age_limit", args.min_age)
                    if(args.vaccine):
                        vaccine_centers = tracker.filter_centers_by_attribute(vaccine_centers, "vaccine", args.vaccine.upper())
                    tracker.display_centers(vaccine_centers)
                except Exception as exc:
                    print('%r generated an exception: %s' % (pin, exc))
        if not args.loop:
            break
        wait_time = randint(45, 90)
        sleep(wait_time)
       