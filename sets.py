#Set - Unordered collection of unique hashable items

john_classes = {'monday', 'tuesday', 'wednesday'}
eric_classes = set(['wednesday', 'thursday'])


print("john_classes: ", john_classes)
print("eric_classes: ", eric_classes)


union = john_classes | eric_classes
print(union)

# Print out a list of all the unique destinations ryanair flies to from czech republic
czech_ryanair = {
    'BRQ' : ['LTN'],
    'PRG' : ['CRL', 'CIA', 'BGY', 'TPS','DUB','STN','LPL'],
    'OSR' : ['BGY', 'STN'],
}

cz_dests = set([destination for destinations in czech_ryanair.values() for destination in destinations])
print("Destinations from CZ:", cz_dests)

destinations = set()
for _, v in czech_ryanair.items():
    destinations = destinations | set(v)
destinations