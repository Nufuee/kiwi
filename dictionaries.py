czech_ryanair = {
    'BRQ' : ['LTN'],
    'PRG' : ['CRL', 'CIA', 'BGY', 'TPS','DUB','STN','LPL'],
    'OSR' : ['BGY', 'STN'],
}

# Iterate through czech_ryanair printing the keys and values
for key, value in czech_ryanair.items():
    print('Key: {}, Value: {}'.format(key, value))

# Which destinations are accessible from Prague (PRG)?
for destination in czech_ryanair['PRG']:
    print("From PRG:", destination)

# Construct a list of all the destinations ryanair flies to from czech republic
cz_dests = [destination for destinations in czech_ryanair.values() for destination in destinations]
print("Destinations from CZ:", cz_dests)

destinations = []
for _, v in czech_ryanair.items():
    destinations += v
print(destinations)