#!/usr/bin/python

# IN:  flights data (SOURCE-DEST-DEP-ARR-FLIGHT_NR-PRICE-BAGS_ALLOWED-BAG_PRICE)
# OUT: flight combinations (min 2 segments) without luggage or with 1 or 2 luggage (A-B-A, C-A-B-A, A-B-A-D)
#      segments have to connect with 1-4 hours for change
#      ignore segments repetition in combination (A-B-A-B)

import argparse
import copy
import csv
import json
import sys
from datetime import datetime, timedelta
from enum import Enum

MIN_FLIGHT_CHANGE = 1
MAX_FLIGHT_CHANGE = 4


class RoutesFinder(object):
    def __init__(self):
        self.flights = []
        self.routes = []
        self.output_data = {"routes": []}

    def execute(self):
        args = self.parse_input()
        # print("Input:", args)

        if args.input_csv:
            # load flights from csv
            self.flights = self.load_csv(args.input_csv)

            # create routes from connecting flights; find connecting flights for each row-flight
            for from_index, from_flight in enumerate(self.flights):
                route = [from_index]
                self.find_routes(from_index, route)

            # create output data {"routes": [{"3->13": {"prices":[], "flights": []}]}
            for route_index, route in enumerate(self.routes):
                prices = self.count_price(route)
                self.output_data["routes"].append({'->'.join(str(i) for i in route): {"flights": [], "prices": []}})
                # print("\nROUTE:", route)

                if isinstance(route, list):
                    for flight_index in route:
                        flight = self.flights[flight_index]
                        self.save_flights(route_index, flight)
                        # print(" ", self.flights[flightIndex])
                else:
                    flight = self.flights[route]
                    self.save_flights(flight)
                    # print(" ", self.flights[route])

                # get final prices for 0,1,2,.. pcs of baggage
                for pieces in range(prices['allowed_baggage'] + 1):
                    self.output_data["routes"][route_index]['->'.join(str(i) for i in route)]["prices"].append(
                        {"tickets + {} bag/s".format(pieces): prices["tickets_price"] + prices["baggage_price"] * pieces})

            return self.output_data

    def parse_input(self):
        parser = argparse.ArgumentParser(description="Process flight information.")
        parser.add_argument("input_csv", default=sys.stdin, help="Input *.csv file path")

        return parser.parse_args()

    def load_csv(self, csv_file):
        flights = []

        try:
            with open(csv_file, 'rt') as csvfile:
                try:
                    reader = csv.DictReader(csvfile) # closed file

                    # for row in reader:
                    #     try:
                    #         flight = Flight(row['source'], row['destination'], row['departure'], row['arrival'],
                    #                         row['flight_number'], row['price'], row['bags_allowed'], row['bag_price'])
                    #         flights.append(flight)
                    #
                    #     except ValueError:
                    #         pass

                    # flights = [Flight(row['source'], row['destination'], row['departure'], row['arrival'],
                    #                   row['flight_number'], row['price'], row['bags_allowed'], row['bag_price'])
                    #            for row in reader]

                    flights = [Flight(**row) for row in reader]

                    return flights
                except csv.Error as e:
                    sys.exit('file {}, line {}: {}'.format(csv_file, flights.line_num, e))
        except OSError as e:
            sys.exit('Cannot open file {}. {}'.format(csv_file, e))

    def find_routes(self, from_index, route):
        from_flight = self.flights[from_index]   # 0

        # find all connecting flights (their index) to from_flight
        connecting_flights = [to_index for to_index, to_flight in enumerate(self.flights)
                              if from_flight.destination == to_flight.source
                              and from_flight.change_possible(to_flight.departure)
                              and from_flight.bags_allowed <= to_flight.bags_allowed]

        if connecting_flights:  # [5,8]
            # append connecting flight to route [5,8] -> [0,5], [0,8]
            for connecting_flight in connecting_flights:
                new_route = copy.copy(route)
                new_route.append(connecting_flight)

                if new_route not in self.routes and not self.visited(route, connecting_flight):
                    self.routes.append(new_route)
                    self.find_routes(connecting_flight, new_route)

    def visited(self, route=[], connection=None):
        """ Ignore segments (visited airports) repetition in combination (A->B->A->B). """

        visited_airports = [self.flights[flight].source for flight in route]

        if self.flights[connection].source in visited_airports:
            # find index of connection source in visited airports on route
            segment_start = visited_airports.index(self.flights[connection].source)

            # check if destination is the same as next visited airport after found index
            if self.flights[connection].destination == visited_airports[segment_start + 1]:
                return True

        return False

    def count_price(self, route=[]):
        """ Get price for all tickets and baggage in a route. """
        tickets_price = 0
        baggage_price = 0
        # get a number of allowed baggage for route (e.g. can't transfer 2 bags to flight with 1 allowed)
        allowed_baggage = min([self.flights[flight].bags_allowed for flight in route])

        for flight in route:
            tickets_price += self.flights[flight].price
            baggage_price += self.flights[flight].bag_price

        return {'tickets_price': tickets_price, 'baggage_price': baggage_price, 'allowed_baggage': allowed_baggage}

    def save_flights(self, route_index, flight):
        # self.output_data["routes"][route_index]['->'.join(str(i) for i in self.routes[route_index])]["flights"].append(
        #     {"flight_number": flight.flight_number,
        #      "source": flight.source,
        #      "departure": flight.departure.strftime('%Y-%m-%dT%H:%M:%S'),
        #      "destination": flight.destination,
        #      "arrival": flight.arrival.strftime('%Y-%m-%dT%H:%M:%S'),
        #      "price": flight.price,
        #      "bag_price": flight.bag_price,
        #      "bags_allowed": flight.bags_allowed
        #     })

        self.output_data["routes"][route_index]['->'.join(str(i) for i in self.routes[route_index])]["flights"].append(
            self.check_date(flight.__dict__))

    def check_date(self, flight):
        """ Change date to string """
        for key, value in flight.items():
            if isinstance(value, datetime):
                flight[key] = value.strftime('%Y-%m-%dT%H:%M:%S')

        return flight


