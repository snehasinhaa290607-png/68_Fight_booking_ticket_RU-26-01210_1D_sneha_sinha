# Fight-booking-ticket-
class Flight:
    def __init__(self, no, origin, dest, seats, fare):
        self.no = no
        self.origin = origin
        self.dest = dest
        self.seats = seats
        self.fare = fare

    def book_seat(self, n):
        self.seats -= n

    def cancel_seat(self, n):
        self.seats += n


count = 0


def create_csv():
    if not os.path.exists("flights.csv"):
        f = open("flights.csv", "w")
        f.write("FlightNo,Origin,Destination,Seats,Fare\n")
        f.write("AI101,Raipur,Delhi,5,6000\n")
        f.write("AI202,Raipur,Mumbai,2,5500\n")
        f.write("AI303,Delhi,Mumbai,0,4800\n")
        f.close()


def load_data():
    flight_list = []
    f = open("flights.csv")
    data = f.readlines()
    f.close()
    for line in data[1:]:
        x = line.strip().split(",")
        flight_list.append(Flight(x[0], x[1], 
x[2], int(x[3]), int(x[4])))
    return flight_list


def search_flight(flight_list):
    origin = input("Origin: ").lower().strip()
    dest = input("Destination: ").lower().strip()
    found = False
    for fl in flight_list:
        if fl.origin.lower() == origin and fl.dest.lower() == dest:
            print(f"{fl.no} | {fl.origin} -> {fl.dest} | Seats: {fl.seats} | Fare: Rs. {fl.fare} per seat")
            found = True
    if not found:
        print("No flights found.")


def book_flight(flight_list, booking_list):
    global count
    no = input("Flight: ").lower().strip()
    chosen = None
    for fl in flight_list:
        if fl.no.lower() == no:
            chosen = fl
    if chosen is None:
        print("Flight not found.")
        return
    name = input("Passenger: ").strip()
    seats = int(input("Seats: "))
    if seats < 1:
        print("Number of seats must be at least 1.")
    elif chosen.seats == 0:
        print(f"Flight {chosen.no} is full.")
    elif seats > chosen.seats:
        print(f"Only {chosen.seats} seat(s) available on {chosen.no}.")
    else:
        chosen.book_seat(seats)
        count += 1
        bid = "BK" + str(count)
        total = seats * chosen.fare
        booking_list.append([bid, name, chosen, seats])
        print(f"Booking confirmed. ID: {bid} | {name} | {chosen.no} | {seats} seat(s) | Total: Rs. {total} | Seats left: {chosen.seats}")


def cancel_booking(booking_list):
    bid = input("Booking ID: ").upper().strip()
    found = False
    for b in booking_list:
        if b[0] == bid:
            b[2].cancel_seat(b[3])
            print(f"Booking {bid} cancelled. Seats left on {b[2].no}: {b[2].seats}")
            booking_list.remove(b)
            found = True
            break
    if not found:
        print("Booking not found.")


def main():
    create_csv()
    flight_list = load_data()
    booking_list = []
    while True:
        print("\n1. Search flights")
        print("2. Book")
        print("3. Cancel booking")
        print("4. Exit")
        ch = input("Menu: ")
        if ch == "1":
            search_flight(flight_list)
        elif ch == "2":
            book_flight(flight_list, booking_list)
        elif ch == "3":
            cancel_booking(booking_list)
        elif ch == "4":
            print("Thank you.")
            break
        else:
            print("Invalid choice.")


main()
