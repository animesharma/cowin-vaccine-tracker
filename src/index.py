import requests
import argparse
import re
import sys
from datetime import datetime

base_url = "https://cdn-api.co-vin.in/api"


def define_arguments(parser):
    parser.add_argument("--pin", 
                        dest="pin", 
                        help="PIN Code (6 digits) to find vaccine centers")
    parser.add_argument("--date", 
                        dest="date", 
                        help="Date (dd-mm-yyyy) at which appointment is sought")
    parser.add_argument("--age",
                        dest="min_age",
                        type=int,
                        help="Minimum Age Limit - 18 or 45")
    parser.add_argument("--vaccine",
                        dest="vaccine",
                        help="Preferred Vaccine: COVAXIN or COVISHIELD. Shows any available by default")

def terminate(error):
    print("Error: " + error)
    sys.exit(-1)

def validate_input(args):
    if not args.pin or not args.date:
        terminate("Valid date and PIN Code not found")
    if not re.match(r"^\d\d\d\d\d\d$", args.pin):
        terminate("Invalid PinCode")
    try:
        datetime.strptime(args.date, "%d-%m-%Y")
    except ValueError as err:
        terminate("Invalid Date format - use dd-mm-yyyy")
    if args.min_age and args.min_age not in {18, 45}:
        terminate("Invalid minimum age - use 18 or 45")
    if args.vaccine and args.vaccine.upper() not in {"COVAXIN", "COVISHIELD"}:
        terminate("Invalid Vaccine preference - specify either COVAXIN or COVISHIELD")
    
def get_vaccine_centers_by_pin(pin, date):
    api_endpoint = "/v2/appointment/sessions/public/calendarByPin"
    parameters = {
        "pincode": pin,
        "date": date
    }
    response = requests.get(url=base_url + api_endpoint, params=parameters, headers={"User-Agent": "PostmanRuntime/8.3.1"})
    if response.ok:
        return response.json().get("centers")
    else:
        terminate("Unable to reach CoWin servers, please try again later.")

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

def display_centers(centers):
    if not centers:
        print("No available slots, please try again later.")
        return

    for center in centers:
        for session in center.get("sessions"):
            print(center.get("name"), " - ", center.get("address"), " - ", center.get("district_name"), " - ", center.get("state_name"))
            print("Date: ", session.get("date"))
            print("Available Capacity: ", session.get("available_capacity"))
            print("Minimum Age Limit: ", session.get("min_age_limit"))
            print("Vaccine: ", session.get("vaccine"), "\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    define_arguments(parser)
    args = parser.parse_args()
    validate_input(args)
    vaccine_centers = get_vaccine_centers_by_pin(args.pin, args.date)
    if(args.min_age):
        vaccine_centers = filter_centers_by_attribute(vaccine_centers, "min_age_limit", args.min_age)
    if(args.vaccine):
        vaccine_centers = filter_centers_by_attribute(vaccine_centers, "vaccine", args.vaccine.upper())
    display_centers(vaccine_centers)