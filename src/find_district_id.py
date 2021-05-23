import requests
import argparse

from vaccine_helper import VaccineHelper

class FindDistrictID(VaccineHelper):
    def __init__(self):
        super().__init__()
        self.state_id_api_endpoint = "/v2/admin/location/states"
        self.district_id_api_endpoint = "/v2/admin/location/districts/"
        self.parser = argparse.ArgumentParser()
        self.define_arguments(self.parser)

    def define_arguments(self, parser):
        parser.add_argument("--state", 
                            dest="state",
                            nargs="+",
                            required=True,
                            help="Enter state to list District IDs")
    
    def validate_input(self, input_state):
        if not input_state.isalpha():
            self.terminate("invaid state name")

    def get_states(self):
        response = requests.get(self.base_url + self.state_id_api_endpoint, headers={"User-Agent": "PostmanRuntime/8.5"})
        if response.ok:
            return response.json().get("states")
        else:
            self.terminate("Failed to fetch State IDs, please try again later.")

    def get_district_ids(self, state_id):
        response = requests.get(self.base_url + self.district_id_api_endpoint + str(state_id), headers={"User-Agent": "PostmanRuntime/8.5"})
        if response.ok:
            return response.json().get("districts")
        else:
            self.terminate("Failed to fetch District IDs, please try again later.")

    @staticmethod
    def compare(str1, str2):
        return [char.lower() for char in str1 if char.isalpha()] == [char.lower() for char in str2 if char.isalpha()]

    def match_state_to_id(self, input_state, states):
        for state in states:
            if self.compare(state.get("state_name"), input_state):
                return state.get("state_id")
        self.terminate("Invalid state name")

    @staticmethod
    def display_districts(districts):
        print("\nDistricts:\n")
        for district in districts:
            print(district.get("district_name"), " - ", district.get("district_id"))

if __name__ == "__main__":
    tracker = FindDistrictID()
    args = tracker.parser.parse_args()
    input_state = "".join(args.state)
    tracker.validate_input(input_state)
    states = tracker.get_states()
    state_id = tracker.match_state_to_id(input_state, states)
    districts = tracker.get_district_ids(state_id)
    tracker.display_districts(districts)