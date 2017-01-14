#!/usr/bin/python3

import argparse
import json
import logging
import requests
import xml.etree.ElementTree as ET
from currency_map import currencies

"""
CURRENCY CONVERTER
==================
IN: amount - amount which we want to convert - float
    input_currency - input currency - 3 letters name or currency symbol
    output_currency - requested/output currency - 3 letters name or currency symbol

FUNCTIONALITY: If output_currency param is missing, convert to all known currencies.
               Fixer api is used to obtain currency rates. If it is not available, ECB rates are used.

OUT: json
     example:
              {
                "input": {
                    "amount": <float>,
                    "currency": <3 letter currency code>
                }
                "output": {
                    <3 letter currency code>: <float>
                }
              }

currency map used from http://www.localeplanet.com/api/auto/currencymap.json
"""

FIXER_URL = "http://api.fixer.io/latest"
ECB_URL = "http://www.ecb.europa.eu/stats/eurofxref/eurofxref-daily.xml"
ECB_NAMESPACES = {'gesmes': 'http://www.gesmes.org/xml/2002-08-01',
                  'rates': 'http://www.ecb.int/vocabulary/2002-08-01/eurofxref'}
ECB_DEFAULT_BASE = 'EUR'


class CurrencyConverter:
    def __init__(self):
        self.args = None
        self.parser = None
        self.rates = None
        self.conversion = {"input": {}, "output": {}}
        self.symbols_map = {currency[0]: currency[1]["symbol_native"] for currency in
                            currencies.items()}  # {"USD": "$", ...}

    def check_currency(self, currency):
        """Check if 3 letters currency name or symbol exist.
        :param currency: commandline parameter for input/output currency
        :return currency code
        """

        if len(currency) == 3 and currency.upper() in currencies.keys():
            return currency.upper()
        elif currency in self.symbols_map.values():
            # get codes for symbol
            codes = [code for code, symbol in self.symbols_map.items() if symbol == currency]
            # same code for more currency codes
            if len(codes) > 1:
                self.parser.error("'{}' is ambiguous. Choose one of {}".format(currency, ", ".join(codes)))
            else:
                return codes[0]
        else:
            self.parser.error("Currency '{}' not supported.".format(currency))

    def parse_parameters(self):
        """Parse commandline parameters"""

        self.parser = argparse.ArgumentParser(description='Currency converter')
        self.parser.add_argument('--amount', type=float, required=True, help='Amount which we want to convert')
        self.parser.add_argument('--input_currency', type=self.check_currency, required=True,
                                 help='3 letters name or currency symbol')
        self.parser.add_argument('--output_currency', type=self.check_currency,
                                 help='3 letters name or currency symbol')

        self.args = self.parser.parse_args()
        logger.debug('%s', self.args)

    def get_json_rates(self):
        """
        Get rates from 'fixer' source.
        :return dict of input currency rates for output currency or all available currencies
                None on failure
        output example: {"base": "CZK", "date": "2017-01-13", "rates": {"AUD": 0.052644, "BGN": 0.072381,...}
        """

        try:
            params = {'base': self.args.input_currency}

            if self.args.output_currency:
                params['symbols'] = self.args.output_currency

            response = requests.get(FIXER_URL, params)

            if response.status_code != 200:
                logger.warning("Failed to obtain currency rates from FIXER: status code %s, reason: %s, text: %s",
                               response.status_code, response.reason, response.text)
            else:
                return json.loads(response.text)
        except requests.exceptions.RequestException as e:
            logger.error("Rates could not be obtained from %s.", FIXER_URL)

        return None

    def get_xml_rates(self):
        """
        Get rates in xml format from 'ECB' source
        @:return xml string with rates for EUR
                 None on failure
        """

        try:
            response = requests.get(ECB_URL)

            if response.status_code != 200:
                logger.warning("Failed to obtain currency rates from ECB: status code {}, reason: {}, text: {}".format(
                    response.status_code, response.reason, response.text))
            else:
                return response.text
        except requests.exceptions.RequestException as e:
            logger.error("Rates could not be obtained from %s.", ECB_URL)

        return None

    def parse_xml_rates(self, xml_string):
        """
        Choose rates only for output currency if specified, otherwise use all.
        @:param xml_string: xml string with rates for EUR
        @:return dictionary of {'base': <currency_code>, 'date': <date>, 'rates': {<currency_code>: <currency_rate>,...}}
        """

        root = ET.fromstring(xml_string)  # Envelope
        element = root.find('rates:Cube', ECB_NAMESPACES)  # Cube

        currencies = {'base': ECB_DEFAULT_BASE, 'rates': {}}

        if element:
            subelements = element.findall(".//")

            for subelement in subelements:
                if 'time' in subelement.attrib:
                    currencies['time'] = subelement.attrib['time']
                elif 'rate' in subelement.attrib:
                    if self.args.output_currency:
                        if subelement.attrib['currency'] == self.args.output_currency:
                            currencies['rates'][subelement.attrib['currency']] = float(subelement.attrib['rate'])
                            break
                    else:
                        currencies['rates'][subelement.attrib['currency']] = float(subelement.attrib['rate'])

        # Add default base from rates. ECB gave rates always for EUR. So EUR rate is not present in rates.
        currencies['rates'][ECB_DEFAULT_BASE] = float(1)

        return currencies

    def convert_rates(self, base, rate):
        """
        Convert rates from default base to input currency - ECB gave rates only for EUR.
        :param base: currency for which rates were obtained. It can not be same as input currency
        :param rate: output currency rate for base currency
        :return float number of converted rate for input currency
        """

        if base != self.args.input_currency:
            return 1 / self.rates['rates'][self.args.input_currency] * rate
        else:
            return rate

    def convert_amount(self):
        """
        Calculates output currency amount
        @:return True if successfully converted
        """

        base = self.rates['base']

        self.conversion["input"] = {"amount": self.args.amount, "currency": self.args.input_currency}

        # same input and output currencies
        if self.args.output_currency and self.args.input_currency == self.args.output_currency:
            self.conversion["output"][self.args.output_currency] = float("{0:.2f}".format(self.args.amount))
        elif self.rates['rates']:
            for curr, rate in self.rates['rates'].items():
                self.conversion["output"][curr] = float(
                    "{0:.2f}".format(self.convert_rates(base, rate) * self.args.amount, 2))
        else:
            logger.error("Currency rates for '{}' were not obtained.", self.args.input_currency)
            return False  # failure

        return True  # success

    def execute(self):
        self.parse_parameters()
        self.rates = self.get_json_rates()

        # in case that fist source is not available, try the second one
        if not self.rates:
            xml_rates = self.get_xml_rates()

            if not xml_rates:
                return None

            self.rates = self.parse_xml_rates(xml_rates)

        if self.convert_amount():
            return json.dumps(self.conversion, indent=4, separators=(',', ': '))
        else:
            return None


if __name__ == "__main__":
    # Setup logger
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)

    console_hndl = logging.StreamHandler()
    console_hndl.setLevel(logging.INFO)

    formatter = logging.Formatter('%(asctime)s %(name)s %(levelname)s: %(message)s')
    console_hndl.setFormatter(formatter)
    logger.addHandler(console_hndl)

    converter = CurrencyConverter()
    output = converter.execute()

    if output:
        print(output)
    else:
        exit(1)
