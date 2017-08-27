#!/usr/bin/env python3
from bs4 import BeautifulSoup as soup
import requests as req
from PIL import Image
from PIL import ImageChops
import argparse, sys, os, subprocess, shutil
from tabulate import tabulate

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
        self.proxies = {}
        self.destination_folder = "output/"
        # Parser
        self.parser = argparse.ArgumentParser()
        # Setup the parser object
        self.setup_parser()
        # Get the args
        self.args = self.parser.parse_args()
        # Set the defaults
        self.set_arg_defaults()
        # Vehicle File Name
        self.vehicle_image_file_name = self.args.registration + ".png"
        self.verbose = False
        # Accept changes to defaults parsed through args
        self.set_arg_defaults()
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

    def setup_parser(self):
        self.parser.add_argument("-r", "--reg", dest="registration", help="The valid registration of a UK vehicle.", required=True)
        self.parser.add_argument("-a", "--all", dest="all", help="Get all data from the car.")
        self.parser.add_argument("-m", "--make", dest="make", help="Output the make of the car.", action="store_true")
        self.parser.add_argument("-i", "--image", dest="image", help="Download an image of the car.", action="store_true")
        self.parser.add_argument("-iS", "--imageShow", dest="show_image", help="Download and open the image of the car.", action="store_true")
        self.parser.add_argument("-iF", "--imageFilename", dest="image_file_name", help="Specify the output file name for car image.")
        self.parser.add_argument("-http", "--httpProxy", dest="http_proxy", help="Supply a http proxy to scrape data.")
        self.parser.add_argument("-https", "--httpsProxy", dest="https_proxy", help="Supply a https proxy to scrape data.")
        self.parser.add_argument("-v", "--verbose", dest="verbose", help="Clearer output of what is happening.", action="store_true")
        self.parser.add_argument("-d", "--destination", dest="destination_folder", help="Supply a destination folder to output to.")
    def set_arg_defaults(self):
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
    def get_car_soup(self):
        url = "https://www.instantcarcheck.co.uk/product-selection"
        numberplate = self.args.registration
        payload={"vrm":numberplate}
        session = req.session()
        if len(self.proxies.keys()) > 0:
            print(self.output_ok_green("Proxie(s) ENABLED..."))
            for key,value in self.proxies.items():
                print(self.output_ok_blue("Using {0} proxy: {1}".format(key.upper(),value)))
            r = session.post(url, data=payload, proxies=self.proxies)
            if self.verbose:
                for header,value in r.headers.items():
                    print(self.output_ok_cyan(header) + " : " + self.output_ok_green(value))
        else:
            r = session.post(url, data=payload)
        car_info = r.content.decode()
        bsoup = soup(car_info,"html.parser")
        return bsoup
    def get_composite_list_data(self):
        vehicle_info_rows = self.soupify.find_all('div',{"class":"vehicle__info--row"})
        values = []
        car_info_data = []

        for i in range(0,len(vehicle_info_rows)):
            cols = vehicle_info_rows[i]
            for col in cols:
                values.append(col.text)
        composite_list = [values[x:x+2] for x in range(0, len(values),2)]
        return composite_list
    def show_composite_list_data(self):
        composite_list = self.get_composite_list_data()
        print(self.output_lg(tabulate(composite_list, headers=['Attribute','Value'])))
        # for each in composite_list:
        #     print("{0}: {1}".format(each[0],self.output_ok_green(each[1])))
    def download_car_image(self):
        vehicle_image = self.soupify.find("img",{"class":"vehicle__img"})
        vehicle_image_url = "https://www.instantcarcheck.co.uk" + vehicle_image["src"]
        response = req.get(vehicle_image_url, stream=True)
        if self.destination_folder[-1] != "/":
            self.destination_folder = self.destination_folder + "/"
        if not os.path.exists(self.destination_folder):
            os.makedirs(self.destination_folder)
        with open(os.getcwd() + "/" + self.destination_folder +  self.vehicle_image_file_name, 'wb') as out_file:
            shutil.copyfileobj(response.raw, out_file)
        del response
        return True
    def show_car_image(self):
        self.download_car_image()
        im1 = Image.open(self.vehicle_image_file_name)
        im2 = Image.open("not_found.png")
        diff = ImageChops.difference(im2, im1)
        if diff.getbbox() != None:
            p = subprocess.Popen(["open",self.vehicle_image_file_name])
        else:
            print("opening")
            class NoImageFound(Exception):
                pass
            raise NoImageFound("Sorry no image was found.")

    def main(self):
        try:
            if self.args.make or self.args.image or self.args.all:
                if self.args.image:
                    if self.args.show_image:
                        if self.verbose:
                            print(self.output_ok_blue("Downloading and opening image..."))
                        self.show_car_image()
                        if self.verbose:
                            print(self.output_ok_green("Image Opened Successfully!"))
                    else:
                        if self.verbose:
                            print(self.output_ok_blue("Finding image..."))
                        found = self.download_car_image()
                        if self.verbose:
                            if found:
                                print(self.output_ok_green("SUCCESS: Found image and saved as {0}".format(self.vehicle_image_file_name)))
                            else:
                                print(self.output_warning("FAIL: Failed to find image.{0}".format(self.vehicle_image_file_name)))
                elif self.args.all:
                    pass
            else:
                self.show_composite_list_data()

        except Exception as e:
            print("ERROR: ", e)
# Check to see if any args are parsed.

if __name__ == "__main__":
    snatch = SnatchCarData()
