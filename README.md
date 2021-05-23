# CoWin Vaccine Tracker
Get vaccine availabilty notification on your email!
Requires an India based IP Address.
​
## Installation
- Install [Python 3.x](https://www.python.org/downloads/)
- Clone or download this repository.
- Install dependencies: `python -m pip install -r ./requirements.txt`
​
## Usage
```
> python .\src\find_vaccine_center.py -h
usage: find_vaccine_center.py [-h] [--district [DISTRICT_ID ...]] [--pin [PIN ...]] [--age {18,45}] [--vaccine {COVAXIN,COVISHIELD,SPUTNIK V}] [--dose {first,second}] [--recipient RECIPIENT] [--loop]
​
optional arguments:
  -h, --help            show this help message and exit
  --district [DISTRICT_ID ...]
                        District ID (3 digits) to find vaccine centers
  --pin [PIN ...]       PIN Code (6 digits) to find vaccine centers
  --age {18,45}         Minimum Age Limit - 18 or 45
  --vaccine {COVAXIN,COVISHIELD,SPUTNIK V}
                        Preferred Vaccine: COVAXIN, COVISHIELD or SUPTNIK V. Shows any available by default
  --dose {first,second}
                        Filter by first or second dose
  --recipient RECIPIENT
                        Email address to notify vaccine availability
  --loop                Specify option to run script on a loop
```
#### This script can get vaccine availablity information based on two parameters - Pincode or DistrictID

### Get vaccine availability via DistrictID:
#### 1. Find out your DistrictID:
- Syntax:
```
> python .\src\find_district_id.py -h
usage: find_district_id.py [-h] --state STATE [STATE ...]
​
optional arguments:
  -h, --help            show this help message and exit
  --state STATE [STATE ...]
                        Enter state to list District IDs
```
- Example:
```
> python .\src\find_district_id.py --state Andaman and Nicobar Islands
​
Districts:
​
Nicobar  -  3
North and Middle Andaman  -  1
South Andaman  -  2
```
#### 2. Get vaccine availability information based on your DistrictID:
- Example (for Bangalore Urban, Karnataka)
```
> python .\src\find_vaccine_center.py --district 265 --dose second    
Available Vaccine Centers:
​Center 1: Sparsh Hospital Basement - 29 P2 The Health City Hosur Rd Bommasandra Industrial Area Bengaluru - Bangalore Urban - Karnataka - 560099
​
Session 1:
​
​        Date: 24-05-2021
        Available First Dose Capacity: 0
        Available Second Dose Capacity: 47
        Minimum Age Limit: 18
        Vaccine: COVISHIELD
​
Book your slot now at: https://selfregistration.cowin.gov.in/
```
NOTE: You can specify multiple DistrictIDs (space separated)
​
### Get vaccine availability via Pincode:
- Example (for Pincode 560099)
```
> python .\src\find_vaccine_center.py --pin 560099
Available Vaccine Centers:
​
Center 1: Sparsh Hospital Basement - 29 P2 The Health City Hosur Rd Bommasandra Industrial Area Bengaluru - Bangalore Urban - Karnataka - 560099
​
Session 1:
​
        Date: 24-05-2021
        Available First Dose Capacity: 0
        Available Second Dose Capacity: 47
        Minimum Age Limit: 18
        Vaccine: COVISHIELD
        Fee Type: Paid
​
Book your slot now at: https://selfregistration.cowin.gov.in/
```
NOTE: You can specify multiple Pincodes (space separated)
​
### Optional arguments:
- `--age` allows filtering results based on minimum age limit. 
  Accepeted values are `18` and `45`
- `--vaccine` allows filtering results base on desired vaccine variant. 
  Accepted values are `COVISHIELD`, `COVAXIN`, `SPUTNIK V`
- `--dose` allows filtering results based on required dose.
  Accepeted values are `first` and `second`
- `--loop` runs the script indefinitely, retriving updated information every minute or so.
- `--recipient` allows user to specify a recipient email address that will recieve notification emails when vaccine slots are available. Use only after setting up an SMTP client.
​
### Setting up and SMTP client:
Settings for the SMTP client are taken from the configuration file located at `./config/email_credentials.json`. A sample configuration file would look like:
​
```
{
    "sender_email": "cowin-vaccine-tracker@yandex.com",
    "password": "********",
    "smtp_url": "smtp.yandex.com",
    "smtp_port": 465
}
​
```
These credentials will be used to send email notifications about vaccine availability to the recipient specified by the `--recipient` argument.
