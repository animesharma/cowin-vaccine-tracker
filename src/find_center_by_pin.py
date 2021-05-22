import argparse
import re

from random import randint
from time import sleep, strftime
from concurrent.futures import ThreadPoolExecutor, as_completed

from vaccine_helper import VaccineHelper

class FindCenterByPin(VaccineHelper):

    def __init__(self):
        super().__init__()
        self.api_endpoint = "/v2/appointment/sessions/public/calendarByPin"
        self.parser = argparse.ArgumentParser()
        self.define_arguments(self.parser)

    def define_arguments(self, parser):
        parser.add_argument("--pin", 
                            dest="pin",
                            type=int,
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
                            choices=["COVAXIN", "COVISHIELD", "SPUTNIK V"],
                            help="Preferred Vaccine: COVAXIN, COVISHIELD or SUPTNIK V. Shows any available by default")
        parser.add_argument("--dose",
                            dest="dose",
                            choices=["first", "second"],
                            help="Filter by first or second dose")
        parser.add_argument("--recipient", 
                            dest="recipient",
                            help="Email address to notify vaccine availability")
        parser.add_argument("--loop",
                            dest="loop",
                            action="store_true",
                            help="Specify option to run script on a loop")

    def validate_input(self, args):
        for pin in args.pin:
            if not re.fullmatch(r"^\d\d\d\d\d\d$", str(pin)):
                self.terminate("Invalid Pincode")
        if args.recipient and not re.fullmatch(r"[^@]+@[^@]+\.[^@]+", args.recipient):
            self.terminate("Invalid recipient email address")

    def get_vaccine_centers_by_pin(self, pin, date):
        parameters = {
            "pincode": pin,
            "date": date
        }
        return self.get_vaccine_centers(self.api_endpoint, parameters)

if __name__ == "__main__":
    tracker = FindCenterByPin()
    args = tracker.parser.parse_args()
    tracker.validate_input(args)
    while(True):
        with ThreadPoolExecutor() as executor:
            future_centers = {executor.submit(tracker.get_vaccine_centers_by_pin, pin, strftime("%d-%m-%Y")):\
                             pin for pin in args.pin}
            for future in as_completed(future_centers):
                pin = future_centers[future]
                try:
                    centers = tracker.filter_centers_by_attribute(future.result(), "available_capacity", "greater", 0)
                    if(args.min_age):
                        centers = tracker.filter_centers_by_attribute(centers, "min_age_limit", "equals", args.min_age)
                    if(args.vaccine):
                        centers = tracker.filter_centers_by_attribute(centers, "vaccine", "equals", args.vaccine.upper())
                    if(args.dose and args.dose.lower() == "first"):
                        centers = tracker.filter_centers_by_attribute(centers, "available_capacity_first_dose", "greater", 0)
                    if(args.dose and args.dose.lower() == "second"):
                        centers = tracker.filter_centers_by_attribute(centers, "available_capacity_second_dose", "greater", 0)
                    if centers: 
                        message_body = tracker.create_formatted_message(centers)
                        print(message_body)
                        if args.recipient:
                            tracker.send_email_notification(args.recipient, message_body)
                except Exception as exc:
                    print('%r generated an exception: %s' % (pin, exc))
        if not args.loop:
            break
        wait_time = randint(45, 90)
        sleep(wait_time)
