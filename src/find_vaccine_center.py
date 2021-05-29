"""Module containing functions to find vaccine availability schedule in a given area"""
import argparse
import re
from random import randint
from time import sleep, strftime, localtime
from concurrent.futures import ThreadPoolExecutor, as_completed
from vaccine_helper import VaccineHelper

class FindVaccineCenter(VaccineHelper):
    """Class containing functions to find vaccine centers"""
    def __init__(self):
        """Constructor"""
        super().__init__()
        self.parser = argparse.ArgumentParser()
        self.define_arguments(self.parser)
        self.vaccines = {"COVAXIN", "COVISHIELD", "SPUTNIK V"}

    @staticmethod
    def define_arguments(parser):
        """"Defines command line arguments"""
        parser.add_argument("--district",
                            dest="district_id",
                            type=int,
                            nargs="*",
                            help="District ID (3 digits) to find vaccine centers")
        parser.add_argument("--pin",
                            dest="pin",
                            type=int,
                            nargs="*",
                            help="PIN Code (6 digits) to find vaccine centers")
        parser.add_argument("--age",
                            dest="min_age",
                            type=int,
                            choices=[18, 45],
                            help="Minimum Age Limit - 18 or 45")
        parser.add_argument("--vaccine",
                            dest="vaccine",
                            help="Preferred Vaccine: COVAXIN, COVISHIELD or SPUTNIK V. \
                                  Shows any available by default")
        parser.add_argument("--dose",
                            dest="dose",
                            choices=["first", "second"],
                            help="Filter by first or second dose")
        parser.add_argument("--recipients",
                            dest="recipients",
                            nargs="*",
                            help="Email addresses to notify vaccine availability")
        parser.add_argument("--loop",
                            dest="loop",
                            action="store_true",
                            help="Specify option to run script on a loop")

    def validate_input(self, args):
        """Validates use input"""
        if (not args.district_id and not args.pin) or (args.district_id and args.pin):
            self.terminate("Specify either --district or --pin")
        if args.district_id:
            for district_id in args.district_id:
                if not re.fullmatch(r"^\d\d\d$", str(district_id)):
                    self.terminate("Invalid District ID")
        if args.pin:
            for pin in args.pin:
                if not re.fullmatch(r"^\d\d\d\d\d\d$", str(pin)):
                    self.terminate("Invalid Pincode")
        if args.recipients:
            for recipient in args.recipients:
                if not re.fullmatch(r"[^@]+@[^@]+\.[^@]+", recipient):
                    self.terminate("Invalid recipient email address(es)")
        if args.vaccine and args.vaccine.upper() not in self.vaccines:
            self.terminate("Invalid vaccine. Select one of {}".format(self.vaccines))

    def get_vaccine_centers_by_district(self, district_id, date):
        """Finds a list of vaccine centers in a given district"""
        api_endpoint = "/v2/appointment/sessions/public/calendarByDistrict"
        parameters = {
            "district_id": district_id,
            "date": date
        }
        return self.get_vaccine_centers(api_endpoint, parameters)

    def get_vaccine_centers_by_pin(self, pin, date):
        """Finds a list of vaccine centers belonging to a given Pincode"""
        api_endpoint = "/v2/appointment/sessions/public/calendarByPin"
        parameters = {
            "pincode": pin,
            "date": date
        }
        return self.get_vaccine_centers(api_endpoint, parameters)

if __name__ == "__main__":
    tracker = FindVaccineCenter()
    args = tracker.parser.parse_args()
    tracker.validate_input(args)
    while True:
        email_sent = False
        with ThreadPoolExecutor() as executor:
            if args.district_id:
                future_centers = {executor.submit(tracker.get_vaccine_centers_by_district, district_id, \
                                 strftime("%d-%m-%Y")): district_id for district_id in args.district_id}
            elif args.pin:
                future_centers = {executor.submit(tracker.get_vaccine_centers_by_pin, pin, \
                                 strftime("%d-%m-%Y")): pin for pin in args.pin}
            for future in as_completed(future_centers):
                identifier = future_centers[future]
                try:
                    centers = tracker.filter_centers_by_attribute(future.result(), "available_capacity", "greater", 0)
                    if args.min_age:
                        centers = tracker.filter_centers_by_attribute(centers, "min_age_limit", "equals", args.min_age)
                    if args.vaccine:
                        centers = tracker.filter_centers_by_attribute(centers, "vaccine", "equals", args.vaccine.upper())
                    if args.dose and args.dose.lower() == "first":
                        centers = tracker.filter_centers_by_attribute(centers, "available_capacity_dose1", "greater", 0)
                    if args.dose and args.dose.lower() == "second":
                        centers = tracker.filter_centers_by_attribute(centers, "available_capacity_dose2", "greater", 0)
                    if centers:
                        message_body, checksum = tracker.create_formatted_message(centers)
                        print(message_body)
                        if args.recipients and checksum not in tracker.sent_email_checksums:
                            tracker.send_email_notification(args.recipients, message_body)
                            tracker.sent_email_checksums.add(checksum)
                            email_sent = True
                    else:
                        print(strftime('%Y-%m-%d %H:%M:%S -', localtime()), identifier, \
                             "- No vaccine appointments available at this time.")
                except Exception as exc:
                    print('Identifier %r generated an exception: %s' % (identifier, exc))
        if not args.loop:
            break
        wait_time = randint(1200, 2400) if email_sent else randint(12, 24)
        sleep(wait_time)
