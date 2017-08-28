#!/usr/bin/env python3
from bs4 import BeautifulSoup as soup
import requests as req
from PIL import Image
from PIL import ImageChops
import argparse
import sys
import os
import subprocess
import shutil
from tabulate import tabulate
import json
from io import BytesIO
from pathlib import Path


class TermColours:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    OKCYAN = '\033[36m'
    WARNING = '\033[93m'
    LIGHT_GREY = '\033[37m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class SnatchCarData:

    """
    A Python3 command line utility to grab vital car information and perform
    fast and easy analysis of this data. Grab information such as bhp, make,
    model and car image.
    """

    def __init__(self):
        # Defaults
        self.proxies = {}
        self.destination_folder = "output/"
        self.verbose = False
        self.out_path_generated = False
        self.out_path = ""
        self.full_path_to_image = ""
        # Parser
        self.parser = argparse.ArgumentParser(description="Car Data Snatch - Passive Data Collection")
        # Setup the parser object
        self.setup_parser()
        # Get the args
        self.args = self.parser.parse_args()
        # Setup Args and Program
        self.setup()
        # Handle Multiple Registrations being passed in.
        if "," in self.args.registration:
            self.multiple_registrations = True
        else:
            self.multiple_registrations = False
        # Run Main Method
        self.main()

    def output_warning(self, message):
        return(TermColours.WARNING + message + TermColours.ENDC)

    def output_lg(self, message):
        return(TermColours.LIGHT_GREY + message + TermColours.ENDC)

    def output_fail(self, message):
        return(TermColours.FAIL + message + TermColours.ENDC)

    def output_ok_green(self, message):
        return(TermColours.OKGREEN + message + TermColours.ENDC)

    def output_ok_blue(self, message):
        return(TermColours.OKBLUE + message + TermColours.ENDC)

    def output_ok_cyan(self, message):
        return(TermColours.OKCYAN + message + TermColours.ENDC)

    def success(self, message):
        return(TermColours.OKGREEN + "SUCCESS: " + message + TermColours.ENDC)

    def warning(self, message):
        return(TermColours.OKCYAN + "WARNING: " + message + TermColours.ENDC)

    def failed(self, message):
        return(TermColours.FAIL + "FAILED: " + message + TermColours.ENDC)

    def status(self, message):
        return(TermColours.OKCYAN + "STATUS: " + message + TermColours.ENDC)

    def setup_parser(self):
        required_arguments_group = self.parser.add_argument_group('Required Arguments')
        required_arguments_group.add_argument(
            "registration", help="The valid registration of a UK vehicle.")

        optional_arguments_group = self.parser.add_argument_group('Actions (At very least 1 Required)')
        optional_arguments_group.add_argument(
            "-a", "--all", dest="all", help="Get all data from the car.", action="store_true")
        optional_arguments_group.add_argument(
            "-j", "--json", dest="json", help="Get all data and store as json.", action="store_true")
        optional_arguments_group.add_argument(
            "-mk", "--make", dest="make", help="Output the make of the car.", action="store_true")
        optional_arguments_group.add_argument(
            "-bhp", "--brakeHorsePower", dest="bhp", help="Output the BHP of the OEM car.", action="store_true")
        optional_arguments_group.add_argument(
            "-md", "--model", dest="model", help="Output the Model of the car.", action="store_true")
        optional_arguments_group.add_argument(
            "-bd", "--body", dest="body", help="Ouput the body design of the car", action="store_true")
        optional_arguments_group.add_argument(
            "-c", "--colour", dest="colour", help="Output the Colour of the car.", action="store_true")
        optional_arguments_group.add_argument(
            "-eS", "--engineSize", dest="engine_size", help="Output the engine size of the car.", action="store_true")
        optional_arguments_group.add_argument(
            "-yr", "--year", dest="year", help="Output the year the car was manufactured.", action="store_true")
        optional_arguments_group.add_argument(
            "-i", "--image", dest="image", help="Download an image of the car.", action="store_true")
        optional_arguments_group.add_argument(
            "-iS", "--imageShow", dest="show_image", help="Download and open the image of the car.", action="store_true")

        flag_arguments_group = self.parser.add_argument_group('Complimentary Arguments / Flags')
        flag_arguments_group.add_argument(
            "-http", "--httpProxy", dest="http_proxy", help="Supply a http proxy to scrape data.")
        flag_arguments_group.add_argument(
            "-https", "--httpsProxy", dest="https_proxy", help="Supply a https proxy to scrape data.")
        flag_arguments_group.add_argument(
            "-v", "--verbose", dest="verbose", help="Clearer output of what is happening.", action="store_true")
        flag_arguments_group.add_argument(
            "-d", "--destination", dest="destination_folder", help="Supply a destination folder to output to.")

    def setup(self):
        if self.args.verbose:
            self.verbose = True
        if self.args.http_proxy:
            self.proxies["http"] = self.args.http_proxy
        if self.args.https_proxy:
            self.proxies["https"] = self.args.https_proxy
        if self.args.destination_folder:
            self.destination_folder = self.args.destination_folder
        if self.destination_folder[-1] != "/":
            self.destination_folder = self.destination_folder + "/"
        self.generate_ouput_path()

    def is_file(self, my_file_path):
        my_path = Path(my_file_path)
        if my_path.is_file():
            return True
        else:
            return False

    def generate_ouput_path(self):
        if not os.path.exists(self.destination_folder):
            os.makedirs(self.destination_folder)
            self.out_path = os.getcwd() + "/" + self.destination_folder

    def get_car_soup(self, reg):
        print(self.status("Collecting data for " +  reg))
        url = "https://www.instantcarcheck.co.uk/product-selection"
        numberplate = reg
        payload = {"vrm": numberplate}
        session = req.session()
        if len(self.proxies.keys()) > 0:
            if self.verbose:
                print(self.status("Proxie(s) ENABLED..."))
                for key, value in self.proxies.items():
                    print(self.status("Using {0} proxy: {1}".format(key.upper(), value)))
            r = session.post(url, data=payload, proxies=self.proxies)
            if self.verbose:
                for header, value in r.headers.items():
                    print(self.output_ok_cyan(header) + " : " + self.output_ok_green(value))
        else:
            r = session.post(url, data=payload)
        car_info = r.content.decode()
        bsoup = soup(car_info, "html.parser")
        return bsoup

    def get_composite_list_data(self, reg):
        custom_soup = self.get_car_soup(reg)
        vehicle_info_rows = custom_soup.find_all('div', {"class": "vehicle__info--row"})
        values = []
        car_info_data = []
        for i in range(0, len(vehicle_info_rows)):
            cols = vehicle_info_rows[i]
            for col in cols:
                values.append(col.text)
        composite_list_data = [values[x:x + 2] for x in range(0, len(values), 2)]

        return composite_list_data

    def show_composite_list_data(self, reg):
        composite_list = self.get_composite_list_data(reg)
        print(self.output_lg(tabulate(composite_list, headers=['Attribute', 'Value'])))
        print("")

    def write_json_data(self):
        if not self.out_path_generated:
            self.generate_ouput_path()
        composite_list = self.get_composite_list_data()
        dict_data = {}
        for each in composite_list:
            dict_data[each[0]] = each[1]
        with open(self.out_path + self.registration + '.json', 'w') as fp:
            json.dump(dict_data, fp)

    def download_car_image(self, reg):
        custom_soup = self.get_car_soup(reg)
        vehicle_image = custom_soup.find("img", {"class": "vehicle__img"})
        vehicle_image_url = "https://www.instantcarcheck.co.uk" + vehicle_image["src"]
        if self.verbose:
            print(self.status("Downloading image - {0}".format(vehicle_image_url)))
        response = req.get(vehicle_image_url, stream=True)
        valid = self.check_image_is_valid(BytesIO(response.content))
        if valid:
            # Set full proposed image path
            full_path_to_image = os.getcwd() + "/" + self.destination_folder + reg + ".png"
            if self.is_file(full_path_to_image):
                # Check to see if verbose is turned on
                if self.verbose:
                    # Image already exists
                    print(self.warning("Image exists here - {0}".format(full_path_to_image)))
                return False
            else:

                # Open the full output path with the image name
                with open(full_path_to_image, 'wb') as out_file:
                    response.raw.decode_content = True
                    out_file.write(response.content)
                # Check to see if verbose is turned on
                if self.verbose:
                    # Tell user image was saved and give path to image
                    print(self.success("Image saved as {0}".format(full_path_to_image)))
            # Image was not found
        else:
            print(self.failed("No image data for this {0} found".format(reg)))
        del response
    def check_image_is_valid(self, image_object):
        im1 = Image.open(image_object)
        im2 = Image.open("res/not_found.png")
        diff = ImageChops.difference(im2, im1)
        if diff.getbbox() != None:
            return True
        else:
            return False
    def show_car_image(self, reg):
        # Download the image
        self.download_car_image(reg)

        path_to_image = os.getcwd() + "/" + self.destination_folder + reg + ".png"
        if self.verbose:
            print(self.status("Opening image..."))
        p = subprocess.Popen(["open", path_to_image])
        if self.verbose:
            print(self.success("Image opened successfully."))

    def ouput_attributes(self,attributes, reg):
        print(attributes)
        data = self.get_composite_list_data(reg)
        output_data = []
        for attrib in attributes:
            for each in data:
                if each[0] == attrib:
                    output_data.append(each)

        print(self.output_lg(tabulate(output_data, headers=['Attribute', 'Value'])))

    def main(self):
        try:
            if not (self.args.all or self.args.image or
                    self.args.show_image or self.args.json or
                    self.args.make or self.args.model or self.args.bhp or
                    self.args.engine_size or self.args.year or self.args.body):
                self.parser.print_help()
                self.parser.error('No action requested, add -a , -i, -iS, -j for more use --help')
            else:
                # Download an image of the car the registration belongs to.
                if self.args.image:
                    if self.multiple_registrations:
                        for reg in self.args.registration.split(","):
                            self.download_car_image(reg)
                    else:
                        self.download_car_image(self.args.registration)
                # Show an image of the kind of car the registration supplied belongs to
                elif self.args.show_image:
                    if self.multiple_registrations == True:
                        for reg in self.args.registration.split(","):
                            self.show_car_image(reg)
                    else:
                        self.show_car_image(self.args.registration)
                # Ouput all data on registration supplied
                if self.args.all:
                    if self.multiple_registrations:
                        for reg in self.args.registration.split(","):
                            self.show_composite_list_data(reg)
                    else:
                        self.show_composite_list_data(self.args.registration)
                else:
                    attribs = []
                    if self.args.make:
                        attribs.append("Make")
                    if self.args.model:
                        attribs.append("Model")
                    if self.args.body:
                        attribs.append("Body")
                    if self.args.colour:
                        attribs.append("Colour")
                    if self.args.bhp:
                        attribs.append("BHP")
                    if self.args.engine_size:
                        attribs.append("Engine Size")
                    if self.args.year:
                        attribs.append("Year")
                    if len(attribs) > 0:
                        if self.multiple_registrations:
                            for reg in self.registration:
                                print(reg)
                                self.ouput_attributes(attribs, reg)
                        else:
                            self.ouput_attributes(attribs, self.registration)
                # Get JSON data of specified reg
                if self.args.json:
                    self.write_json_data()

        except Exception as e:
            print("Error: ", e)

if __name__ == "__main__":
    snatch = SnatchCarData()
