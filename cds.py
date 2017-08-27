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
        # Parser
        self.parser = argparse.ArgumentParser()
        # Setup the parser object
        self.setup_parser()
        # Get the args
        self.args = self.parser.parse_args()
        # Vehicle File Names
        self.registration = self.args.registration
        self.vehicle_image_file_name = self.args.registration + ".png"
        # Setup Args and Program
        self.setup()
        # Get the car data page Soup
        self.soupify = self.get_car_soup()
        # Run main
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

        optional_arguments_group = self.parser.add_argument_group('Ouput Options (1 Required)')
        optional_arguments_group.add_argument(
            "-a", "--all", dest="all", help="Get all data from the car.", action="store_true")
        optional_arguments_group.add_argument(
            "-j", "--json", dest="json", help="Get all data and store as json.", action="store_true")
        optional_arguments_group.add_argument(
            "-m", "--make", dest="make", help="Output the make of the car.", action="store_true")
        optional_arguments_group.add_argument(
            "-i", "--image", dest="image", help="Download an image of the car.", action="store_true")
        optional_arguments_group.add_argument(
            "-iS", "--imageShow", dest="show_image", help="Download and open the image of the car.", action="store_true")

        flag_arguments_group = self.parser.add_argument_group('Flag Arguments')
        flag_arguments_group.add_argument(
            "-iF", "--imageFilename", dest="image_file_name", help="Specify the output file name for car image.")
        flag_arguments_group.add_argument(
            "-http", "--httpProxy", dest="http_proxy", help="Supply a http proxy to scrape data.")
        flag_arguments_group.add_argument(
            "-https", "--httpsProxy", dest="https_proxy", help="Supply a https proxy to scrape data.")
        flag_arguments_group.add_argument(
            "-v", "--verbose", dest="verbose", help="Clearer output of what is happening.", action="store_true")
        flag_arguments_group.add_argument(
            "-d", "--destination", dest="destination_folder", help="Supply a destination folder to output to.")

    def setup(self):
        if self.args.image_file_name:
            self.vehicle_image_file_name = self.args.image_file_name
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
        if not os.path.exists(self.destination_folder):
            os.makedirs(self.destination_folder)
        self.out_path = os.getcwd() + "/" + self.destination_folder

    def get_car_soup(self):
        url = "https://www.instantcarcheck.co.uk/product-selection"
        numberplate = self.args.registration
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

    def get_composite_list_data(self):
        vehicle_info_rows = self.soupify.find_all('div', {"class": "vehicle__info--row"})
        values = []
        car_info_data = []

        for i in range(0, len(vehicle_info_rows)):
            cols = vehicle_info_rows[i]
            for col in cols:
                values.append(col.text)
        composite_list = [values[x:x + 2] for x in range(0, len(values), 2)]
        return composite_list

    def show_composite_list_data(self):
        composite_list = self.get_composite_list_data()
        print(self.output_lg(tabulate(composite_list, headers=['Attribute', 'Value'])))
        
    def write_json_data(self):
        composite_list = self.get_composite_list_data()
        dict_data = {}
        for each in composite_list:
            dict_data[each[0]] = each[1]
        with open(self.out_path + self.registration + '.json', 'w') as fp:
            json.dump(dict_data, fp)

    def download_car_image(self):
        vehicle_image = self.soupify.find("img", {"class": "vehicle__img"})
        vehicle_image_url = "https://www.instantcarcheck.co.uk" + vehicle_image["src"]
        if self.verbose:
            print(self.status("Downloading image..."))
        response = req.get(vehicle_image_url, stream=True)
        if response.status_code == 200:
            if self.verbose:
                print(self.status("Writing local image..."))
            with open(os.getcwd() + "/" + self.destination_folder + self.vehicle_image_file_name, 'wb') as out_file:
                shutil.copyfileobj(response.raw, out_file)
            if self.verbose:
                print(self.success("Image saved as {0}".format(
                    os.getcwd() + "/" + self.destination_folder + self.vehicle_image_file_name)))
        else:
            if self.verbose:
                print(self.warning("No image found - {0}".format(self.vehicle_image_file_name)))
            else:
                print(self.warning("No image found."))
        del response

    def show_car_image(self):
        self.download_car_image()
        path_to_image = os.getcwd() + "/" + self.destination_folder + self.vehicle_image_file_name
        im1 = Image.open(path_to_image)
        im2 = Image.open("res/not_found.png")
        diff = ImageChops.difference(im2, im1)
        if diff.getbbox() != None:
            if self.verbose:
                print(self.status("Opening image..."))
            p = subprocess.Popen(["open", path_to_image])
            if self.verbose:
                print(self.success("Image opened successfully."))
        else:
            class NoImageFound(Exception):
                pass
            raise NoImageFound("Sorry no image was found.")

    def main(self):
        try:
            if self.args.make or self.args.image or self.args.all or self.args.json:
                if self.args.image:
                    if self.args.show_image:
                        self.show_car_image()
                    else:
                        self.download_car_image()
                if self.args.all:
                    self.show_composite_list_data()
                if self.args.json:
                    self.write_json_data()
            else:
                self.show_composite_list_data()
        except Exception as e:
            print("Error: ", e)

if __name__ == "__main__":
    snatch = SnatchCarData()