class Flight:
    def __init__(self, source, destination, departure, arrival, flight_number, price, bags_allowed, bag_price):
        self.source = source                                                    # airport code - USM
        self.destination = destination                                          # airport code - HKT
        self.departure = datetime.strptime(departure, '%Y-%m-%dT%H:%M:%S')      # time - 2017-02-11T06:25:00
        self.arrival = datetime.strptime(arrival, '%Y-%m-%dT%H:%M:%S')          # time - 2017-02-11T07:25:00
        self.flight_number = flight_number                                      # unique segment identifier - PV404
        self.price = float(price)                                               # flight ticket price without luggage - 24
        self.bags_allowed = int(bags_allowed)                                   # number of baggage to buy - 1
        self.bag_price = float(bag_price)                                       # price for 1 piece of baggage - 9

        self.min_departure_time = self.arrival + timedelta(hours=MIN_FLIGHT_CHANGE)
        self.max_departure_time = self.arrival + timedelta(hours=MAX_FLIGHT_CHANGE)

    def __str__(self):
        return "#Flight: {} {} {} -> {} {}, ticket price: {}, luggage price: {} (max {} pcs)".format(self.flight_number,
                                                                                                     self.source,
                                                                                                     self.departure,
                                                                                                     self.destination,
                                                                                                     self.arrival,
                                                                                                     self.price,
                                                                                                     self.bag_price,
                                                                                                     self.bags_allowed)

    def change_possible(self, departure_time):
        """ Check if there is enough time space for flight change. """
        if (departure_time >= self.min_departure_time) and (departure_time <= self.max_departure_time):
            return True

        return False


if __name__ == "__main__":

    finder = RoutesFinder()
    output = finder.execute()

    print(json.dumps(output, indent=4, separators=(',', ':')))

